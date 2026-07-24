"""Tests for subscription tiers and subscriber management."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session


def _create_sample_tier(db_session: Session) -> dict:
    """Helper: create a subscription tier and return its id."""
    from app.models.subscription import SubscriptionTier

    tier = SubscriptionTier(
        name="Pro Plan",
        description="Professional plan",
        price=99.0,
        currency="CNY",
        period="monthly",
        features=[{"key": "unlimited_downloads", "label": "Unlimited Downloads"}],
        is_active=True,
    )
    db_session.add(tier)
    db_session.commit()
    db_session.refresh(tier)
    return {"id": tier.id, "name": tier.name}


class TestListTiers:
    def test_returns_all_tiers(self, client: TestClient, db_session: Session):
        _create_sample_tier(db_session)
        resp = client.get("/api/subscription/tiers")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert len(data) >= 1
        assert data[0]["name"] == "Pro Plan"

    def test_filters_by_is_active(self, client: TestClient, db_session: Session):
        _create_sample_tier(db_session)
        resp = client.get("/api/subscription/tiers?is_active=true")
        assert resp.status_code == 200
        data = resp.json()["data"]
        for t in data:
            assert t["is_active"] is True

    def test_empty_when_no_tiers(self, client: TestClient):
        resp = client.get("/api/subscription/tiers")
        assert resp.status_code == 200
        assert resp.json()["data"] == []


class TestCreateTier:
    def test_creates_tier(self, client: TestClient, db_session: Session):
        payload = {
            "name": "Basic Plan",
            "price": 29.0,
            "description": "Entry level",
            "currency": "CNY",
            "period": "monthly",
            "features": [{"key": "basic", "label": "Basic access"}],
            "is_active": True,
        }
        resp = client.post("/api/subscription/tiers", json=payload)
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["name"] == "Basic Plan"
        assert data["price"] == 29.0
        assert data["currency"] == "CNY"

    def test_defaults(self, client: TestClient, db_session: Session):
        payload = {"name": "Minimal", "price": 0}
        resp = client.post("/api/subscription/tiers", json=payload)
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["currency"] == "CNY"
        assert data["period"] == "monthly"
        assert data["is_active"] is True


class TestUpdateTier:
    def test_updates_price(self, client: TestClient, db_session: Session):
        tier = _create_sample_tier(db_session)
        resp = client.put(
            f"/api/subscription/tiers/{tier['id']}",
            json={"price": 199.0},
        )
        assert resp.status_code == 200
        assert resp.json()["data"]["price"] == 199.0

    def test_404_on_missing(self, client: TestClient):
        resp = client.put(
            "/api/subscription/tiers/nonexistent",
            json={"name": "Ghost"},
        )
        assert resp.status_code == 404


class TestDeleteTier:
    def test_deletes_tier(self, client: TestClient, db_session: Session):
        tier = _create_sample_tier(db_session)
        resp = client.delete(f"/api/subscription/tiers/{tier['id']}")
        assert resp.status_code == 200
        assert resp.json()["data"]["success"] is True

    def test_404_on_missing(self, client: TestClient):
        resp = client.delete("/api/subscription/tiers/nonexistent")
        assert resp.status_code == 404


class TestSubscribe:
    def test_subscribes_to_tier(self, client: TestClient, db_session: Session):
        tier = _create_sample_tier(db_session)
        payload = {"user_id": "user_456", "tier_id": tier["id"]}
        resp = client.post("/api/subscription/subscribe", json=payload)
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["status"] == "active"
        assert data["user_id"] == "user_456"
        assert data["tier_id"] == tier["id"]

    def test_rejects_inactive_tier(self, client: TestClient, db_session: Session):
        tier = _create_sample_tier(db_session)
        # Deactivate the tier
        client.put(f"/api/subscription/tiers/{tier['id']}", json={"is_active": False})
        payload = {"user_id": "user_789", "tier_id": tier["id"]}
        resp = client.post("/api/subscription/subscribe", json=payload)
        assert resp.status_code == 404

    def test_rejects_duplicate_subscription(self, client: TestClient, db_session: Session):
        tier = _create_sample_tier(db_session)
        payload = {"user_id": "user_dup", "tier_id": tier["id"]}
        # First subscribe succeeds
        resp1 = client.post("/api/subscription/subscribe", json=payload)
        assert resp1.status_code == 200
        # Second subscribe fails with conflict
        resp2 = client.post("/api/subscription/subscribe", json=payload)
        assert resp2.status_code == 409


class TestCancelSubscription:
    def test_cancels_subscription(self, client: TestClient, db_session: Session):
        tier = _create_sample_tier(db_session)
        # Subscribe first
        client.post(
            "/api/subscription/subscribe",
            json={"user_id": "user_cancel", "tier_id": tier["id"]},
        )
        # Cancel
        resp = client.post(
            "/api/subscription/cancel",
            json={"user_id": "user_cancel"},
        )
        assert resp.status_code == 200
        assert resp.json()["data"]["status"] == "cancelled"

    def test_404_when_no_subscription(self, client: TestClient):
        resp = client.post(
            "/api/subscription/cancel",
            json={"user_id": "nonexistent_user"},
        )
        assert resp.status_code == 404


class TestListSubscribers:
    def test_lists_subscribers(self, client: TestClient, db_session: Session):
        tier = _create_sample_tier(db_session)
        client.post(
            "/api/subscription/subscribe",
            json={"user_id": "user_list", "tier_id": tier["id"]},
        )
        resp = client.get("/api/subscription/subscribers")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert len(data) >= 1

    def test_filters_by_status(self, client: TestClient, db_session: Session):
        tier = _create_sample_tier(db_session)
        client.post(
            "/api/subscription/subscribe",
            json={"user_id": "user_f1", "tier_id": tier["id"]},
        )
        # Cancel one
        client.post(
            "/api/subscription/cancel",
            json={"user_id": "user_f1"},
        )
        resp = client.get("/api/subscription/subscribers?status=cancelled")
        assert resp.status_code == 200
        data = resp.json()["data"]
        for s in data:
            assert s["status"] == "cancelled"
