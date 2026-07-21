"""POD 月度结算数据模型."""

from datetime import datetime

from sqlalchemy import Column, String, DateTime, ForeignKey, Numeric, Text, Index
from sqlalchemy.orm import relationship

from app.database import Base
from app.models.work import generate_uuid


class PodSettlement(Base):
    """POD 月度结算单."""
    __tablename__ = "pod_settlements"

    id = Column(String(32), primary_key=True, default=generate_uuid)
    user_id = Column(String(32), ForeignKey("users.id"), nullable=False, index=True)
    period = Column(String(7), nullable=False)  # "2026-07"
    total_sales_yuan = Column(Numeric(12, 2), default=0)
    total_cost_yuan = Column(Numeric(12, 2), default=0)
    creator_earnings_yuan = Column(Numeric(12, 2), default=0)
    platform_fee_yuan = Column(Numeric(12, 2), default=0)
    status = Column(String(20), default="pending", index=True)  # pending/confirmed/settled/cancelled
    confirmed_at = Column(DateTime, nullable=True)
    settled_at = Column(DateTime, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    items = relationship("PodSettlementItem", back_populates="settlement", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_settle_user_period", "user_id", "period"),
    )


class PodSettlementItem(Base):
    """结算单项."""
    __tablename__ = "pod_settlement_items"

    id = Column(String(32), primary_key=True, default=generate_uuid)
    settlement_id = Column(String(32), ForeignKey("pod_settlements.id", ondelete="CASCADE"), nullable=False)
    sale_id = Column(String(32), ForeignKey("pod_sales.id"), nullable=True)
    product_id = Column(String(32), ForeignKey("pod_products.id"), nullable=True)
    sale_amount_yuan = Column(Numeric(12, 2), nullable=False)
    cost_yuan = Column(Numeric(12, 2), nullable=False)
    creator_earning_yuan = Column(Numeric(12, 2), nullable=False)
    platform_fee_yuan = Column(Numeric(12, 2), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    settlement = relationship("PodSettlement", back_populates="items")

    __table_args__ = (
        Index("idx_item_settlement", "settlement_id"),
    )
