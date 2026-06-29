"""订阅系统数据模型."""

from datetime import datetime

from sqlalchemy import Column, String, Text, DateTime, Boolean, ForeignKey, Index, Float, JSON
from sqlalchemy.orm import relationship

from app.database import Base
from app.models.work import generate_uuid


class SubscriptionTier(Base):
    """订阅等级."""
    __tablename__ = "subscription_tiers"

    id = Column(String(32), primary_key=True, default=generate_uuid)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    price = Column(Float, nullable=False, default=0.0)
    currency = Column(String(10), default="CNY")
    period = Column(String(20), nullable=False, default="monthly")  # monthly / yearly
    features = Column(JSON, nullable=True)  # [{key, label, value}]
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    subscribers = relationship(
        "SubscriptionSubscriber",
        back_populates="tier",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        Index("idx_tier_name", "name"),
        Index("idx_tier_active", "is_active"),
    )


class SubscriptionSubscriber(Base):
    """订阅用户."""
    __tablename__ = "subscription_subscribers"

    id = Column(String(32), primary_key=True, default=generate_uuid)
    user_id = Column(String(32), nullable=False)
    tier_id = Column(
        String(32),
        ForeignKey("subscription_tiers.id", ondelete="CASCADE"),
        nullable=False,
    )
    status = Column(String(20), default="active")  # active / cancelled / expired
    subscribed_at = Column(DateTime, default=datetime.utcnow)
    cancelled_at = Column(DateTime, nullable=True)
    expires_at = Column(DateTime, nullable=True)

    tier = relationship("SubscriptionTier", back_populates="subscribers")

    __table_args__ = (
        Index("idx_sub_user", "user_id"),
        Index("idx_sub_tier", "tier_id"),
        Index("idx_sub_status", "status"),
    )
