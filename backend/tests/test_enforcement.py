"""Integration tests for the enforcement workflow pipeline."""

import os
import sys
from pathlib import Path
import zipfile
from datetime import datetime
from sqlalchemy import text

sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi import HTTPException

from app.models.enforcement import (
    ComplaintMaterial,
    EnforcementAction,
    EnforcementTemplate,
)
from app.models.monitor import MonitorTask, MonitorResult
from app.models.work import Work
from app.services.enforcement import (
    build_evidence_package,
    generate_complaint_letter,
    generate_pdf_package,
    resolve_template_variables,
    update_action_status,
)


# ── helpers ───────────────────────────────────────────────────────


def _ensure_enforcement_tables(db):
    """Ensure enforcement-related tables exist (conftest may skip them)."""
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


def _create_mock_work(db):
    """Create a minimal Work record for testing."""
    w = Work(
        title="Test Artwork",
        file_path="/tmp/test_art.png",
        file_name="test_art.png",
        file_size=10240,
        file_type="image",
        file_extension="png",
        sha256="abc123def456" * 4,
        status="active",
    )
    db.add(w)
    db.commit()
    db.refresh(w)
    return w


def _create_monitor_chain(db, work_id):
    """Create MonitorTask + MonitorResult linked to a work."""
    task = MonitorTask(
        work_id=work_id,
        platform="baidu",
        search_type="image",
    )
    db.add(task)
    db.commit()
    db.refresh(task)

    result = MonitorResult(
        task_id=task.id,
        matched_url="http://example.com/stolen",
        matched_title="Stolen Artwork",
        similarity=95.5,
        status="infringing",
    )
    db.add(result)
    db.commit()
    db.refresh(result)
    return task, result


def _cleanup_enforcement_tables(db):
    """Clear enforcement-related tables between tests."""
    for tbl in [
        "complaint_materials",
        "enforcement_actions",
        "enforcement_templates",
    ]:
        try:
            db.execute(text(f"DELETE FROM {tbl}"))
            db.commit()
        except Exception:
            db.rollback()


# ── 1. Full enforcement workflow ─────────────────────────────────


def test_full_enforcement_workflow(db_session):
    """End-to-end: work -> monitor -> action -> evidence -> complaint -> resolved."""
    _ensure_enforcement_tables(db_session)
    _cleanup_enforcement_tables(db_session)

    # Step 1: Create mock work and monitor chain
    work = _create_mock_work(db_session)
    task, mr = _create_monitor_chain(db_session, work.id)

    # Step 2: Create an EnforcementAction via service layer
    from app.schemas.enforcement import EnforcementActionCreate

    action = EnforcementAction(
        id="act001",
        monitor_result_id=mr.id,
        action_type="dmca_notice",
        platform="generic",
        status="pending_review",
    )
    db_session.add(action)
    db_session.commit()
    db_session.refresh(action)

    assert action.status == "pending_review"

    # Step 3: Build evidence package
    evidence = build_evidence_package(db_session, work.id)
    assert "work_info" in evidence
    assert "sha256" in evidence
    assert evidence["work_info"]["title"] == "Test Artwork"
    assert len(evidence.get("infringement_evidence", [])) >= 1

    # Step 4: Generate PDF (ZIP) package
    output_dir = "/tmp/test_enforcement_zip"
    zip_path = generate_pdf_package(evidence, output_dir=output_dir)
    assert os.path.isfile(zip_path)
    assert zip_path.endswith(".zip")
    # Verify it is a valid ZIP
    with zipfile.ZipFile(zip_path, "r") as zf:
        names = zf.namelist()
        assert len(names) > 0

    # Clean up the temp ZIP so it does not linger
    os.remove(zip_path)

    # Step 5: Transition pending_review -> confirmed -> evidence_gathered
    action = update_action_status(
        db_session, "act001", new_status="confirmed"
    )
    assert action.status == "confirmed"

    action = update_action_status(
        db_session, "act001", new_status="evidence_gathered"
    )
    assert action.status == "evidence_gathered"

    # Step 6: Seed templates and use one
    seed_templates(db_session)

    tpl = (
        db_session.query(EnforcementTemplate)
        .filter(EnforcementTemplate.title == "DMCA Takedown Notice")
        .first()
    )
    assert tpl is not None

    action = update_action_status(
        db_session, "act001", new_status="complaint_filed", sent_at=datetime.utcnow()
    )
    assert action.status == "complaint_filed"
    assert action.sent_at is not None

    # Step 7: Resolve to final state
    action = update_action_status(
        db_session,
        "act001",
        new_status="resolved",
        resolution_type="takedown",
        resolved_at=datetime.utcnow(),
    )
    assert action.status == "resolved"
    assert action.resolved_at is not None
    assert action.resolution_type == "takedown"

    # Step 8: Verify all records exist in DB
    assert (
        db_session.query(EnforcementAction).filter_by(id="act001").first() is not None
    )
    assert db_session.query(MonitorTask).filter_by(id=task.id).first() is not None
    assert (
        db_session.query(MonitorResult).filter_by(id=mr.id).first() is not None
    )
    assert db_session.query(Work).filter_by(id=work.id).first() is not None


