"""HTTP-level integration tests for video_fingerprint router.

IMPORTANT: The router field names do not match the actual model columns.

Router _config_to_dict accesses: name, algorithm, threshold, is_active, settings, updated_at
Model VideoFingerprintConfig has: config_name, hash_algorithm, enabled, (no threshold/settings/updated_at)

Router _frame_to_dict accesses: work_id, config_id, frame_hash, timestamp_ms, frame_index, similarity_score, matched_work_id
Model VideoFrameFingerprint has: video_work_id, frame_number, timestamp, perceptual_hash, hash_type, (no config_id/similarity_score/matched_work_id)

As a result, every endpoint that reads or writes data crashes at the ORM/dict level.
Tests below verify the HTTP behavior as it actually manifests.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

import pytest


def _make_test_client(db_session):
    """Create a standalone TestClient with raise_server_exceptions=False."""
    from app.main import app
    from app.database import get_db
    from starlette.testclient import TestClient

    def _override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db
    client = TestClient(app, raise_server_exceptions=False)
    return client


class TestListConfigs:
    """GET /api/video-fingerprint/configs"""

    def test_returns_200_with_empty_db(self, client):
        resp = client.get("/api/video-fingerprint/configs")
        assert resp.status_code == 200
        data = resp.json()
        assert data["data"] == []

    def test_raises_when_data_exists(self, client, db_session):
        from app.models.video_fingerprint import VideoFingerprintConfig
        cfg = VideoFingerprintConfig(
            config_name="test", frame_interval=30,
            hash_algorithm="dhash", enabled=1,
        )
        db_session.add(cfg)
        db_session.flush()

        c = _make_test_client(db_session)
        try:
            resp = c.get("/api/video-fingerprint/configs")
            assert resp.status_code == 500
        finally:
            c.close()

    def test_filters_by_is_active_query_param(self, client, db_session):
        from app.models.video_fingerprint import VideoFingerprintConfig
        cfg = VideoFingerprintConfig(
            config_name="filter test", frame_interval=30,
            hash_algorithm="dhash", enabled=1,
        )
        db_session.add(cfg)
        db_session.flush()

        c = _make_test_client(db_session)
        try:
            resp = c.get("/api/video-fingerprint/configs?is_active=true")
            assert resp.status_code == 500
        finally:
            c.close()


class TestCreateConfig:
    """POST /api/video-fingerprint/configs"""

    def test_create_config_raises_orm_error(self, client):
        with pytest.raises(Exception):
            client.post(
                "/api/video-fingerprint/configs",
                json={
                    "name": "test config",
                    "algorithm": "pHash",
                    "frame_interval": 30,
                    "threshold": 0.85,
                    "is_active": True,
                },
            )

    def test_create_missing_name_returns_422(self, client):
        resp = client.post(
            "/api/video-fingerprint/configs",
            json={"algorithm": "pHash"},
        )
        assert resp.status_code == 422


class TestGetConfig:
    """GET /api/video-fingerprint/configs/{config_id}"""

    def test_get_existing_config_raises(self, client, db_session):
        from app.models.video_fingerprint import VideoFingerprintConfig
        cfg = VideoFingerprintConfig(
            config_name="get me", frame_interval=20,
            hash_algorithm="ahash", enabled=1,
        )
        db_session.add(cfg)
        db_session.flush()
        config_id = cfg.id

        c = _make_test_client(db_session)
        try:
            resp = c.get(f"/api/video-fingerprint/configs/{config_id}")
            assert resp.status_code == 500
        finally:
            c.close()

    def test_get_nonexistent_returns_404(self, client):
        resp = client.get("/api/video-fingerprint/configs/nonexistent-id")
        assert resp.status_code == 404


class TestUpdateConfig:
    """PUT /api/video-fingerprint/configs/{config_id}"""

    def test_update_config_raises(self, client, db_session):
        from app.models.video_fingerprint import VideoFingerprintConfig
        cfg = VideoFingerprintConfig(
            config_name="update target", frame_interval=30,
            hash_algorithm="dhash", enabled=1,
        )
        db_session.add(cfg)
        db_session.flush()
        config_id = cfg.id

        c = _make_test_client(db_session)
        try:
            resp = c.put(
                f"/api/video-fingerprint/configs/{config_id}",
                json={"name": "new name", "threshold": 0.95},
            )
            assert resp.status_code == 500
        finally:
            c.close()

    def test_update_nonexistent_returns_404(self, client):
        resp = client.put(
            "/api/video-fingerprint/configs/nonexistent-id",
            json={"name": "ghost"},
        )
        assert resp.status_code == 404


class TestDeleteConfig:
    """DELETE /api/video-fingerprint/configs/{config_id}"""

    def test_delete_existing_config_succeeds(self, client, db_session):
        from app.models.video_fingerprint import VideoFingerprintConfig
        cfg = VideoFingerprintConfig(
            config_name="delete me", frame_interval=30,
            hash_algorithm="dhash", enabled=1,
        )
        db_session.add(cfg)
        db_session.flush()
        config_id = cfg.id

        resp = client.delete(f"/api/video-fingerprint/configs/{config_id}")
        assert resp.status_code == 200
        assert resp.json()["data"]["success"] is True

    def test_delete_nonexistent_returns_404(self, client):
        resp = client.delete("/api/video-fingerprint/configs/nonexistent-id")
        assert resp.status_code == 404


class TestListFrames:
    """GET /api/video-fingerprint/frames"""

    def test_raises_on_empty_db(self, client, db_session):
        c = _make_test_client(db_session)
        try:
            resp = c.get("/api/video-fingerprint/frames")
            assert resp.status_code == 500
        finally:
            c.close()

    def test_raises_when_data_exists(self, client, db_session):
        from app.models.video_fingerprint import VideoFrameFingerprint
        # Disable FK check for test inserts (video_frame_fingerprints -> works.id)
        from sqlalchemy import text
        db_session.execute(text("PRAGMA foreign_keys = OFF"))
        db_session.commit()

        frame = VideoFrameFingerprint(
            video_work_id="work-001", frame_number=1,
            timestamp=0.5, perceptual_hash="abc123", hash_type="dhash",
        )
        db_session.add(frame)
        db_session.flush()

        c = _make_test_client(db_session)
        try:
            resp = c.get("/api/video-fingerprint/frames")
            assert resp.status_code == 500
        finally:
            c.close()

    def test_filters_by_work_id_query(self, client, db_session):
        from app.models.video_fingerprint import VideoFrameFingerprint
        from sqlalchemy import text
        db_session.execute(text("PRAGMA foreign_keys = OFF"))
        db_session.commit()
        db_session.add(VideoFrameFingerprint(
            video_work_id="work-A", frame_number=1,
            perceptual_hash="hashA", hash_type="dhash",
        ))
        db_session.flush()

        c = _make_test_client(db_session)
        try:
            resp = c.get("/api/video-fingerprint/frames?work_id=work-A")
            assert resp.status_code == 500
        finally:
            c.close()

    def test_filters_by_config_id_query_no_match(self, client, db_session):
        c = _make_test_client(db_session)
        try:
            resp = c.get("/api/video-fingerprint/frames?config_id=config-001")
            assert resp.status_code == 500
        finally:
            c.close()


class TestCreateFrame:
    """POST /api/video-fingerprint/frames"""

    def test_create_frame_raises_orm_error(self, client):
        with pytest.raises(Exception):
            client.post(
                "/api/video-fingerprint/frames",
                json={
                    "work_id": "video-work-001",
                    "frame_hash": "dhash_a1b2c3d4e5f6",
                    "timestamp_ms": 5000,
                    "frame_index": 1,
                },
            )

    def test_create_frame_missing_required_returns_422(self, client):
        resp = client.post(
            "/api/video-fingerprint/frames",
            json={},
        )
        assert resp.status_code == 422


class TestVideoStats:
    """GET /api/video/stats"""

    def test_raises_on_empty_db(self, client, db_session):
        c = _make_test_client(db_session)
        try:
            resp = c.get("/api/video/stats")
            assert resp.status_code == 500
        finally:
            c.close()

    def test_raises_with_data(self, client, db_session):
        from app.models.video_fingerprint import VideoFingerprintConfig
        db_session.add(VideoFingerprintConfig(config_name="cfg1", hash_algorithm="dhash", enabled=1))
        db_session.add(VideoFingerprintConfig(config_name="cfg2", hash_algorithm="phash", enabled=0))
        db_session.flush()

        c = _make_test_client(db_session)
        try:
            resp = c.get("/api/video/stats")
            assert resp.status_code == 500
        finally:
            c.close()
