"""Invoice 数据模型."""

import uuid
from datetime import datetime

from sqlalchemy import Column, String, Float, DateTime, Boolean, Integer, ForeignKey, Index, Text
from sqlalchemy.orm import relationship

from app.database import Base


class Invoice(Base):
    """发票管理表."""

    __tablename__ = "invoices"

    id = Column(String(32), primary_key=True, default=lambda: uuid.uuid4().hex)
    user_id = Column(String(32), nullable=False, index=True)
    invoice_number = Column(String(50), nullable=False, unique=True)  # INV/YYYY/MM/XXXX
    amount_yuan = Column(Float, nullable=False)
    tax_rate = Column(Float, default=0.11)  # PPN 11%
    subtotal_yuan = Column(Float, nullable=False)
    tax_amount_yuan = Column(Float, default=0)
    total_yuan = Column(Float, nullable=False)
    status = Column(String(20), default="pending")  # pending / paid / cancelled
    due_date = Column(DateTime, nullable=True)
    paid_at = Column(DateTime, nullable=True)
    description = Column(Text, nullable=True)
    payment_method = Column(String(50), nullable=True)  # bank_transfer / ewallet / qris
    payment_proof_path = Column(String(500), nullable=True)
    is_auto_renewal = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index("idx_invoice_user", "user_id"),
        Index("idx_invoice_status", "status"),
        Index("idx_invoice_number", "invoice_number"),
    )


class SubscriptionAutoRenewal(Base):
    """自动续费配置表."""

    __tablename__ = "subscription_auto_renewals"

    id = Column(String(32), primary_key=True, default=lambda: uuid.uuid4().hex)
    subscriber_id = Column(
        String(32),
        ForeignKey("subscription_subscribers.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    enabled = Column(Boolean, default=True)
    last_renewal_attempt = Column(DateTime, nullable=True)
    next_renewal_date = Column(DateTime, nullable=True)
    failed_attempts = Column(Integer, default=0)
    max_failed_attempts = Column(Integer, default=3)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    subscriber = relationship("SubscriptionSubscriber")

    __table_args__ = (
        Index("idx_auto_renewal_subscriber", "subscriber_id"),
        Index("idx_auto_renewal_enabled", "enabled"),
    )
