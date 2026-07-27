"""HTTP-level integration tests for tax_agent router."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

import pytest


class TestCreateAgent:
    """POST /api/tax/agents"""

    def test_create_agent(self, client):
        resp = client.post(
            "/api/tax/agents",
            json={
                "participant_id": "p1",
                "name": "Test Tax Agent",
                "license_no": "TA-001",
                "service_areas": ["Beijing", "Shanghai"],
                "fee_rate": 0.05,
                "avalara_account_id": "av-123",
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert data["data"]["participant_id"] == "p1"
        assert data["data"]["name"] == "Test Tax Agent"
        assert data["data"]["status"] == "pending"

    def test_create_agent_minimal(self, client):
        """Create with only required fields."""
        resp = client.post(
            "/api/tax/agents",
            json={
                "participant_id": "p2",
                "name": "Minimal Agent",
                "fee_rate": 0.1,
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["data"]["participant_id"] == "p2"
        assert data["data"]["fee_rate"] == 0.1

    def test_create_agent_with_optional_fields(self, client):
        resp = client.post(
            "/api/tax/agents",
            json={
                "participant_id": "p3",
                "name": "Full Agent",
                "license_no": "TA-002",
                "service_areas": [],
                "fee_rate": 0.08,
                "avalara_account_id": None,
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["data"]["service_areas"] == []
        assert data["data"]["avalara_account_id"] is None


class TestListAgents:
    """GET /api/tax/agents"""

    def test_list_agents_empty(self, client):
        resp = client.get("/api/tax/agents")
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert isinstance(data["data"], list)
        assert len(data["data"]) == 0

    def test_list_agents_with_data(self, client, db_session):
        from app.models.tax_settlement import TaxAgent as TaxAgentModel
        agent = TaxAgentModel(
            participant_id="p1",
            name="Existing Agent",
            license_no="TA-EXIST",
            fee_rate=0.05,
            status="active",
        )
        db_session.add(agent)
        db_session.commit()

        resp = client.get("/api/tax/agents")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["data"]) >= 1
        names = [a["name"] for a in data["data"]]
        assert "Existing Agent" in names

    def test_list_agents_filter_by_status(self, client, db_session):
        from app.models.tax_settlement import TaxAgent as TaxAgentModel
        active = TaxAgentModel(
            participant_id="pa", name="Active Agent", fee_rate=0.05, status="active",
        )
        inactive = TaxAgentModel(
            participant_id="pi", name="Inactive Agent", fee_rate=0.05, status="inactive",
        )
        db_session.add_all([active, inactive])
        db_session.commit()

        resp = client.get("/api/tax/agents", params={"status": "active"})
        assert resp.status_code == 200
        data = resp.json()
        names = [a["name"] for a in data["data"]]
        assert "Active Agent" in names
        assert "Inactive Agent" not in names

    def test_list_agents_filter_by_nonexistent_status(self, client):
        resp = client.get("/api/tax/agents", params={"status": "nonexistent"})
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["data"]) == 0


class TestGetAgent:
    """GET /api/tax/agents/{agent_id}"""

    def test_get_existing_agent(self, client, db_session):
        from app.models.tax_settlement import TaxAgent as TaxAgentModel
        agent = TaxAgentModel(
            participant_id="p1",
            name="Get Me",
            license_no="TA-GET",
            fee_rate=0.07,
            status="active",
        )
        db_session.add(agent)
        db_session.commit()

        resp = client.get(f"/api/tax/agents/{agent.id}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["data"]["name"] == "Get Me"
        assert data["data"]["license_no"] == "TA-GET"

    def test_get_nonexistent_agent(self, client):
        resp = client.get("/api/tax/agents/nonexistent-id")
        assert resp.status_code == 404

    def test_get_agent_returns_all_fields(self, client, db_session):
        from app.models.tax_settlement import TaxAgent as TaxAgentModel
        agent = TaxAgentModel(
            participant_id="p1",
            name="Full Fields Agent",
            license_no="TA-FULL",
            service_areas=["CN", "US"],
            fee_rate=0.1,
            avalara_account_id="av-full",
            status="active",
            rating=4.5,
            review_count=10,
        )
        db_session.add(agent)
        db_session.commit()

        resp = client.get(f"/api/tax/agents/{agent.id}")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["id"] == agent.id
        assert data["rating"] == 4.5
        assert data["review_count"] == 10
        assert data["service_areas"] == ["CN", "US"]


class TestUpdateAgent:
    """PATCH /api/tax/agents/{agent_id}"""

    def test_update_agent_fee_rate(self, client, db_session):
        from app.models.tax_settlement import TaxAgent as TaxAgentModel
        agent = TaxAgentModel(
            participant_id="p1",
            name="Update Me",
            fee_rate=0.05,
            status="active",
        )
        db_session.add(agent)
        db_session.commit()

        resp = client.patch(
            f"/api/tax/agents/{agent.id}",
            json={"fee_rate": 0.15},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["data"]["fee_rate"] == 0.15

    def test_update_agent_status(self, client, db_session):
        from app.models.tax_settlement import TaxAgent as TaxAgentModel
        agent = TaxAgentModel(
            participant_id="p1",
            name="Status Update",
            fee_rate=0.05,
            status="active",
        )
        db_session.add(agent)
        db_session.commit()

        resp = client.patch(
            f"/api/tax/agents/{agent.id}",
            json={"status": "suspended"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["data"]["status"] == "suspended"

    def test_update_agent_rating(self, client, db_session):
        from app.models.tax_settlement import TaxAgent as TaxAgentModel
        agent = TaxAgentModel(
            participant_id="p1",
            name="Rate Me",
            fee_rate=0.05,
            status="active",
        )
        db_session.add(agent)
        db_session.commit()

        resp = client.patch(
            f"/api/tax/agents/{agent.id}",
            json={"rating": 4.9},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["data"]["rating"] == 4.9

    def test_update_multiple_fields(self, client, db_session):
        from app.models.tax_settlement import TaxAgent as TaxAgentModel
        agent = TaxAgentModel(
            participant_id="p1",
            name="Multi Update",
            fee_rate=0.05,
            status="active",
        )
        db_session.add(agent)
        db_session.commit()

        resp = client.patch(
            f"/api/tax/agents/{agent.id}",
            json={"status": "active", "rating": 4.0, "fee_rate": 0.12},
        )
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["status"] == "active"
        assert data["rating"] == 4.0
        assert data["fee_rate"] == 0.12

    def test_update_nonexistent_agent(self, client):
        resp = client.patch(
            "/api/tax/agents/nonexistent-id",
            json={"fee_rate": 0.1},
        )
        assert resp.status_code == 404


class TestListReports:
    """GET /api/tax/reports"""

    def test_list_reports_empty(self, client):
        resp = client.get("/api/tax/reports", params={"participant_id": "p1"})
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data["data"], list)
        assert len(data["data"]) == 0

    def test_list_reports_with_data(self, client, db_session):
        from app.models.tax_settlement import TaxReport as TaxReportModel
        report = TaxReportModel(
            participant_id="p1",
            report_period="2026-Q1",
            total_income=10000,
            total_tax_withheld=1000,
            total_tax_owed=500,
            currency="CNY",
            status="draft",
        )
        db_session.add(report)
        db_session.commit()

        resp = client.get("/api/tax/reports", params={"participant_id": "p1"})
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["data"]) >= 1
        assert data["data"][0]["report_period"] == "2026-Q1"
        assert data["data"][0]["total_income"] == 10000.0

    def test_list_reports_different_participant(self, client, db_session):
        from app.models.tax_settlement import TaxReport as TaxReportModel
        report_p1 = TaxReportModel(
            participant_id="p1", report_period="2026-Q1",
            total_income=5000, total_tax_withheld=500, total_tax_owed=200,
            currency="CNY", status="finalized",
        )
        report_p2 = TaxReportModel(
            participant_id="p2", report_period="2026-Q1",
            total_income=8000, total_tax_withheld=800, total_tax_owed=300,
            currency="USD", status="draft",
        )
        db_session.add_all([report_p1, report_p2])
        db_session.commit()

        resp = client.get("/api/tax/reports", params={"participant_id": "p2"})
        assert resp.status_code == 200
        data = resp.json()
        ids = [r["id"] for r in data["data"]]
        assert report_p2.id in ids
        assert report_p1.id not in ids


class TestCreateReport:
    """POST /api/tax/reports"""

    def test_create_report(self, client):
        resp = client.post(
            "/api/tax/reports",
            json={
                "participant_id": "p1",
                "period": "2026-Q2",
                "currency": "CNY",
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert data["data"]["participant_id"] == "p1"
        assert data["data"]["report_period"] == "2026-Q2"
        assert data["data"]["status"] == "draft"

    def test_create_report_default_currency(self, client):
        resp = client.post(
            "/api/tax/reports",
            json={
                "participant_id": "p2",
                "period": "2026-Q3",
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["data"]["currency"] == "CNY"

    def test_create_report_with_usd(self, client):
        resp = client.post(
            "/api/tax/reports",
            json={
                "participant_id": "p3",
                "period": "2026-Q4",
                "currency": "USD",
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["data"]["currency"] == "USD"
