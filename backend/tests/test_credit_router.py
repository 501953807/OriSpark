"""Credit Router HTTP-level integration tests — covers all 4 endpoints."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

import pytest


_BASE = "/api/credit"


class TestRecordBehavior:
    """POST /credit/behavior"""

    def test_record_behavior_success(self, client):
        resp = client.post(f"{_BASE}/behavior", json={
            "user_id": "test_user_1",
            "behavior_type": "transaction_completed",
            "description": "Completed a transaction",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "rating" in data
        assert "behavior" in data
        assert data["rating"]["total_score"] >= 100
        assert data["behavior"]["score_delta"] > 0

    def test_negative_behavior(self, client):
        resp = client.post(f"{_BASE}/behavior", json={
            "user_id": "test_user_2",
            "behavior_type": "bad_review",
            "description": "Received a bad review",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["behavior"]["score_delta"] < 0

    def test_unknown_behavior_type(self, client):
        """Unknown behavior type should still work with score_delta=0."""
        resp = client.post(f"{_BASE}/behavior", json={
            "user_id": "test_user_3",
            "behavior_type": "unknown_action",
        })
        assert resp.status_code == 200


class TestGetRating:
    """GET /credit/rating/{user_id}"""

    def test_rating_not_found(self, client):
        resp = client.get(f"{_BASE}/rating/nonexistent_user")
        assert resp.status_code == 404

    def test_rating_after_behavior(self, client):
        # Record a behavior first to create the rating
        client.post(f"{_BASE}/behavior", json={
            "user_id": "rating_test_user",
            "behavior_type": "contract_signed",
        })
        resp = client.get(f"{_BASE}/rating/rating_test_user")
        assert resp.status_code == 200
        data = resp.json()
        assert data["user_id"] == "rating_test_user"
        assert "tier" in data
        assert "total_score" in data
        assert "created_at" in data


class TestGetBehaviors:
    """GET /credit/behaviors/{user_id}"""

    def test_empty_behaviors(self, client):
        resp = client.get(f"{_BASE}/behaviors/empty_user")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)
        assert len(resp.json()) == 0

    def test_list_behaviors(self, client):
        # Create two behaviors
        for bt in ["payment_on_time", "on_time_delivery"]:
            client.post(f"{_BASE}/behavior", json={
                "user_id": "behavior_test_user",
                "behavior_type": bt,
            })
        resp = client.get(f"{_BASE}/behaviors/behavior_test_user")
        assert resp.status_code == 200
        items = resp.json()
        assert isinstance(items, list)
        assert len(items) >= 2
        assert items[0]["user_id"] == "behavior_test_user"


class TestImprovementSuggestions:
    """GET /credit/improvement-suggestions/{user_id}"""

    def test_suggestions_for_new_user(self, client):
        resp = client.get(f"{_BASE}/improvement-suggestions/new_user_no_rating")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["user_id"] == "new_user_no_rating"
        assert data["current_score"] is None
        assert len(data["suggestions"]) > 0
        assert any(s["priority"] == "high" for s in data["suggestions"])

    def test_suggestions_after_rating(self, client):
        # Create a rating by recording a behavior
        client.post(f"{_BASE}/behavior", json={
            "user_id": "suggestion_test_user",
            "behavior_type": "transaction_completed",
        })
        resp = client.get(f"{_BASE}/improvement-suggestions/suggestion_test_user")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["user_id"] == "suggestion_test_user"
        assert data["current_score"] is not None
        assert data["tier"] is not None