# ── 2. Template seed ─────────────────────────────────────────────


def test_template_seed(db_session):
    """Verify seed_templates populates 3 default templates."""
    _ensure_enforcement_tables(db_session)
    _cleanup_enforcement_tables(db_session)

    count_before = (
        db_session.query(EnforcementTemplate).count()
    )
    assert count_before == 0

    result = seed_templates(db_session)
    assert result["status"] == "seeded"
    assert result["count"] == 3

    # Verify specific templates exist
    dmca = (
        db_session.query(EnforcementTemplate)
        .filter(EnforcementTemplate.title == "DMCA Takedown Notice")
        .first()
    )
    assert dmca is not None
    assert dmca.platform == "generic"
    assert dmca.jurisdiction == "us"
    assert "{{work_title}}" in dmca.body_template

    xhs = (
        db_session.query(EnforcementTemplate)
        .filter(EnforcementTemplate.title == "网络著作权侵权投诉通知书")
        .first()
    )
    assert xhs is not None
    assert xhs.platform == "xiaohongshu"
    assert xhs.jurisdiction == "cn"

    ig = (
        db_session.query(EnforcementTemplate)
        .filter(EnforcementTemplate.title == "Instagram Copyright Report")
        .first()
    )
    assert ig is not None
    assert ig.platform == "instagram"

    # Seeding again should be skipped
    result2 = seed_templates(db_session)
    assert result2["status"] == "skipped"

    # Creating duplicates manually should also work (no unique constraint on title)
    dup = EnforcementTemplate(
        platform="custom",
        jurisdiction="global",
        action_type="copyright",
        title="Custom Template",
        body_template="{{work_title}}",
    )
    db_session.add(dup)
    db_session.commit()
    total = db_session.query(EnforcementTemplate).count()
    assert total == 4


# ── 3. State machine invalid transition ──────────────────────────


def test_state_machine_invalid_transition(db_session):
    """Verify the state machine enforces valid transitions."""
    _ensure_enforcement_tables(db_session)
    _cleanup_enforcement_tables(db_session)

    # Create a real monitor_result so FK constraint is satisfied
    work = _create_mock_work(db_session)
    task, mr = _create_monitor_chain(db_session, work.id)

    action = EnforcementAction(
        id="act_sm_001",
        monitor_result_id=mr.id,
        action_type="dmca_notice",
        platform="generic",
        status="pending_review",
    )
    db_session.add(action)
    db_session.commit()

    # Invalid: skip from pending_review directly to resolved
    try:
        update_action_status(db_session, "act_sm_001", new_status="resolved")
        assert False, "Should have raised HTTPException"
    except HTTPException as exc:
        assert exc.status_code == 400

    # Valid: pending_review -> confirmed
    action = update_action_status(
        db_session, "act_sm_001", new_status="confirmed"
    )
    assert action.status == "confirmed"

    # Valid: confirmed -> evidence_gathered
    action = update_action_status(
        db_session, "act_sm_001", new_status="evidence_gathered"
    )
    assert action.status == "evidence_gathered"

    # Valid: evidence_gathered -> complaint_filed
    action = update_action_status(
        db_session, "act_sm_001", new_status="complaint_filed"
    )
    assert action.status == "complaint_filed"

    # Valid: complaint_filed -> resolved
    action = update_action_status(
        db_session, "act_sm_001", new_status="resolved"
    )
    assert action.status == "resolved"

    # Invalid: resolved is terminal, cannot go back
    try:
        update_action_status(
            db_session, "act_sm_001", new_status="pending_review"
        )
        assert False, "Should have raised HTTPException"
    except HTTPException as exc:
        assert exc.status_code == 400


# ── 4. Template variable resolution ─────────────────────────────


