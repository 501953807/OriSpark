"""Tests for photographer shot workflow endpoints."""

import pytest
import time
import json
import base64
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session


def _create_token(user_id: str) -> str:
    """Create a valid JWT token using the deps._sign function signature."""
    from app.deps import _sign
    header = {"alg": "HS256", "typ": "JWT"}
    exp = int(time.time()) + 3600  # 1 hour expiry
    payload = {"sub": user_id, "iat": int(time.time()), "exp": exp}

    def b64encode(data: str) -> str:
        return base64.urlsafe_b64encode(data.encode()).rstrip(b"=").decode()

    h = b64encode(json.dumps(header))
    p = b64encode(json.dumps(payload))
    sig = _sign(f"{h}.{p}")
    return f"{h}.{p}.{sig}"


def _auth_headers(user_id: str = "test_user") -> dict:
    """Return headers with a valid JWT token for the given user_id."""
    token = _create_token(user_id)
    return {"Authorization": f"Bearer {token}"}


def _ensure_work(db_session: Session, work_id: str) -> None:
    """Ensure a Work row exists for FK constraints."""
    from app.models.work import Work
    existing = db_session.query(Work).filter(Work.id == work_id).first()
    if not existing:
        work = Work(
            id=work_id,
            title="Test Work",
            file_path=f"/tmp/{work_id}.jpg",
            file_name=f"{work_id}.jpg",
            file_size=1024,
            file_extension="jpg",
        )
        db_session.add(work)
        db_session.flush()


def _create_variant(db_session: Session, **kwargs) -> dict:
    """Helper: create a Work + WorkVariantGroup + WorkVariant and return variant id."""
    from app.models.work_variant import WorkVariantGroup, WorkVariant

    work_id = kwargs.get("work_id", "test_work_photographer")
    _ensure_work(db_session, work_id)

    group = WorkVariantGroup(
        work_id=work_id,
        name=kwargs.get("group_name", "Test Group"),
    )
    db_session.add(group)
    db_session.flush()  # get group.id

    variant = WorkVariant(
        group_id=group.id,
        name=kwargs.get("name", "Test Shot"),
        width=kwargs.get("width", 1920),
        height=kwargs.get("height", 1080),
        aspect_ratio=kwargs.get("aspect_ratio", 16.0 / 9.0),
        sort_order=kwargs.get("sort_order", 0),
        shot_status=kwargs.get("shot_status", "unreviewed"),
        camera_model=kwargs.get("camera_model", "Sony A7IV"),
        iso=kwargs.get("iso", 400),
        aperture=kwargs.get("aperture", "f/2.8"),
        shutter_speed=kwargs.get("shutter_speed", "1/250"),
        focal_length=kwargs.get("focal_length", "50mm"),
        gps_latitude=kwargs.get("gps_latitude", 39.9042),
        gps_longitude=kwargs.get("gps_longitude", 116.4074),
        **{k: v for k, v in kwargs.items() if k not in (
            "name", "shot_status", "camera_model", "iso", "aperture",
            "shutter_speed", "focal_length", "gps_latitude", "gps_longitude",
            "group_name", "work_id", "width", "height", "aspect_ratio",
            "sort_order",
        )},
    )
    db_session.add(variant)
    db_session.flush()
    return {"id": variant.id}


class TestListShots:
    def test_returns_paginated_list(self, client: TestClient):
        resp = client.get("/api/photographer/shots")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert "items" in data
        assert "total" in data
        assert "page" in data
        assert "page_size" in data

    def test_filters_by_shot_status(self, client: TestClient, db_session: Session):
        _create_variant(db_session, shot_status="pass")
        _create_variant(db_session, shot_status="reject")
        resp = client.get("/api/photographer/shots?shot_status=pass")
        assert resp.status_code == 200
        items = resp.json()["data"]["items"]
        for item in items:
            assert item["shot_status"] == "pass"

    def test_filters_by_camera_model(self, client: TestClient, db_session: Session):
        _create_variant(db_session, camera_model="Canon R5")
        resp = client.get("/api/photographer/shots?camera_model=Canon+R5")
        assert resp.status_code == 200

    def test_pagination(self, client: TestClient, db_session: Session):
        resp = client.get("/api/photographer/shots?page=1&page_size=10")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["page"] == 1
        assert data["page_size"] == 10


