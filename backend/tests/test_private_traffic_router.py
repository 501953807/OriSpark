"""Private Traffic Router HTTP-level integration tests — covers all 7 endpoints."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

import pytest


_BASE = "/api/private-traffic"


class TestSubscriptionLinks:
    """POST/PATCH/GET /private-traffic/subscriptions"""

    def test_create_subscription(self, client):
        resp = client.post(f"{_BASE}/subscriptions", json={
            "platform": "wechat",
            "url": "https://mp.weixin.qq.com/s/test",
            "subscriber_count": 100,
            "monthly_revenue": 5000.0,
            "currency": "CNY",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["platform"] == "wechat"
        assert data["user_id"] is not None
        assert "created_at" in data

    def test_list_subscriptions(self, client):
        client.post(f"{_BASE}/subscriptions", json={
            "platform": "twitter",
            "url": "https://twitter.com/test",
            "subscriber_count": 50,
            "monthly_revenue": 2000.0,
        })
        client.post(f"{_BASE}/subscriptions", json={
            "platform": "youtube",
            "url": "https://youtube.com/test",
            "subscriber_count": 200,
            "monthly_revenue": 8000.0,
        })
        resp = client.get(f"{_BASE}/subscriptions")
        assert resp.status_code == 200
        items = resp.json()
        assert isinstance(items, list)
        assert len(items) >= 2

    def test_update_subscriber_count(self, client):
        create_resp = client.post(f"{_BASE}/subscriptions", json={
            "platform": "weibo",
            "url": "https://weibo.com/test",
            "subscriber_count": 10,
        })
        link_id = create_resp.json()["id"]
        resp = client.patch(f"{_BASE}/subscriptions/{link_id}", json={
            "subscriber_count": 999,
        })
        assert resp.status_code == 200
        assert resp.json()["subscriber_count"] == 999


class TestFanCommunities:
    """POST/GET /private-traffic/communities"""

    def test_create_community(self, client):
        resp = client.post(f"{_BASE}/communities", json={
            "platform": "discord",
            "name": "OriStudio Fan Club",
            "invite_url": "https://discord.gg/test",
            "member_count": 50,
            "tags": ["fans", "community"],
            "description": "Official fan community",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["name"] == "OriStudio Fan Club"
        assert data["platform"] == "discord"
        assert data["is_active"] is True

    def test_list_communities(self, client):
        client.post(f"{_BASE}/communities", json={
            "platform": "telegram",
            "name": "Channel A",
            "member_count": 100,
        })
        client.post(f"{_BASE}/communities", json={
            "platform": "whatsapp",
            "name": "Group B",
            "member_count": 30,
        })
        resp = client.get(f"{_BASE}/communities")
        assert resp.status_code == 200
        items = resp.json()
        assert isinstance(items, list)
        assert len(items) >= 2


class TestFunnel:
    """POST/GET /private-traffic/funnel*"""

    def test_add_funnel_entry(self, client):
        resp = client.post(f"{_BASE}/funnel", json={
            "source_platform": "xiaohongshu",
            "public_views": 1000,
            "profile_clicks": 200,
            "link_clicks": 50,
            "converted_subscribers": 10,
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["source_platform"] == "xiaohongshu"
        assert data["public_views"] == 1000

    def test_funnel_summary(self, client):
        # Add multiple funnel entries
        for platform, views in [("xiaohongshu", 1000), ("weibo", 500)]:
            client.post(f"{_BASE}/funnel", json={
                "source_platform": platform,
                "public_views": views,
                "profile_clicks": views // 5,
                "link_clicks": views // 20,
                "converted_subscribers": views // 100,
            })

        resp = client.get(f"{_BASE}/funnel-summary")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_public_views"] == 1500
        assert len(data["by_platform"]) >= 2
        assert "overall_conversion_rate" in data
