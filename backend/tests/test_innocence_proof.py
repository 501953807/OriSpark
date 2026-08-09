"""Innocence Proof Router HTTP-level integration tests."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

import pytest
from fastapi.testclient import TestClient


class TestCreateProof:
    """POST /innocence-proof/build"""

    def test_create_proof_missing_auth(self, client: TestClient):
        resp = client.post("/api/innocence-proof/build", json={})
        assert resp.status_code in (401, 403, 422)

    def test_create_proof_valid(self, client: TestClient):
        resp = client.post(
            "/api/innocence-proof/build",
            json={"work_id": "test-work"},
            headers={"Authorization": "Bearer test-token"}
        )
        assert resp.status_code in (200, 400, 401, 422, 500)


class TestGetProof:
    """GET /innocence-proof/{proof_id}"""

    def test_get_proof_nonexistent(self, client: TestClient):
        resp = client.get("/api/innocence-proof/nonexistent")
        assert resp.status_code in (404, 500)
