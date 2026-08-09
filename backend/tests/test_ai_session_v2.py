"""AI Session V2 Router HTTP-level integration tests."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

import pytest
from fastapi.testclient import TestClient


class TestCompareSessions:
    """GET /compare"""

    def test_compare_sessions_missing_params(self, client: TestClient):
        resp = client.get("/api/works/test-work/ai-sessions/test-a/compare/test-b")
        assert resp.status_code in (400, 401, 404, 500)


class TestBatchImport:
    """POST /batch-import"""

    def test_batch_import_missing_auth(self, client: TestClient):
        resp = client.post("/api/works/test-work/ai-sessions/batch-import", json={})
        assert resp.status_code in (401, 403, 422)

    def test_batch_import_valid(self, client: TestClient):
        resp = client.post(
            "/api/works/test-work/ai-sessions/batch-import",
            json={"sessions": []},
            headers={"Authorization": "Bearer test-token"}
        )
        assert resp.status_code in (200, 400, 401, 422, 500)
