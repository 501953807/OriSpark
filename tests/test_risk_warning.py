"""Tests for G8 Risk Warning module."""

import pytest
from unittest.mock import MagicMock
from datetime import date, timedelta

from app.services.risk_warning_service import detect_burnout_risk


class TestBurnoutDetection:
    """Test burnout risk detection logic."""

    def test_no_metrics_returns_low(self):
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.order_by.return_value.all.return_value = []
        result = detect_burnout_risk(mock_db, "user1")
        assert result["risk_level"] == "low"
        assert len(result["factors"]) > 0

    def test_long_hours_high_risk(self):
        metrics = self._make_metrics(12, 0, False, 3, 5)
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.order_by.return_value.all.return_value = metrics
        result = detect_burnout_risk(mock_db, "user1")
        assert result["score"] >= 30  # At least some risk from long hours

    def test_good_health_low_risk(self):
        metrics = self._make_metrics(6, 2, True, 8, 5)
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.order_by.return_value.all.return_value = metrics
        result = detect_burnout_risk(mock_db, "user1")
        assert result["score"] < 30
        assert result["risk_level"] in ("low", "medium")

    def test_burnout_has_recommendation(self):
        metrics = self._make_metrics(14, 0, False, 2, 7)
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.order_by.return_value.all.return_value = metrics
        result = detect_burnout_risk(mock_db, "user1")
        assert len(result["recommendation"]) > 0

    @staticmethod
    def _make_metrics(hours, works, break_taken, mood, days_ago=0):
        from datetime import date, timedelta
        d = date.today() - timedelta(days=days_ago)
        m = MagicMock()
        m.daily_work_hours = hours
        m.works_created = works
        m.has_break_taken = break_taken
        m.mood_score = mood
        m.recorded_date = d
        return [m]


class TestTaxDeadlines:
    """Test tax deadline endpoint."""

    def test_deadline_has_days_remaining(self):
        mock_deadline = MagicMock()
        mock_deadline.id = "1"
        mock_deadline.tax_type = "quarterly_vat"
        mock_deadline.due_date = date.today() + timedelta(days=30)
        mock_deadline.amount_yuan = 5000
        mock_deadline.is_completed = False
        mock_deadline.user_id = "local"

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.order_by.return_value.all.return_value = [mock_deadline]

        from app.routers.risk_warning import list_tax_deadlines
        result = list_tax_deadlines(mock_db)
        assert len(result) == 1
        assert result[0]["days_remaining"] == 30
