"""Matchmaking Router HTTP-level integration tests — covers all 7 endpoints."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

import pytest


_BASE = "/api/matchmaking"


class TestCreateRequest:
    """POST /matchmaking"""

    def test_create_match_request(self, client):
        resp = client.post(_BASE, json={
            "buyer_id": "test_buyer",
            "title": "Need 100 custom mugs",
            "category": "crafts",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "id" in data
        assert data["title"] == "Need 100 custom mugs"
        assert data["buyer_id"] == "test_buyer"

    def test_create_minimal_request(self, client):
        resp = client.post(_BASE, json={
            "buyer_id": "b2",
            "title": "Minimal request",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["title"] == "Minimal request"

    def test_create_with_all_fields(self, client):
        resp = client.post(_BASE, json={
            "buyer_id": "b3",
            "title": "Full request",
            "description": "Need minimalist logo design",
            "category": "illustration",
            "style_tags": ["minimalist", "modern"],
            "budget_min_yuan": 500.0,
            "budget_max_yuan": 2000.0,
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["category"] == "illustration"


class TestListRequests:
    """GET /matchmaking"""

    def test_list_empty(self, client):
        resp = client.get(_BASE)
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)

    def test_list_with_requests(self, client):
        # Create a request first
        client.post(_BASE, json={
            "buyer_id": "b4",
            "title": "Listable request",
            "category": "photo",
        })
        resp = client.get(_BASE)
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        assert any(item["title"] == "Listable request" for item in data)


class TestMatch:
    """POST /matchmaking/{request_id}/match"""

    def test_match_creators(self, client):
        # Create a request first
        create_resp = client.post(_BASE, json={
            "buyer_id": "b5",
            "title": "Matchable request",
            "category": "music",
        })
        assert create_resp.status_code == 200
        request_id = create_resp.json()["id"]

        resp = client.post(f"{_BASE}/{request_id}/match", json=["seller_1", "seller_2"])
        assert resp.status_code == 200
        data = resp.json()
        assert data["matched_count"] == 2

    def test_match_nonexistent(self, client):
        resp = client.post(f"{_BASE}/nonexistent_id/match", json=["s1"])
        assert resp.status_code == 404


class TestAward:
    """POST /matchmaking/{request_id}/award"""

    def test_award_success(self, client):
        # Create and match first
        create_resp = client.post(_BASE, json={
            "buyer_id": "b6",
            "title": "Awardable request",
            "category": "video",
        })
        request_id = create_resp.json()["id"]
        client.post(f"{_BASE}/{request_id}/match", json=["s1"])

        resp = client.post(f"{_BASE}/{request_id}/award", params={
            "seller_id": "s1",
            "amount_yuan": 800.0,
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "id" in data
        assert data["agreed_amount_yuan"] == 800.0
        assert data["payment_status"] == "pending"

    def test_award_nonexistent(self, client):
        resp = client.post(f"{_BASE}/nonexistent_id/award", params={
            "seller_id": "s1",
            "amount_yuan": 500.0,
        })
        assert resp.status_code == 400


class TestDelivery:
    """PATCH /matchmaking/transactions/{tx_id}/delivery"""

    def test_update_delivery(self, client):
        # Create request -> match -> award to get a transaction
        create_resp = client.post(_BASE, json={
            "buyer_id": "b7",
            "title": "Deliverable request",
        })
        request_id = create_resp.json()["id"]
        client.post(f"{_BASE}/{request_id}/match", json=["s1"])
        award_resp = client.post(f"{_BASE}/{request_id}/award", params={
            "seller_id": "s1",
            "amount_yuan": 500.0,
        })
        tx_id = award_resp.json()["id"]

        resp = client.patch(f"{_BASE}/transactions/{tx_id}/delivery", params={
            "delivery_status": "delivered",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["delivery_status"] == "delivered"

    def test_delivery_nonexistent_tx(self, client):
        resp = client.patch(f"{_BASE}/transactions/nonexistent_tx/delivery", params={
            "delivery_status": "shipped",
        })
        assert resp.status_code == 404


class TestAutoMatch:
    """POST /matchmaking/auto-match/{request_id}"""

    def test_auto_match_nonexistent(self, client):
        resp = client.post(f"{_BASE}/auto-match/nonexistent_id")
        assert resp.status_code == 404

    def test_auto_match_existing_request(self, client):
        # Create a request so auto-match has something to work with
        create_resp = client.post(_BASE, json={
            "buyer_id": "b8",
            "title": "Auto-matchable request",
            "category": "illustration",
            "budget_min_yuan": 100.0,
            "budget_max_yuan": 5000.0,
        })
        request_id = create_resp.json()["id"]

        resp = client.post(f"{_BASE}/auto-match/{request_id}")
        assert resp.status_code == 200
        data = resp.json()
        assert "results" in data
        assert "total" in data


class TestMatchScore:
    """GET /matchmaking/match-score"""

    def test_match_score_missing_params(self, client):
        resp = client.get(f"{_BASE}/match-score")
        assert resp.status_code in (400, 422)

    def test_match_score_nonexistent(self, client):
        resp = client.get(f"{_BASE}/match-score", params={
            "listing_id": "nonexist_listing",
            "request_id": "nonexist_request",
        })
        assert resp.status_code == 404
