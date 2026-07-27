"""Factory/RFQ Router HTTP-level integration tests."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

import pytest


_BASE = "/api/factory"


class TestRFQ:
    """RFQ CRUD"""

    def test_list_rfqs_empty(self, client):
        resp = client.get(f"{_BASE}/rfq")
        assert resp.status_code == 200
        data = resp.json()
        assert "data" in data

    def test_create_rfq(self, client):
        resp = client.post(f"{_BASE}/rfq", json={
            "title": "Custom Ceramic Mugs",
            "description": "Need 500 custom mugs",
            "materials": ["ceramic"],
            "quantity": 500,
        })
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert "id" in data
        assert data["title"] == "Custom Ceramic Mugs"

    def test_get_rfq(self, client):
        create_resp = client.post(f"{_BASE}/rfq", json={
            "title": "Get Me RFQ",
        })
        if create_resp.status_code != 200:
            pytest.skip("Cannot create RFQ")
        rfq_id = create_resp.json()["data"]["id"]

        resp = client.get(f"{_BASE}/rfq/{rfq_id}")
        assert resp.status_code == 200
        assert resp.json()["data"]["title"] == "Get Me RFQ"

    def test_get_nonexistent_rfq(self, client):
        resp = client.get(f"{_BASE}/rfq/nonexistent")
        assert resp.status_code == 404

    def test_update_rfq(self, client):
        create_resp = client.post(f"{_BASE}/rfq", json={
            "title": "Update Me RFQ",
        })
        if create_resp.status_code != 200:
            pytest.skip("Cannot create RFQ")
        rfq_id = create_resp.json()["data"]["id"]

        resp = client.put(f"{_BASE}/rfq/{rfq_id}", json={
            "title": "Updated RFQ",
            "status": "published",
        })
        assert resp.status_code == 200
        assert resp.json()["data"]["title"] == "Updated RFQ"

    def test_delete_rfq(self, client):
        create_resp = client.post(f"{_BASE}/rfq", json={
            "title": "Delete Me RFQ",
        })
        if create_resp.status_code != 200:
            pytest.skip("Cannot create RFQ")
        rfq_id = create_resp.json()["data"]["id"]

        resp = client.delete(f"{_BASE}/rfq/{rfq_id}")
        assert resp.status_code == 200


class TestSamples:
    """Sample management under RFQ"""

    def test_list_samples_empty(self, client):
        resp = client.get(f"{_BASE}/rfq/test_rfq/samples")
        assert resp.status_code == 200

    def test_create_sample(self, client):
        # Create RFQ first
        rfq_resp = client.post(f"{_BASE}/rfq", json={
            "title": "Sample RFQ",
        })
        if rfq_resp.status_code != 200:
            pytest.skip("Cannot create RFQ")
        rfq_id = rfq_resp.json()["data"]["id"]

        resp = client.post(f"{_BASE}/rfq/{rfq_id}/samples", json={
            "notes": "First sample request",
        })
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["rfq_id"] == rfq_id


class TestQualityReport:
    """Quality report management"""

    def test_create_quality_report(self, client):
        # Create RFQ + sample first
        rfq_resp = client.post(f"{_BASE}/rfq", json={
            "title": "QR RFQ",
        })
        if rfq_resp.status_code != 200:
            pytest.skip("Cannot create RFQ")
        rfq_id = rfq_resp.json()["data"]["id"]

        sample_resp = client.post(f"{_BASE}/rfq/{rfq_id}/samples", json={})
        if sample_resp.status_code != 200:
            pytest.skip("Cannot create sample")
        sample_id = sample_resp.json()["data"]["id"]

        resp = client.post(f"{_BASE}/sample/{sample_id}/quality-report", json={
            "aql_level": "S-2",
            "passed": 9,
            "total_inspected": 10,
        })
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["passed"] == 9
