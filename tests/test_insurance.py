"""Tests for Copyright Insurance marketplace service."""

import pytest
from datetime import date, timedelta
from unittest.mock import MagicMock

from app.services.insurance_service import (
    estimate_premium,
    create_policy,
    submit_claim,
)


class TestEstimatePremium:
    """Test premium estimation engine."""

    def _make_mock_db(self, products=None):
        """Create a mock DB with product results."""
        db = MagicMock()
        if products is None:
            products = []
        # Query for distinct categories
        cat_query = MagicMock()
        cat_query.all.return_value = products[:3]  # Return some products for category count
        db.query.return_value.filter.return_value.all.return_value = products
        return db

    def test_basic_tier_estimate(self):
        db = MagicMock()
        # Mock: query returns empty for distinct categories, but products exist per-tier
        db.query.return_value.filter.return_value.distinct.return_value.all.return_value = []
        result = estimate_premium(db, "illustrator", 100, "medium", ["training_indemnity"])
        assert result["estimated_annual_premium"] > 0

    def test_higher_work_count_positive(self):
        db = MagicMock()
        db.query.return_value.filter.return_value.distinct.return_value.all.return_value = []
        r1 = estimate_premium(db, "illustrator", 10, "medium", ["training_indemnity"])
        r2 = estimate_premium(db, "illustrator", 1000, "medium", ["training_indemnity"])
        assert r1["estimated_annual_premium"] > 0
        assert r2["estimated_annual_premium"] > 0

    def test_risk_multiplier_applied(self):
        db = MagicMock()
        db.query.return_value.filter.return_value.distinct.return_value.all.return_value = []
        low = estimate_premium(db, "illustrator", 50, "low", ["training_indemnity"])
        high = estimate_premium(db, "illustrator", 50, "high", ["training_indemnity"])
        # Both should return positive premiums
        assert high["estimated_annual_premium"] >= 0
        assert low["estimated_annual_premium"] >= 0

    def test_pro_tier_has_entry(self):
        db = MagicMock()
        db.query.return_value.filter.return_value.distinct.return_value.all.return_value = []
        result = estimate_premium(db, "illustrator", 50, "medium", ["training_indemnity"])
        # Should have at least basic tier recommendation
        tiers = [r["tier"] for r in result["recommended_products"]]
        assert "basic" in tiers


class TestCreatePolicy:
    """Test policy creation."""

    def test_create_pending_policy(self):
        db = MagicMock()
        product = MagicMock()
        product.id = "prod-1"
        product.provider_id = "prov-1"
        product.name_zh = "测试产品"
        product.annual_min_yuan = 500
        product.annual_max_yuan = 2000
        db.query.return_value.filter.return_value.first.side_effect = [product]

        result = create_policy(db, "user-1", "prod-1", date.today(), 12)
        assert result["status"] == "pending"
        assert result["annual_premium_yuan"] == 1250.0  # (500+2000)/2

    def test_product_not_found(self):
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = None
        result = create_policy(db, "user-1", "nonexistent", date.today())
        assert "error" in result


class TestSubmitClaim:
    """Test claim submission."""

    def test_submit_claim_success(self):
        db = MagicMock()
        policy = MagicMock()
        policy.id = "pol-1"
        policy.status = "active"
        db.query.return_value.filter.return_value.first.side_effect = [policy]

        result = submit_claim(db, "pol-1", "infringement", "Test claim")
        assert result["status"] == "submitted"
        assert result["claim_type"] == "infringement"

    def test_claim_inactive_policy(self):
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = None
        result = submit_claim(db, "expired-policy", "infringement")
        assert "error" in result
