import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

import pytest
from app.services.matchmaking_service import (
    create_match_request, match_creators, award_match, update_delivery,
)
from sqlalchemy.orm import sessionmaker

# Use conftest's db_session fixture instead of custom db fixture


def test_create_and_match(db_session):
    mr = create_match_request(db_session, {
        "buyer_id": "b1", "title": "Need logo design",
        "category": "illustration", "style_tags": ["modern", "minimal"],
        "budget_min_yuan": 500, "budget_max_yuan": 2000,
    })
    assert mr is not None
    assert mr.status == "pending"

    matched = match_creators(db_session, mr.id, ["s1", "s2", "s3"])
    assert matched is not None
    assert matched.status == "matching"
    assert len(matched.matched_seller_ids) == 3


def test_award_match(db_session):
    mr = create_match_request(db_session, {
        "buyer_id": "b1", "title": "Need music",
        "category": "music",
    })
    # Must match first before awarding
    match_creators(db_session, mr.id, ["s1"])
    tx = award_match(db_session, mr.id, "s1", 800)
    assert tx is not None
    assert tx.agreed_amount_yuan == 800
    assert tx.payment_status == "pending"

    db_session.refresh(mr)
    assert mr.status == "awarded"
    assert mr.awarded_to == "s1"


def test_update_delivery(db_session):
    mr = create_match_request(db_session, {"buyer_id": "b1", "title": "Test"})
    match_creators(db_session, mr.id, ["s1"])
    tx = award_match(db_session, mr.id, "s1", 500)
    updated = update_delivery(db_session, tx.id, "delivered")
    assert updated is not None
    assert updated.delivery_status == "delivered"
