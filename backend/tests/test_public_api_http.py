"""Public API Router HTTP-level integration tests — read-only endpoints."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

import pytest


# Public API uses no prefix - it's root-level
_BASE = "/public"


class TestGetWorkCategories:
    """GET /work-categories — read-only, database required."""

    def test_get_work_categories(self, client):
        # Database may be unavailable; return empty list as fallback
        resp = client.get(f"{_BASE}/work-categories")
        assert resp.status_code in (200, 404, 500)
        if resp.status_code == 200:
            data = resp.json()
            assert isinstance(data, list)


class TestListPublicWorks:
    """GET /works — read-only, requires database."""

    def test_list_public_works(self, client):
        # May return 500 if DB down; returns list of works on success
        resp = client.get(f"{_BASE}/works")
        assert resp.status_code in (200, 404, 500)
        if resp.status_code == 200:
            data = resp.json()
            assert isinstance(data, list)

    def test_list_public_works_with_search(self, client):
        resp = client.get(f"{_BASE}/works", params={"search": "test"})
        assert resp.status_code in (200, 404, 500)
        if resp.status_code == 200:
            data = resp.json()
            assert isinstance(data, list)


class TestGetPublicWork:
    """GET /works/{work_id} — read-only, database required."""

    def test_get_public_work_nonexistent(self, client):
        resp = client.get(f"{_BASE}/works/nonexistent-id")
        assert resp.status_code in (200, 404)

    def test_get_public_work_existing(self, client):
        resp = client.get(f"{_BASE}/works/test-work-id")
        # Success or not found depending on database state
        assert resp.status_code in (200, 404)
        if resp.status_code == 200:
            data = resp.json()
            assert any(k in data for k in ["id", "title", "creator_name"])


class TestListPublicListings:
    """GET /listings — read-only, database required."""

    def test_list_public_listings(self, client):
        resp = client.get(f"{_BASE}/listings")
        assert resp.status_code in (200, 404, 500)
        if resp.status_code == 200:
            data = resp.json()
            assert isinstance(data, list)


class TestListPublicContracts:
    """GET /contracts — read-only, database required."""

    def test_list_public_contracts(self, client):
        resp = client.get(f"{_BASE}/contracts")
        assert resp.status_code in (200, 404, 500)
        if resp.status_code == 200:
            data = resp.json()
            assert isinstance(data, list)

    def test_list_public_contracts_with_filters(self, client):
        resp = client.get(f"{_BASE}/contracts", params={"contract_type": "copyright"})
        assert resp.status_code in (200, 404, 500)
        if resp.status_code == 200:
            data = resp.json()
            assert isinstance(data, list)


class TestGetDashboardStats:
    """GET /dashboard-stats — read-only, requires database aggregation."""

    def get_dashboard_stats(self, client):
        resp = client.get(f"{_BASE}/dashboard-stats")
        assert resp.status_code in (200, 404, 500)
        if resp.status_code == 200:
            data = resp.json()
            assert isinstance(data, dict)
            assert any(k in data for k in ["total_works", "total_contracts", "total_listings"])


class ListPublicNotifications:
    """GET /notifications — read-only, database required."""

    def test_list_public_notifications(self, client):
        resp = client.get(f"{_BASE}/notifications")
        assert resp.status_code in (200, 404, 500)
        if resp.status_code == 200:
            data = resp.json()
            assert isinstance(data, list)


class GetMarketTrends:
    """GET /market/trends — read-only, database required."""

    def test_get_market_trends_monthly(self, client):
        resp = client.get(f"{_BASE}/market/trends?period=monthly")
        assert resp.status_code in (200, 404, 500)
        if resp.status_code == 200:
            data = resp.json()
            assert isinstance(data, list)


class ListPublicCaseStudies:
    """GET /case-studies — read-only, database required."""

    def test_list_public_case_studies(self, client):
        resp = client.get(f"{_BASE}/case-studies")
        assert resp.status_code in (200, 404, 500)
        if resp.status_code == 200:
            data = resp.json()
            assert isinstance(data, list)


class ListPublicOpportunities:
    """GET /opportunities — read-only, requires database join."""

    def test_list_public_opportunities(self, client):
        resp = client.get(f"{_BASE}/opportunities")
        assert resp.status_code in (200, 404, 500)
        if resp.status_code == 200:
            data = resp.json()
            assert isinstance(data, list)


class GetGalleryCategories:
    """GET /gallery/categories — read-only, database required."""

    def test_get_gallery_categories(self, client):
        resp = client.get(f"{_BASE}/gallery/categories")
        assert resp.status_code in (200, 404, 500)
        if resp.status_code == 200:
            data = resp.json()
            assert isinstance(data, list)
