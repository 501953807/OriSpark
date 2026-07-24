import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

import pytest
from datetime import datetime, timedelta
from sqlalchemy import text
from app.services.revenue_service import (
    calculate_diversity_index,
    record_revenue,
    get_revenue_summary,
)
from app.models.publish import RevenueRecord

# Import ALL models so they register with Base.metadata BEFORE conftest creates tables
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
import app.models.publish       # noqa: F401 - includes RevenueRecord


@pytest.fixture(autouse=True)
def _cleanup_revenue(db_session):
    """Truncate revenue_records between tests for isolation."""
    yield
    try:
        db_session.execute(text("DELETE FROM revenue_records"))
        db_session.flush()
        db_session.rollback()
    except Exception:
        db_session.rollback()


def test_empty_diversity_index():
    """Empty records should return 0 diversity index."""
    result = calculate_diversity_index([])
    assert result["diversity_index"] == 0.0
    assert result["total_sources"] == 0
    assert len(result["warnings"]) > 0


def test_single_source_low_diversity(db_session):
    """Single income source should have low diversity index."""
    records = [
        RevenueRecord(
            user_id="u1",
            income_category="ad_revenue",
            amount=1000,
            recorded_date=datetime.utcnow(),
        ),
    ]
    result = calculate_diversity_index(records)
    assert result["diversity_index"] == pytest.approx(0.0, abs=0.01)
    assert result["total_sources"] == 1
    assert any("⚠️" in w or "单一" in w or "暂无" in w for w in result["warnings"])


def test_two_sources_moderate_diversity(db_session):
    """Two equal sources should have moderate diversity."""
    records = [
        RevenueRecord(
            user_id="u2",
            income_category="ad_revenue",
            amount=500,
            recorded_date=datetime.utcnow(),
        ),
        RevenueRecord(
            user_id="u2",
            income_category="subscription",
            amount=500,
            recorded_date=datetime.utcnow(),
        ),
    ]
    result = calculate_diversity_index(records)
    assert result["diversity_index"] == pytest.approx(1.0, abs=0.01)
    assert result["total_sources"] == 2


def test_multiple_sources_high_diversity(db_session):
    """Many balanced sources should have high diversity index."""
    categories = ["ad_revenue", "sponsorship", "subscription", "tip", "ecommerce"]
    records = [
        RevenueRecord(
            user_id="u3",
            income_category=cat,
            amount=200,
            recorded_date=datetime.utcnow(),
        )
        for cat in categories
    ]
    result = calculate_diversity_index(records)
    assert result["diversity_index"] > 0.6
    assert result["total_sources"] == 5
    assert not any("⚠️" in w for w in result["warnings"])


def test_single_source_warning(db_session):
    """Single source >70% should trigger warning."""
    records = [
        RevenueRecord(
            user_id="u4",
            income_category="ad_revenue",
            amount=900,
            recorded_date=datetime.utcnow(),
        ),
        RevenueRecord(
            user_id="u4",
            income_category="subscription",
            amount=100,
            recorded_date=datetime.utcnow(),
        ),
    ]
    result = calculate_diversity_index(records)
    assert any("⚠️" in w and "90.0%" in w for w in result["warnings"])


def test_record_revenue(db_session):
    """Test recording a single revenue entry."""
    record = record_revenue(
        db_session, "u5", "ad_revenue", 500.0, platform="YouTube",
        source_description="Monthly ad revenue",
    )
    assert record.user_id == "u5"
    assert record.income_category == "ad_revenue"
    assert record.amount == 500.0
    assert record.platform == "YouTube"


def test_get_revenue_summary(db_session):
    """Test revenue summary calculation."""
    # Add some records
    now = datetime.utcnow()
    for i in range(3):
        record_revenue(
            db_session, "u6", "subscription", 100.0,
            recorded_date=now - timedelta(days=30 * i),
        )
    for i in range(2):
        record_revenue(
            db_session, "u6", "ecommerce", 200.0,
            recorded_date=now - timedelta(days=30 * i),
        )

    summary = get_revenue_summary(db_session, "u6", months=12)
    assert summary["total_revenue"] == 700.0
    assert summary["months"] == 12
    assert summary["diversity"]["total_sources"] == 2
    assert len(summary["monthly_trend"]) > 0