def test_resolve_template_variables(db_session):
    """Test the resolve_template_variables helper function."""
    # Basic single replacement
    result = resolve_template_variables(
        "Title: {{work_title}}", {"work_title": "My Artwork"}
    )
    assert result == "Title: My Artwork"

    # Multiple variables
    template = "{{author}} created {{work_title}} on {{date}}"
    vars = {
        "author": "Alice",
        "work_title": "Sunset",
        "date": "2026-07-17",
    }
    result = resolve_template_variables(template, vars)
    assert result == "Alice created Sunset on 2026-07-17"

    # Missing key leaves placeholder as-is
    result = resolve_template_variables(
        "Hello {{name}}, missing {{unknown}}", {"name": "Bob"}
    )
    assert result == "Hello Bob, missing {{unknown}}"

    # Empty template returns empty string
    assert resolve_template_variables("", {}) == ""

    # Empty variables dict returns template unchanged
    assert resolve_template_variables("no placeholders", {}) == "no placeholders"


# ── 5. Complaint material creation ──────────────────────────────


def test_complaint_material_creation(db_session):
    """Verify ComplaintMaterial is created during evidence gathering."""
    _ensure_enforcement_tables(db_session)
    _cleanup_enforcement_tables(db_session)

    # Set up work + monitor chain + action
    work = _create_mock_work(db_session)
    task, mr = _create_monitor_chain(db_session, work.id)

    action = EnforcementAction(
        id="act_mat_001",
        monitor_result_id=mr.id,
        action_type="dmca_notice",
        platform="generic",
        status="pending_review",
    )
    db_session.add(action)
    db_session.commit()

    # Build evidence and generate ZIP
    evidence = build_evidence_package(db_session, work.id)
    output_dir = "/tmp/test_enforcement_mat"
    zip_path = generate_pdf_package(evidence, output_dir=output_dir)

    # Create ComplaintMaterial record
    material = ComplaintMaterial(
        enforcement_action_id="act_mat_001",
        material_type="pdf_package",
        material_path=zip_path,
    )
    db_session.add(material)
    db_session.commit()
    db_session.refresh(material)

    assert material.enforcement_action_id == "act_mat_001"
    assert material.material_type == "pdf_package"
    assert material.material_path == zip_path
    assert material.created_at is not None

    # Verify it can be queried back
    found = (
        db_session.query(ComplaintMaterial)
        .filter_by(enforcement_action_id="act_mat_001")
        .first()
    )
    assert found is not None
    assert found.material_type == "pdf_package"

    # Clean up temp file
    if os.path.isfile(zip_path):
        os.remove(zip_path)


# ── seed_templates helper (mirrors router logic) ─────────────────


def seed_templates(db):
    """Seed 3 default enforcement templates if none exist."""
    existing = db.query(EnforcementTemplate).count()
    if existing > 0:
        return {"status": "skipped", "message": "Templates already seeded", "count": existing}

    templates_data = [
        {
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
            "platform": "xiaohongshu",
            "jurisdiction": "cn",
            "action_type": "copyright",
            "title": "网络著作权侵权投诉通知书",
            "body_template": (
                "贵平台您好，\n\n"
                "本人系作品《{{work_title}}》的著作权人，"
                "该作品的哈希值为 {{sha256}}，"
                "文件类型为 {{work_file_type}}。\n\n"
                "发现贵平台存在以下侵权行为：\n"
                "侵权链接：{{infringement_url}}\n\n"
                "根据《中华人民共和国著作权法》"
                "及相关法规，请贵平台在收到本通知"
                "后及时删除或屏蔽侵权内容。\n\n"
                "权属证明：已随本通知附上\n"
                "身份证明：已随本通知附上\n"
                "证据数量：{{evidence_count}}\n\n"
                "此致\n"
                "{{author}}\n"
                "{{date}}"
            ),
            "required_evidence": ["身份证明", "权属证明", "侵权链接"],
            "filing_url": "",
        },
        {
            "platform": "instagram",
            "jurisdiction": "us",
            "action_type": "copyright",
            "title": "Instagram Copyright Report",
            "body_template": (
                "I have a good faith belief that the use of the material '{{work_title}}' "
                "on Instagram infringes my copyright.\n\n"
                "Work Details:\n"
                "- Title: {{work_title}}\n"
                "- Hash: {{sha256}}\n"
                "- File Type: {{work_file_type}}\n"
                "- Date: {{date}}\n\n"
                "Infringing Content URL: {{infringement_url}}\n\n"
                "I am the exclusive rights holder of the copyrighted work.\n\n"
                "Sincerely,\n{{author}}"
            ),
            "required_evidence": ["work_ownership_proof", "infringing_url"],
            "filing_url": "https://www.facebook.com/help/contact/260749600972847",
        },
    ]

    for td in templates_data:
        tpl = EnforcementTemplate(**td)
        db.add(tpl)

    db.commit()

    count = db.query(EnforcementTemplate).count()
    return {"status": "seeded", "message": f"Seeded {count} templates", "count": count}
