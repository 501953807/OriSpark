"""Tests for G6 Multi-Platform Content Pipeline."""

import pytest
from unittest.mock import MagicMock
from datetime import datetime, timedelta

from app.services.content_pipeline_service import (
    simulate_publish, get_publish_stats,
    PLATFORMS,
)


class TestSimulatePublish:
    """Test multi-platform publish simulation."""

    def test_simulate_single_platform(self):
        results = simulate_publish("My Artwork", None, ["xiaohongshu"])
        assert len(results) == 1
        assert results[0]["platform"] == "xiaohongshu"
        assert results[0]["platform_name"] == "小红书"
        assert results[0]["recommended_cover"] == "vertical"

    def test_simulate_multiple_platforms(self):
        results = simulate_publish("Test", None, ["bilibili", "douyin", "weibo"])
        assert len(results) == 3
        platforms = [r["platform"] for r in results]
        assert "bilibili" in platforms
        assert "douyin" in platforms
        assert "weibo" in platforms

    def test_simulate_unknown_platform_skipped(self):
        results = simulate_publish("Test", None, ["unknown_platform"])
        assert len(results) == 0

    def test_simulate_title_adaptation(self):
        results = simulate_publish("Sunset Painting", None, ["xiaohongshu"])
        assert "【" in results[0]["title_adapted"]
        assert "】" in results[0]["title_adapted"]

    def test_simulate_tags_check(self):
        results = simulate_publish("Test", None, ["bilibili"], ["tag1", "tag2", "tag3", "tag4", "tag5", "tag6"])
        assert results[0]["tags_count"] == 6
        assert results[0]["tags_ok"] is False  # bilibili max is 5


class TestPlatformDefs:
    """Test platform definitions."""

    def test_all_platforms_have_chinese_name(self):
        for key, info in PLATFORMS.items():
            assert "name_zh" in info
            assert len(info["name_zh"]) > 0

    def test_cover_types_defined(self):
        for info in PLATFORMS.values():
            assert info["recommended_cover"] in ("vertical", "horizontal", "square", "auto")


class TestGetPublishStats:
    """Test publish statistics."""

    def test_empty_stats(self):
        mock_query = MagicMock()
        mock_query.filter.return_value.count.return_value = 0
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.count.return_value = 0
        mock_db.query.return_value.filter.return_value.order_by.return_value.all.return_value = []
        result = get_publish_stats(mock_db, "user1")
        assert result["total_schedules"] == 0
        assert result["scheduled"] == 0
        assert result["published"] == 0
        assert result["failed"] == 0
