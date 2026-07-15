import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

import pytest
from app.services.matchmaking_service import (
    create_match_request, match_creators, award_match, update_delivery,
)
from app.database import engine, Base
from sqlalchemy.orm import sessionmaker

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="session", autouse=True)
def setup():
    Base.metadata.create_all(bind=engine)
    yield


@pytest.fixture
def db():
    s = TestingSessionLocal()
    yield s
    s.close()


def test_create_and_match(db):
    mr = create_match_request(db, {
        "buyer_id": "b1", "title": "Need logo design",
        "category": "illustration", "style_tags": ["modern", "minimal"],
        "budget_min_yuan": 500, "budget_max_yuan": 2000,
    })
    assert mr is not None
    assert mr.status == "pending"

    matched = match_creators(db, mr.id, ["s1", "s2", "s3"])
    assert matched is not None
    assert matched.status == "matching"
    assert len(matched.matched_seller_ids) == 3


def test_award_match(db):
    mr = create_match_request(db, {
        "buyer_id": "b1", "title": "Need music",
        "category": "music",
    })
    # Must match first before awarding
    match_creators(db, mr.id, ["s1"])
    tx = award_match(db, mr.id, "s1", 800)
    assert tx is not None
    assert tx.agreed_amount_yuan == 800
    assert tx.payment_status == "pending"

    db.refresh(mr)
    assert mr.status == "awarded"
    assert mr.awarded_to == "s1"


def test_update_delivery(db):
    mr = create_match_request(db, {"buyer_id": "b1", "title": "Test"})
    match_creators(db, mr.id, ["s1"])
    tx = award_match(db, mr.id, "s1", 500)
    updated = update_delivery(db, tx.id, "delivered")
    assert updated is not None
    assert updated.delivery_status == "delivered"
