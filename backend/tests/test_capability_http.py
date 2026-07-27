"""HTTP-level integration tests for Creator Capability Assessment router."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

import pytest


class TestListDimensions:
    """GET /capability/dimensions"""

    def test_dimensions_empty(self, client):
        resp = client.get("/api/capability/dimensions")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)

    def test_dimensions_with_data(self, client, db_session):
        from app.models.capability import CapabilityDimension
        dim = CapabilityDimension(
            dimension_key="artistic_skill",
            name_zh="艺术技能",
            description="Creativity and artistic ability",
            weight=1.5,
            is_active=True,
        )
        db_session.add(dim)
        db_session.commit()

        resp = client.get("/api/capability/dimensions")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        assert data[0]["dimension_key"] == "artistic_skill"
        assert data[0]["is_active"] is True

    def test_dimensions_filters_inactive(self, client, db_session):
        from app.models.capability import CapabilityDimension
        active_dim = CapabilityDimension(
            dimension_key="active_dim",
            name_zh="Active Dimension",
            is_active=True,
        )
        inactive_dim = CapabilityDimension(
            dimension_key="inactive_dim",
            name_zh="Inactive Dimension",
            is_active=False,
        )
        db_session.add_all([active_dim, inactive_dim])
        db_session.commit()

        resp = client.get("/api/capability/dimensions")
        assert resp.status_code == 200
        data = resp.json()
        keys = [d["dimension_key"] for d in data]
        assert "active_dim" in keys
        assert "inactive_dim" not in keys


class TestPostAssessment:
    """POST /capability/assessments"""

    def test_assessment_success(self, client):
        resp = client.post(
            "/api/capability/assessments",
            json={"dimension_scores": {"artistic_skill": 80, "market_awareness": 60}},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "id" in data
        assert "user_id" in data
        assert "overall_score" in data
        assert "dimension_scores" in data
        assert "created_at" in data

    def test_assessment_empty_scores(self, client):
        resp = client.post(
            "/api/capability/assessments",
            json={"dimension_scores": {}},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "id" in data

    def test_assessment_single_dimension(self, client):
        resp = client.post(
            "/api/capability/assessments",
            json={"dimension_scores": {"drawing": 95}},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["dimension_scores"]["drawing"] == 95.0


class TestCalcPremium:
    """POST /capability/premium"""

    def test_premium_single_skill(self, client):
        resp = client.post(
            "/api/capability/premium",
            json={"skills": ["drawing"], "years_experience": 3, "work_count": 20},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "premium_percent" in data
        assert "breakdown" in data
        assert data["premium_percent"] >= 0

    def test_premium_multiple_skills(self, client):
        resp = client.post(
            "/api/capability/premium",
            json={"skills": ["drawing", "painting", "sculpture"], "years_experience": 5, "work_count": 50},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["premium_percent"] > 0
        assert len(data["breakdown"]) > 0

    def test_premium_many_skills(self, client):
        resp = client.post(
            "/api/capability/premium",
            json={"skills": ["a", "b", "c", "d", "e", "f", "g"], "years_experience": 10, "work_count": 100},
        )
        assert resp.status_code == 200
        data = resp.json()
        # More skills should yield higher premium
        assert data["premium_percent"] > 0


class TestPredictAIRisk:
    """POST /capability/ai-risk"""

    def test_ai_risk_high_execution(self, client):
        resp = client.post(
            "/api/capability/ai-risk",
            json={
                "current_skills": ["basic_drawing", "color_mixing"],
                "work_type": "illustration",
                "experience_years": 2,
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "risk_level" in data
        assert "risk_score" in data
        assert "vulnerable_skills" in data
        assert "moat_building_tips" in data
        assert data["risk_level"] in ("low", "medium", "high")

    def test_ai_risk_creative_work(self, client):
        resp = client.post(
            "/api/capability/ai-risk",
            json={
                "current_skills": ["brand_identity", "art_direction"],
                "work_type": "design",
                "experience_years": 5,
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["risk_level"] in ("low", "medium", "high")

    def test_ai_risk_unknown_work_type(self, client):
        resp = client.post(
            "/api/capability/ai-risk",
            json={
                "current_skills": ["photography"],
                "work_type": "unknown_type_xyz",
                "experience_years": 1,
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "risk_level" in data


class TestGetStageRecommendation:
    """GET /capability/stage-recommendation"""

    def test_stage_beginner(self, client):
        resp = client.get("/api/capability/stage-recommendation", params={"score": 15})
        assert resp.status_code == 200
        data = resp.json()
        assert data["stage_key"] == "beginner"

    def test_stage_intermediate(self, client):
        resp = client.get("/api/capability/stage-recommendation", params={"score": 40})
        assert resp.status_code == 200
        data = resp.json()
        assert data["stage_key"] == "intermediate"

    def test_stage_advanced(self, client):
        resp = client.get("/api/capability/stage-recommendation", params={"score": 70})
        assert resp.status_code == 200
        data = resp.json()
        assert data["stage_key"] == "advanced"

    def test_stage_expert(self, client):
        resp = client.get("/api/capability/stage-recommendation", params={"score": 90})
        assert resp.status_code == 200
        data = resp.json()
        assert data["stage_key"] == "expert"

    def test_stage_boundary_low(self, client):
        resp = client.get("/api/capability/stage-recommendation", params={"score": 0})
        assert resp.status_code == 200

    def test_stage_boundary_high(self, client):
        resp = client.get("/api/capability/stage-recommendation", params={"score": 100})
        assert resp.status_code == 200
