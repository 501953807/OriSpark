"""Notary Router HTTP-level integration tests."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

import pytest
from fastapi.testclient import TestClient


_BASE = "/api/notary"


class TestPlatforms:
    """GET /notary/platforms"""

    def test_list_platforms(self, client):
        resp = client.get(f"{_BASE}/platforms")
        assert resp.status_code == 200
        data = resp.json()
        assert "data" in data
        # Should return at least 3 hardcoded platforms
        items = data["data"]
        assert len(items) >= 3


class TestRecords:
    """Record CRUD"""

    def test_list_records_empty(self, client):
        resp = client.get(f"{_BASE}/records")
        assert resp.status_code == 200

    def test_list_records_with_filters(self, client):
        resp = client.get(f"{_BASE}/records", params={
            "page": 1, "page_size": 20, "status": "confirmed", "platform": "antchain"
        })
        assert resp.status_code == 200

    def test_create_record_no_work(self, client):
        resp = client.post(f"{_BASE}/records", json={
            "work_id": "nonexistent_work",
            "platform": "antchain",
        })
        assert resp.status_code == 404

    def test_get_nonexistent_record(self, client):
        resp = client.get(f"{_BASE}/records/nonexistent")
        assert resp.status_code == 404


class TestConfirmRecord:
    """POST /notary/records/{id}/confirm"""

    def test_confirm_nonexistent(self, client):
        resp = client.post(f"{_BASE}/records/nonexistent/confirm")
        assert resp.status_code == 404


class TestBatchNotarize:
    """POST /notary/batch"""

    def test_batch_notarize_invalid_platform(self, client):
        resp = client.post(f"{_BASE}/batch", json={
            "work_ids": ["w1"],
            "platform": "invalid_platform",
        })
        assert resp.status_code == 400

    def test_batch_notarize_no_works(self, client):
        resp = client.post(f"{_BASE}/batch", json={
            "work_ids": ["nonexistent1", "nonexistent2"],
            "platform": "antchain",
        })
        # Returns 200 with count=0 since no works exist
        assert resp.status_code in (200, 404)


class TestCertificates:
    """Certificate CRUD"""

    def test_get_nonexistent_certificate(self, client):
        resp = client.get(f"{_BASE}/certificates/nonexistent")
        assert resp.status_code == 404

    def test_download_nonexistent_certificate(self, client):
        resp = client.get(f"{_BASE}/certificates/nonexistent/download")
        assert resp.status_code == 404


class TestC2PA:
    """C2PA manifest operations"""

    def test_generate_c2pa_nonexistent_work(self, client):
        resp = client.post(f"{_BASE}/c2pa/nonexistent/generate")
        assert resp.status_code == 404

    def test_verify_c2pa_nonexistent_work(self, client):
        resp = client.get(f"{_BASE}/verify/c2pa/nonexistent")
        assert resp.status_code == 404


class TestDID:
    """DID operations"""

    def test_generate_did(self, client):
        resp = client.post(f"{_BASE}/did/generate")
        assert resp.status_code == 200
        data = resp.json()
        assert "data" in data
        assert "did" in data["data"]

    def test_resolve_did_invalid(self, client):
        resp = client.get(f"{_BASE}/did/resolve", params={"did": "invalid:did"})
        assert resp.status_code == 400

    def test_resolve_did_valid_key(self, client):
        # First generate a DID, then resolve it
        gen_resp = client.post(f"{_BASE}/did/generate")
        if gen_resp.status_code != 200:
            pytest.skip("Cannot generate DID")
        did = gen_resp.json()["data"]["did"]
        resp = client.get(f"{_BASE}/did/resolve", params={"did": did})
        assert resp.status_code == 200


class TestVC:
    """Verifiable Credential operations"""

    def test_generate_vc_nonexistent_work(self, client):
        resp = client.post(f"{_BASE}/vc/nonexistent/generate")
        assert resp.status_code == 404

    def test_verify_vc_valid(self, client):
        resp = client.post(f"{_BASE}/vc/verify", json={
            "@context": ["https://www.w3.org/2018/credentials/v1"],
            "type": ["VerifiableCredential"],
            "issuer": "did:key:test",
            "issuanceDate": "2024-01-01T00:00:00Z",
            "credentialSubject": {"id": "test"},
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "data" in data


class TestMerkle:
    """Merkle tree batch anchoring"""

    def test_merkle_batch_insufficient_platform(self, client):
        resp = client.post(f"{_BASE}/merkle/batch", json={
            "work_ids": ["w1", "w2"],
            "platform": "invalid",
        })
        assert resp.status_code == 400

    def test_merkle_batch_no_works(self, client):
        resp = client.post(f"{_BASE}/merkle/batch", json={
            "work_ids": ["nonexistent1", "nonexistent2"],
            "platform": "antchain",
        })
        # Needs at least 2 works with hashes
        assert resp.status_code in (200, 400)


class TestCompareRecommend:
    """Platform comparison and recommendation"""

    def test_compare_platforms(self, client):
        resp = client.get(f"{_BASE}/compare", params={
            "work_count": 5,
            "work_type": "image",
            "budget": 50.0,
            "legal_level": "commercial",
            "priority": "cost",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "data" in data

    def test_recommend_nonexistent_work(self, client):
        resp = client.get(f"{_BASE}/recommend", params={"work_id": "nonexistent"})
        assert resp.status_code == 404


class TestAuditTrail:
    """Audit trail queries"""

    def test_audit_trail_nonexistent_record(self, client):
        resp = client.get(f"{_BASE}/records/nonexistent/audit-trail")
        assert resp.status_code == 404


class TestPolygonTimestamp:
    """Polygon anchor and timestamp"""

    def test_anchor_polygon_nonexistent_work(self, client):
        resp = client.post(f"{_BASE}/polygon", json={"work_id": "nonexistent"})
        assert resp.status_code == 404

    def test_timestamp_nonexistent_work(self, client):
        resp = client.post(f"{_BASE}/timestamp", json={"work_id": "nonexistent"})
        assert resp.status_code == 404


class TestUniversalVerify:
    """GET /notary/verify/{record_id}"""

    def test_verify_nonexistent_record(self, client):
        resp = client.get(f"{_BASE}/verify/nonexistent")
        assert resp.status_code == 404


class TestTraceAudit:
    """Provenance chain operations"""

    def test_build_provenance_missing_work_id(self, client):
        resp = client.post(f"{_BASE}/trace/audit/build", json={})
        assert resp.status_code == 400

    def test_build_provenance_nonexistent_work(self, client):
        resp = client.post(f"{_BASE}/trace/audit/build", json={
            "work_id": "nonexistent",
        })
        assert resp.status_code == 404

    def test_verify_provenance_nonexistent_work(self, client):
        resp = client.get(f"{_BASE}/trace/audit/verify/nonexistent")
        assert resp.status_code == 404

    def test_trace_status_nonexistent_work(self, client):
        resp = client.get(f"{_BASE}/trace/audit/status/nonexistent")
        assert resp.status_code == 200
        data = resp.json()
        assert "data" in data


class TestTripleAuth:
    """Triple authentication pipeline"""

    def test_triple_auth_missing_work_id(self, client):
        resp = client.post(f"{_BASE}/trace/triple/authenticate", json={})
        assert resp.status_code == 400

    def test_triple_auth_nonexistent_work(self, client):
        resp = client.post(f"{_BASE}/trace/triple/authenticate", json={
            "work_id": "nonexistent",
        })
        assert resp.status_code == 404

    def test_verify_triple_auth_nonexistent_work(self, client):
        resp = client.get(f"{_BASE}/trace/triple/verify/nonexistent")
        assert resp.status_code == 404
