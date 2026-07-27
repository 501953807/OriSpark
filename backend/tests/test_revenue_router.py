"""Revenue Router HTTP-level integration tests — covers all 3 endpoints."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

import pytest


_BASE = "/api/revenue"


class TestRecordRevenue:
    """POST /revenue/records"""

    def test_record_valid_revenue(self, client):
        resp = client.post(f"{_BASE}/records", json={
            "income_category": "ad_revenue",
            "amount": 5000.0,
            "platform": "youtube",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["income_category"] == "ad_revenue"
        assert data["amount"] == 5000.0
        assert data["currency"] == "CNY"

    def test_record_invalid_category(self, client):
        resp = client.post(f"{_BASE}/records", json={
            "income_category": "nonexistent_type",
            "amount": 100.0,
        })
        assert resp.status_code == 400

    def test_record_with_all_fields(self, client):
        resp = client.post(f"{_BASE}/records", json={
            "income_category": "ip_licensing",
            "amount": 25000.0,
            "currency": "USD",
            "platform": "custom",
            "source_description": "License for artwork collection",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["amount"] == 25000.0
        assert data["currency"] == "USD"
        assert data["source_description"] == "License for artwork collection"


class TestRevenueSummary:
    """GET /revenue/summary/{user_id}"""

    def test_summary_no_records(self, client):
        resp = client.get(f"{_BASE}/summary/revenue_test_user")
        assert resp.status_code == 200
        data = resp.json()
        assert data["user_id"] == "revenue_test_user"
        assert data["total_revenue"] == 0.0
        assert data["currency"] == "CNY"

    def test_summary_with_records(self, client):
        # Record some revenue first (stored under "current_user")
        client.post(f"{_BASE}/records", json={
            "income_category": "tip",
            "amount": 200.0,
        })
        resp = client.get(f"{_BASE}/summary/current_user")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_revenue"] > 0


class TestDiversityIndex:
    """GET /revenue/diversity/{user_id}"""

    def test_diversity_empty(self, client):
        resp = client.get(f"{_BASE}/diversity/diversity_test_user")
        assert resp.status_code == 200
        data = resp.json()
        assert data["diversity_index"] == 0.0
        assert data["total_sources"] == 0
        assert len(data["warnings"]) > 0

    def test_diversity_multiple_categories(self, client):
        # Record multiple categories (stored under "current_user")
        for cat in ["ad_revenue", "sponsorship", "tip"]:
            client.post(f"{_BASE}/records", json={
                "income_category": cat,
                "amount": 1000.0,
            })
        resp = client.get(f"{_BASE}/diversity/current_user")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_sources"] >= 1
        assert data["diversity_index"] >= 0.0
