"""Enforcement ROI Router HTTP-level integration tests — covers all 7 endpoints."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

import pytest
from app.models.enforcement_roi import CaseReference


_BASE = "/api/enforcement-roi"


class TestDecisionTree:
    """GET /enforcement-roi/decision-tree"""

    def test_returns_recommended_actions(self, client):
        resp = client.get(f"{_BASE}/decision-tree", params={
            "infringement_type": "platform_copy",
            "loss_amount": 3000.0,
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "recommended_actions" in data
        assert "primary_recommendation" in data
        assert "reasoning" in data

    def test_filters_by_loss_amount(self, client):
        """Low loss (< ¥5K) should exclude civil_lawsuit and criminal_report."""
        resp = client.get(f"{_BASE}/decision-tree", params={
            "infringement_type": "commercial_use",
            "loss_amount": 2000.0,
        })
        assert resp.status_code == 200
        actions = [a["action_key"] for a in resp.json()["recommended_actions"]]
        assert "civil_lawsuit" not in actions
        assert "criminal_report" not in actions


class TestRoiPredictor:
    """POST /enforcement-roi/predict"""

    def test_predict_returns_roi_data(self, client):
        resp = client.post(f"{_BASE}/predict", json={
            "work_value_yuan": 50000.0,
            "infringement_type": "commercial_use",
            "target_platform": "taobao",
            "action_type": "cease_desist",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["expected_cost"] >= 0
        assert data["win_probability"] > 0
        assert "risk_level" in data
        assert data["risk_level"] in ("low", "medium", "high")

    def test_civil_lawsuit_has_higher_cost(self, client):
        r_cd = client.post(f"{_BASE}/predict", json={
            "work_value_yuan": 50000.0,
            "infringement_type": "commercial_use",
            "target_platform": "amazon",
            "action_type": "cease_desist",
        }).json()
        r_cl = client.post(f"{_BASE}/predict", json={
            "work_value_yuan": 50000.0,
            "infringement_type": "commercial_use",
            "target_platform": "amazon",
            "action_type": "civil_lawsuit",
        }).json()
        assert r_cl["expected_cost"] > r_cd["expected_cost"]
        assert r_cl["expected_duration_days"] > r_cd["expected_duration_days"]


class TestDefenseTiers:
    """GET /enforcement-roi/defense-tiers"""

    def test_returns_four_tiers(self, client):
        resp = client.get(f"{_BASE}/defense-tiers")
        assert resp.status_code == 200
        tiers = resp.json()
        assert len(tiers) == 4
        keys = [t["tier_key"] for t in tiers]
        assert keys == ["zero", "low", "mid", "high"]

    def test_zero_tier_is_free(self, client):
        tiers = client.get(f"{_BASE}/defense-tiers").json()
        zero = next(t for t in tiers if t["tier_key"] == "zero")
        assert zero["monthly_cost_low"] == 0
        assert zero["monthly_cost_high"] == 0


class TestCaseReferences:
    """GET /enforcement-roi/cases-reference"""

    def test_returns_list(self, client):
        resp = client.get(f"{_BASE}/cases-reference")
        assert resp.status_code == 200
        refs = resp.json()
        assert isinstance(refs, list)

    def test_filter_by_infringement_type(self, client):
        resp = client.get(f"{_BASE}/cases-reference", params={
            "infringement_type": "platform_copy",
        })
        assert resp.status_code == 200
        refs = resp.json()
        assert isinstance(refs, list)


class TestSaveCase:
    """POST /enforcement-roi/cases"""

    def test_save_case_success(self, client):
        resp = client.post(f"{_BASE}/cases", json={
            "work_id": "w_test_001",
            "infringement_type": "platform_copy",
            "target_platform": "xiaohongshu",
            "estimated_loss_yuan": 5000.0,
            "action_taken": "platform_complaint",
            "cost_yuan": 0,
            "compensation_received_yuan": 0,
            "outcome": "no_response",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["infringement_type"] == "platform_copy"
        assert data["user_id"] is not None
        assert "created_at" in data

    def test_save_case_with_compensation(self, client):
        resp = client.post(f"{_BASE}/cases", json={
            "infringement_type": "commercial_use",
            "target_platform": "taobao",
            "estimated_loss_yuan": 20000.0,
            "action_taken": "civil_lawsuit",
            "cost_yuan": 10000.0,
            "compensation_received_yuan": 30000.0,
            "outcome": "successful",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["roi_percent"] is not None
        assert data["roi_percent"] > 0


class TestMyCases:
    """GET /enforcement-roi/my-cases"""

    def test_returns_cases_and_summary(self, client):
        resp = client.get(f"{_BASE}/my-cases")
        assert resp.status_code == 200
        data = resp.json()
        assert "cases" in data
        assert "summary" in data
        summary = data["summary"]
        assert "total_cases" in summary
        assert "success_rate_percent" in summary


class TestCaseReferenceDetail:
    """GET /enforcement-roi/cases-reference/{case_id}"""

    def test_get_reference_by_id(self, client, db_session):
        """Fetch a case reference by ID — seed one if the table is empty."""
        # Seed a reference if none exist (CaseReference table has no seed data)
        count = db_session.query(CaseReference).count()
        if count == 0:
            ref = CaseReference(
                infringement_type="platform_copy",
                target_platform="taobao",
                typical_cost_range_low=0.0,
                typical_cost_range_high=500.0,
                resolution_time_days_low=1,
                resolution_time_days_high=7,
                win_rate_percent=80.0,
                avg_compensation_yuan=2000.0,
                roi_tier="high",
                description_zh="平台内容复制，通过平台投诉即可解决",
                is_active=True,
            )
            db_session.add(ref)
            db_session.commit()

        list_resp = client.get(f"{_BASE}/cases-reference")
        assert list_resp.status_code == 200
        refs = list_resp.json()
        assert len(refs) > 0, "Seeded reference should be visible via API"
        case_id = refs[0]["id"]

        detail_resp = client.get(f"{_BASE}/cases-reference/{case_id}")
        assert detail_resp.status_code == 200
        data = detail_resp.json()
        assert data["id"] == case_id
        assert data["infringement_type"] == "platform_copy"
        assert data["target_platform"] == "taobao"
        assert data["roi_tier"] == "high"

    def test_get_nonexistent_reference_returns_404(self, client):
        """A UUID that does not exist should return 404."""
        resp = client.get(f"{_BASE}/cases-reference/nonexistent-id")
        assert resp.status_code == 404
