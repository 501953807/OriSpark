"""Tests for Growth Stage module."""

import pytest
from unittest.mock import MagicMock

from app.services.growth_stage_service import evaluate_stage, get_progress_dashboard


class TestEvaluateStage:
    """Test stage evaluation logic."""

    def test_beginner_zero_metrics(self):
        result = evaluate_stage(0, 0, 0, 50)
        assert result["stage_key"] == "beginner"
        assert result["stage_name_zh"] == "起步期"

    def test_growing_moderate_metrics(self):
        result = evaluate_stage(50000, 100, 10, 70)
        assert result["stage_key"] == "growing"
        assert result["stage_name_zh"] == "成长期"

    def test_scaling_high_metrics(self):
        result = evaluate_stage(500000, 300, 30, 80)
        assert result["stage_key"] == "scaling"
        assert result["stage_name_zh"] == "规模化期"

    def test_ecosystem_very_high(self):
        result = evaluate_stage(2000000, 600, 60, 90)
        assert result["stage_key"] == "ecosystem"
        assert result["next_stage"] is None

    def test_progress_increases_with_revenue(self):
        # Same stage: higher revenue = higher progress
        r1 = evaluate_stage(15000, 60, 8, 60)
        r2 = evaluate_stage(80000, 200, 30, 70)
        assert r2["stage_progress"] > r1["stage_progress"]

    def test_next_stage_available_below_ceiling(self):
        result = evaluate_stage(50000, 100, 10, 70)
        assert result["next_stage"] is not None


class TestProgressDashboard:
    """Test progress dashboard generation."""

    def test_empty_user_defaults(self):
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.order_by.return_value.first.return_value = None
        result = get_progress_dashboard(mock_db, "new_user")
        assert result["current_stage"]["key"] == "beginner"
        assert len(result["tasks"]) > 0

    def test_existing_user_uses_metrics(self):
        mock_stage = MagicMock()
        mock_stage.monthly_revenue_yuan = 50000
        mock_stage.total_works = 100
        mock_stage.total_certificates = 10
        mock_stage.credit_score = 70
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.order_by.return_value.first.return_value = mock_stage
        result = get_progress_dashboard(mock_db, "existing_user")
        assert result["current_stage"]["key"] == "growing"
