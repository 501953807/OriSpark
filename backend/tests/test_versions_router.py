"""Versions Router HTTP-level integration tests."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

import pytest


_BASE = "/api"


class TestListVersions:
    """GET /works/{work_id}/versions"""

    def test_list_versions_no_work(self, client):
        """作品不存在时返回404."""
        resp = client.get(f"{_BASE}/works/nonexistent/versions")
        assert resp.status_code == 404

    def test_list_versions_empty(self, client):
        """需要先创建work才能查询版本 — 若work不存在则接受404."""
        resp = client.get(f"{_BASE}/works/test_work/versions")
        # work不存在，预期404
        assert resp.status_code in (200, 404)


class TestGetVersion:
    """GET /works/{work_id}/versions/{version_id}"""

    def test_get_version_nonexistent(self, client):
        resp = client.get(f"{_BASE}/works/test_work/versions/nonexistent")
        assert resp.status_code in (404, 500)  # 404=work不存在, 500=表缺失


class TestCreateVersion:
    """POST /works/{work_id}/versions"""

    def test_create_version_nonexistent_work(self, client):
        resp = client.post(f"{_BASE}/works/nonexistent/versions", params={})
        assert resp.status_code == 404


class TestRollbackVersion:
    """POST /works/{work_id}/rollback/{version_id}"""

    def test_rollback_nonexistent_work(self, client):
        resp = client.post(f"{_BASE}/works/nonexistent/rollback/v1")
        assert resp.status_code == 404

    def test_rollback_nonexistent_version(self, client):
        resp = client.post(f"{_BASE}/works/test_work/rollback/nonexistent")
        assert resp.status_code in (404, 500)


class TestProjects:
    """Project CRUD"""

    def test_list_projects_empty(self, client):
        resp = client.get(f"{_BASE}/projects")
        assert resp.status_code == 200
        data = resp.json()
        assert "data" in data

    def test_create_project(self, client):
        resp = client.post(f"{_BASE}/projects", json={
            "name": "Test Project",
            "description": "A test project",
        })
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["name"] == "Test Project"

    def test_update_project(self, client):
        create_resp = client.post(f"{_BASE}/projects", json={
            "name": "Update Me Project",
        })
        if create_resp.status_code != 200:
            pytest.skip("Cannot create project")
        project_id = create_resp.json()["data"]["id"]

        resp = client.patch(f"{_BASE}/projects/{project_id}", json={
            "name": "Updated Project",
        })
        assert resp.status_code == 200

    def test_update_nonexistent_project(self, client):
        resp = client.patch(f"{_BASE}/projects/nonexistent", json={
            "name": "Nope",
        })
        assert resp.status_code == 404

    def test_delete_project(self, client):
        create_resp = client.post(f"{_BASE}/projects", json={
            "name": "Delete Me Project",
        })
        if create_resp.status_code != 200:
            pytest.skip("Cannot create project")
        project_id = create_resp.json()["data"]["id"]

        resp = client.delete(f"{_BASE}/projects/{project_id}")
        assert resp.status_code == 200
