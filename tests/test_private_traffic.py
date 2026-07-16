"""Tests for Private Traffic module."""

import pytest
from unittest.mock import MagicMock, patch

from app.services.private_traffic_service import get_funnel_summary


class TestConversionFunnel:
    """Test conversion funnel calculations."""

    def test_empty_funnel(self):
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.all.return_value = []
        result = get_funnel_summary(mock_db, "user1")
        assert result["total_public_views"] == 0
        assert result["overall_conversion_rate"] == 0

    def test_zero_views_no_division(self):
        mock_entry = MagicMock()
        mock_entry.source_platform = "xiaohongshu"
        mock_entry.public_views = 0
        mock_entry.profile_clicks = 0
        mock_entry.link_clicks = 0
        mock_entry.converted_subscribers = 0
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.all.return_value = [mock_entry]
        result = get_funnel_summary(mock_db, "user1")
        # Should not raise ZeroDivisionError
        assert result["total_public_views"] == 0

    def test_conversion_rate_calculation(self):
        mock_entry = MagicMock()
        mock_entry.source_platform = "douyin"
        mock_entry.public_views = 10000
        mock_entry.profile_clicks = 500
        mock_entry.link_clicks = 100
        mock_entry.converted_subscribers = 10
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.all.return_value = [mock_entry]
        result = get_funnel_summary(mock_db, "user1")
        assert result["total_public_views"] == 10000
        assert result["total_converted"] == 10
        assert result["overall_conversion_rate"] == 0.1  # 10/10000 * 100

    def test_by_platform_stats(self):
        mock_entry = MagicMock()
        mock_entry.source_platform = "youtube"
        mock_entry.public_views = 5000
        mock_entry.profile_clicks = 250
        mock_entry.link_clicks = 50
        mock_entry.converted_subscribers = 5
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.all.return_value = [mock_entry]
        result = get_funnel_summary(mock_db, "user1")
        assert len(result["by_platform"]) == 1
        p = result["by_platform"][0]
        assert p["views"] == 5000
        assert p["profile_ctr"] == 5.0  # 250/5000 * 100
        assert p["link_ctr"] == 20.0  # 50/250 * 100
        assert p["conv_rate"] == 10.0  # 5/50 * 100


class TestMultiPlatform:
    """Test funnel aggregation across platforms."""

    def test_two_platforms_aggregated(self):
        e1 = MagicMock()
        e1.source_platform = "xiaohongshu"
        e1.public_views = 3000
        e1.profile_clicks = 150
        e1.link_clicks = 30
        e1.converted_subscribers = 3

        e2 = MagicMock()
        e2.source_platform = "douyin"
        e2.public_views = 7000
        e2.profile_clicks = 350
        e2.link_clicks = 70
        e2.converted_subscribers = 7

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.all.return_value = [e1, e2]
        result = get_funnel_summary(mock_db, "user1")
        assert result["total_public_views"] == 10000
        assert len(result["by_platform"]) == 2
