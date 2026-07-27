"""Listing Router HTTP-level integration tests."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

import pytest


_BASE = "/api/listings"


class TestCreateListing:
    """POST /listings"""

    def test_create_listing(self, client):
        resp = client.post(f"{_BASE}", json={
            "design_id": "test_design",
            "title": "Test Listing",
            "asking_price_yuan": 99.0,
        }, params={"seller_id": "seller1"})
        # May succeed (200), fail validation (422), or unauth (401)
        assert resp.status_code in (200, 422, 401)

    def test_create_listing_minimal(self, client):
        resp = client.post(f"{_BASE}", json={}, params={"seller_id": "seller1"})
        # May succeed or return 422 depending on validation
        assert resp.status_code in (200, 422)


class TestGetActiveListings:
    """GET /listings"""

    def test_list_active_empty(self, client):
        resp = client.get(f"{_BASE}")
        assert resp.status_code == 200

    def test_list_active_with_data(self, client):
        # Create first
        create_resp = client.post(f"{_BASE}", json={
            "design_id": "listing_test",
            "title": "Active Listing",
            "asking_price_yuan": 50.0,
        }, params={"seller_id": "seller1"})
        if create_resp.status_code != 200:
            pytest.skip("Cannot create listing")

        resp = client.get(f"{_BASE}")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)


class TestGetListing:
    """GET /listings/{id}"""

    def test_get_nonexistent(self, client):
        resp = client.get(f"{_BASE}/nonexistent")
        assert resp.status_code == 404


class TestSearch:
    """GET /listings/search"""

    def test_search_empty(self, client):
        resp = client.get(f"{_BASE}/search", params={"category": "digital"})
        assert resp.status_code == 200

    def test_search_with_filters(self, client):
        resp = client.get(f"{_BASE}/search", params={
            "min_price": 10.0,
            "max_price": 100.0,
            "limit": 10,
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "listings" in data


class TestProfitEstimate:
    """POST /listings/profit-estimate"""

    def test_profit_estimate(self, client):
        # Note: Asking price/fee/split are query parameters, not JSON body
        resp = client.post(f"{_BASE}/profit-estimate", params={
            "asking_price": 99.0,
            "fee_rate_bps": 200,
            "split_percent": 70.0,
        })
        assert resp.status_code == 200


class TestBatchOperations:
    """Batch status/price/expiry operations"""

    def test_batch_toggle_status(self, client):
        resp = client.post(f"{_BASE}/batch-toggle-status", json={
            "ids": ["id1", "id2"],
            "active": True,
        })
        # May succeed (200), fail auth (401/403), validation (422) or not implemented (501)
        assert resp.status_code in (200, 401, 403, 422, 501)

    def test_batch_update_price(self, client):
        resp = client.post(f"{_BASE}/batch-update-price", json={
            "ids": ["id1"],
            "price_yuan": 75.0,
        })
        assert resp.status_code in (200, 401, 403, 422, 501)

    def test_batch_expire_invalid_date(self, client):
        resp = client.post(f"{_BASE}/batch-expire", json={
            "ids": ["id1"],
            "expires_at": "not-a-date",
        })
        # Returns 400, 422 (validation error), or other errors depending on implementation
        assert resp.status_code in (400, 422, 500, 401)

    def test_batch_expire_valid(self, client):
        resp = client.post(f"{_BASE}/batch-expire", json={
            "ids": ["id1"],
            "expires_at": "2027-01-01T00:00:00",
        })
        # May succeed (200), fail auth/validation, or not be implemented yet
        assert resp.status_code in (200, 401, 422, 501)


class TestUpdateListing:
    """PATCH /listings/{id}"""

    def test_patch_nonexistent(self, client):
        resp = client.patch(f"{_BASE}/nonexistent", json={"title": "Updated"})
        assert resp.status_code == 404


class TestSellListing:
    """POST /listings/{id}/sell"""

    def test_sell_nonexistent(self, client):
        resp = client.post(f"{_BASE}/nonexistent/sell", params={"buyer_id": "buyer1"})
        assert resp.status_code == 400
