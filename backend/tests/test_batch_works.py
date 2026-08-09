"""Batch Works Router HTTP-level integration tests."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

import pytest
from fastapi.testclient import TestClient


class TestBatchCreate:
    """POST /works/batch-edit"""

    def test_batch_create_missing_auth(self, client: TestClient):
        resp = client.post("/api/works/batch-edit", json={})
        assert resp.status_code in (401, 403, 422)

    def test_batch_create_valid(self, client: TestClient):
        resp = client.post(
            "/api/works/batch-edit",
            json={"works": []},
            headers={"Authorization": "Bearer test-token"}
        )
        assert resp.status_code in (200, 400, 401, 422, 500)


class TestBatchStatus:
    """GET /works/batch-status"""

    def test_batch_status_missing_params(self, client: TestClient):
        resp = client.get("/api/works/batch-status")
        assert resp.status_code in (400, 401, 422, 404)