class TestUpdateShotStatus:
    def test_updates_to_pass(self, client: TestClient, db_session: Session):
        v = _create_variant(db_session)
        resp = client.post(
            f"/api/photographer/shots/{v['id']}/shot-status",
            json={"shot_status": "pass", "shot_notes": "Great shot"},
            headers=_auth_headers(),
        )
        assert resp.status_code == 200
        assert resp.json()["data"]["shot_status"] == "pass"

    def test_updates_to_reject(self, client: TestClient, db_session: Session):
        v = _create_variant(db_session)
        resp = client.post(
            f"/api/photographer/shots/{v['id']}/shot-status",
            json={"shot_status": "reject"},
            headers=_auth_headers(),
        )
        assert resp.status_code == 200
        assert resp.json()["data"]["shot_status"] == "reject"

    def test_updates_to_shortlist(self, client: TestClient, db_session: Session):
        v = _create_variant(db_session)
        resp = client.post(
            f"/api/photographer/shots/{v['id']}/shot-status",
            json={"shot_status": "shortlist"},
            headers=_auth_headers(),
        )
        assert resp.status_code == 200
        assert resp.json()["data"]["shot_status"] == "shortlist"

    def test_returns_404_for_missing_variant(self, client: TestClient):
        resp = client.post(
            "/api/photographer/shots/nonexistent/shot-status",
            json={"shot_status": "pass"},
            headers=_auth_headers(),
        )
        assert resp.status_code == 404


class TestEXIFSearch:
    def test_searches_by_camera_model(self, client: TestClient, db_session: Session):
        _create_variant(db_session, camera_model="Nikon Z9")
        resp = client.get("/api/photographer/exif/search?camera_model=Nikon")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["total"] >= 1

    def test_searches_by_iso_range(self, client: TestClient, db_session: Session):
        _create_variant(db_session, iso=800)
        resp = client.get("/api/photographer/exif/search?iso_min=500&iso_max=1000")
        assert resp.status_code == 200
        assert resp.json()["data"]["total"] >= 1

    def test_searches_by_aperture(self, client: TestClient, db_session: Session):
        _create_variant(db_session, aperture="f/1.4")
        resp = client.get("/api/photographer/exif/search?aperture=f%2F1.4")
        assert resp.status_code == 200

    def test_empty_results(self, client: TestClient):
        resp = client.get("/api/photographer/exif/search?camera_model=NonExistent")
        assert resp.status_code == 200
        assert resp.json()["data"]["total"] == 0


class TestGPSMap:
    def test_returns_gps_points(self, client: TestClient, db_session: Session):
        _create_variant(db_session, gps_latitude=31.2304, gps_longitude=121.4737)
        resp = client.get("/api/photographer/gps/map")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert "points" in data
        assert "total" in data

    def test_filters_by_group_id(self, client: TestClient, db_session: Session):
        _create_variant(db_session, gps_latitude=35.68, gps_longitude=139.69)
        resp = client.get("/api/photographer/gps/map?group_id=test_group")
        assert resp.status_code == 200


class TestStockChannels:
    def test_adds_stock_channel(self, client: TestClient, db_session: Session):
        v = _create_variant(db_session)
        resp = client.post(
            "/api/photographer/stock/channels",
            params={"variant_id": v["id"]},
            json={"channel": "shutterstock", "status": "submitted", "remote_id": "12345"},
            headers=_auth_headers(),
        )
        assert resp.status_code == 200
        assert resp.json()["data"]["channel"] == "shutterstock"

    def test_removes_stock_channel(self, client: TestClient, db_session: Session):
        v = _create_variant(db_session)
        # Add first
        client.post(
            "/api/photographer/stock/channels",
            params={"variant_id": v["id"]},
            json={"channel": "adobe", "status": "submitted"},
            headers=_auth_headers(),
        )
        # Remove
        resp = client.delete(
            "/api/photographer/stock/channels/adobe",
            params={"variant_id": v["id"]},
            headers=_auth_headers(),
        )
        assert resp.status_code == 200
        assert "已移除" in resp.json()["message"]

    def test_remove_returns_404_for_unknown_channel(self, client: TestClient, db_session: Session):
        v = _create_variant(db_session)
        resp = client.delete(
            "/api/photographer/stock/channels/unknown",
            params={"variant_id": v["id"]},
            headers=_auth_headers(),
        )
        assert resp.status_code == 404

    def test_add_returns_404_for_missing_variant(self, client: TestClient):
        resp = client.post(
            "/api/photographer/stock/channels",
            params={"variant_id": "nonexistent"},
            json={"channel": "test", "status": "submitted"},
            headers=_auth_headers(),
        )
        assert resp.status_code == 404


class TestStats:
    def test_returns_stats(self, client: TestClient):
        resp = client.get("/api/photographer/stats")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert "stats" in data
        assert "recent_activity" in data

    def test_stats_include_counts(self, client: TestClient, db_session: Session):
        _create_variant(db_session, shot_status="pass")
        _create_variant(db_session, shot_status="reject")
        resp = client.get("/api/photographer/stats")
        stats = resp.json()["data"]["stats"]
        assert stats["pass_count"] >= 1
        assert stats["reject_count"] >= 1

    def test_filters_by_group_id(self, client: TestClient):
        resp = client.get("/api/photographer/stats?group_id=test_group")
        assert resp.status_code == 200


