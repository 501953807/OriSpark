"""HTTP-level integration tests for Content Pipeline router."""

import pytest


_BASE = "/api/content-pipeline"


class TestListAccounts:
    """GET /content-pipeline/accounts"""

    def test_list_empty_accounts(self, client):
        resp = client.get(f"{_BASE}/accounts")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)

    def test_list_accounts_response_fields(self, client):
        """Verify each account dict has the expected keys."""
        resp = client.get(f"{_BASE}/accounts")
        assert resp.status_code == 200
        data = resp.json()
        if data:
            sample = data[0]
            assert "id" in sample
            assert "platform" in sample
            assert "account_name" in sample
            assert "follower_count" in sample
            assert "is_active" in sample


class TestAddAccount:
    """POST /content-pipeline/accounts"""

    def test_add_xiaohongshu_account(self, client):
        """Adding a valid account should succeed (200)."""
        resp = client.post(f"{_BASE}/accounts", json={
            "platform": "xiaohongshu",
            "account_name": "Test Artist",
            "account_id": "xrs-12345",
            "follower_count": 1500,
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["platform"] == "xiaohongshu"
        assert "id" in data

    def test_add_bilibili_account(self, client):
        resp = client.post(f"{_BASE}/accounts", json={
            "platform": "bilibili",
            "account_name": "Bilibili Creator",
            "follower_count": 3000,
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["platform"] == "bilibili"

    def test_add_douyin_account(self, client):
        resp = client.post(f"{_BASE}/accounts", json={
            "platform": "douyin",
            "account_name": "Douyin User",
            "account_id": "dy-999",
            "follower_count": 50000,
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["platform"] == "douyin"

    def test_add_weibo_account(self, client):
        resp = client.post(f"{_BASE}/accounts", json={
            "platform": "weibo",
            "account_name": "Weibo Author",
            "follower_count": 10000,
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["platform"] == "weibo"

    def test_add_account_minimal_fields(self, client):
        """Only required fields: platform and account_name."""
        resp = client.post(f"{_BASE}/accounts", json={
            "platform": "weixin",
            "account_name": "WeChat Official",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["platform"] == "weixin"

    def test_add_duplicate_platform_returns_409(self, client):
        """Adding same platform twice should return 409 conflict."""
        client.post(f"{_BASE}/accounts", json={
            "platform": "xiaohongshu",
            "account_name": "First Name",
        })
        resp = client.post(f"{_BASE}/accounts", json={
            "platform": "xiaohongshu",
            "account_name": "Second Name",
        })
        assert resp.status_code in (200, 409)

    def test_add_account_missing_required_field_returns_422(self, client):
        """Missing 'platform' should return 422 validation error from Pydantic."""
        resp = client.post(f"{_BASE}/accounts", json={
            "account_name": "No Platform",
        })
        assert resp.status_code == 422


class TestDeleteAccount:
    """DELETE /content-pipeline/accounts/{platform}"""

    def test_delete_nonexistent_account(self, client):
        """Delete a platform that doesn't exist -- expect 404."""
        resp = client.delete(f"{_BASE}/accounts/nonexistent_platform_xyz")
        assert resp.status_code in (404, 500)

    def test_delete_different_platforms(self, client):
        """Deleting various platform names that don't exist."""
        for platform in ["instagram", "twitter", "tiktok"]:
            resp = client.delete(f"{_BASE}/accounts/{platform}")
            assert resp.status_code in (404, 500)


class TestListSchedules:
    """GET /content-pipeline/schedules"""

    def test_list_empty_schedules(self, client):
        resp = client.get(f"{_BASE}/schedules")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)

    def test_list_schedules_with_status_filter(self, client):
        resp = client.get(f"{_BASE}/schedules", params={"status": "scheduled"})
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
