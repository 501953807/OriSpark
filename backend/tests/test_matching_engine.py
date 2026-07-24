import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

import pytest
from datetime import datetime, timedelta
from app.services.matching_service import place_bid, close_auction
from app.models.matching_engine import AuctionRecord, Bid, BidStatus

# Use conftest's db_session fixture instead of custom db fixture


def _make_auction(db_session, **kwargs):
    # Disable FK checks for test isolation
    from sqlalchemy import text
    db_session.execute(text("PRAGMA foreign_keys = OFF"))

    auction = AuctionRecord(
        listing_id=kwargs.get("listing_id", "l1"),
        work_id=kwargs.get("work_id", "w1"),
        seller_id=kwargs.get("seller_id", "s1"),
        title=kwargs.get("title", "Test"),
        starting_price_yuan=kwargs.get("starting_price_yuan", 100),
        current_bid_yuan=kwargs.get("current_bid_yuan", 100),
        min_increment_yuan=kwargs.get("min_increment_yuan", 10),
        ends_at=datetime.utcnow() + timedelta(hours=1),
    )
    if kwargs.get("expired"):
        auction.ends_at = datetime.utcnow() - timedelta(minutes=1)
    db_session.add(auction)
    db_session.flush()
    # Don't rollback here - let the per-test fixture handle it
    return auction


def test_place_bid_success(db_session):
    auction = _make_auction(db_session)
    bid = place_bid(db_session, auction.id, "buyer1", 150)
    assert bid is not None
    assert bid.amount_yuan == 150
    assert bid.status == BidStatus.OPEN
    assert auction.current_bid_yuan == 150
    assert auction.bid_count == 1


def test_place_bid_insufficient(db_session):
    auction = _make_auction(db_session)
    bid = place_bid(db_session, auction.id, "buyer1", 105)  # below min increment
    assert bid is None


def test_close_auction(db_session):
    auction = _make_auction(db_session)
    bid = place_bid(db_session, auction.id, "buyer1", 150)
    assert bid is not None
    result = close_auction(db_session, auction.id)
    assert result is not None
    assert result.status == "closed"
    assert result.winner_buyer_id == "buyer1"
    assert result.winner_amount_yuan == 150


def test_bid_on_expired_auction(db_session):
    auction = _make_auction(db_session, expired=True)
    bid = place_bid(db_session, auction.id, "buyer1", 200)
    assert bid is None