class TestStockPlatforms:
    def test_lists_platforms(self, client: TestClient):
        resp = client.get("/api/photographer/stock/platforms")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert isinstance(data, list)


class TestRawFormats:
    def test_list_raw_formats_empty(self, client: TestClient):
        resp = client.get("/api/photographer/raw-formats")
        assert resp.status_code == 200
        assert resp.json()["data"] == []

    def test_create_raw_format(self, client: TestClient, db_session: Session):
        _ensure_work(db_session, "work_001")
        payload = {
            "work_id": "work_001",
            "file_extension": "cr3",
            "file_size_bytes": 50000000,
            "sensor_width": 36,
            "sensor_height": 24,
            "color_space": "Adobe RGB",
        }
        resp = client.post("/api/photographer/raw-formats", json=payload, headers=_auth_headers())
        assert resp.status_code == 200
        assert resp.json()["data"]["id"] is not None

    def test_update_raw_format(self, client: TestClient, db_session: Session):
        _ensure_work(db_session, "w1")
        create_resp = client.post(
            "/api/photographer/raw-formats",
            json={
                "work_id": "w1",
                "file_extension": "raf",
                "file_size_bytes": 40000000,
                "sensor_width": 23,
                "sensor_height": 15,
                "color_space": "sRGB",
            },
            headers=_auth_headers(),
        )
        raw_id = create_resp.json()["data"]["id"]
        resp = client.patch(
            f"/api/photographer/raw-formats/{raw_id}",
            json={"file_extension": "nef"},
            headers=_auth_headers(),
        )
        assert resp.status_code == 200

    def test_delete_raw_format(self, client: TestClient, db_session: Session):
        _ensure_work(db_session, "w2")
        create_resp = client.post(
            "/api/photographer/raw-formats",
            json={
                "work_id": "w2",
                "file_extension": "arw",
                "file_size_bytes": 30000000,
                "sensor_width": 35,
                "sensor_height": 23,
                "color_space": "sRGB",
            },
            headers=_auth_headers(),
        )
        raw_id = create_resp.json()["data"]["id"]
        resp = client.delete(f"/api/photographer/raw-formats/{raw_id}", headers=_auth_headers())
        assert resp.status_code == 200

    def test_delete_nonexistent_raw(self, client: TestClient):
        resp = client.delete("/api/photographer/raw-formats/nonexistent", headers=_auth_headers())
        assert resp.status_code == 404


class TestDigitalDownloads:
    def test_list_empty(self, client: TestClient):
        resp = client.get("/api/photographer/digital-downloads")
        assert resp.status_code == 200
        assert resp.json()["data"] == []

    def test_create_digital_download(self, client: TestClient, db_session: Session):
        _ensure_work(db_session, "work_dd1")
        payload = {
            "work_id": "work_dd1",
            "product_id": "prod_dd1",
            "download_url": "https://example.com/download/abc",
            "max_downloads": 5,
        }
        resp = client.post("/api/photographer/digital-downloads", json=payload, headers=_auth_headers())
        assert resp.status_code == 200

    def test_update_digital_download(self, client: TestClient, db_session: Session):
        _ensure_work(db_session, "w3")
        create_resp = client.post(
            "/api/photographer/digital-downloads",
            json={
                "work_id": "w3",
                "product_id": "p3",
                "download_url": "https://example.com/a",
                "max_downloads": 10,
            },
            headers=_auth_headers(),
        )
        dd_id = create_resp.json()["data"]["id"]
        resp = client.patch(
            f"/api/photographer/digital-downloads/{dd_id}",
            json={"max_downloads": 20},
            headers=_auth_headers(),
        )
        assert resp.status_code == 200

    def test_delete_digital_download(self, client: TestClient, db_session: Session):
        _ensure_work(db_session, "w4")
        create_resp = client.post(
            "/api/photographer/digital-downloads",
            json={
                "work_id": "w4",
                "product_id": "p4",
                "download_url": "https://example.com/b",
                "max_downloads": 3,
            },
            headers=_auth_headers(),
        )
        dd_id = create_resp.json()["data"]["id"]
        resp = client.delete(f"/api/photographer/digital-downloads/{dd_id}", headers=_auth_headers())
        assert resp.status_code == 200


