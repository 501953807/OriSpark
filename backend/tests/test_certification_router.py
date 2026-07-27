"""Certification Router HTTP-level integration tests."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

import pytest


_BASE = "/api/certification"


class TestSingleCertification:
    """POST /certification/single"""

    def test_single_nonexistent_work(self, client):
        resp = client.post(f"{_BASE}/single", json={
            "work_id": "nonexistent_work",
        })
        assert resp.status_code == 404

    def test_single_missing_work_id(self, client):
        resp = client.post(f"{_BASE}/single", json={})
        assert resp.status_code in (400, 422)


class TestBatchCertification:
    """POST /certification/batch"""

    def test_batch_without_work_ids(self, client):
        resp = client.post(f"{_BASE}/batch", json={
            "work_id": "test_work",
        })
        assert resp.status_code == 400

    def test_batch_empty_work_ids(self, client):
        resp = client.post(f"{_BASE}/batch", json={
            "work_id": "test_work",
            "batch": [],
        })
        # May fail with empty list or succeed
        assert resp.status_code in (200, 400, 422)
