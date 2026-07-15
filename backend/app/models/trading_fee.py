import enum
import uuid
from datetime import datetime

from sqlalchemy import Column, String, DateTime, Float, ForeignKey, Integer, Boolean, JSON
from app.database import Base


class FeeTier(enum.StrEnum):
    TIER_1 = "tier_1"        # base ≤ ¥10K → 2%
    TIER_2 = "tier_2"        # > ¥10K, ≤ ¥100K → 1.5%
    TIER_3 = "tier_3"        # > ¥100K, ≤ ¥500K → 1%
    TIER_4 = "tier_4"        # > ¥500K → 0.5%


class TransactionFee(Base):
    """交易费用记录."""
    __tablename__ = "transaction_fees"

    id = Column(String(32), primary_key=True, default=lambda: uuid.uuid4().hex)
    transaction_id = Column(String(32), nullable=False, index=True)
    seller_work_id = Column(String(32), ForeignKey("works.id"), nullable=True, index=True)
    buyer_id = Column(String(32), nullable=True, index=True)
    amount_yuan = Column(Float, nullable=False)
    fee_rate_bps = Column(Integer, nullable=False)  # basis points: 200 = 2%
    fee_amount_yuan = Column(Float, nullable=False)
    tier = Column(String(20), nullable=False, default="tier_1")
    is_discounted = Column(Boolean, default=False)
    discount_reason = Column(String(200), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class CommissionRule(Base):
    """佣金规则表 — 支持按创作者等级/品类差异化费率."""
    __tablename__ = "commission_rules"

    id = Column(String(32), primary_key=True, default=lambda: uuid.uuid4().hex)
    creator_type = Column(String(50), nullable=True, index=True)  # null = global default
    category = Column(String(50), nullable=True)
    min_volume_yuan = Column(Float, default=0)
    base_rate_bps = Column(Integer, default=200)  # 2% default
    volume_discount_rate_bps = Column(Integer, default=200)
    credit_bonus_rate_bps = Column(Integer, default=0)
    active = Column(Boolean, default=True)
    notes = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
