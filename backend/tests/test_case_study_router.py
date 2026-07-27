"""Case Study Router HTTP-level integration tests."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

import pytest


_BASE = "/api/case-studies"


class TestCategories:
    """GET /case-studies/categories"""

    def test_get_categories(self, client):
        resp = client.get(f"{_BASE}/categories")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) > 0
        assert "key" in data[0]
        assert "name_zh" in data[0]


class TestListCases:
    """GET /case-studies"""

    def test_list_all(self, client):
        resp = client.get(_BASE)
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)

    def test_filter_by_category(self, client):
        resp = client.get(_BASE, params={"category": "copyright"})
        assert resp.status_code == 200

    def test_filter_by_tag(self, client):
        resp = client.get(_BASE, params={"tag": "test"})
        assert resp.status_code == 200

    def test_filter_by_case_type(self, client):
        resp = client.get(_BASE, params={"case_type": "success"})
        assert resp.status_code == 200

    def test_filter_multiple_params(self, client):
        resp = client.get(_BASE, params={
            "category": "monetization",
            "case_type": "lesson",
            "tag": "platform",
        })
        assert resp.status_code == 200


class TestCreateCase:
    """POST /case-studies"""

    def test_create_valid_case(self, client):
        resp = client.post(_BASE, json={
            "title": "Test Case via API",
            "category": "copyright",
            "case_type": "success",
            "description": "A test case for verification",
            "tags": ["test", "api"],
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "id" in data
        assert data["title"] == "Test Case via API"

    def test_create_with_minimal_fields(self, client):
        resp = client.post(_BASE, json={
            "title": "Minimal Case",
            "category": "platform_growth",
            "case_type": "success",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "id" in data

    def test_create_with_full_payload(self, client):
        resp = client.post(_BASE, json={
            "title": "Full Case",
            "category": "brand_collab",
            "case_type": "lesson",
            "description": "Detailed description here",
            "key_metrics": {"revenue": 50000, "followers": 10000},
            "tags": ["brand", "collaboration"],
            "takeaways": ["Lesson 1", "Lesson 2"],
            "source_url": "https://example.com/case",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "id" in data

    def test_create_invalid_category(self, client):
        resp = client.post(_BASE, json={
            "title": "Invalid Case",
            "category": "nonexistent_category",
            "case_type": "success",
            "description": "Should fail",
        })
        assert resp.status_code == 400


class TestGetOne:
    """GET /case-studies/{case_id}"""

    def test_get_nonexistent(self, client):
        resp = client.get(f"{_BASE}/nonexistent_id")
        assert resp.status_code == 404


class TestUpdateCase:
    """PATCH /case-studies/{case_id}"""

    def test_update_nonexistent(self, client):
        resp = client.patch(f"{_BASE}/nonexistent_id", json={
            "title": "Updated Title",
        })
        assert resp.status_code == 404


class TestDeleteCase:
    """DELETE /case-studies/{case_id}"""

    def test_delete_nonexistent(self, client):
        resp = client.delete(f"{_BASE}/nonexistent_id")
        assert resp.status_code == 404


class TestStats:
    """GET /case-studies/stats"""

    def test_stats_empty(self, client):
        resp = client.get(f"{_BASE}/stats")
        assert resp.status_code == 200
        data = resp.json()
        assert "total" in data
        assert "by_category" in data

    def test_stats_with_data(self, client):
        """Create cases then check stats reflect them."""
        client.post(_BASE, json={
            "title": "Stat Case 1",
            "category": "copyright",
            "case_type": "success",
        })
        client.post(_BASE, json={
            "title": "Stat Case 2",
            "category": "monetization",
            "case_type": "lesson",
        })
        resp = client.get(f"{_BASE}/stats")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] >= 2
        assert "by_type" in data
        assert "top_tags" in data


class TestSearch:
    """GET /case-studies/search"""

    def test_search_no_results(self, client):
        resp = client.get(f"{_BASE}/search", params={"q": "zzzzz_notfound"})
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)

    def test_search_with_matching_case(self, client):
        """Create a case with known title, then search for it."""
        client.post(_BASE, json={
            "title": "Copyright Protection Guide",
            "category": "copyright",
            "case_type": "success",
            "description": "How to protect your work",
        })
        resp = client.get(f"{_BASE}/search", params={"q": "Protection"})
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        assert any("Copyright" in d["title"] for d in data)
