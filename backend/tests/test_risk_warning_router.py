"""Risk Warning Router HTTP-level integration tests."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

import pytest


_BASE = "/api/risk-warning"


class TestCheckRiskWarning:
    """POST /risk-warning/check"""

    def test_check_risk_warning(self, client):
        resp = client.post(f"{_BASE}/check", json={
            "user_id": "local",
            "prompt": "a sunset over mountains",
            "work_title": "Test Work",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "data" in data
        assert isinstance(data["data"], list)


class TestBatchCheckRiskWarning:
    """POST /risk-warning/batch-check"""

    def test_batch_check(self, client):
        resp = client.post(f"{_BASE}/batch-check", json={
            "items": [
                {"prompt": "sunset mountains", "work_title": "Work A"},
                {"prompt": "city skyline", "work_title": "Work B"},
            ],
            "user_id": "local",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "data" in data
        assert isinstance(data["data"], list)


class TestDismissWarning:
    """PATCH /risk-warning/{warning_id}/dismiss"""

    def test_dismiss_nonexistent(self, client):
        resp = client.patch(f"{_BASE}/nonexistent-id/dismiss")
        assert resp.status_code == 404

    def test_dismiss_after_create_warning(self, client, db_session):
        from app.models.risk_warning import RiskWarning
        from datetime import datetime, timedelta
        from app.models.work import Work

        # Ensure a Work exists (FK constraint)
        work_id = "test_work_dismiss"
        _ensure_work(db_session, work_id)

        warning = RiskWarning(
            user_id="local",
            work_id=work_id,
            warning_type="copyright",
            severity="high",
            title="Potential copyright issue",
            description="Similar work found",
            confidence=0.85,
            dismissed=False,
            created_at=datetime.now(timezone.utc) - timedelta(days=1),
        )
        db_session.add(warning)
        db_session.flush()
        warning_id = warning.id

        resp = client.patch(f"{_BASE}/{warning_id}/dismiss")
        assert resp.status_code == 200
        data = resp.json()
        assert data["message"] == "已标记为查看"


class TestCompleteTaxDeadline:
    """PATCH /risk-warning/tax-deadlines/{deadline_id}/complete"""

    def test_complete_nonexistent(self, client):
        resp = client.patch(f"{_BASE}/tax-deadlines/nonexistent-id/complete")
        assert resp.status_code == 404

    def test_complete_tax_deadline(self, client):
        # First create a deadline
        create_resp = client.post(f"{_BASE}/tax-deadlines", json={
            "tax_type": "vat",
            "due_date": "2026-12-31",
            "amount_yuan": 1000.0,
        })
        assert create_resp.status_code == 200
        deadline_id = create_resp.json()["id"]

        resp = client.patch(f"{_BASE}/tax-deadlines/{deadline_id}/complete")
        assert resp.status_code == 200
        data = resp.json()
        assert data["message"] == "已标记完成"


class TestWorkWarnings:
    """GET /risk-warning/work/{work_id}"""

    def test_work_warnings_empty(self, client):
        resp = client.get(f"{_BASE}/work/test_work")
        assert resp.status_code in (200, 404)


class TestListWarnings:
    """GET /risk-warning"""

    def test_list_all(self, client):
        resp = client.get(f"{_BASE}")
        assert resp.status_code == 200
        data = resp.json()
        assert "data" in data
        assert isinstance(data["data"], list)


class TestTaxDeadlines:
    """CRUD for /risk-warning/tax-deadlines"""

    def test_create_tax_deadline(self, client):
        resp = client.post(f"{_BASE}/tax-deadlines", json={
            "tax_type": "income_tax",
            "due_date": "2026-12-31",
            "amount_yuan": 5000.0,
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "id" in data
        assert data["tax_type"] == "income_tax"

    def test_list_tax_deadlines(self, client):
        resp = client.get(f"{_BASE}/tax-deadlines")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)


class TestHealthMetrics:
    """POST /risk-warning/health-metrics"""

    def test_log_health_metric(self, client):
        resp = client.post(f"{_BASE}/health-metrics", json={
            "daily_work_hours": 8.0,
            "works_created": 2,
            "has_break_taken": True,
            "mood_score": 7,
            "recorded_date": "2026-07-20",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "data" in data


class TestBurnoutRisk:
    """GET /risk-warning/burnout-risk"""

    def test_burnout_risk(self, client):
        resp = client.get(f"{_BASE}/burnout-risk")
        assert resp.status_code == 200
        data = resp.json()
        assert "risk_level" in data
        assert "score" in data
        assert "factors" in data
        assert "recommendation" in data


def _ensure_work(db_session, work_id: str) -> None:
    """Ensure a Work row exists for FK constraints."""
    from app.models.work import Work
    existing = db_session.query(Work).filter(Work.id == work_id).first()
    if not existing:
        work = Work(
            id=work_id,
            title="Test Work",
            file_path=f"/tmp/{work_id}.jpg",
            file_name=f"{work_id}.jpg",
            file_size=1024,
            file_extension="jpg",
        )
        db_session.add(work)
        db_session.flush()
