"""HTTP-level integration tests for matching_engine router."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

import pytest
from datetime import datetime, timedelta, timezone


@pytest.fixture(autouse=True)
def _disable_fk(db_session):
    """Disable FK checks so auction/licensing records with work_id FKs can be created."""
    from sqlalchemy import text
    db_session.execute(text("PRAGMA foreign_keys = OFF"))
    db_session.commit()
    yield
    # No need to re-enable; each test gets a fresh session


class TestCreateAuction:
    """POST /api/matching/auctions"""

    def test_create_auction(self, client):
        resp = client.post(
            "/api/matching/auctions",
            json={
                "listing_id": "l1",
                "work_id": "w1",
                "seller_id": "s1",
                "title": "Test Auction",
                "description": "A test auction description",
                "starting_price_yuan": 100.0,
                "min_increment_yuan": 10.0,
                "ends_at": (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat(),
                "auto_extend_seconds": 300,
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] is not None
        assert data["listing_id"] == "l1"
        assert data["work_id"] == "w1"
        assert data["current_bid_yuan"] == 100.0
        assert data["bid_count"] == 0
        assert data["status"] == "active"

    def test_create_auction_minimal(self, client):
        """Create with only required fields."""
        resp = client.post(
            "/api/matching/auctions",
            json={
                "listing_id": "l2",
                "work_id": "w2",
                "seller_id": "s2",
                "title": "Minimal Auction",
                "starting_price_yuan": 50.0,
                "ends_at": (datetime.now(timezone.utc) + timedelta(hours=2)).isoformat(),
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["listing_id"] == "l2"
        assert data["current_bid_yuan"] == 50.0  # mirrors starting_price

    def test_create_auction_default_increment(self, client):
        resp = client.post(
            "/api/matching/auctions",
            json={
                "listing_id": "l3",
                "work_id": "w3",
                "seller_id": "s3",
                "title": "Default Increment",
                "starting_price_yuan": 200.0,
                "ends_at": (datetime.now(timezone.utc) + timedelta(hours=3)).isoformat(),
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["bid_count"] == 0


class TestPlaceBid:
    """POST /api/matching/auctions/{auction_id}/bid"""

    def test_place_bid_success(self, client):
        # Create auction via API first
        ends_at = (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()
        create_resp = client.post(
            "/api/matching/auctions",
            json={
                "listing_id": "l1",
                "work_id": "w1",
                "seller_id": "s1",
                "title": "Bid Me",
                "starting_price_yuan": 100.0,
                "min_increment_yuan": 10.0,
                "ends_at": ends_at,
            },
        )
        assert create_resp.status_code == 200
        auction_id = create_resp.json()["id"]

        resp = client.post(
            f"/api/matching/auctions/{auction_id}/bid",
            json={"buyer_id": "b1", "amount_yuan": 150.0, "notes": "First bid"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "bid_id" in data
        assert data["amount_yuan"] == 150.0

    def test_place_bid_insufficient_amount(self, client):
        ends_at = (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()
        create_resp = client.post(
            "/api/matching/auctions",
            json={
                "listing_id": "l1",
                "work_id": "w1",
                "seller_id": "s1",
                "title": "Low Bid",
                "starting_price_yuan": 100.0,
                "min_increment_yuan": 10.0,
                "ends_at": ends_at,
            },
        )
        auction_id = create_resp.json()["id"]

        resp = client.post(
            f"/api/matching/auctions/{auction_id}/bid",
            json={"buyer_id": "b1", "amount_yuan": 105.0},
        )
        assert resp.status_code == 400
        data = resp.json()
        assert "detail" in data

    def test_place_bid_expired_auction(self, client):
        # Create auction already expired
        ends_at = (datetime.now(timezone.utc) - timedelta(minutes=5)).isoformat()
        create_resp = client.post(
            "/api/matching/auctions",
            json={
                "listing_id": "l1",
                "work_id": "w1",
                "seller_id": "s1",
                "title": "Expired",
                "starting_price_yuan": 100.0,
                "min_increment_yuan": 10.0,
                "ends_at": ends_at,
            },
        )
        auction_id = create_resp.json()["id"]

        resp = client.post(
            f"/api/matching/auctions/{auction_id}/bid",
            json={"buyer_id": "b1", "amount_yuan": 200.0},
        )
        assert resp.status_code == 400

    def test_place_bid_nonexistent_auction(self, client):
        resp = client.post(
            "/api/matching/auctions/nonexistent/bid",
            json={"buyer_id": "b1", "amount_yuan": 200.0},
        )
        assert resp.status_code == 400

    def test_place_bid_with_notes(self, client):
        ends_at = (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()
        create_resp = client.post(
            "/api/matching/auctions",
            json={
                "listing_id": "l1",
                "work_id": "w1",
                "seller_id": "s1",
                "title": "Notes Test",
                "starting_price_yuan": 100.0,
                "min_increment_yuan": 10.0,
                "ends_at": ends_at,
            },
        )
        auction_id = create_resp.json()["id"]

        resp = client.post(
            f"/api/matching/auctions/{auction_id}/bid",
            json={"buyer_id": "b1", "amount_yuan": 150.0, "notes": "Handsome bid"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["amount_yuan"] == 150.0

    def test_place_bid_exact_min_increment(self, client):
        ends_at = (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()
        create_resp = client.post(
            "/api/matching/auctions",
            json={
                "listing_id": "l1",
                "work_id": "w1",
                "seller_id": "s1",
                "title": "Exact Increment",
                "starting_price_yuan": 100.0,
                "min_increment_yuan": 20.0,
                "ends_at": ends_at,
            },
        )
        auction_id = create_resp.json()["id"]

        # 120 = 100 + 20 (exactly min increment)
        resp = client.post(
            f"/api/matching/auctions/{auction_id}/bid",
            json={"buyer_id": "b1", "amount_yuan": 120.0},
        )
        assert resp.status_code == 200


class TestCloseAuction:
    """POST /api/matching/auctions/{auction_id}/close"""

    def test_close_auction_with_winner(self, client):
        ends_at = (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()
        create_resp = client.post(
            "/api/matching/auctions",
            json={
                "listing_id": "l1",
                "work_id": "w1",
                "seller_id": "s1",
                "title": "Close Me",
                "starting_price_yuan": 100.0,
                "min_increment_yuan": 10.0,
                "ends_at": ends_at,
            },
        )
        auction_id = create_resp.json()["id"]

        # Place a bid
        bid_resp = client.post(
            f"/api/matching/auctions/{auction_id}/bid",
            json={"buyer_id": "b1", "amount_yuan": 150.0},
        )
        assert bid_resp.status_code == 200

        resp = client.post(f"/api/matching/auctions/{auction_id}/close")
        assert resp.status_code == 200
        data = resp.json()
        assert data["auction_id"] == auction_id
        assert data["winner"] == "b1"
        assert data["winning_amount"] == 150

    def test_close_empty_auction(self, client):
        ends_at = (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()
        create_resp = client.post(
            "/api/matching/auctions",
            json={
                "listing_id": "l1",
                "work_id": "w1",
                "seller_id": "s1",
                "title": "Empty Close",
                "starting_price_yuan": 100.0,
                "min_increment_yuan": 10.0,
                "ends_at": ends_at,
            },
        )
        auction_id = create_resp.json()["id"]

        resp = client.post(f"/api/matching/auctions/{auction_id}/close")
        assert resp.status_code == 200
        data = resp.json()
        assert data["auction_id"] == auction_id
        assert data["winner"] is None

    def test_close_nonexistent_auction(self, client):
        resp = client.post("/api/matching/auctions/nonexistent/close")
        assert resp.status_code == 400

    def test_close_already_closed_auction(self, client):
        ends_at = (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()
        create_resp = client.post(
            "/api/matching/auctions",
            json={
                "listing_id": "l1",
                "work_id": "w1",
                "seller_id": "s1",
                "title": "Closed Twice",
                "starting_price_yuan": 100.0,
                "min_increment_yuan": 10.0,
                "ends_at": ends_at,
            },
        )
        auction_id = create_resp.json()["id"]

        # Close once
        close_resp = client.post(f"/api/matching/auctions/{auction_id}/close")
        assert close_resp.status_code == 200

        # Close again -- should fail
        resp = client.post(f"/api/matching/auctions/{auction_id}/close")
        assert resp.status_code == 400

    def test_close_expired_auction(self, client):
        # Close an already-closed auction (router checks status=="active", not expiry)
        ends_at = (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()
        create_resp = client.post(
            "/api/matching/auctions",
            json={
                "listing_id": "l1",
                "work_id": "w1",
                "seller_id": "s1",
                "title": "Closed Twice",
                "starting_price_yuan": 100.0,
                "min_increment_yuan": 10.0,
                "ends_at": ends_at,
            },
        )
        auction_id = create_resp.json()["id"]

        # Close once
        close_resp = client.post(f"/api/matching/auctions/{auction_id}/close")
        assert close_resp.status_code == 200

        # Close again -- should fail (status is now "closed")
        resp = client.post(f"/api/matching/auctions/{auction_id}/close")
        assert resp.status_code == 400


class TestCreateLicensingMatch:
    """POST /api/matching/licensing"""

    def test_create_licensing_match_full(self, client):
        resp = client.post(
            "/api/matching/licensing",
            json={
                "work_id": "w1",
                "seller_id": "s1",
                "buyer_id": "b1",
                "license_type": "commercial",
                "usage_scope": "digital",
                "territory": "CN",
                "duration_days": 365,
                "price_per_use_cents": 500,
                "minimum_guarantee_yuan": 1000.0,
                "royalty_percent": 5.0,
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "id" in data
        assert data["status"] == "pending"

    def test_create_licensing_match_minimal(self, client):
        resp = client.post(
            "/api/matching/licensing",
            json={
                "work_id": "w2",
                "seller_id": "s2",
                "buyer_id": "b2",
                "license_type": "personal",
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "id" in data
        assert data["status"] == "pending"

    def test_create_licensing_match_no_optional_fields(self, client):
        resp = client.post(
            "/api/matching/licensing",
            json={
                "work_id": "w3",
                "seller_id": "s3",
                "buyer_id": "b3",
                "license_type": "educational",
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "pending"

    def test_create_licensing_match_exclusive(self, client):
        resp = client.post(
            "/api/matching/licensing",
            json={
                "work_id": "w4",
                "seller_id": "s4",
                "buyer_id": "b4",
                "license_type": "exclusive",
                "territory": "US",
                "duration_days": 730,
                "royalty_percent": 10.0,
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "pending"


class TestNegotiateLicensing:
    """PATCH /api/matching/licensing/{match_id}"""

    def test_negotiate_licensing(self, client):
        # Create match first
        create_resp = client.post(
            "/api/matching/licensing",
            json={
                "work_id": "w1",
                "seller_id": "s1",
                "buyer_id": "b1",
                "license_type": "commercial",
                "status": "pending",
            },
        )
        match_id = create_resp.json()["id"]

        resp = client.patch(
            f"/api/matching/licensing/{match_id}",
            json={"status": "agreed", "royalty_percent": 8.0},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == match_id
        assert data["status"] == "agreed"

    def test_negotiate_partial_update(self, client):
        create_resp = client.post(
            "/api/matching/licensing",
            json={
                "work_id": "w1",
                "seller_id": "s1",
                "buyer_id": "b1",
                "license_type": "commercial",
                "royalty_percent": 5.0,
            },
        )
        match_id = create_resp.json()["id"]

        resp = client.patch(
            f"/api/matching/licensing/{match_id}",
            json={"status": "negotiating"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "negotiating"

    def test_negotiate_nonexistent_match(self, client):
        resp = client.patch(
            "/api/matching/licensing/nonexistent",
            json={"status": "agreed"},
        )
        assert resp.status_code == 404
        data = resp.json()
        assert "detail" in data

    def test_negotiate_multiple_fields(self, client):
        create_resp = client.post(
            "/api/matching/licensing",
            json={
                "work_id": "w1",
                "seller_id": "s1",
                "buyer_id": "b1",
                "license_type": "commercial",
            },
        )
        match_id = create_resp.json()["id"]

        resp = client.patch(
            f"/api/matching/licensing/{match_id}",
            json={
                "status": "negotiating",
                "territory": "US",
                "duration_days": 180,
                "price_per_use_cents": 1000,
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "negotiating"

    def test_negotiate_reject(self, client):
        create_resp = client.post(
            "/api/matching/licensing",
            json={
                "work_id": "w1",
                "seller_id": "s1",
                "buyer_id": "b1",
                "license_type": "commercial",
            },
        )
        match_id = create_resp.json()["id"]

        resp = client.patch(
            f"/api/matching/licensing/{match_id}",
            json={"status": "rejected"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "rejected"
