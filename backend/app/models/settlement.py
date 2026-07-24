"""多币种结算和税务计算数据模型."""

from datetime import datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import Column, String, Text, DateTime, JSON, Index, Numeric
from sqlalchemy.orm import relationship

from app.database import Base
from app.models.work import generate_uuid


class TaxCalculation(Base):
    """单次税务计算结果."""
    __tablename__ = "tax_calculations"

    id = Column(String(32), primary_key=True, default=generate_uuid)
    contract_id = Column(String(32), nullable=True)
    transaction_id = Column(String(100), nullable=True)
    seller_location = Column(JSON, nullable=False)  # {"country": "CN", "state": "SH"}
    buyer_location = Column(JSON, nullable=False)
    product_type = Column(String(20), nullable=False)  # digital/physical/license
    amount = Column(Numeric(12, 2), nullable=False)
    currency = Column(String(10), nullable=False)
    tax_amount = Column(Numeric(12, 2), nullable=True)
    tax_rate = Column(Numeric(5, 4), nullable=True)
    tax_jurisdiction = Column(String(200), nullable=True)
    exemption_status = Column(String(50), nullable=True)
    calculated_by = Column(String(20), default="manual")  # avalara/manual
    calculated_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    __table_args__ = (
        Index("idx_tc_calculated_at", "calculated_at"),
        Index("idx_tc_product_type", "product_type"),
    )


class MultiCurrencySettlement(Base):
    """多币种结算记录."""
    __tablename__ = "multi_currency_settlements"

    id = Column(String(32), primary_key=True, default=generate_uuid)
    contract_id = Column(String(32), nullable=False, index=True)
    participant_id = Column(String(32), nullable=False, index=True)
    source_currency = Column(String(10), nullable=False)
    source_amount = Column(Numeric(12, 2), nullable=False)
    target_currency = Column(String(10), nullable=False)
    target_amount = Column(Numeric(12, 2), nullable=False)
    exchange_rate = Column(Numeric(12, 8), nullable=False)
    exchange_source = Column(String(50), nullable=True)  # stripe/ecb/manual
    settled_at = Column(DateTime, nullable=True)
    status = Column(String(20), default="pending")  # pending/settled/failed/refunded
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("idx_mcs_status", "status"),
        Index("idx_mcs_participant", "participant_id"),
    )