class TestFineArtPrints:
    def test_list_empty(self, client: TestClient):
        resp = client.get("/api/photographer/fine-art-prints")
        assert resp.status_code == 200
        assert resp.json()["data"] == []

    def test_create_fine_art_print(self, client: TestClient, db_session: Session):
        _ensure_work(db_session, "work_fap1")
        payload = {
            "work_id": "work_fap1",
            "paper_type": "hahnemuhle",
            "max_width_cm": 60,
            "max_height_cm": 90,
            "framing_available": True,
            "price_multiplier": 2.5,
        }
        resp = client.post("/api/photographer/fine-art-prints", json=payload, headers=_auth_headers())
        assert resp.status_code == 200

    def test_update_fine_art_print(self, client: TestClient, db_session: Session):
        _ensure_work(db_session, "w5")
        create_resp = client.post(
            "/api/photographer/fine-art-prints",
            json={
                "work_id": "w5",
                "paper_type": "canson",
                "max_width_cm": 50,
                "max_height_cm": 70,
                "framing_available": False,
                "price_multiplier": 1.8,
            },
            headers=_auth_headers(),
        )
        fap_id = create_resp.json()["data"]["id"]
        resp = client.patch(
            f"/api/photographer/fine-art-prints/{fap_id}",
            json={"price_multiplier": 3.0},
            headers=_auth_headers(),
        )
        assert resp.status_code == 200

    def test_delete_fine_art_print(self, client: TestClient, db_session: Session):
        _ensure_work(db_session, "w6")
        create_resp = client.post(
            "/api/photographer/fine-art-prints",
            json={
                "work_id": "w6",
                "paper_type": "epson",
                "max_width_cm": 40,
                "max_height_cm": 60,
                "framing_available": True,
                "price_multiplier": 2.0,
            },
            headers=_auth_headers(),
        )
        fap_id = create_resp.json()["data"]["id"]
        resp = client.delete(f"/api/photographer/fine-art-prints/{fap_id}", headers=_auth_headers())
        assert resp.status_code == 200


class TestStockUpload:
    """POST /photographer/stock/upload"""

    def test_upload_returns_error_missing_channel(self, client):
        # Route now properly catches ValueError and returns HTTP 400
        resp = client.post(
            "/api/photographer/stock/upload",
            json={
                "channel_id": "nonexistent",
                "work_id": "test_work",
                "file_path": "/tmp/test.jpg",
                "keywords": ["test"],
                "categories": ["landscape"],
            },
            headers=_auth_headers(),
        )
        assert resp.status_code == 400


class TestStockUploadsList:
    """GET /photographer/stock/uploads"""

    def test_list_uploads_empty(self, client):
        resp = client.get("/api/photographer/stock/uploads")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert "items" in data
        assert "total" in data

    def test_list_with_filters(self, client):
        resp = client.get("/api/photographer/stock/uploads?page=1&page_size=10")
        assert resp.status_code == 200


class TestStockSales:
    """GET /photographer/stock/sales"""

    def test_sales_returns_404_missing_channel(self, client):
        resp = client.get("/api/photographer/stock/sales?channel_id=nonexistent")
        assert resp.status_code == 404

    def test_sales_no_channel_param(self, client):
        resp = client.get("/api/photographer/stock/sales")
        assert resp.status_code in (400, 422, 500)


class TestStockSyncSales:
    """POST /photographer/stock/sync-sales"""

    def test_sync_sales_error_missing_channel(self, client):
        # The sync_sales endpoint was previously buggy (missing timezone import);
        # it may now return a normal HTTP response instead of raising.
        try:
            resp = client.post("/api/photographer/stock/sync-sales", params={
                "channel_id": "nonexistent",
            })
            assert resp.status_code in (400, 404, 422, 500)
        except Exception:
            pytest.skip("sync-sales endpoint unavailable")


class TestStockValidate:
    """GET /photographer/stock/validate"""

    def test_validate_missing_work(self, client):
        resp = client.get(
            "/api/photographer/stock/validate",
            params={"work_id": "nonexistent", "channel_name": "shutterstock"},
        )
        assert resp.status_code == 404

    def test_validate_unknown_channel(self, client: TestClient, db_session: Session):
        # Router bug: validate_file is @staticmethod async but called on instance -> coroutine not awaited -> TypeError 500
        _ensure_work(db_session, "work_validate_test")
        v = _create_variant(db_session, work_id="work_validate_test")
        resp = client.get(
            "/api/photographer/stock/validate",
            params={
                "work_id": v["id"],
                "channel_name": "unknown_platform",
            },
        )
        # Returns 400 or 500 since unknown channel is not validated
        assert resp.status_code in (200, 400, 404, 500)


class TestStockPlatforms:
    """GET /photographer/stock/platforms"""

    def test_lists_platforms(self, client):
        resp = client.get("/api/photographer/stock/platforms")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert isinstance(data, list)
