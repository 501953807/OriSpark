"""Tests for commission project CRUD and related endpoints."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.database import SessionLocal


def _create_sample_project(db_session: Session) -> dict:
    """Helper: create a commission project and return its dict representation."""
    from app.models.commission import CommissionProject

    project = CommissionProject(
        user_id="test_user",
        title="Test Commission Project",
        description="A test project",
        client_name="Test Client",
        status="brief",
        payment_terms=[{"name": "50% upfront", "amount": 50.0}],
    )
    db_session.add(project)
    db_session.commit()
    db_session.refresh(project)
    return {
        "id": project.id,
        "title": project.title,
        "user_id": project.user_id,
    }


class TestListProjects:
    def test_returns_paginated_list(self, client: TestClient):
        resp = client.get("/api/commission/projects")
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert "data" in data
        items = data["data"]["items"]
        assert isinstance(items, list)
        assert data["data"]["total"] >= 0

    def test_filters_by_user_id(self, client: TestClient, db_session: Session):
        proj = _create_sample_project(db_session)
        resp = client.get(f"/api/commission/projects?user_id={proj['user_id']}")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["total"] >= 1

    def test_filters_by_status(self, client: TestClient, db_session: Session):
        proj = _create_sample_project(db_session)
        resp = client.get("/api/commission/projects?status=brief")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["total"] >= 1

    def test_empty_when_no_projects(self, client: TestClient):
        resp = client.get("/api/commission/projects?user_id=nonexistent")
        assert resp.status_code == 200
        assert resp.json()["data"]["total"] == 0


class TestCreateProject:
    def test_creates_project(self, client: TestClient, db_session: Session):
        payload = {
            "title": "New Project",
            "user_id": "user_123",
            "description": "Description here",
            "client_name": "ACME Corp",
            "status": "proposal",
            "payment_terms": [{"name": "30%", "amount": 30.0}],
        }
        resp = client.post("/api/commission/projects", json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert data["data"]["title"] == "New Project"
        assert data["data"]["client_name"] == "ACME Corp"
        assert data["message"] == "项目创建成功"

    def test_project_has_generated_id(self, client: TestClient, db_session: Session):
        payload = {"title": "Minimal Project", "user_id": "u1"}
        resp = client.post("/api/commission/projects", json=payload)
        assert resp.status_code == 200
        assert "id" in resp.json()["data"]

    def test_default_status_is_brief(self, client: TestClient, db_session: Session):
        payload = {"title": "Default Status", "user_id": "u2"}
        resp = client.post("/api/commission/projects", json=payload)
        assert resp.status_code == 200
        assert resp.json()["data"]["status"] == "brief"


class TestGetProject:
    def test_returns_project(self, client: TestClient, db_session: Session):
        proj = _create_sample_project(db_session)
        resp = client.get(f"/api/commission/projects/{proj['id']}")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["title"] == "Test Commission Project"

    def test_returns_404_for_missing(self, client: TestClient):
        resp = client.get("/api/commission/projects/nonexistent-id")
        assert resp.status_code == 404


class TestUpdateProject:
    def test_updates_title(self, client: TestClient, db_session: Session):
        proj = _create_sample_project(db_session)
        resp = client.put(
            f"/api/commission/projects/{proj['id']}",
            json={"title": "Updated Title"},
        )
        assert resp.status_code == 200
        assert resp.json()["data"]["title"] == "Updated Title"

    def test_partial_update(self, client: TestClient, db_session: Session):
        proj = _create_sample_project(db_session)
        resp = client.put(
            f"/api/commission/projects/{proj['id']}",
            json={"client_name": "New Client"},
        )
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["client_name"] == "New Client"
        # Original title unchanged
        assert data["title"] == "Test Commission Project"


class TestDeleteProject:
    def test_deletes_project(self, client: TestClient, db_session: Session):
        proj = _create_sample_project(db_session)
        resp = client.delete(f"/api/commission/projects/{proj['id']}")
        assert resp.status_code == 200
        assert resp.json()["data"]["success"] is True

    def test_returns_404_for_missing(self, client: TestClient):
        resp = client.delete("/api/commission/projects/nonexistent-id")
        assert resp.status_code == 404


class TestOrders:
    def test_create_order(self, client: TestClient, db_session: Session):
        proj = _create_sample_project(db_session)
        payload = {"order_type": "design", "amount": 500.0}
        resp = client.post(
            f"/api/commission/projects/{proj['id']}/orders", json=payload
        )
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["order_type"] == "design"
        assert data["amount"] == 500.0

    def test_list_orders(self, client: TestClient, db_session: Session):
        proj = _create_sample_project(db_session)
        client.post(
            f"/api/commission/projects/{proj['id']}/orders",
            json={"order_type": "photo", "amount": 300.0},
        )
        resp = client.get(f"/api/commission/projects/{proj['id']}/orders")
        assert resp.status_code == 200
        assert len(resp.json()["data"]) >= 1

    def test_404_on_missing_project(self, client: TestClient):
        resp = client.post(
            "/api/commission/projects/nonexistent/orders",
            json={"order_type": "design", "amount": 100.0},
        )
        assert resp.status_code == 404


class TestMessages:
    def test_send_message(self, client: TestClient, db_session: Session):
        proj = _create_sample_project(db_session)
        payload = {"sender_id": "user_a", "content": "Hello project!"}
        resp = client.post(
            f"/api/commission/projects/{proj['id']}/messages", json=payload
        )
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["content"] == "Hello project!"
        assert data["sender_id"] == "user_a"

    def test_list_messages(self, client: TestClient, db_session: Session):
        proj = _create_sample_project(db_session)
        client.post(
            f"/api/commission/projects/{proj['id']}/messages",
            json={"sender_id": "u1", "content": "Msg 1"},
        )
        resp = client.get(f"/api/commission/projects/{proj['id']}/messages")
        assert resp.status_code == 200
        assert len(resp.json()["data"]) >= 1


class TestMilestones:
    def test_create_milestone(self, client: TestClient, db_session: Session):
        proj = _create_sample_project(db_session)
        payload = {"name": "Draft Phase", "order_index": 1, "description": "First draft"}
        resp = client.post(
            f"/api/commission/projects/{proj['id']}/milestones", json=payload
        )
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["name"] == "Draft Phase"
        assert data["status"] == "pending"

    def test_list_milestones(self, client: TestClient, db_session: Session):
        proj = _create_sample_project(db_session)
        client.post(
            f"/api/commission/projects/{proj['id']}/milestones",
            json={"name": "M1", "order_index": 1},
        )
        resp = client.get(f"/api/commission/projects/{proj['id']}/milestones")
        assert resp.status_code == 200
        assert len(resp.json()["data"]) >= 1

    def test_update_milestone(self, client: TestClient, db_session: Session):
        proj = _create_sample_project(db_session)
        ms_resp = client.post(
            f"/api/commission/projects/{proj['id']}/milestones",
            json={"name": "Old Name", "order_index": 1},
        )
        mid = ms_resp.json()["data"]["id"]
        resp = client.patch(
            f"/api/commission/projects/{proj['id']}/milestones/{mid}",
            json={"name": "New Name"},
        )
        assert resp.status_code == 200
        assert resp.json()["data"]["name"] == "New Name"

    def test_delete_milestone(self, client: TestClient, db_session: Session):
        proj = _create_sample_project(db_session)
        ms_resp = client.post(
            f"/api/commission/projects/{proj['id']}/milestones",
            json={"name": "To Delete", "order_index": 1},
        )
        mid = ms_resp.json()["data"]["id"]
        resp = client.delete(f"/api/commission/projects/{proj['id']}/milestones/{mid}")
        assert resp.status_code == 200


class TestPayments:
    def test_create_payment(self, client: TestClient, db_session: Session):
        proj = _create_sample_project(db_session)
        payload = {"amount": 250.0, "method": "bank_transfer"}
        resp = client.post(
            f"/api/commission/projects/{proj['id']}/payments", json=payload
        )
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["amount"] == 250.0
        assert data["method"] == "bank_transfer"

    def test_list_payments(self, client: TestClient, db_session: Session):
        proj = _create_sample_project(db_session)
        client.post(
            f"/api/commission/projects/{proj['id']}/payments",
            json={"amount": 100.0, "method": "alipay"},
        )
        resp = client.get(f"/api/commission/projects/{proj['id']}/payments")
        assert resp.status_code == 200
        assert len(resp.json()["data"]) >= 1


class TestRevisions:
    def test_create_revision(self, client: TestClient, db_session: Session):
        proj = _create_sample_project(db_session)
        payload = {
            "description": "Change colors to blue",
            "client_feedback": "Looks good but change colors",
            "created_by": "designer_1",
        }
        resp = client.post(
            f"/api/commission/projects/{proj['id']}/revisions", json=payload
        )
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["description"] == "Change colors to blue"

    def test_list_revisions(self, client: TestClient, db_session: Session):
        proj = _create_sample_project(db_session)
        client.post(
            f"/api/commission/projects/{proj['id']}/revisions",
            json={"description": "Revision 1", "created_by": "u1"},
        )
        resp = client.get(f"/api/commission/projects/{proj['id']}/revisions")
        assert resp.status_code == 200
        assert len(resp.json()["data"]) >= 1


class TestTimeline:
    def test_returns_empty_timeline(self, client: TestClient, db_session: Session):
        proj = _create_sample_project(db_session)
        resp = client.get(f"/api/commission/projects/{proj['id']}/timeline")
        assert resp.status_code == 200
        assert resp.json()["data"] == []


class TestPaymentUpdateDelete:
    """Test PATCH and DELETE for payments."""

    def test_update_payment_status(self, client: TestClient, db_session: Session):
        proj = _create_sample_project(db_session)
        pay_resp = client.post(
            f"/api/commission/projects/{proj['id']}/payments",
            json={"amount": 500.0, "method": "bank_transfer"},
        )
        pid = pay_resp.json()["data"]["id"]
        resp = client.patch(
            f"/api/commission/projects/{proj['id']}/payments/{pid}",
            json={"status": "received"},
        )
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["status"] == "received"

    def test_delete_payment(self, client: TestClient, db_session: Session):
        proj = _create_sample_project(db_session)
        pay_resp = client.post(
            f"/api/commission/projects/{proj['id']}/payments",
            json={"amount": 100.0, "method": "alipay"},
        )
        pid = pay_resp.json()["data"]["id"]
        resp = client.delete(f"/api/commission/projects/{proj['id']}/payments/{pid}")
        assert resp.status_code == 200

    def test_update_missing_payment_returns_404(self, client: TestClient):
        resp = client.patch(
            "/api/commission/projects/fake-id/payments/nonexistent",
            json={"status": "received"},
        )
        assert resp.status_code == 404

    def test_delete_missing_payment_returns_404(self, client: TestClient):
        resp = client.delete("/api/commission/projects/fake-id/payments/nonexistent")
        assert resp.status_code == 404


class TestRevisionDelete:
    """Test DELETE for revisions."""

    def test_delete_revision(self, client: TestClient, db_session: Session):
        proj = _create_sample_project(db_session)
        rev_resp = client.post(
            f"/api/commission/projects/{proj['id']}/revisions",
            json={"description": "Rev 1", "created_by": "u1"},
        )
        rid = rev_resp.json()["data"]["id"]
        resp = client.delete(f"/api/commission/projects/{proj['id']}/revisions/{rid}")
        assert resp.status_code == 200

    def test_delete_missing_revision_returns_404(self, client: TestClient):
        resp = client.delete("/api/commission/projects/fake-id/revisions/nonexistent")
        assert resp.status_code == 404


class TestCalendar:
    """Test commission calendar endpoint."""

    def test_returns_empty_calendar(self, client: TestClient, db_session: Session):
        resp = client.get("/api/commission/calendar")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert "events" in data

    def test_calendar_with_date_range(self, client: TestClient, db_session: Session):
        from datetime import date, timedelta
        today = date.today()
        from_fmt = (today - timedelta(days=30)).isoformat()
        to_fmt = (today + timedelta(days=30)).isoformat()
        resp = client.get(f"/api/commission/calendar?from={from_fmt}&to={to_fmt}")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert "events" in data


class TestDashboard:
    """Test commission dashboard endpoint."""

    def test_returns_dashboard_stats(self, client: TestClient, db_session: Session):
        resp = client.get("/api/commission/dashboard")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert "active_count" in data
        assert "pending_payment" in data
        assert "monthly_revenue" in data
        assert "avg_ticket" in data


class TestBalance:
    """Test commission balance endpoint."""

    def test_returns_balance(self, client: TestClient, db_session: Session):
        resp = client.get("/api/commission/balance")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert "available_yuan" in data
        assert "frozen_yuan" in data
        assert "total_earned_yuan" in data


class TestWithdraw:
    """Test commission withdraw endpoints."""

    def test_create_withdrawal(self, client: TestClient, db_session: Session):
        resp = client.post("/api/commission/withdraw", json={
            "amount_yuan": 100.0,
            "method": "bank_transfer",
            "account_info": {"bank": "ICBC", "account": "123456"},
        })
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert "id" in data
        assert data["status"] == "pending"
        assert data["net_amount_yuan"] < data["amount_yuan"]

    def test_withdraw_invalid_amount(self, client: TestClient):
        resp = client.post("/api/commission/withdraw", json={
            "amount_yuan": -10.0,
        })
        assert resp.status_code == 400

    def test_get_withdrawals(self, client: TestClient, db_session: Session):
        # Create a withdrawal first
        client.post("/api/commission/withdraw", json={
            "amount_yuan": 50.0,
            "method": "alipay",
        })
        resp = client.get("/api/commission/withdrawals?limit=10")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert isinstance(data, list)

    def test_get_withdrawals_filtered(self, client: TestClient, db_session: Session):
        client.post("/api/commission/withdraw", json={
            "amount_yuan": 200.0,
            "method": "bank_transfer",
        })
        resp = client.get("/api/commission/withdrawals?status=pending&limit=10")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert isinstance(data, list)


class TestStatistics:
    """Test commission statistics endpoints."""

    def test_monthly_stats(self, client: TestClient, db_session: Session):
        resp = client.get("/api/commission/statistics/monthly")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert "monthly" in data
        assert "records" in data

    def test_monthly_stats_with_year(self, client: TestClient, db_session: Session):
        resp = client.get("/api/commission/statistics/monthly?year=2026")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert "monthly" in data

    def test_yearly_stats(self, client: TestClient, db_session: Session):
        resp = client.get("/api/commission/statistics/yearly")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert "year" in data
        assert "total_commission" in data
        assert "record_count" in data

    def test_yearly_stats_with_year(self, client: TestClient, db_session: Session):
        resp = client.get("/api/commission/statistics/yearly?year=2025")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["year"] == 2025
