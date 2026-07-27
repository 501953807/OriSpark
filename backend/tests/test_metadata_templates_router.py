"""Metadata Templates Router HTTP-level integration tests."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

import pytest


_BASE = "/api/metadata-templates"


class TestListTemplates:
    """GET /metadata-templates"""

    def test_list_templates(self, client):
        resp = client.get(f"{_BASE}")
        assert resp.status_code == 200
        data = resp.json()
        assert "data" in data

    def test_list_default_only(self, client):
        resp = client.get(f"{_BASE}", params={"is_default": "true"})
        assert resp.status_code == 200


class TestTemplateCRUD:
    """Template create/update/delete"""

    def test_create_template(self, client):
        resp = client.post(f"{_BASE}", json={
            "name": "Custom Template",
            "description": "My custom template",
            "is_default": False,
        })
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["name"] == "Custom Template"

    def test_update_template(self, client):
        create_resp = client.post(f"{_BASE}", json={
            "name": "Update Me Template",
        })
        if create_resp.status_code != 200:
            pytest.skip("Cannot create template")
        template_id = create_resp.json()["data"]["id"]

        resp = client.put(f"{_BASE}/{template_id}", json={
            "name": "Updated Template",
            "description": "Modified description",
        })
        assert resp.status_code == 200
        assert resp.json()["data"]["name"] == "Updated Template"

    def test_update_nonexistent_template(self, client):
        resp = client.put(f"{_BASE}/nonexistent", json={
            "name": "Nope",
        })
        assert resp.status_code == 404

    def test_delete_template(self, client):
        create_resp = client.post(f"{_BASE}", json={
            "name": "Delete Me Template",
        })
        if create_resp.status_code != 200:
            pytest.skip("Cannot create template")
        template_id = create_resp.json()["data"]["id"]

        resp = client.delete(f"{_BASE}/{template_id}")
        assert resp.status_code == 200


class TestFieldCRUD:
    """Template field management"""

    def test_add_field(self, client):
        # Create template first
        tpl_resp = client.post(f"{_BASE}", json={
            "name": "Field Template",
        })
        if tpl_resp.status_code != 200:
            pytest.skip("Cannot create template")
        template_id = tpl_resp.json()["data"]["id"]

        resp = client.post(f"{_BASE}/{template_id}/fields", json={
            "field_key": "custom_field",
            "label": "Custom Label",
            "field_type": "string",
            "required": True,
        })
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["field_key"] == "custom_field"

    def test_list_fields(self, client):
        resp = client.get(f"{_BASE}/test_template/fields")
        assert resp.status_code in (200, 404)

    def test_update_field(self, client):
        tpl_resp = client.post(f"{_BASE}", json={
            "name": "Update Field Template",
        })
        if tpl_resp.status_code != 200:
            pytest.skip("Cannot create template")
        template_id = tpl_resp.json()["data"]["id"]

        field_resp = client.post(f"{_BASE}/{template_id}/fields", json={
            "field_key": "update_me",
            "label": "Original Label",
        })
        if field_resp.status_code != 200:
            pytest.skip("Cannot create field")
        field_id = field_resp.json()["data"]["id"]

        resp = client.put(f"{_BASE}/{template_id}/fields/{field_id}", json={
            "label": "Updated Label",
        })
        assert resp.status_code == 200

    def test_delete_field(self, client):
        tpl_resp = client.post(f"{_BASE}", json={
            "name": "Delete Field Template",
        })
        if tpl_resp.status_code != 200:
            pytest.skip("Cannot create template")
        template_id = tpl_resp.json()["data"]["id"]

        field_resp = client.post(f"{_BASE}/{template_id}/fields", json={
            "field_key": "delete_me",
            "label": "To Delete",
        })
        if field_resp.status_code != 200:
            pytest.skip("Cannot create field")
        field_id = field_resp.json()["data"]["id"]

        resp = client.delete(f"{_BASE}/{template_id}/fields/{field_id}")
        assert resp.status_code == 200


class TestApplyTemplate:
    """POST /metadata-templates/{id}/apply"""

    def test_apply_template(self, client):
        tpl_resp = client.post(f"{_BASE}", json={
            "name": "Apply Template",
        })
        if tpl_resp.status_code != 200:
            pytest.skip("Cannot create template")
        template_id = tpl_resp.json()["data"]["id"]

        resp = client.post(f"{_BASE}/{template_id}/apply", json={
            "work_id": "test_work_1",
        })
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["work_id"] == "test_work_1"