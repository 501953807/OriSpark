"""HTTP-level integration tests for Enforcement router endpoints."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

import pytest


# ── helpers to set up minimal data chain ────────────────────────────


def _ensure_enforcement_tables(db):
    """Ensure enforcement-related tables exist (conftest may skip them)."""
    from sqlalchemy import text

    db.execute(text("""
        CREATE TABLE IF NOT EXISTS enforcement_actions (
            id TEXT PRIMARY KEY,
            monitor_result_id TEXT NOT NULL REFERENCES monitor_results(id),
            action_type TEXT NOT NULL DEFAULT 'platform_complaint',
            platform TEXT NOT NULL DEFAULT 'generic',
            status TEXT NOT NULL DEFAULT 'pending_review',
            complaint_text TEXT,
            template_used TEXT,
            sent_at DATETIME,
            response_text TEXT,
            resolved_at DATETIME,
            resolution_type TEXT,
            compensation_amount REAL,
            notes TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """))
    db.execute(text("""
        CREATE TABLE IF NOT EXISTS enforcement_templates (
            id TEXT PRIMARY KEY,
            platform TEXT NOT NULL DEFAULT 'generic',
            jurisdiction TEXT NOT NULL DEFAULT 'global',
            action_type TEXT NOT NULL DEFAULT 'copyright',
            title TEXT NOT NULL,
            body_template TEXT NOT NULL,
            required_evidence JSON,
            filing_url TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """))
    db.execute(text("""
        CREATE TABLE IF NOT EXISTS complaint_materials (
            id TEXT PRIMARY KEY,
            enforcement_action_id TEXT NOT NULL REFERENCES enforcement_actions(id),
            material_type TEXT,
            material_path TEXT,
            variables JSON,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """))
    db.commit()


def _seed_templates(db):
    """Seed 3 default enforcement templates."""
    from app.models.enforcement import EnforcementTemplate

    existing = db.query(EnforcementTemplate).count()
    if existing > 0:
        return existing

    templates_data = [
        {
            "id": "tpl-dmca",
            "platform": "generic",
            "jurisdiction": "us",
            "action_type": "dmca",
            "title": "DMCA Takedown Notice",
            "body_template": (
                "To Whom It May Concern,\n\n"
                "I have a good faith belief that the use of the material '{{work_title}}' "
                "on your platform constitutes copyright infringement.\n\n"
                "Work Details:\n"
                "- Title: {{work_title}}\n"
                "- Hash: {{sha256}}\n"
                "- File Type: {{work_file_type}}\n"
                "- Date: {{date}}\n\n"
                "Infringing URL: {{infringement_url}}\n\n"
                "This work was created by and is owned by the undersigned. "
                "The information provided is accurate and I consent to penalties for perjury.\n\n"
                "Sincerely,\n{{author}}"
            ),
            "required_evidence": ["work_ownership_proof", "infringement_url", "identity_verification"],
            "filing_url": "https://www.copyright.gov/online/notice.html",
        },
        {
            "id": "tpl-xhs",
            "platform": "xiaohongshu",
            "jurisdiction": "cn",
            "action_type": "copyright",
            "title": "网络著作权侵权投诉通知书",
            "body_template": "贵平台您好，\n\n本人系作品《{{work_title}}》的著作权人。",
            "required_evidence": ["身份证明", "权属证明", "侵权链接"],
            "filing_url": "",
        },
        {
            "id": "tpl-ig",
            "platform": "instagram",
            "jurisdiction": "us",
            "action_type": "copyright",
            "title": "Instagram Copyright Report",
            "body_template": "I have a good faith belief that the use of the material '{{work_title}}' on Instagram infringes my copyright.",
            "required_evidence": ["work_ownership_proof", "infringing_url"],
            "filing_url": "https://www.facebook.com/help/contact/260749600972847",
        },
    ]

    for td in templates_data:
        tpl = EnforcementTemplate(**td)
        db.add(tpl)
    db.commit()
    return len(templates_data)


class TestCreateAction:
    """POST /api/enforcement/actions"""

    def test_create_action_success(self, client, db_session):
        """Create an action from a valid monitor_result_id."""
        _ensure_enforcement_tables(db_session)
        _, mr_id = _create_monitor_chain(db_session)

        resp = client.post(
            "/api/enforcement/actions",
            json={
                "monitor_result_id": mr_id,
                "action_type": "dmca_notice",
                "platform": "generic",
            },
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["id"] is not None
        assert data["action_type"] == "dmca_notice"
        assert data["status"] == "pending_review"

    def test_create_action_missing_monitor_result(self, client):
        """Non-existent monitor_result_id returns 404."""
        resp = client.post(
            "/api/enforcement/actions",
            json={
                "monitor_result_id": "nonexistent-mr-999",
                "action_type": "dmca_notice",
                "platform": "generic",
            },
        )
        assert resp.status_code == 404

    def test_create_action_with_template(self, client, db_session):
        """Create action referencing a template."""
        _ensure_enforcement_tables(db_session)
        _, mr_id = _create_monitor_chain(db_session)
        _seed_templates(db_session)

        resp = client.post(
            "/api/enforcement/actions",
            json={
                "monitor_result_id": mr_id,
                "action_type": "dmca_notice",
                "platform": "generic",
                "template_id": "tpl-dmca",
            },
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["template_used"] == "DMCA Takedown Notice"


class TestGetAction:
    """GET /api/enforcement/actions/{action_id}"""

    def test_get_existing_action(self, client, db_session):
        """Fetch an existing action."""
        _ensure_enforcement_tables(db_session)
        _, mr_id = _create_monitor_chain(db_session)

        from app.models.enforcement import EnforcementAction

        action = EnforcementAction(
            id="act-get-001",
            monitor_result_id=mr_id,
            action_type="platform_complaint",
            platform="baidu",
            status="pending_review",
        )
        db_session.add(action)
        db_session.commit()

        resp = client.get(f"/api/enforcement/actions/{action.id}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == action.id
        assert data["action_type"] == "platform_complaint"

    def test_get_nonexistent_action(self, client):
        """Fetch a non-existent action returns 404."""
        resp = client.get("/api/enforcement/actions/nonexistent-act-999")
        assert resp.status_code == 404


class TestUpdateAction:
    """PATCH /api/enforcement/actions/{action_id}"""

    def test_update_status_to_complaint_filed(self, client, db_session):
        """Transition action status to complaint_filed."""
        _ensure_enforcement_tables(db_session)
        _, mr_id = _create_monitor_chain(db_session)

        from app.models.enforcement import EnforcementAction

        action = EnforcementAction(
            id="act-patch-001",
            monitor_result_id=mr_id,
            action_type="dmca_notice",
            platform="generic",
            status="evidence_gathered",
        )
        db_session.add(action)
        db_session.commit()

        resp = client.patch(
            f"/api/enforcement/actions/{action.id}",
            json={"status": "complaint_filed"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "complaint_filed"

    def test_update_status_to_resolved(self, client, db_session):
        """Transition action to resolved."""
        _ensure_enforcement_tables(db_session)
        _, mr_id = _create_monitor_chain(db_session)

        from app.models.enforcement import EnforcementAction

        action = EnforcementAction(
            id="act-resolve-001",
            monitor_result_id=mr_id,
            action_type="dmca_notice",
            platform="generic",
            status="complaint_filed",
        )
        db_session.add(action)
        db_session.commit()

        resp = client.patch(
            f"/api/enforcement/actions/{action.id}",
            json={"status": "resolved", "resolution_type": "takedown"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "resolved"
        assert data["resolution_type"] == "takedown"

    def test_update_non_status_fields(self, client, db_session):
        """Update non-status fields like complaint_text and notes."""
        _ensure_enforcement_tables(db_session)
        _, mr_id = _create_monitor_chain(db_session)

        from app.models.enforcement import EnforcementAction

        action = EnforcementAction(
            id="act-fields-001",
            monitor_result_id=mr_id,
            action_type="dmca_notice",
            platform="generic",
            status="pending_review",
        )
        db_session.add(action)
        db_session.commit()

        resp = client.patch(
            f"/api/enforcement/actions/{action.id}",
            json={
                "complaint_text": "Custom complaint text",
                "notes": "Special handling requested",
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["complaint_text"] == "Custom complaint text"
        assert data["notes"] == "Special handling requested"

    def test_update_nonexistent_action(self, client):
        """Updating a non-existent action returns 404."""
        resp = client.patch(
            "/api/enforcement/actions/nonexistent-act-999",
            json={"status": "confirmed"},
        )
        assert resp.status_code == 404


class TestGatherEvidence:
    """POST /api/enforcement/actions/{action_id}/evidence"""

    def test_gather_evidence_success(self, client, db_session):
        """Gather evidence package for an existing action."""
        _ensure_enforcement_tables(db_session)
        work_id, mr_id = _create_monitor_chain(db_session)

        from app.models.enforcement import EnforcementAction

        action = EnforcementAction(
            id="act-evidence-001",
            monitor_result_id=mr_id,
            action_type="dmca_notice",
            platform="generic",
            status="confirmed",
        )
        db_session.add(action)
        db_session.commit()

        resp = client.post(f"/api/enforcement/actions/{action.id}/evidence")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "evidence_gathered"
        assert "material_path" in data
        assert "evidence" in data

    def test_gather_evidence_nonexistent_action(self, client):
        """Gathering evidence for a non-existent action returns 404."""
        resp = client.post("/api/enforcement/actions/nonexistent-act-999/evidence")
        assert resp.status_code == 404


class TestSubmitComplaint:
    """POST /api/enforcement/actions/{action_id}/submit"""

    def test_submit_complaint_success(self, client, db_session):
        """Submit a complaint for an existing action."""
        _ensure_enforcement_tables(db_session)
        _, mr_id = _create_monitor_chain(db_session)

        from app.models.enforcement import EnforcementAction

        action = EnforcementAction(
            id="act-submit-001",
            monitor_result_id=mr_id,
            action_type="dmca_notice",
            platform="generic",
            status="evidence_gathered",
        )
        db_session.add(action)
        db_session.commit()

        resp = client.post(f"/api/enforcement/actions/{action.id}/submit")
        assert resp.status_code == 200
        data = resp.json()
        assert data["action_id"] == action.id
        assert "complaint_text" in data
        assert data["status"] == "complaint_filed"

    def test_submit_complaint_nonexistent_action(self, client):
        """Submitting complaint for a non-existent action returns 404."""
        resp = client.post("/api/enforcement/actions/nonexistent-act-999/submit")
        assert resp.status_code == 404


class TestListTemplates:
    """GET /api/enforcement/templates"""

    def test_templates_empty(self, client):
        """No templates — returns empty list."""
        resp = client.get("/api/enforcement/templates")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) == 0

    def test_templates_with_data(self, client, db_session):
        """Templates exist — returns them."""
        _ensure_enforcement_tables(db_session)
        _seed_templates(db_session)

        resp = client.get("/api/enforcement/templates")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) >= 3

    def test_templates_filter_by_platform(self, client, db_session):
        """Filter templates by platform."""
        _ensure_enforcement_tables(db_session)
        _seed_templates(db_session)

        resp = client.get("/api/enforcement/templates", params={"platform": "xiaohongshu"})
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) >= 1
        assert data[0]["platform"] == "xiaohongshu"

    def test_templates_filter_by_jurisdiction(self, client, db_session):
        """Filter templates by jurisdiction."""
        _ensure_enforcement_tables(db_session)
        _seed_templates(db_session)

        resp = client.get("/api/enforcement/templates", params={"jurisdiction": "cn"})
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) >= 1
        assert data[0]["jurisdiction"] == "cn"

    def test_templates_combined_filters(self, client, db_session):
        """Filter by both platform and jurisdiction."""
        _ensure_enforcement_tables(db_session)
        _seed_templates(db_session)

        resp = client.get(
            "/api/enforcement/templates",
            params={"platform": "xiaohongshu", "jurisdiction": "cn"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) >= 1
        assert data[0]["platform"] == "xiaohongshu"
        assert data[0]["jurisdiction"] == "cn"


class TestSeedTemplates:
    """POST /api/enforcement/templates/seed"""

    def test_seed_templates_success(self, client, db_session):
        """Seed templates when none exist."""
        _ensure_enforcement_tables(db_session)

        # Make sure no templates exist
        from app.models.enforcement import EnforcementTemplate
        db_session.query(EnforcementTemplate).delete()
        db_session.commit()

        resp = client.post("/api/enforcement/templates/seed")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "seeded"
        assert data["count"] == 3

    def test_seed_templates_already_seeded(self, client, db_session):
        """Seeding when templates already exist returns skipped."""
        _ensure_enforcement_tables(db_session)
        _seed_templates(db_session)

        resp = client.post("/api/enforcement/templates/seed")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "skipped"


class TestCreateActionFromWork:
    """POST /api/enforcement/actions/from-work/{work_id}"""

    def test_from_work_no_matches(self, client):
        """Work with no monitor results returns empty actions."""
        resp = client.post("/api/enforcement/actions/from-work/nonexistent-work-999")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] in ("no_matches", "matches_found", "already_enforced")

    def test_from_work_with_monitor_chain(self, client, db_session):
        """Work with monitor results can generate actions."""
        _ensure_enforcement_tables(db_session)
        work_id, mr_id = _create_monitor_chain(db_session)

        resp = client.post(f"/api/enforcement/actions/from-work/{work_id}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] in ("matches_found", "already_enforced")


class TestListActionsByWork:
    """GET /api/enforcement/actions/by-work/{work_id}"""

    def test_by_work_no_actions(self, client):
        """Work with no linked actions returns empty list."""
        resp = client.get("/api/enforcement/actions/by-work/nonexistent-work-999")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) == 0

    def test_by_work_with_actions(self, client, db_session):
        """Work with linked actions returns them."""
        _ensure_enforcement_tables(db_session)
        work_id, mr_id = _create_monitor_chain(db_session)

        from app.models.enforcement import EnforcementAction

        action = EnforcementAction(
            id="act-bywork-001",
            monitor_result_id=mr_id,
            action_type="dmca_notice",
            platform="generic",
            status="pending_review",
        )
        db_session.add(action)
        db_session.commit()

        resp = client.get(f"/api/enforcement/actions/by-work/{work_id}")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        assert data[0]["action_type"] == "dmca_notice"


# ── fixtures ────────────────────────────────────────────────────────


def _create_monitor_chain(db_session):
    """Create Work -> MonitorTask -> MonitorResult chain. Returns (work_id, monitor_result_id)."""
    from app.models.work import Work
    from app.models.monitor import MonitorTask, MonitorResult

    work = Work(
        title="Test Artwork",
        file_path="/tmp/test_art.png",
        file_name="test_art.png",
        file_size=10240,
        file_type="image",
        file_extension="png",
        sha256="abc123def456" * 4,
        status="active",
    )
    db_session.add(work)
    db_session.commit()
    db_session.refresh(work)

    task = MonitorTask(
        work_id=work.id,
        platform="baidu",
        search_type="image",
    )
    db_session.add(task)
    db_session.commit()
    db_session.refresh(task)

    result = MonitorResult(
        task_id=task.id,
        matched_url="http://example.com/stolen",
        matched_title="Stolen Artwork",
        similarity=95.5,
        status="infringing",
    )
    db_session.add(result)
    db_session.commit()
    db_session.refresh(result)

    return work.id, result.id
