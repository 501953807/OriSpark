"""Listing Router HTTP-level integration tests."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

import pytest


_BASE = "/api/listings"


class TestCreateListing:
    """POST /listings"""

    def test_create_listing_missing_fields(self, client):
        resp = client.post(f"{_BASE}", json={
            "seller_id": "test_seller",
        }, params={"seller_id": "test_seller"})
        # Should fail validation for missing required fields
        assert resp.status_code in (400, 422)


class TestListActive:
    """GET /listings"""

    def test_list_active_empty(self, client):
        resp = client.get(_BASE)
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)


class TestGetOne:
    """GET /listings/{listing_id}"""

    def test_get_nonexistent(self, client):
        resp = client.get(f"{_BASE}/nonexistent_id")
        assert resp.status_code == 404


class TestUpdateListing:
    """PATCH /listings/{listing_id}"""

    def test_update_nonexistent(self, client):
        resp = client.patch(f"{_BASE}/nonexistent_id", json={
            "asking_price_yuan": 200.0,
        })
        assert resp.status_code == 404


class TestSellListing:
    """POST /listings/{listing_id}/sell"""

    def test_sell_nonexistent(self, client):
        resp = client.post(f"{_BASE}/nonexistent_id/sell", params={
            "buyer_id": "test_buyer",
        })
        assert resp.status_code == 400


class TestProfitEstimate:
    """POST /listings/profit-estimate"""

    def test_profit_estimate(self, client):
        resp = client.post(f"{_BASE}/profit-estimate", params={
            "asking_price": 150.0,
            "fee_rate_bps": 200,
            "split_percent": 70.0,
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "net_profit_yuan" in data
        assert "platform_fee_yuan" in data


class TestBatchToggleStatus:
    """POST /listings/batch-toggle-status"""

    def test_batch_toggle_empty_ids(self, client):
        # Batch endpoints expect ids as repeated query params and active as bool
        resp = client.post(f"{_BASE}/batch-toggle-status", params={
            "ids[]": [],  # Empty list
            "active": True,
        })
        assert resp.status_code in (200, 422)  # May fail if empty list not accepted


class TestBatchUpdatePrice:
    """POST /listings/batch-update-price"""

    def test_batch_update_empty(self, client):
        resp = client.post(f"{_BASE}/batch-update-price", params={
            "ids[]": [],
            "price_yuan": 100.0,
        })
        assert resp.status_code in (200, 422)


class TestBatchExpire:
    """POST /listings/batch-expire"""

    def test_batch_expire_invalid_date(self, client):
        resp = client.post(f"{_BASE}/batch-expire", params={
            "ids[]": [],
            "expires_at": "not-a-date",
        })
        assert resp.status_code in (400, 422)

    def test_batch_expire_valid(self, client):
        resp = client.post(f"{_BASE}/batch-expire", params={
            "ids[]": [],
            "expires_at": "2026-12-31T23:59:59",
        })
        assert resp.status_code in (200, 422)


class TestSearch:
    """GET /listings/search"""

    def test_search_all(self, client):
        resp = client.get(f"{_BASE}/search")
        assert resp.status_code == 200
        data = resp.json()
        assert "listings" in data
        assert "total" in data

    def test_search_with_filters(self, client):
        resp = client.get(f"{_BASE}/search", params={
            "min_price": 50.0,
            "max_price": 500.0,
            "sort_by": "price_asc",
        })
        assert resp.status_code == 200
