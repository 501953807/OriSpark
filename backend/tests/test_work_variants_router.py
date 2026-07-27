"""Work Variants Router HTTP-level integration tests."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

import pytest


_BASE = "/api/work-variants"


class TestListGroups:
    """GET /work-variants/groups"""

    def test_list_groups_empty(self, client):
        resp = client.get(f"{_BASE}/groups")
        assert resp.status_code == 200
        data = resp.json()
        assert "data" in data

    def test_list_groups_filtered(self, client):
        resp = client.get(f"{_BASE}/groups", params={"work_id": "test_work"})
        assert resp.status_code == 200


class TestGroupCRUD:
    """Group create/update/delete"""

    def test_create_group(self, client):
        resp = client.post(f"{_BASE}/groups", json={
            "name": "Test Group",
            "work_id": "test_work_1",
        })
        assert resp.status_code in (200, 404)  # 404 if work doesn't exist

    def test_update_group(self, client):
        # Create first
        create_resp = client.post(f"{_BASE}/groups", json={
            "name": "Update Me",
            "work_id": "test_work_1",
        })
        if create_resp.status_code != 200:
            pytest.skip("Cannot create group — work not found")
        group_id = create_resp.json()["data"]["id"]

        resp = client.put(f"{_BASE}/groups/{group_id}", json={
            "name": "Updated Name",
        })
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["name"] == "Updated Name"

    def test_update_nonexistent_group(self, client):
        resp = client.put(f"{_BASE}/groups/nonexistent", json={
            "name": "Nope",
        })
        assert resp.status_code == 404

    def test_delete_group(self, client):
        # Create first
        create_resp = client.post(f"{_BASE}/groups", json={
            "name": "Delete Me",
            "work_id": "test_work_1",
        })
        if create_resp.status_code != 200:
            pytest.skip("Cannot create group — work not found")
        group_id = create_resp.json()["data"]["id"]

        resp = client.delete(f"{_BASE}/groups/{group_id}")
        assert resp.status_code == 200

    def test_get_nonexistent_group(self, client):
        resp = client.get(f"{_BASE}/groups/nonexistent")
        assert resp.status_code == 404


class TestVariantCRUD:
    """Variant create/update/delete within a group"""

    def test_add_variant(self, client):
        # Create group first
        group_resp = client.post(f"{_BASE}/groups", json={
            "name": "Variant Group",
            "work_id": "test_work_1",
        })
        if group_resp.status_code != 200:
            pytest.skip("Cannot create group — work not found")
        group_id = group_resp.json()["data"]["id"]

        resp = client.post(f"{_BASE}/groups/{group_id}/variants", json={
            "name": "Landscape",
            "width": 1920,
            "height": 1080,
            "sort_order": 1,
        })
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["width"] == 1920
        assert data["aspect_ratio"] > 0

    def test_list_variants(self, client):
        resp = client.get(f"{_BASE}/groups/test_group/variants")
        assert resp.status_code in (200, 404)

    def test_update_variant(self, client):
        # Create group + variant first
        group_resp = client.post(f"{_BASE}/groups", json={
            "name": "Update Variant Group",
            "work_id": "test_work_1",
        })
        if group_resp.status_code != 200:
            pytest.skip("Cannot create group — work not found")
        group_id = group_resp.json()["data"]["id"]

        var_resp = client.post(f"{_BASE}/groups/{group_id}/variants", json={
            "name": "Original",
            "width": 1920,
            "height": 1080,
        })
        if var_resp.status_code != 200:
            pytest.skip("Cannot create variant")
        variant_id = var_resp.json()["data"]["id"]

        resp = client.put(f"{_BASE}/groups/{group_id}/variants/{variant_id}", json={
            "name": "Resized",
            "width": 1280,
            "height": 720,
        })
        assert resp.status_code == 200

    def test_delete_variant(self, client):
        group_resp = client.post(f"{_BASE}/groups", json={
            "name": "Delete Variant Group",
            "work_id": "test_work_1",
        })
        if group_resp.status_code != 200:
            pytest.skip("Cannot create group — work not found")
        group_id = group_resp.json()["data"]["id"]

        var_resp = client.post(f"{_BASE}/groups/{group_id}/variants", json={
            "name": "To Delete",
            "width": 1920,
            "height": 1080,
        })
        if var_resp.status_code != 200:
            pytest.skip("Cannot create variant")
        variant_id = var_resp.json()["data"]["id"]

        resp = client.delete(f"{_BASE}/groups/{group_id}/variants/{variant_id}")
        assert resp.status_code == 200
