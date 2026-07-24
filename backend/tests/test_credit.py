import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

import pytest
from app.services.credit_service import record_behavior, get_rating_by_user
from app.models.credit import CreditTier, BehaviorType, CreditRating, CreditBehavior

from sqlalchemy.orm import sessionmaker

# Use conftest's db_session fixture instead of custom db fixture


@pytest.fixture(autouse=True)
def cleanup(db_session):
    """Truncate credit tables between tests for isolation."""
    yield
    from sqlalchemy import text
    try:
        db_session.execute(text("DELETE FROM credit_behaviors"))
        db_session.execute(text("DELETE FROM credit_ratings"))
        db_session.flush()
        db_session.rollback()
    except Exception:
        db_session.rollback()


def test_newbie_start(db_session):
    rating, behavior = record_behavior(db_session, {
        "user_id": "u1", "user_type": "creator",
        "behavior_type": BehaviorType.TRANSACTION_COMPLETED,
    })
    assert rating.total_score == 105  # 100 + 5
    assert rating.tier == CreditTier.GOOD  # 105 >= 100


def test_tier_upgrades(db_session):
    # Start fresh
    rating, _ = record_behavior(db_session, {
        "user_id": "u2", "user_type": "creator",
        "behavior_type": BehaviorType.TRANSACTION_COMPLETED,
    })

    # Accumulate good behaviors to reach excellent
    for _ in range(8):
        rating, _ = record_behavior(db_session, {
            "user_id": "u2", "user_type": "creator",
            "behavior_type": BehaviorType.ON_TIME_DELIVERY,
        })

    # 105 + 8*3 = 129 → still GOOD (140 needed for EXCELLENT)
    assert rating.total_score == 129
    assert rating.tier == CreditTier.GOOD

    # One more good transaction to reach 132... still not excellent
    record_behavior(db_session, {"user_id": "u2", "user_type": "creator",
                         "behavior_type": BehaviorType.CONTRACT_SIGNED})
    assert rating.total_score == 132
    assert rating.tier == CreditTier.GOOD

    # Enough to reach excellent
    record_behavior(db_session, {"user_id": "u2", "user_type": "creator",
                         "behavior_type": BehaviorType.CERTIFICATION_CREATED})
    assert rating.total_score == 134
    assert rating.tier == CreditTier.GOOD  # 134 < 140

    record_behavior(db_session, {"user_id": "u2", "user_type": "creator",
                         "behavior_type": BehaviorType.REVIEW_RECEIVED})
    assert rating.total_score == 135
    assert rating.tier == CreditTier.GOOD  # 135 < 140

    record_behavior(db_session, {"user_id": "u2", "user_type": "creator",
                         "behavior_type": BehaviorType.TRANSACTION_COMPLETED})
    assert rating.total_score == 140
    assert rating.tier == CreditTier.EXCELLENT


def test_dispute_penalties(db_session):
    rating, _ = record_behavior(db_session, {
        "user_id": "u3", "user_type": "merchant",
        "behavior_type": BehaviorType.TRANSACTION_COMPLETED,
    })
    assert rating.total_score == 105

    # Lose a dispute: -10
    rating, _ = record_behavior(db_session, {
        "user_id": "u3", "user_type": "merchant",
        "behavior_type": BehaviorType.DISPUTE_LOST,
    })
    assert rating.total_score == 95
    assert rating.tier == CreditTier.NEWBIE  # dropped below 100
    assert rating.dispute_count == 1


def test_bad_review_penalty(db_session):
    rating, _ = record_behavior(db_session, {
        "user_id": "u4", "user_type": "creator",
        "behavior_type": BehaviorType.BAD_REVIEW,
    })
    assert rating.total_score == 92  # 100 - 8


def test_get_rating_by_user(db_session):
    record_behavior(db_session, {
        "user_id": "u5", "user_type": "creator",
        "behavior_type": BehaviorType.TRANSACTION_COMPLETED,
    })
    rating = get_rating_by_user(db_session, "u5")
    assert rating is not None
    assert rating.user_id == "u5"
    assert rating.total_score == 105


def test_tier_history(db_session):
    # Good behavior first → tier changes from NEWBIE to GOOD
    record_behavior(db_session, {
        "user_id": "u6", "user_type": "creator",
        "behavior_type": BehaviorType.TRANSACTION_COMPLETED,
    })
    rating = get_rating_by_user(db_session, "u6")
    assert rating.tier == CreditTier.GOOD
    assert rating.tier_history is not None
    assert len(rating.tier_history) >= 1  # NEWBIE → GOOD transition recorded
