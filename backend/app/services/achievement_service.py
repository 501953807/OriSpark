"""成就徽章与排行榜服务."""

from datetime import datetime
from sqlalchemy.orm import Session
from app.models.achievement import AchievementBadge, UserAchievement, LeaderboardEntry


def get_available_badges(db: Session) -> list[dict]:
    """获取所有可用成就徽章."""
    badges = db.query(AchievementBadge).filter(AchievementBadge.is_active == True).all()
    return [
        {
            "id": b.id,
            "badge_key": b.badge_key,
            "badge_name": b.badge_name,
            "badge_description": b.badge_description,
            "icon_url": b.icon_url,
            "color_hex": b.color_hex,
            "xp_reward": b.xp_reward,
        }
        for b in badges
    ]


def unlock_achievement(user_id: str, badge_key: str, db: Session) -> dict | None:
    """解锁成就徽章."""
    badge = db.query(AchievementBadge).filter(
        AchievementBadge.badge_key == badge_key,
        AchievementBadge.is_active == True,
    ).first()
    if not badge:
        return None

    existing = db.query(UserAchievement).filter(
        UserAchievement.user_id == user_id,
        UserAchievement.badge_id == badge.id,
    ).first()
    if existing:
        return {"status": "already_unlocked", "badge_key": badge_key}

    user_achievement = UserAchievement(
        user_id=user_id,
        badge_id=badge.id,
        unlocked_at=datetime.utcnow(),
    )
    db.add(user_achievement)
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise

    return {
        "status": "unlocked",
        "badge_key": badge_key,
        "badge_name": badge.badge_name,
        "xp_reward": badge.xp_reward,
    }


def get_user_achievements(user_id: str, db: Session) -> list[dict]:
    """获取用户已获得的成就."""
    achievements = (
        db.query(UserAchievement)
        .filter(UserAchievement.user_id == user_id)
        .order_by(UserAchievement.unlocked_at.desc())
        .all()
    )
    return [
        {
            "id": a.id,
            "user_id": a.user_id,
            "badge_id": a.badge_id,
            "unlocked_at": a.unlocked_at.isoformat() if a.unlocked_at else None,
        }
        for a in achievements
    ]


def update_leaderboard(creator_type: str, db: Session, period: str = "monthly") -> list[dict]:
    """更新排行榜数据."""
    now = datetime.utcnow()
    period_start = now - timedelta(days=30) if period == "monthly" else now - timedelta(days=7)

    entries = (
        db.query(LeaderboardEntry)
        .filter(
            LeaderboardEntry.creator_type == creator_type,
            LeaderboardEntry.period == period,
        )
        .order_by(LeaderboardEntry.score.desc())
        .all()
    )

    return [
        {
            "rank": i + 1,
            "user_id": e.user_id,
            "score": e.score,
            "total_xp": e.total_xp,
        }
        for i, e in enumerate(entries)
    ]


def get_leaderboard(creator_type: str, period: str = "monthly", limit: int = 50) -> list[dict]:
    """获取排行榜."""
    entries = (
        db.query(LeaderboardEntry)
        .filter(
            LeaderboardEntry.creator_type == creator_type,
            LeaderboardEntry.period == period,
        )
        .order_by(LeaderboardEntry.rank_position.asc())
        .limit(limit)
        .all()
    )
    return [
        {
            "id": e.id,
            "user_id": e.user_id,
            "creator_type": e.creator_type,
            "rank_position": e.rank_position,
            "score": e.score,
            "total_xp": e.total_xp,
            "period": e.period,
        }
        for e in entries
    ]
