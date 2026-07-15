import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

import pytest
from app.services.risk_service import evaluate_risk, add_blacklist_entry, is_blacklisted, remove_blacklist_entry
from app.models.risk_control import RiskRule, RiskAssessment, BlacklistEntry

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
import app.models.risk_control  # noqa: F401

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
    """Truncate risk tables between tests for isolation."""
    yield
    from app.models.risk_control import RiskRule, RiskAssessment, BlacklistEntry
    db.query(RiskAssessment).delete()
    db.query(BlacklistEntry).delete()
    db.query(RiskRule).delete()
    db.commit()


def test_add_default_rules(db):
    """Add default risk rules."""
    rules = [
        RiskRule(
            name="price_anomaly_low",
            rule_type="price_anomaly",
            condition={"field": "price_yuan", "operator": "lt", "value": 10},
            severity="high",
            action="review",
        ),
        RiskRule(
            name="credit_drop_significant",
            rule_type="credit_drop",
            condition={"field": "score_delta", "operator": "lt", "value": -5},
            severity="medium",
            action="flag",
        ),
    ]
    for r in rules:
        db.add(r)
    db.commit()

    count = db.query(RiskRule).count()
    assert count == 2


def test_evaluate_safe_user(db):
    """Safe user with no triggered rules gets allow decision."""
    # Add a rule that won't match
    db.add(RiskRule(
        name="low_price_check",
        rule_type="price_anomaly",
        condition={"field": "price_yuan", "operator": "lt", "value": 100},
        severity="high",
        action="review",
    ))
    db.commit()

    # Context has price=500, won't trigger the rule
    assessment = evaluate_risk(
        db, "user1", "transaction", "tx1", {"price_yuan": 500}
    )
    assert assessment.decision == "allow"
    assert assessment.risk_level in ("safe", "low")


def test_evaluate_high_risk(db):
    """User with triggering rules gets review/block decision."""
    db.add(RiskRule(
        name="low_price_check",
        rule_type="price_anomaly",
        condition={"field": "price_yuan", "operator": "lt", "value": 100},
        severity="high",
        action="review",
    ))
    db.commit()

    # Context has price=50, will trigger the rule
    assessment = evaluate_risk(
        db, "user2", "transaction", "tx2", {"price_yuan": 50}
    )
    assert assessment.decision in ("review", "block")
    assert len(assessment.triggered_rules) >= 1


def test_blacklist_add_and_check(db):
    """Test adding to blacklist and checking status."""
    entry = add_blacklist_entry(
        db, "user3", "Copyright infringement", "copyright",
        added_by="admin1",
    )
    assert entry.user_id == "user3"
    assert entry.category == "copyright"

    assert is_blacklisted(db, "user3") is True
    assert is_blacklisted(db, "nonexistent_user") is False


def test_blacklist_remove(db):
    """Test removing from blacklist."""
    add_blacklist_entry(db, "user4", "Spam", "spam", added_by="admin1")
    assert is_blacklisted(db, "user4") is True

    removed = remove_blacklist_entry(db, "user4")
    assert removed == 1
    assert is_blacklisted(db, "user4") is False


def test_multiple_rules_trigger(db):
    """Multiple rules can trigger and composite score reflects it."""
    db.add(RiskRule(
        name="rule_a",
        rule_type="price_anomaly",
        condition={"field": "price_yuan", "operator": "lt", "value": 100},
        severity="high",
        action="review",
    ))
    db.add(RiskRule(
        name="rule_b",
        rule_type="frequency",
        condition={"field": "bid_count", "operator": "gt", "value": 10},
        severity="critical",
        action="block",
    ))
    db.commit()

    assessment = evaluate_risk(
        db, "user5", "transaction", "tx5",
        {"price_yuan": 50, "bid_count": 15}
    )
    assert len(assessment.triggered_rules) == 2
    assert assessment.decision == "block"
