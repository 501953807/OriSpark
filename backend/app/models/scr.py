"""SCR 分布式信誉系统数据模型."""

import uuid
from datetime import datetime

from sqlalchemy import (
    Column, String, DateTime, Float, Integer, ForeignKey, Text, JSON, Index
)
from sqlalchemy.orm import relationship

from app.database import Base


class SCRRating(Base):
    """SCR 分布式信誉评级表 - 半成品的分布式信誉评分."""
    __tablename__ = "scr_ratings"

    id = Column(String(32), primary_key=True, default=lambda: uuid.uuid4().hex)
    user_id = Column(String(32), nullable=False, index=True, comment="被评分用户")
    rater_id = Column(String(32), nullable=False, index=True, comment="评分者用户")
    rating_type = Column(String(20), nullable=False, default="overall", comment="评分类型")
    status = Column(String(20), nullable=False, default="active", comment="active/suspended/revoked")
    tier = Column(String(20), nullable=False, default="draft", comment="unrated/draft/pending/confirmed/archived")

    raw_score = Column(Float, nullable=False, default=0.0, comment="原始评分 0-100")
    confidence = Column(Float, nullable=False, default=0.0, comment="置信度 0-1")
    consensus_count = Column(Integer, nullable=False, default=0, comment="达成共识的评分者数量")
    min_required_consensus = Column(Integer, nullable=False, default=3, comment="所需最少共识数")

    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True, comment="过期时间")

    metadata_json = Column(JSON, nullable=True, comment="扩展元数据")
    notes = Column(Text, nullable=True)

    behaviors = relationship("SCRBehavior", back_populates="rating", cascade="all, delete-orphan")
    trust_links = relationship("SCRTrustLink", back_populates="source_rating", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_scr_user", "user_id"),
        Index("idx_scr_rater", "rater_id"),
        Index("idx_scr_status", "status"),
        Index("idx_scr_tier", "tier"),
    )


class SCRBehavior(Base):
    """SCR 行为记录 - 每次评分事件."""
    __tablename__ = "scr_behaviors"

    id = Column(String(32), primary_key=True, default=lambda: uuid.uuid4().hex)
    rating_id = Column(String(32), ForeignKey("scr_ratings.id"), nullable=False, index=True)
    user_id = Column(String(32), nullable=False, index=True)
    rater_id = Column(String(32), nullable=False, index=True)
    behavior_type = Column(String(50), nullable=False)
    score_delta = Column(Float, nullable=False, default=0.0)
    description = Column(String(500), nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    rating = relationship("SCRRating", back_populates="behaviors")

    __table_args__ = (
        Index("idx_scrb_user", "user_id"),
        Index("idx_scrb_rater", "rater_id"),
    )


class SCRTrustLink(Base):
    """SCR 信任关系表 - 用户间的信任链接."""
    __tablename__ = "scr_trust_links"

    id = Column(String(32), primary_key=True, default=lambda: uuid.uuid4().hex)
    rating_id = Column(String(32), ForeignKey("scr_ratings.id", ondelete="CASCADE"), nullable=False, index=True, comment="关联评级")
    source_user_id = Column(String(32), nullable=False, index=True, comment="信任方")
    target_user_id = Column(String(32), nullable=False, index=True, comment="被信任方")
    trust_score = Column(Float, nullable=False, default=0.0, comment="信任分数 0-1")
    weight = Column(Float, nullable=False, default=1.0, comment="权重")
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)

    source_rating = relationship("SCRRating", back_populates="trust_links", foreign_keys=[rating_id])

    __table_args__ = (
        Index("idx_srcl_source", "source_user_id"),
        Index("idx_srcl_target", "target_user_id"),
        Index("idx_srcl_unique", "source_user_id", "target_user_id", unique=True),
    )


SCR_BEHAVIOR_SCORES = {
    "work_submitted": 2.0,
    "work_approved": 5.0,
    "work_rejected": -3.0,
    "collaboration_completed": 4.0,
    "collaboration_failed": -4.0,
    "on_time_delivery": 3.0,
    "late_delivery": -2.0,
    "positive_feedback": 2.0,
    "negative_feedback": -5.0,
    "consensus_achieved": 1.0,
    "consensus_failed": -2.0,
}

SCR_TIER_THRESHOLDS = {
    "confirmed": 80.0,
    "pending": 50.0,
    "draft": 0.0,
}


def calculate_scr_tier(score: float) -> str:
    for tier, threshold in sorted(SCR_TIER_THRESHOLDS.items(), key=lambda x: x[1], reverse=True):
        if score >= threshold:
            return tier
    return "draft"


def apply_scr_behavior(rating: SCRRating, behavior_type: str, score_delta: float) -> SCRRating:
    rating.raw_score += score_delta
    rating.updated_at = datetime.utcnow()
    rating.raw_score = max(0.0, min(100.0, rating.raw_score))
    new_tier = calculate_scr_tier(rating.raw_score)
    if new_tier != rating.tier:
        rating.tier = new_tier
        rating.updated_at = datetime.utcnow()
    return rating
