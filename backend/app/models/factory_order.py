"""工厂订单数据模型 — v6.0 运营者视角的生产订单."""

import uuid
from datetime import datetime, date, timezone
from typing import Optional

from sqlalchemy import Column, String, Float, Integer, Text, Date, DateTime, Boolean, ForeignKey, JSON, Index
from sqlalchemy.orm import relationship

from app.database import Base


def generate_uuid() -> str:
    return uuid.uuid4().hex[:32]


class FactoryOrder(Base):
    """运营者视角的生产订单 — 关联合约与工厂.

    用于将合约认购转化为实际生产任务，跟踪从下单到交付的全流程.
    """
    __tablename__ = "factory_orders"

    id = Column(String(32), primary_key=True, default=generate_uuid)
    order_number = Column(String(50), nullable=False, unique=True, index=True)

    contract_id = Column(
        String(32), ForeignKey("contract_instances.id", ondelete="SET NULL"), nullable=True,
    )
    work_id = Column(String(32), nullable=True, index=True)

    operator_id = Column(
        String(32), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True,
    )
    factory_id = Column(
        String(32), ForeignKey("partners.id", ondelete="SET NULL"), nullable=True,
    )

    product_name = Column(String(500), nullable=False)
    product_category = Column(String(100), nullable=True)
    quantity = Column(Integer, nullable=False, default=1)
    unit_price = Column(Float, default=0.0)
    total_amount = Column(Float, default=0.0)

    scope_regions = Column(JSON, nullable=True)
    scope_channels = Column(JSON, nullable=True)
    scope_products = Column(JSON, nullable=True)

    status = Column(String(20), nullable=False, default="draft")
    # draft → quoting → confirmed → in_production → quality_check → shipped → completed → cancelled

    quality_report_id = Column(String(32), nullable=True)
    quality_passed = Column(Boolean, nullable=True)
    quality_notes = Column(Text, nullable=True)

    expected_date = Column(Date, nullable=True)
    actual_ship_date = Column(Date, nullable=True)
    actual_deliver_date = Column(Date, nullable=True)

    shipping_method = Column(String(100), nullable=True)
    tracking_number = Column(String(200), nullable=True)

    pod_platform = Column(String(50), nullable=True)  # printful/printify/gelato/None
    pod_order_id = Column(String(200), nullable=True)

    notes = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=datetime.now(timezone.utc), onupdate=datetime.now(timezone.utc))

    contract = relationship("ContractInstance", backref="factory_orders")
    operator = relationship("User", backref="factory_orders_operator")
    factory = relationship("Partner", backref="factory_orders")

    __table_args__ = (
        Index("idx_for_operator", "operator_id", "status"),
        Index("idx_for_contract", "contract_id"),
        Index("idx_for_work", "work_id"),
        Index("idx_for_factory", "factory_id"),
    )


class FactoryQualification(Base):
    """工厂资质认证记录."""
    __tablename__ = "factory_qualifications"

    id = Column(String(32), primary_key=True, default=generate_uuid)
    partner_id = Column(
        String(32), ForeignKey("partners.id", ondelete="CASCADE"), nullable=False, index=True,
    )
    qual_type = Column(String(50), nullable=False)  # business_license/iso9001/product_cert/safety_cert
    file_path = Column(String(2000), nullable=False)
    file_name = Column(String(500), nullable=True)
    expire_date = Column(Date, nullable=True)
    verified = Column(Boolean, default=False)
    verified_by = Column(String(32), nullable=True)
    verified_at = Column(DateTime, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.now(timezone.utc))

    __table_args__ = (
        Index("idx_fq_partner", "partner_id"),
        Index("idx_fq_type", "qual_type"),
    )


class PODConfig(Base):
    """POD 平台配置 — 预留 Printful/Printify/Gelato 等对接接口."""
    __tablename__ = "pod_configs"

    id = Column(String(32), primary_key=True, default=generate_uuid)
    platform = Column(String(50), nullable=False, unique=True)  # printful/printify/gelato/custom
    operator_id = Column(
        String(32), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True,
    )
    api_key_encrypted = Column(Text, nullable=False)
    api_secret_encrypted = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    default_store_id = Column(String(200), nullable=True)
    settings = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=datetime.now(timezone.utc), onupdate=datetime.now(timezone.utc))

    __table_args__ = (
        Index("idx_pod_platform", "platform"),
    )
