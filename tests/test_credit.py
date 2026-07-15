import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

import pytest
from app.services.credit_service import record_behavior, get_rating_by_user
from app.models.credit import CreditTier, BehaviorType, CreditRating, CreditBehavior

from app.database import engine, Base
from sqlalchemy.orm import sessionmaker

# Import ALL models so they register with Base.metadata BEFORE create_all
import app.models.work          # noqa: F401
import app.models.certification # noqa: F401
import app.models.ai_training_license  # noqa: F401
import app.models.ip_commercialization  # noqa: F401
import app.models.trading_fee   # noqa: F401
import app.models.listing       # noqa: F401
import app.models.matching_engine  # noqa: F401
import app.models.matchmaking   # noqa: F401
import app.models.credit        # noqa: F401

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


@pytest.fixture(autouse=True)
def cleanup(db):
    """Truncate credit tables between tests for isolation."""
    yield
    db.query(CreditBehavior).delete()
    db.query(CreditRating).delete()
    db.commit()


def test_newbie_start(db):
    rating, behavior = record_behavior(db, {
        "user_id": "u1", "user_type": "creator",
        "behavior_type": BehaviorType.TRANSACTION_COMPLETED,
    })
    assert rating.total_score == 105  # 100 + 5
    assert rating.tier == CreditTier.GOOD  # 105 >= 100


def test_tier_upgrades(db):
    # Start fresh
    rating, _ = record_behavior(db, {
        "user_id": "u2", "user_type": "creator",
        "behavior_type": BehaviorType.TRANSACTION_COMPLETED,
    })

    # Accumulate good behaviors to reach excellent
    for _ in range(8):
        rating, _ = record_behavior(db, {
            "user_id": "u2", "user_type": "creator",
            "behavior_type": BehaviorType.ON_TIME_DELIVERY,
        })

    # 105 + 8*3 = 129 → still GOOD (140 needed for EXCELLENT)
    assert rating.total_score == 129
    assert rating.tier == CreditTier.GOOD

    # One more good transaction to reach 132... still not excellent
    record_behavior(db, {"user_id": "u2", "user_type": "creator",
                         "behavior_type": BehaviorType.CONTRACT_SIGNED})
    assert rating.total_score == 132
    assert rating.tier == CreditTier.GOOD

    # Enough to reach excellent
    record_behavior(db, {"user_id": "u2", "user_type": "creator",
                         "behavior_type": BehaviorType.CERTIFICATION_CREATED})
    assert rating.total_score == 134
    assert rating.tier == CreditTier.GOOD  # 134 < 140

    record_behavior(db, {"user_id": "u2", "user_type": "creator",
                         "behavior_type": BehaviorType.REVIEW_RECEIVED})
    assert rating.total_score == 135
    assert rating.tier == CreditTier.GOOD  # 135 < 140

    record_behavior(db, {"user_id": "u2", "user_type": "creator",
                         "behavior_type": BehaviorType.TRANSACTION_COMPLETED})
    assert rating.total_score == 140
    assert rating.tier == CreditTier.EXCELLENT


def test_dispute_penalties(db):
    rating, _ = record_behavior(db, {
        "user_id": "u3", "user_type": "merchant",
        "behavior_type": BehaviorType.TRANSACTION_COMPLETED,
    })
    assert rating.total_score == 105

    # Lose a dispute: -10
    rating, _ = record_behavior(db, {
        "user_id": "u3", "user_type": "merchant",
        "behavior_type": BehaviorType.DISPUTE_LOST,
    })
    assert rating.total_score == 95
    assert rating.tier == CreditTier.NEWBIE  # dropped below 100
    assert rating.dispute_count == 1


def test_bad_review_penalty(db):
    rating, _ = record_behavior(db, {
        "user_id": "u4", "user_type": "creator",
        "behavior_type": BehaviorType.BAD_REVIEW,
    })
    assert rating.total_score == 92  # 100 - 8


def test_get_rating_by_user(db):
    record_behavior(db, {
        "user_id": "u5", "user_type": "creator",
        "behavior_type": BehaviorType.TRANSACTION_COMPLETED,
    })
    rating = get_rating_by_user(db, "u5")
    assert rating is not None
    assert rating.user_id == "u5"
    assert rating.total_score == 105


def test_tier_history(db):
    # Good behavior first → tier changes from NEWBIE to GOOD
    record_behavior(db, {
        "user_id": "u6", "user_type": "creator",
        "behavior_type": BehaviorType.TRANSACTION_COMPLETED,
    })
    rating = get_rating_by_user(db, "u6")
    assert rating.tier == CreditTier.GOOD
    assert rating.tier_history is not None
    assert len(rating.tier_history) >= 1  # NEWBIE → GOOD transition recorded
