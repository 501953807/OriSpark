"""Achievement Router HTTP-level integration tests — covers all 5 endpoints."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

import pytest


@pytest.fixture
def test_badge(db_session):
    """创建一个激活的成就徽章."""
    from app.models.achievement import AchievementBadge
    b = AchievementBadge(
        id="badge_first_upload",
        badge_key="first_upload",
        badge_name="首次上传",
        badge_description="完成第一次作品上传",
        icon_url="/icons/first_upload.svg",
        color_hex="#FFD700",
        xp_reward=100,
        is_active=True,
    )
    db_session.add(b)
    db_session.commit()
    return b


_BASE = "/api/growth"

# Auth header — "Bearer local" falls through to get_current_user_id → "local" user
_AUTH = {"headers": {"Authorization": "Bearer local"}}


class TestBadges:
    """GET /growth/badges"""

    def test_returns_list_of_badges(self, client, test_badge):
        resp = client.get(f"{_BASE}/badges")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert isinstance(data, list)
        assert any(item["badge_key"] == "first_upload" for item in data)

    def test_empty_when_no_badges(self, client, db_session):
        """无激活徽章时返回空列表."""
        from app.models.achievement import AchievementBadge
        db_session.query(AchievementBadge).delete()
        db_session.commit()
        resp = client.get(f"{_BASE}/badges")
        assert resp.status_code == 200
        assert resp.json()["data"] == []


class TestUnlockBadge:
    """POST /growth/badges/{key}/unlock"""

    def test_unlock_success(self, client, test_badge):
        resp = client.post(
            f"{_BASE}/badges/first_upload/unlock",
            headers={"Authorization": "Bearer local"},
        )
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["status"] == "unlocked"
        assert data["badge_key"] == "first_upload"
        assert data["xp_reward"] == 100

    def test_already_unlocked(self, client, test_badge, db_session):
        """已解锁的徽章应返回 already_unlocked."""
        from app.models.achievement import UserAchievement
        ua = UserAchievement(
            id="ua_test_001",
            user_id="local",
            badge_id=test_badge.id,
        )
        db_session.add(ua)
        db_session.flush()
        resp = client.post(
            f"{_BASE}/badges/first_upload/unlock",
            headers={"Authorization": "Bearer local"},
        )
        assert resp.status_code == 200
        assert resp.json()["data"]["status"] == "already_unlocked"

    def test_nonexistent_badge(self, client):
        resp = client.post(
            f"{_BASE}/badges/nonexist/unlock",
            headers={"Authorization": "Bearer local"},
        )
        assert resp.status_code == 404


class TestMyAchievements:
    """GET /growth/achievements"""

    def test_returns_user_achievements(self, client, test_badge, db_session):
        from app.models.achievement import UserAchievement
        ua = UserAchievement(
            id="ua_achieve_test",
            user_id="local",
            badge_id=test_badge.id,
        )
        db_session.add(ua)
        db_session.flush()
        resp = client.get(
            f"{_BASE}/achievements",
            headers={"Authorization": "Bearer local"},
        )
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert isinstance(data, list)
        assert len(data) >= 1
        assert data[0]["user_id"] == "local"

    def test_empty_for_new_user(self, client):
        resp = client.get(
            f"{_BASE}/achievements",
            headers={"Authorization": "Bearer local"},
        )
        assert resp.status_code == 200
        assert resp.json()["data"] == []


class TestLeaderboard:
    """GET /growth/leaderboard"""

    def test_returns_leaderboard_list(self, client, test_badge, db_session):
        from app.models.achievement import LeaderboardEntry
        le = LeaderboardEntry(
            id="lb_test_001",
            user_id="local",
            creator_type="illustrator",
            rank_position=1,
            score=1000.0,
            total_xp=500,
            period="monthly",
        )
        db_session.add(le)
        db_session.flush()
        resp = client.get(f"{_BASE}/leaderboard", params={
            "creator_type": "illustrator",
            "period": "monthly",
            "limit": 50,
        })
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert isinstance(data, list)
        assert len(data) >= 1
        assert data[0]["user_id"] == "local"
