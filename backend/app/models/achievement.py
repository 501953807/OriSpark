"""Achievement Badge 数据模型."""

import uuid
from datetime import datetime

from sqlalchemy import Column, String, Integer, Float, DateTime, Boolean, ForeignKey, Index, Text
from sqlalchemy.orm import relationship

from app.database import Base


class AchievementBadge(Base):
    """成就徽章定义表."""

    __tablename__ = "achievement_badges"

    id = Column(String(32), primary_key=True, default=lambda: uuid.uuid4().hex)
    badge_key = Column(String(50), nullable=False, unique=True)  # "first_upload", "certified", etc.
    badge_name = Column(String(100), nullable=False)
    badge_description = Column(Text, nullable=True)
    icon_url = Column(String(500), nullable=True)
    color_hex = Column(String(7), nullable=True)  # e.g., "#FFD700"
    xp_reward = Column(Integer, default=100)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("idx_achievement_key", "badge_key"),
        Index("idx_achievement_active", "is_active"),
    )


class UserAchievement(Base):
    """用户已获得的成就."""

    __tablename__ = "user_achievements"

    id = Column(String(32), primary_key=True, default=lambda: uuid.uuid4().hex)
    user_id = Column(String(32), nullable=False, index=True)
    badge_id = Column(
        String(32),
        ForeignKey("achievement_badges.id", ondelete="CASCADE"),
        nullable=False,
    )
    unlocked_at = Column(DateTime, default=datetime.utcnow)

    badge = relationship("AchievementBadge")

    __table_args__ = (
        Index("idx_user_achievement_user", "user_id"),
        Index("idx_user_achievement_unique", "user_id", "badge_id", unique=True),
    )


class LeaderboardEntry(Base):
    """排行榜条目."""

    __tablename__ = "leaderboard_entries"

    id = Column(String(32), primary_key=True, default=lambda: uuid.uuid4().hex)
    user_id = Column(String(32), nullable=False, index=True)
    creator_type = Column(String(50), nullable=False)  # illustrator, photographer, etc.
    rank_position = Column(Integer, nullable=False)
    score = Column(Float, default=0.0)
    total_xp = Column(Integer, default=0)
    period = Column(String(20), default="monthly")  # weekly / monthly / all_time
    period_start = Column(DateTime, nullable=True)
    period_end = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index("idx_leaderboard_user", "user_id"),
        Index("idx_leaderboard_creator", "creator_type"),
        Index("idx_leaderboard_period", "period"),
    )
