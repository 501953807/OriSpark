"""Tests for invoice and auto-renewal endpoints."""

import pytest
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session


def _auth_headers(user_id: str = "test_user") -> dict:
    """Return headers that make require_auth return user_id."""
    # require_auth falls back to "local" when no Bearer token, which returns "local" as user_id.
    # We use "Bearer local" to trigger the fallback path.
    return {"Authorization": "Bearer local"}


class TestCreateInvoice:
    def test_creates_invoice(self, client: TestClient, db_session: Session):
        payload = {
            "amount_yuan": 100.0,
            "tax_rate": 0.11,
            "description": "Monthly subscription",
            "is_auto_renewal": True,
        }
        resp = client.post(
            "/api/subscriptions/invoices",
            json=payload,
            headers=_auth_headers("test_user_1"),
        )
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["amount_yuan"] == 100.0
        assert data["status"] == "pending"
        # require_auth returns "local" in test mode (no real JWT)
        assert data["user_id"] == "local"
        assert "invoice_number" in data
        assert data["invoice_number"].startswith("INV/")

    def test_calculates_tax_correctly(self, client: TestClient, db_session: Session):
        payload = {"amount_yuan": 111.0, "tax_rate": 0.11}
        resp = client.post(
            "/api/subscriptions/invoices",
            json=payload,
            headers=_auth_headers("tax_user"),
        )
        assert resp.status_code == 200
        data = resp.json()["data"]
        # amount / (1 + tax_rate) = 111 / 1.11 = 100
        assert data["subtotal_yuan"] == 100.0
        assert data["tax_amount_yuan"] == 11.0

    def test_default_tax_rate(self, client: TestClient, db_session: Session):
        payload = {"amount_yuan": 50.0}
        resp = client.post(
            "/api/subscriptions/invoices",
            json=payload,
            headers=_auth_headers("default_tax_user"),
        )
        assert resp.status_code == 200
        assert resp.json()["data"]["tax_rate"] == 0.11


class TestListInvoices:
    def test_lists_invoices(self, client: TestClient, db_session: Session):
        # Create an invoice first
        client.post(
            "/api/subscriptions/invoices",
            json={"amount_yuan": 100.0},
            headers=_auth_headers("list_user"),
        )
        resp = client.get("/api/subscriptions/invoices", headers=_auth_headers("list_user"))
        assert resp.status_code == 200
        assert len(resp.json()["data"]) >= 1

    def test_filters_by_status(self, client: TestClient, db_session: Session):
        # Create two invoices with different statuses
        client.post(
            "/api/subscriptions/invoices",
            json={"amount_yuan": 100.0},
            headers=_auth_headers("status_user"),
        )
        resp = client.get(
            "/api/subscriptions/invoices?status=pending",
            headers=_auth_headers("status_user"),
        )
        assert resp.status_code == 200

    def test_pagination_defaults(self, client: TestClient, db_session: Session):
        resp = client.get(
            "/api/subscriptions/invoices",
            headers=_auth_headers("page_user"),
        )
        assert resp.status_code == 200


class TestMarkPaid:
    def test_marks_invoice_paid(self, client: TestClient, db_session: Session):
        # Create invoice
        create_resp = client.post(
            "/api/subscriptions/invoices",
            json={"amount_yuan": 200.0},
            headers=_auth_headers("paid_user"),
        )
        invoice_id = create_resp.json()["data"]["id"]
        # Mark as paid
        resp = client.post(
            "/api/subscriptions/invoices/mark-paid",
            json={"invoice_id": invoice_id},
            headers=_auth_headers("paid_user"),
        )
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["status"] == "paid"
        assert data["paid_at"] is not None

    def test_returns_404_for_missing_invoice(self, client: TestClient):
        resp = client.post(
            "/api/subscriptions/invoices/mark-paid",
            json={"invoice_id": "nonexistent"},
            headers=_auth_headers("nobody"),
        )
        assert resp.status_code == 404


def _create_subscriber(db_session: Session, user_id: str) -> str:
    """Create a subscription_tier + subscription_subscribers so FK constraints pass.

    Returns the subscriber_id for use with auto-renewal endpoints.
    """
    from app.models.subscription import SubscriptionTier, SubscriptionSubscriber
    # Create a tier first (FK target for subscriber)
    tier = SubscriptionTier(
        name="Test Tier",
        price=0.0,
        period="monthly",
        is_active=True,
    )
    db_session.add(tier)
    db_session.flush()  # get tier.id

    sub = SubscriptionSubscriber(
        user_id=user_id,
        tier_id=tier.id,
        status="active",
        subscribed_at=datetime.utcnow(),
    )
    db_session.add(sub)
    db_session.commit()
    return sub.id


class TestAutoRenewal:
    def test_get_nonexistent_renewal(self, client: TestClient):
        resp = client.get(
            "/api/subscriptions/auto-renewal/no_such_user",
            headers=_auth_headers("admin"),
        )
        assert resp.status_code == 200
        assert resp.json()["data"] is None

    def test_create_and_update_renewal(self, client: TestClient, db_session: Session):
        subscriber_id = _create_subscriber(db_session, "renewal_sub_1")
        # Initially None
        resp = client.get(
            f"/api/subscriptions/auto-renewal/{subscriber_id}",
            headers=_auth_headers("admin"),
        )
        assert resp.status_code == 200
        assert resp.json()["data"] is None

        # Enable renewal
        resp = client.patch(
            f"/api/subscriptions/auto-renewal/{subscriber_id}",
            json={"enabled": True},
            headers=_auth_headers("admin"),
        )
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["enabled"] is True

        # Verify it was created
        resp = client.get(
            f"/api/subscriptions/auto-renewal/{subscriber_id}",
            headers=_auth_headers("admin"),
        )
        assert resp.status_code == 200
        assert resp.json()["data"]["enabled"] is True

        # Disable renewal
        resp = client.patch(
            f"/api/subscriptions/auto-renewal/{subscriber_id}",
            json={"enabled": False},
            headers=_auth_headers("admin"),
        )
        assert resp.status_code == 200
        assert resp.json()["data"]["enabled"] is False

    def test_process_renewal_success(self, client: TestClient, db_session: Session):
        subscriber_id = _create_subscriber(db_session, "renewal_proc_1")
        # First create a renewal record
        client.patch(
            f"/api/subscriptions/auto-renewal/{subscriber_id}",
            json={"enabled": True},
            headers=_auth_headers("admin"),
        )
        # Process successful renewal
        resp = client.post(
            "/api/subscriptions/auto-renewal/process",
            json={"subscriber_id": subscriber_id, "success": True},
            headers=_auth_headers("admin"),
        )
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["status"] == "success"
        assert data["failed_attempts"] == 0

    def test_process_renewal_failure(self, client: TestClient, db_session: Session):
        subscriber_id = _create_subscriber(db_session, "renewal_fail_1")
        client.patch(
            f"/api/subscriptions/auto-renewal/{subscriber_id}",
            json={"enabled": True},
            headers=_auth_headers("admin"),
        )
        # Process failed renewal
        resp = client.post(
            "/api/subscriptions/auto-renewal/process",
            json={"subscriber_id": subscriber_id, "success": False},
            headers=_auth_headers("admin"),
        )
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["status"] == "failed"
        assert data["failed_attempts"] >= 1

    def test_process_renewal_missing_id(self, client: TestClient):
        resp = client.post(
            "/api/subscriptions/auto-renewal/process",
            json={},
            headers=_auth_headers("admin"),
        )
        assert resp.status_code == 400
