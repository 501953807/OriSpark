"""Dashboard Router HTTP-level integration tests — covers all 4 endpoints."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

import pytest


class TestDashboardStats:
    """GET /dashboard/stats"""

    def test_stats_empty(self, client):
        resp = client.get("/api/dashboard/stats")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert "total_works" in data
        assert "total_notarized" in data
        assert "infringement_alerts" in data
        assert "monthly_revenue" in data
        assert "recent_works" in data


class TestRecentWorks:
    """GET /dashboard/recent"""

    def test_recent_empty(self, client):
        resp = client.get("/api/dashboard/recent")
        assert resp.status_code == 200
        data = resp.json()
        assert "data" in data
        assert isinstance(data["data"], list)

    def test_recent_with_limit(self, client):
        resp = client.get("/api/dashboard/recent", params={"limit": 5})
        assert resp.status_code == 200


class TestDashboardRevenue:
    """GET /dashboard/revenue"""

    def test_revenue_empty(self, client):
        resp = client.get("/api/dashboard/revenue")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert "total_revenue" in data
        assert "revenue_by_month" in data


class TestDashboardTrends:
    """GET /dashboard/trends"""

    def test_trends_empty(self, client):
        resp = client.get("/api/dashboard/trends")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert "daily_trends" in data
        assert "total_works_30d" in data
        assert "avg_daily" in data
        # Should always return 30 days of trends
        assert len(data["daily_trends"]) == 30
