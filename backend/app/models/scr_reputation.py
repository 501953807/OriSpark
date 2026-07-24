"""SCR 分布式信誉系统数据模型."""

from datetime import datetime

from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Index, Numeric, Integer
from sqlalchemy.orm import relationship

from app.database import Base
from app.models.work import generate_uuid


class SCRScore(Base):
    """SCR 信誉评分 - 每个用户一条记录."""
    __tablename__ = "scr_scores"

    id = Column(String(32), primary_key=True, default=generate_uuid)
    user_id = Column(String(32), nullable=False, unique=True, index=True)
    overall_score = Column(Numeric(5, 2), default=50.00, nullable=False)  # 0-100
    rating_level = Column(String(20), default="starter", nullable=False)  # starter/bronze/silver/gold
    fulfillment_count = Column(Integer, default=0, nullable=False)
    default_count = Column(Integer, default=0, nullable=False)
    late_review_count = Column(Integer, default=0, nullable=False)
    complaint_count = Column(Integer, default=0, nullable=False)
    cleared_count = Column(Integer, default=0, nullable=False)
    avg_response_hours = Column(Numeric(6, 1), default=24.0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    history = relationship(
        "SCRHistory",
        back_populates="score",
        cascade="all, delete-orphan",
        order_by="SCRHistory.created_at.desc()",
    )

    __table_args__ = (
        Index("idx_scr_score", "overall_score"),
        Index("idx_scr_rating", "rating_level"),
    )


class SCRHistory(Base):
    """SCR 信誉变动历史 - 每次评分变化一条记录."""
    __tablename__ = "scr_history"

    id = Column(String(32), primary_key=True, default=generate_uuid)
    user_id = Column(String(32), nullable=False, index=True)
    score_delta = Column(Numeric(5, 2), nullable=False)  # 本次增减（可正可负）
    reason = Column(String(50), nullable=False)  # fulfillment/default/late_review/complaint/cleared
    related_transaction_id = Column(String(100), nullable=True)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    score_id = Column(String(32), ForeignKey("scr_scores.id"), nullable=True)
    score = relationship("SCRScore", back_populates="history")

    __table_args__ = (
        Index("idx_shr_user", "user_id"),
        Index("idx_shr_reason", "reason"),
        Index("idx_shr_created", "created_at"),
    )
