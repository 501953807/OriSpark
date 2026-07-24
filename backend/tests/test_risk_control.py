import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

import pytest
from app.services.risk_service import evaluate_risk, add_blacklist_entry, is_blacklisted, remove_blacklist_entry
from app.models.risk_control import RiskRule, RiskAssessment, BlacklistEntry


# Use conftest's db_session fixture instead of custom db fixture


@pytest.fixture(autouse=True)
def cleanup(db_session):
    """Truncate risk tables between tests for isolation."""
    yield
    from sqlalchemy import text
    try:
        db_session.execute(text("DELETE FROM blacklist_entries"))
        db_session.execute(text("DELETE FROM risk_assessments"))
        db_session.execute(text("DELETE FROM risk_rules"))
        # Don't rollback here - let the per-test fixture handle it
    except Exception:
        pass


def test_add_default_rules(db_session):
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
        db_session.add(r)
    db_session.flush()
    # Don't rollback - let per-test fixture handle it

    count = db_session.query(RiskRule).count()
    assert count == 2


def test_evaluate_safe_user(db_session):
    """Safe user with no triggered rules gets allow decision."""
    # Add a rule that won't match
    db_session.add(RiskRule(
        name="low_price_check",
        rule_type="price_anomaly",
        condition={"field": "price_yuan", "operator": "lt", "value": 100},
        severity="high",
        action="review",
    ))
    db_session.flush()
    # Don't rollback

    # Context has price=500, won't trigger the rule
    assessment = evaluate_risk(
        db_session, "user1", "transaction", "tx1", {"price_yuan": 500}
    )
    assert assessment.decision == "allow"
    assert assessment.risk_level in ("safe", "low")


def test_evaluate_high_risk(db_session):
    """User with triggering rules gets review/block decision."""
    db_session.add(RiskRule(
        name="low_price_check",
        rule_type="price_anomaly",
        condition={"field": "price_yuan", "operator": "lt", "value": 100},
        severity="high",
        action="review",
    ))
    db_session.flush()
    # Don't rollback

    # Context has price=50, will trigger the rule
    assessment = evaluate_risk(
        db_session, "user2", "transaction", "tx2", {"price_yuan": 50}
    )
    assert assessment.decision in ("review", "block")
    assert len(assessment.triggered_rules) >= 1


def test_blacklist_add_and_check(db_session):
    """Test adding to blacklist and checking status."""
    entry = add_blacklist_entry(
        db_session, "user3", "Copyright infringement", "copyright",
        added_by="admin1",
    )
    assert entry.user_id == "user3"
    assert entry.category == "copyright"

    assert is_blacklisted(db_session, "user3") is True
    assert is_blacklisted(db_session, "nonexistent_user") is False


def test_blacklist_remove(db_session):
    """Test removing from blacklist."""
    add_blacklist_entry(db_session, "user4", "Spam", "spam", added_by="admin1")
    assert is_blacklisted(db_session, "user4") is True

    removed = remove_blacklist_entry(db_session, "user4")
    assert removed == 1
    assert is_blacklisted(db_session, "user4") is False


def test_multiple_rules_trigger(db_session):
    """Multiple rules can trigger and composite score reflects it."""
    db_session.add(RiskRule(
        name="rule_a",
        rule_type="price_anomaly",
        condition={"field": "price_yuan", "operator": "lt", "value": 100},
        severity="high",
        action="review",
    ))
    db_session.add(RiskRule(
        name="rule_b",
        rule_type="frequency",
        condition={"field": "bid_count", "operator": "gt", "value": 10},
        severity="critical",
        action="block",
    ))
    db_session.flush()
    # Don't rollback

    assessment = evaluate_risk(
        db_session, "user5", "transaction", "tx5",
        {"price_yuan": 50, "bid_count": 15}
    )
    assert len(assessment.triggered_rules) == 2
    assert assessment.decision == "block"
