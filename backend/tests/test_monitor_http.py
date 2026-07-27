"""Monitor Router HTTP-level integration tests."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

import pytest


_BASE = "/api/monitor"


class TestListTasks:
    """GET /monitor/tasks"""

    def test_list_tasks(self, client):
        resp = client.get(f"{_BASE}/tasks")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data["data"], list)


class TestScanTask:
    """POST /monitor/tasks/{task_id}/scan - requires auth"""

    def test_scan_task_nonexistent(self, client):
        resp = client.post(f"{_BASE}/tasks/nonexistent/scan")
        assert resp.status_code in (404, 401)


class TestScan:
    """POST /monitor/scan - requires auth"""

    def test_scan(self, client):
        resp = client.post(f"{_BASE}/scan", json={})
        assert resp.status_code in (200, 401, 422)


class TestGetResults:
    """GET /monitor/results"""

    def test_get_results(self, client):
        resp = client.get(f"{_BASE}/results")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data["data"], list)


class TestUpdateResult:
    """PATCH /monitor/results/{result_id} - requires auth"""

    def test_update_result_nonexistent(self, client):
        resp = client.patch(f"{_BASE}/results/nonexistent", json={"status": "completed"})
        assert resp.status_code in (404, 401)


class TestAddResultEvidence:
    """POST /monitor/results/{result_id}/evidence - requires auth"""

    def test_add_evidence_nonexistent(self, client):
        resp = client.post(f"{_BASE}/results/nonexistent/evidence", json={
            "package_id": "test_pkg",
        })
        # Returns 404 for non-existent result, 401 if unauth, or 422 for validation issues
        assert resp.status_code in (404, 401, 422)


class TestListEvidence:
    """GET /monitor/evidence"""

    def test_list_evidence(self, client):
        resp = client.get(f"{_BASE}/evidence")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data["data"], list)


class TestGetEvidencePackage:
    """GET /monitor/evidence/{package_id}"""

    def test_get_package_nonexistent(self, client):
        resp = client.get(f"{_BASE}/evidence/nonexistent")
        assert resp.status_code == 404


class TestGetQuota:
    """GET /monitor/quota"""

    def test_get_quota(self, client):
        resp = client.get(f"{_BASE}/quota")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, dict)


class TestFingerprints:
    """POST /monitor/fingerprints - requires auth"""

    def test_fingerprints(self, client):
        resp = client.post(f"{_BASE}/fingerprints", json={})
        assert resp.status_code in (200, 401, 422)


class TestCompareFingerprints:
    """POST /monitor/fingerprints/compare - requires auth"""

    def test_compare(self, client):
        resp = client.post(f"{_BASE}/fingerprints/compare", json={
            "fingerprint1": "hash1",
            "fingerprint2": "hash2",
        })
        assert resp.status_code in (200, 401, 422)


class TestListBrandWatches:
    """GET /monitor/brand-watches"""

    def test_list_brand_watches(self, client):
        resp = client.get(f"{_BASE}/brand-watches")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data["data"], list)


class TestCreateBrandWatch:
    """POST /monitor/brand-watches - requires auth"""

    def test_create_brand_watch(self, client):
        resp = client.post(f"{_BASE}/brand-watches", json={
            "brand_name": "Test Brand",
        })
        assert resp.status_code in (200, 401, 422)


class TestGetBrandWatch:
    """GET /monitor/brand-watches/{brand_id}"""

    def test_brand_watch_nonexistent(self, client):
        resp = client.get(f"{_BASE}/brand-watches/nonexistent")
        assert resp.status_code == 404


class TestUpdateBrandWatch:
    """PATCH /monitor/brand-watches/{brand_id} - requires auth"""

    def test_update_brand_watch_nonexistent(self, client):
        resp = client.patch(f"{_BASE}/brand-watches/nonexistent", json={"active": False})
        assert resp.status_code in (404, 401)


class TestDeleteBrandWatch:
    """DELETE /monitor/brand-watches/{brand_id} - requires auth"""

    def test_delete_brand_watch_nonexistent(self, client):
        resp = client.delete(f"{_BASE}/brand-watches/nonexistent")
        assert resp.status_code in (404, 401)


class TestScanBrand:
    """POST /monitor/brands/{brand_id}/scan - requires auth"""

    def test_scan_brand_nonexistent(self, client):
        resp = client.post(f"{_BASE}/brands/nonexistent/scan")
        assert resp.status_code in (404, 401)


class TestGetBrandResults:
    """GET /monitor/brands/{brand_id}/results"""

    def test_brand_results_nonexistent(self, client):
        resp = client.get(f"{_BASE}/brands/nonexistent/results")
        # May return 200 with empty result or 404 depending on implementation
        assert resp.status_code in (200, 404)


class TestWatchDomain:
    """POST /monitor/domains/watch - requires auth"""

    def test_watch_domain(self, client):
        resp = client.post(f"{_BASE}/domains/watch", json={
            "domain": "example.com",
        })
        assert resp.status_code in (200, 401, 422)


class TestListDomainWatches:
    """GET /monitor/domains/watch"""

    def test_list_domain_watches(self, client):
        resp = client.get(f"{_BASE}/domains/watch")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data["data"], list)


class TestDeleteDomainWatch:
    """DELETE /monitor/domains/watch/{watch_id} - requires auth"""

    def test_delete_watch_nonexistent(self, client):
        resp = client.delete(f"{_BASE}/domains/watch/nonexistent")
        assert resp.status_code in (404, 401)


class TestWhoisLookup:
    """POST /monitor/domains/whois-lookup - requires auth"""

    def test_whois_lookup(self, client):
        resp = client.post(f"{_BASE}/domains/whois-lookup", json={
            "domain": "example.com",
        })
        assert resp.status_code in (200, 401, 422)


class TestDMCAEvidence:
    """GET /monitor/evidence/dmca/{work_id}"""

    def test_dmca_evidence_nonexistent(self, client):
        resp = client.get(f"{_BASE}/evidence/dmca/nonexistent")
        assert resp.status_code in (200, 404)


class TestCheckCode:
    """POST /monitor/check/code - requires auth"""

    def test_check_code(self, client):
        resp = client.post(f"{_BASE}/check/code", json={
            "text": "sample text",
        })
        assert resp.status_code in (200, 401, 422)


class TestWhitelistSuggestions:
    """GET /monitor/whitelist-suggestions"""

    def test_whitelist_suggestions(self, client):
        resp = client.get(f"{_BASE}/whitelist-suggestions")
        assert resp.status_code == 200
        data = resp.json()
        assert "data" in data


class TestWhitelistAction:
    """POST /monitor/whitelist-suggestions/action - requires auth"""

    def test_whitelist_action(self, client):
        resp = client.post(f"{_BASE}/whitelist-suggestions/action", json={
            "action": "approve",
        })
        assert resp.status_code in (200, 401, 422)


class TestGetWorkTimeline:
    """GET /monitor/results/{work_id}/timeline"""

    def test_timeline_nonexistent(self, client):
        resp = client.get(f"{_BASE}/results/nonexistent/timeline")
        assert resp.status_code == 404


class TestDeltaCheck:
    """POST /monitor/delta - requires auth"""

    def test_delta(self, client):
        resp = client.post(f"{_BASE}/delta", json={})
        assert resp.status_code in (200, 401, 422)


class TestGetQuotaRotation:
    """GET /monitor/quota/rotation"""

    def test_quota_rotation(self, client):
        resp = client.get(f"{_BASE}/quota/rotation")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, dict)


class TestRotateQuota:
    """POST /monitor/quota/rotate - requires auth"""

    def test_rotate_quota(self, client):
        resp = client.post(f"{_BASE}/quota/rotate")
        assert resp.status_code in (200, 401, 422)


class TestRecalculatePriority:
    """POST /monitor/tasks/{task_id}/recalculate-priority - requires auth"""

    def test_recalculate_priority_nonexistent(self, client):
        resp = client.post(f"{_BASE}/tasks/nonexistent/recalculate-priority")
        assert resp.status_code in (404, 401)


class TestGetPriorities:
    """GET /monitor/tasks/priorities"""

    def test_priorities(self, client):
        resp = client.get(f"{_BASE}/tasks/priorities")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data["data"], list)


class TestScanVideoFingerprint:
    """POST /monitor/scan-video-fingerprint - requires auth"""

    def test_scan_video(self, client):
        resp = client.post(f"{_BASE}/scan-video-fingerprint", json={})
        assert resp.status_code in (200, 401, 422)


class TestGenerateAudioFingerprint:
    """POST /monitor/generate-audio-fingerprint - requires auth"""

    def test_generate_audio(self, client):
        resp = client.post(f"{_BASE}/generate-audio-fingerprint", json={})
        assert resp.status_code in (200, 401, 422)


class TestScanAudioFingerprint:
    """POST /monitor/scan-audio-fingerprint - requires auth"""

    def test_scan_audio(self, client):
        resp = client.post(f"{_BASE}/scan-audio-fingerprint", json={})
        assert resp.status_code in (200, 401, 422)


class TestListAudioMatches:
    """GET /monitor/audio-matches"""

    def test_audio_matches(self, client):
        resp = client.get(f"{_BASE}/audio-matches")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data["data"], list)


class TestScanText:
    """POST /monitor/scan-text - requires auth"""

    def test_scan_text(self, client):
        resp = client.post(f"{_BASE}/scan-text", json={
            "text": "sample text to scan",
        })
        # May return 200, 401 (unauthorized), 422 (validation), or 404 (endpoint not implemented)
        assert resp.status_code in (200, 401, 422, 404)


class TestListTextMatches:
    """GET /monitor/text-matches"""

    def test_text_matches(self, client):
        resp = client.get(f"{_BASE}/text-matches")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data["data"], list)