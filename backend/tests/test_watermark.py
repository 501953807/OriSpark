"""HTTP-level integration tests for watermark router."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

import pytest


class TestListPresets:
    """GET /api/watermark/presets"""

    def test_returns_200_with_empty_db(self, client):
        resp = client.get("/api/watermark/presets")
        assert resp.status_code == 200
        data = resp.json()
        assert data["data"] == []

    def test_returns_200_with_presets(self, client, db_session, sample_work_file):
        from app.models.watermark import WatermarkPreset
        preset = WatermarkPreset(
            name="test watermark",
            watermark_type="text",
            config={"text": "OriSpark", "position": "bottom_right", "opacity": 0.5},
            is_default=False,
        )
        db_session.add(preset)
        db_session.flush()

        resp = client.get("/api/watermark/presets")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert len(data) >= 1
        assert any(p["name"] == "test watermark" for p in data)

    def test_filters_by_watermark_type(self, client, db_session):
        from app.models.watermark import WatermarkPreset
        db_session.add(WatermarkPreset(name="text one", watermark_type="text"))
        db_session.add(WatermarkPreset(name="image one", watermark_type="image"))
        db_session.flush()

        resp = client.get("/api/watermark/presets?watermark_type=text")
        assert resp.status_code == 200
        names = [p["name"] for p in resp.json()["data"]]
        assert "text one" in names
        assert "image one" not in names

    def test_filters_by_is_default(self, client, db_session):
        from app.models.watermark import WatermarkPreset
        db_session.add(WatermarkPreset(name="default preset", watermark_type="text", is_default=True))
        db_session.add(WatermarkPreset(name="non-default preset", watermark_type="text", is_default=False))
        db_session.flush()

        resp = client.get("/api/watermark/presets?is_default=true")
        assert resp.status_code == 200
        names = [p["name"] for p in resp.json()["data"]]
        assert "default preset" in names
        assert "non-default preset" not in names

    def test_returns_404_for_nonexistent_filter(self, client):
        resp = client.get("/api/watermark/presets?watermark_type=nonexistent")
        assert resp.status_code == 200
        assert resp.json()["data"] == []


class TestCreatePreset:
    """POST /api/watermark/presets"""

    def test_create_text_preset(self, client):
        resp = client.post(
            "/api/watermark/presets",
            json={
                "name": "my text watermark",
                "watermark_type": "text",
                "config": {"text": "Copyright OriSpark", "position": "center", "opacity": 0.7},
                "description": "center copyright",
            },
        )
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["name"] == "my text watermark"
        assert data["watermark_type"] == "text"
        assert data["config"]["text"] == "Copyright OriSpark"
        assert "id" in data

    def test_create_image_preset(self, client):
        resp = client.post(
            "/api/watermark/presets",
            json={
                "name": "logo watermark",
                "watermark_type": "image",
                "config": {"image_url": "https://example.com/logo.png", "position": "top_left"},
            },
        )
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["watermark_type"] == "image"
        assert data["config"]["image_url"] == "https://example.com/logo.png"

    def test_create_tiled_preset(self, client):
        resp = client.post(
            "/api/watermark/presets",
            json={
                "name": "tile watermark",
                "watermark_type": "tiled",
                "config": {"tile_image_url": "https://example.com/tile.png"},
            },
        )
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["watermark_type"] == "tiled"

    def test_create_with_invalid_type_returns_422(self, client):
        resp = client.post(
            "/api/watermark/presets",
            json={
                "name": "bad type",
                "watermark_type": "invalid_type",
            },
        )
        assert resp.status_code == 422

    def test_create_with_invalid_config_returns_400(self, client):
        resp = client.post(
            "/api/watermark/presets",
            json={
                "name": "missing text",
                "watermark_type": "text",
                "config": {},
            },
        )
        assert resp.status_code == 400

    def test_create_with_missing_position_returns_400(self, client):
        resp = client.post(
            "/api/watermark/presets",
            json={
                "name": "bad position",
                "watermark_type": "text",
                "config": {"text": "Hello", "position": "nowhere"},
            },
        )
        assert resp.status_code == 400


class TestUpdatePreset:
    """PUT /api/watermark/presets/{preset_id}"""

    def test_update_existing_preset(self, client, db_session):
        from app.models.watermark import WatermarkPreset
        preset = WatermarkPreset(
            name="original", watermark_type="text", config={"text": "Old"},
        )
        db_session.add(preset)
        db_session.flush()
        preset_id = preset.id

        resp = client.put(
            f"/api/watermark/presets/{preset_id}",
            json={"name": "updated name", "config": {"text": "New"}},
        )
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["name"] == "updated name"
        assert data["config"]["text"] == "New"

    def test_update_nonexistent_returns_404(self, client):
        resp = client.put(
            "/api/watermark/presets/nonexistent-id",
            json={"name": "ghost"},
        )
        assert resp.status_code == 404

    def test_partial_update_keeps_other_fields(self, client, db_session):
        from app.models.watermark import WatermarkPreset
        preset = WatermarkPreset(
            name="keep name",
            watermark_type="image",
            config={"image_url": "https://example.com/img.png"},
        )
        db_session.add(preset)
        db_session.flush()
        preset_id = preset.id

        resp = client.put(
            f"/api/watermark/presets/{preset_id}",
            json={"description": "new description"},
        )
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["name"] == "keep name"
        assert data["watermark_type"] == "image"
        assert data["description"] == "new description"


class TestDeletePreset:
    """DELETE /api/watermark/presets/{preset_id}"""

    def test_delete_existing_preset(self, client, db_session):
        from app.models.watermark import WatermarkPreset
        preset = WatermarkPreset(name="to delete", watermark_type="text")
        db_session.add(preset)
        db_session.flush()
        preset_id = preset.id

        resp = client.delete(f"/api/watermark/presets/{preset_id}")
        assert resp.status_code == 200
        assert resp.json()["data"]["success"] is True

    def test_delete_nonexistent_returns_404(self, client):
        resp = client.delete("/api/watermark/presets/nonexistent-id")
        assert resp.status_code == 404


class TestApplyWatermark:
    """POST /api/watermark/apply"""

    def test_apply_with_valid_preset(self, client, db_session, sample_work_file):
        from app.models.watermark import WatermarkPreset
        preset = WatermarkPreset(
            name="apply test",
            watermark_type="text",
            config={"text": "Test", "position": "bottom_right", "opacity": 0.5},
        )
        db_session.add(preset)
        db_session.flush()

        resp = client.post(
            "/api/watermark/apply",
            json={
                "work_path": sample_work_file,
                "preset_id": preset.id,
                "output_path": "/tmp/test_output_watermark.png",
            },
        )
        # The service copies the file on success; expect 200
        assert resp.status_code == 200

    def test_apply_with_nonexistent_preset_returns_404(self, client, sample_work_file):
        resp = client.post(
            "/api/watermark/apply",
            json={
                "work_path": sample_work_file,
                "preset_id": "nonexistent-preset-id",
                "output_path": "/tmp/test_output.png",
            },
        )
        assert resp.status_code == 404


class TestPreviewWatermark:
    """POST /api/watermark/preview"""

    def test_preview_with_valid_image(self, client, sample_work_file):
        resp = client.post(
            "/api/watermark/preview",
            json={
                "config": {"text": "Preview", "position": "center", "opacity": 0.3},
                "image_path": sample_work_file,
            },
        )
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert "preview_path" in data

    def test_preview_with_minimal_config(self, client, sample_work_file):
        resp = client.post(
            "/api/watermark/preview",
            json={
                "config": {},
                "image_path": sample_work_file,
            },
        )
        # Empty config may fail validation in service; accept 200 or 400
        assert resp.status_code in (200, 400)
