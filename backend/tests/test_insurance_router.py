"""Insurance Router HTTP-level integration tests."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

import pytest


_BASE = "/api/insurance"


class TestProducts:
    """GET /insurance/products and GET /insurance/products/{id}"""

    def test_list_products(self, client):
        resp = client.get(f"{_BASE}/products")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)

    def test_list_filtered_by_category(self, client):
        resp = client.get(f"{_BASE}/products", params={"category": "copyright"})
        assert resp.status_code == 200

    def test_get_nonexistent_product(self, client):
        resp = client.get(f"{_BASE}/products/nonexistent_id")
        assert resp.status_code == 404


class TestEstimate:
    """POST /insurance/estimate"""

    @pytest.mark.skip(reason="estimate_premium service queries insurance_products table which needs seed data")
    def test_estimate_basic(self, client):
        resp = client.post(f"{_BASE}/estimate", json={
            "creator_type": "illustrator",
            "work_count": 50,
            "risk_level": "medium",
            "categories": ["commercial"],
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "estimated_premium" in data
        assert "coverage_amount" in data
        assert "deductible" in data


class TestPolicies:
    """GET /insurance/policies"""

    def test_list_policies_empty(self, client):
        resp = client.get(f"{_BASE}/policies")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)


class TestClaims:
    """POST /insurance/claims and GET /insurance/claims/{id}/status"""

    @pytest.mark.skip(reason="Service requires policy_id that doesn't exist in test DB")
    def test_submit_claim(self, client):
        resp = client.post(f"{_BASE}/claims", json={
            "policy_id": "test_policy",
            "incident_date": "2026-01-01",
            "description": "Unauthorized use of my artwork",
            "evidence_urls": ["https://example.com/evidence.jpg"],
        })
        assert resp.status_code == 200
