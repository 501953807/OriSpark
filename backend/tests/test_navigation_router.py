"""Navigation Router HTTP-level integration tests."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

import pytest


_BASE = "/api/navigation"


class TestStatus:
    """GET /navigation/status/{user_id}"""

    def test_status_onboarding(self, client):
        resp = client.get(f"{_BASE}/status/current_user", params={"path": "onboarding"})
        assert resp.status_code == 200
        data = resp.json()
        assert "current_task" in data
        assert "completed_tasks" in data
        assert "active_path" in data

    def test_status_default_path(self, client):
        resp = client.get(f"{_BASE}/status/current_user")
        assert resp.status_code == 200


class TestCompleteTask:
    """POST /navigation/complete/{task_key}"""

    @pytest.mark.skip(reason="FastAPI TestClient raises ResponseValidationError on HTTPException from router without response_model")
    def test_complete_nonexistent_task(self, client):
        resp = client.post(f"{_BASE}/complete/nonexistent_task")
        assert resp.status_code in (400, 500)


class TestListTasks:
    """GET /navigation/tasks"""

    def test_list_onboarding_tasks(self, client):
        resp = client.get(f"{_BASE}/tasks", params={"category": "onboarding"})
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)

    def test_list_distraction_tasks(self, client):
        resp = client.get(f"{_BASE}/tasks", params={"category": "distraction_free"})
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)


class TestSwitchPath:
    """POST /navigation/switch-path"""

    def test_switch_to_compliance(self, client):
        resp = client.post(f"{_BASE}/switch-path", json={"path": "compliance"})
        assert resp.status_code == 200
        data = resp.json()
        assert "active_path" in data

    def test_switch_invalid_path(self, client):
        resp = client.post(f"{_BASE}/switch-path", json={"path": "invalid_path"})
        assert resp.status_code in (400, 500)
