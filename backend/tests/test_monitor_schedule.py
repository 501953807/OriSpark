"""Monitor schedule API + Google Vision integration tests."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

import pytest

_BASE = "/api/monitor"


class TestGetSchedule:
    """GET /monitor/schedule"""

    def test_returns_entries(self, client):
        resp = client.get(f"{_BASE}/schedule")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert isinstance(data["schedules"], list)
        assert data["total"] > 0
        for entry in data["schedules"]:
            assert "task" in entry
            assert "schedule_seconds" in entry
            assert "description" in entry

    def test_scheduled_scan_daily_present(self, client):
        resp = client.get(f"{_BASE}/schedule")
        data = resp.json()["data"]["schedules"]
        task_names = {e["task"] for e in data}
        assert "scheduled-scan-daily" in task_names


class TestToggleSchedule:
    """POST /monitor/schedule/toggle"""

    def test_enable_task(self, client):
        resp = client.post(f"{_BASE}/schedule/toggle", params={"task": "scheduled-scan-daily", "enabled": True})
        assert resp.status_code == 200
        body = resp.json()
        assert body["message"] == "任务 scheduled-scan-daily 已启用"

    def test_disable_task(self, client):
        resp = client.post(f"{_BASE}/schedule/toggle", params={"task": "scheduled-scan-daily", "enabled": False})
        assert resp.status_code == 200
        body = resp.json()
        assert body["message"] == "任务 scheduled-scan-daily 已禁用"

    def test_invalid_task_returns_404(self, client):
        resp = client.post(f"{_BASE}/schedule/toggle", params={"task": "nonexistent-task", "enabled": True})
        assert resp.status_code == 404
        body = resp.json()
        assert "不存在" in body.get("detail", "") or "不存在" in body.get("message", "")

    def test_invalid_task_message(self, client):
        resp = client.post(f"{_BASE}/schedule/toggle", params={"task": "fake-task-xyz", "enabled": True})
        assert resp.status_code == 404


class TestGoogleVisionMonitorService:
    """GoogleVisionMonitorService.detect_infringement"""

    def test_detect_infringement_without_api_key(self, client, tmp_path):
        from app.services.google_vision_monitor_service import GoogleVisionMonitorService
        from app.models.work import Work
        from app.models.monitor import MonitorTask

        img_file = tmp_path / "test.png"
        img_file.write_bytes(b"fake-image-data")

        # Inject db into service via test client's session
        from app.database import get_db
        db = next(get_db())

        work = Work(
            id="work_gv_test", title="Test Work", description="test", status="active",
            file_path="/tmp/test_work.bin", file_name="test_work.bin", file_size=100,
            file_type="image", file_extension="png",
        )
        db.add(work)
        db.flush()

        task = MonitorTask(
            id="task_gv_test", work_id="work_gv_test",
            search_type="image", platform="google_vision", interval="manual",
        )
        db.add(task)
        db.flush()

        svc = GoogleVisionMonitorService(db=db)
        results = svc.detect_infringement(str(img_file), "work_gv_test")

        assert isinstance(results, list)
        assert len(results) > 0
        for r in results:
            assert "url" in r
            assert "similarity" in r

    def test_detect_infringement_invalid_work_id(self, client, tmp_path):
        from app.services.google_vision_monitor_service import GoogleVisionMonitorService
        from app.database import get_db

        img_file = tmp_path / "test.png"
        img_file.write_bytes(b"fake-image-data")

        db = next(get_db())
        svc = GoogleVisionMonitorService(db=db)
        with pytest.raises(ValueError):
            svc.detect_infringement(str(img_file), "nonexistent-work")
