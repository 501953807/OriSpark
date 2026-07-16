"""Tests for Creator Navigation service."""

import pytest
from unittest.mock import MagicMock, patch

from app.services.navigation_service import (
    _safe_eval_expression,
    get_navigation_status,
    complete_task,
    switch_path,
)


class TestSafeEvalExpression:
    """Test safe expression evaluation."""

    def test_simple_true(self):
        assert _safe_eval_expression("True", {}) is True

    def test_simple_false(self):
        assert _safe_eval_expression("False", {}) is False

    def test_comparison(self):
        ctx = {"count": 5}
        assert _safe_eval_expression("count > 3", ctx) is True

    def test_string_check(self):
        ctx = {"role": "creator"}
        assert _safe_eval_expression('role == "creator"', ctx) is True

    def test_builtin_disabled(self):
        # Safe eval returns False instead of executing builtins
        assert _safe_eval_expression("__import__('os').system('echo pwned')", {}) is False

    def test_dict_access_blocked(self):
        assert _safe_eval_expression("dict.popitem()", {}) is False

    def test_empty_expression(self):
        assert _safe_eval_expression("", {}) is False

    def test_none_expression(self):
        assert _safe_eval_expression(None, {}) is False


class TestSwitchPath:
    """Test path switching."""

    def test_switch_to_valid_path(self):
        db = MagicMock()
        nav = MagicMock()
        nav.active_path = "onboarding"
        db.query.return_value.filter.return_value.first.side_effect = [nav]
        db.query.return_value.filter.return_value.count.return_value = 5

        result = switch_path(db, "user-1", "compliance")

        assert "error" not in result
        assert result["active_path"] == "compliance"

    def test_switch_invalid_path(self):
        db = MagicMock()
        result = switch_path(db, "user-1", "admin")
        assert "error" in result

    @pytest.mark.parametrize("invalid_path", ["dashboard", "settings"])
    def test_switch_other_invalid_paths(self, invalid_path):
        db = MagicMock()
        result = switch_path(db, "user-1", invalid_path)
        assert "error" in result


class TestCompleteTask:
    """Test task completion."""

    def test_task_not_found(self):
        db = MagicMock()
        nav = MagicMock()
        nav.completed_tasks = []
        db.query.return_value.filter.return_value.first.side_effect = [nav, None]
        result = complete_task(db, "user-1", "nonexistent")
        assert "error" in result

    def test_already_completed(self):
        db = MagicMock()
        nav = MagicMock()
        nav.completed_tasks = ["task-1"]
        nav.active_path = "onboarding"
        task = MagicMock()
        task.task_key = "task-1"
        task.category = "onboarding"
        db.query.return_value.filter.return_value.first.side_effect = [nav, task]
        result = complete_task(db, "user-1", "task-1")
        assert result["status"] == "already_completed"


class TestGetNavigationStatus:
    """Test navigation status retrieval."""

    def test_new_user_creates_record(self):
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = None

        # Mock task query
        task_mock = MagicMock()
        task_mock.task_key = "task-1"
        task_mock.category = "onboarding"
        task_mock.title = "Test Task"
        task_mock.description = "Test Description"
        task_mock.priority = 1
        db.query.return_value.filter.return_value.all.return_value = [task_mock]

        result = get_navigation_status(db, "new-user", "onboarding")

        assert "progress_percent" in result
        assert "current_task" in result
        db.add.assert_called_once()
