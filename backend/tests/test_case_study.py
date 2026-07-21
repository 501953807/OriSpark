"""Tests for G9 Case Study Knowledge Base."""

import pytest
from unittest.mock import MagicMock

from app.services.case_study_service import (
    create_case, list_cases, get_case_stats, search_cases, CATEGORIES,
)


class TestCategories:
    """Test category definitions."""

    def test_all_categories_have_chinese_name(self):
        for key, info in CATEGORIES.items():
            assert "name_zh" in info
            assert len(info["name_zh"]) > 0

    def test_five_categories_defined(self):
        assert len(CATEGORIES) == 5


class TestCaseCreation:
    """Test case study CRUD."""

    def test_create_case(self):
        mock_db = MagicMock()
        result = create_case(
            mock_db, "user1", "My Case", "monetization",
            description="A great case", tags=["pod", "redbubble"],
        )
        assert "id" in result
        assert result["title"] == "My Case"

    def test_create_invalid_category_still_creates(self):
        """create_case itself doesn't validate; the router layer does."""
        mock_db = MagicMock()
        result = create_case(mock_db, "user1", "Bad", "invalid_cat")
        assert "id" in result
        assert result["title"] == "Bad"

    def test_list_cases_filtered_by_category(self):
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.filter.return_value.order_by.return_value.all.return_value = []
        result = list_cases(mock_db, "user1", category="monetization")
        assert isinstance(result, list)


class TestStats:
    """Test case statistics."""

    def test_empty_stats(self):
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.all.return_value = []
        result = get_case_stats(mock_db, "user1")
        assert result["total"] == 0
        assert result["by_type"]["success"] == 0

    def test_stats_with_cases(self):
        c1 = MagicMock()
        c1.category = "monetization"
        c1.case_type = "success"
        c1.tags = ["pod", "redbubble"]

        c2 = MagicMock()
        c2.category = "copyright"
        c2.case_type = "lesson"
        c2.tags = ["takedown"]

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.all.return_value = [c1, c2]
        result = get_case_stats(mock_db, "user1")
        assert result["total"] == 2
        assert result["by_category"]["monetization"] == 1
        assert result["by_type"]["success"] == 1


class TestSearch:
    """Test case search."""

    def test_search_returns_matching_cases(self):
        c = MagicMock()
        c.title = "Redbubble Success"
        c.description = "How I made $10K on Redbubble"
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.order_by.return_value.all.return_value = [c]
        result = search_cases(mock_db, "user1", "Redbubble")
        assert len(result) == 1
