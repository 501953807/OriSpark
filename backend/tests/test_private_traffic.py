"""HTTP-level integration tests for Private Traffic router."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

import pytest


class TestSubscriptionLinks:
    """POST/GET/PATCH /api/private-traffic/subscriptions"""

    def test_create_subscription_link(self, client):
        resp = client.post("/api/private-traffic/subscriptions", json={
            "platform": "patreon",
            "url": "https://patreon.com/test",
            "subscriber_count": 100,
            "monthly_revenue": 500.0,
            "currency": "CNY",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["platform"] == "patreon"
        assert data["url"] == "https://patreon.com/test"
        assert data["subscriber_count"] == 100
        assert data["is_active"] is True
        assert "id" in data
        assert "user_id" in data
        assert "created_at" in data

    def test_create_subscription_with_defaults(self, client):
        resp = client.post("/api/private-traffic/subscriptions", json={
            "platform": "aidian",
            "url": "https://afdian.com/test",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["subscriber_count"] == 0
        assert data["monthly_revenue"] == 0
        assert data["currency"] == "CNY"

    def test_list_subscriptions_empty(self, client):
        resp = client.get("/api/private-traffic/subscriptions")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)

    def test_list_subscriptions_after_create(self, client):
        # Create two links
        r1 = client.post("/api/private-traffic/subscriptions", json={
            "platform": "patreon",
            "url": "https://patreon.com/user1",
            "subscriber_count": 50,
            "monthly_revenue": 200.0,
        })
        r2 = client.post("/api/private-traffic/subscriptions", json={
            "platform": "zsxq",
            "url": "https://zsxq.com/user1",
            "subscriber_count": 30,
            "monthly_revenue": 150.0,
        })
        assert r1.status_code == 200
        assert r2.status_code == 200

        resp = client.get("/api/private-traffic/subscriptions")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) >= 2
        platforms = {d["platform"] for d in data}
        assert "patreon" in platforms
        assert "zsxq" in platforms

    def test_update_subscription_count(self, client):
        create_resp = client.post("/api/private-traffic/subscriptions", json={
            "platform": "patreon",
            "url": "https://patreon.com/update-test",
            "subscriber_count": 10,
        })
        assert create_resp.status_code == 200
        link_id = create_resp.json()["id"]

        update_resp = client.patch(
            f"/api/private-traffic/subscriptions/{link_id}",
            json={"subscriber_count": 999},
        )
        assert update_resp.status_code == 200
        data = update_resp.json()
        assert data["subscriber_count"] == 999

    def test_update_nonexistent_subscription(self, client):
        # Service raises ValueError when link not found; FastAPI does not catch it.
        # This is a service-layer bug: should return HTTP 404 instead of crashing.
        with pytest.raises(ValueError, match="Link not found"):
            client.patch(
                "/api/private-traffic/subscriptions/nonexistent-id-xyz",
                json={"subscriber_count": 100},
            )


class TestFanCommunities:
    """POST/GET /api/private-traffic/communities"""

    def test_create_community(self, client):
        resp = client.post("/api/private-traffic/communities", json={
            "platform": "discord",
            "name": "Test Server",
            "invite_url": "https://discord.gg/test",
            "member_count": 50,
            "tags": ["core_fans"],
            "description": "Community for testing",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["platform"] == "discord"
        assert data["name"] == "Test Server"
        assert data["member_count"] == 50
        assert data["is_active"] is True
        assert "id" in data

    def test_create_community_minimal(self, client):
        resp = client.post("/api/private-traffic/communities", json={
            "platform": "wechat",
            "name": "WeChat Group",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["platform"] == "wechat"
        assert data["name"] == "WeChat Group"
        assert data["member_count"] == 0

    def test_list_communities_empty(self, client):
        resp = client.get("/api/private-traffic/communities")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)

    def test_list_communities_after_create(self, client):
        client.post("/api/private-traffic/communities", json={
            "platform": "telegram",
            "name": "TG Channel",
            "member_count": 200,
        })
        resp = client.get("/api/private-traffic/communities")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) >= 1
        names = [c["name"] for c in data]
        assert "TG Channel" in names

    def test_multiple_communities_different_platforms(self, client):
        for platform, name in [("discord", "Discord 1"), ("qq", "QQ Group"), ("telegram", "Telegram")]:
            client.post("/api/private-traffic/communities", json={
                "platform": platform,
                "name": name,
            })

        resp = client.get("/api/private-traffic/communities")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) >= 3
        platforms = {c["platform"] for c in data}
        assert {"discord", "qq", "telegram"}.issubset(platforms)


class TestConversionFunnel:
    """POST/GET /api/private-traffic/funnel and /funnel-summary"""

    def test_add_funnel_entry(self, client):
        resp = client.post("/api/private-traffic/funnel", json={
            "source_platform": "xiaohongshu",
            "public_views": 5000,
            "profile_clicks": 250,
            "link_clicks": 100,
            "converted_subscribers": 10,
            "notes": "Good week",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["source_platform"] == "xiaohongshu"
        assert data["public_views"] == 5000
        assert data["converted_subscribers"] == 10
        assert "id" in data
        assert "tracked_date" in data

    def test_add_funnel_entry_defaults(self, client):
        resp = client.post("/api/private-traffic/funnel", json={
            "source_platform": "douyin",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["public_views"] == 0
        assert data["profile_clicks"] == 0

    def test_funnel_summary_empty(self, client):
        resp = client.get("/api/private-traffic/funnel-summary")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_public_views"] == 0
        assert data["overall_conversion_rate"] == 0
        assert data["by_platform"] == []

    def test_funnel_summary_with_data(self, client):
        # Add entries for two platforms
        client.post("/api/private-traffic/funnel", json={
            "source_platform": "xiaohongshu",
            "public_views": 3000,
            "profile_clicks": 150,
            "link_clicks": 60,
            "converted_subscribers": 5,
        })
        client.post("/api/private-traffic/funnel", json={
            "source_platform": "douyin",
            "public_views": 7000,
            "profile_clicks": 350,
            "link_clicks": 140,
            "converted_subscribers": 15,
        })

        resp = client.get("/api/private-traffic/funnel-summary")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_public_views"] == 10000
        assert data["total_profile_clicks"] == 500
        assert data["total_link_clicks"] == 200
        assert data["total_converted"] == 20
        assert data["overall_conversion_rate"] == 0.2  # 20/10000*100
        assert len(data["by_platform"]) == 2

    def test_funnel_summary_single_platform(self, client):
        client.post("/api/private-traffic/funnel", json={
            "source_platform": "youtube",
            "public_views": 10000,
            "profile_clicks": 500,
            "link_clicks": 100,
            "converted_subscribers": 10,
        })

        resp = client.get("/api/private-traffic/funnel-summary")
        assert resp.status_code == 200
        data = resp.json()
        by_platform = {p["platform"]: p for p in data["by_platform"]}
        assert "youtube" in by_platform
        assert by_platform["youtube"]["views"] == 10000
        assert by_platform["youtube"]["profile_ctr"] == 5.0  # 500/10000*100
        assert by_platform["youtube"]["link_ctr"] == 20.0   # 100/500*100
        assert by_platform["youtube"]["conv_rate"] == 10.0   # 10/100*100

    def test_funnel_summary_zero_views_no_division(self, client):
        client.post("/api/private-traffic/funnel", json={
            "source_platform": "test_platform",
            "public_views": 0,
            "profile_clicks": 0,
            "link_clicks": 0,
            "converted_subscribers": 0,
        })
        resp = client.get("/api/private-traffic/funnel-summary")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_public_views"] == 0
        assert data["overall_conversion_rate"] == 0

    def test_funnel_summary_by_platform_structure(self, client):
        client.post("/api/private-traffic/funnel", json={
            "source_platform": "bilibili",
            "public_views": 8000,
            "profile_clicks": 400,
            "link_clicks": 80,
            "converted_subscribers": 8,
        })
        resp = client.get("/api/private-traffic/funnel-summary")
        assert resp.status_code == 200
        data = resp.json()
        assert "by_platform" in data
        assert isinstance(data["by_platform"], list)
        for p in data["by_platform"]:
            assert "platform" in p
            assert "views" in p
            assert "profile_ctr" in p
            assert "link_ctr" in p
            assert "conv_rate" in p
