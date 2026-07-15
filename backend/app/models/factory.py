"""工厂连接数据模型 (P3-6: RFQ + Samples + Quality Reports)."""

import uuid
from datetime import datetime

from sqlalchemy import Column, String, Integer, Float, Text, DateTime, ForeignKey, JSON, Index
from sqlalchemy.orm import relationship

from app.database import Base


def generate_uuid():
    return uuid.uuid4().hex[:32]


class RFQRequest(Base):
    """询价请求表."""
    __tablename__ = "rfq_requests"

    id = Column(String(32), primary_key=True, default=generate_uuid)
    user_id = Column(String(32), nullable=False)
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    materials = Column(JSON, nullable=True)  # [{"name": "cotton", "qty": 100}]
    quantity = Column(Integer, nullable=True)
    deadline = Column(String(20), nullable=True)
    status = Column(String(20), default="draft")  # draft/sent/accepted/rejected/closed
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index("idx_rfq_user", "user_id"),
        Index("idx_rfq_status", "status"),
    )


class Sample(Base):
    """样品表."""
    __tablename__ = "samples"

    id = Column(String(32), primary_key=True, default=generate_uuid)
    rfq_id = Column(String(32), ForeignKey("rfq_requests.id"), nullable=True)
    status = Column(String(20), default="requested")  # requested/sent/received/inspected
    shipped_at = Column(DateTime, nullable=True)
    received_at = Column(DateTime, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (Index("idx_samples_rfq", "rfq_id"),)


class QualityReport(Base):
    """质检报告表."""
    __tablename__ = "quality_reports"

    id = Column(String(32), primary_key=True, default=generate_uuid)
    sample_id = Column(String(32), ForeignKey("samples.id"), nullable=True)
    aql_level = Column(String(10), default="S-3")  # AQL sampling level
    defects = Column(JSON, nullable=True)  # [{"type": "scratch", "count": 2}]
    passed = Column(Integer, default=0)
    total_inspected = Column(Integer, default=0)
    inspector_notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (Index("idx_qr_sample", "sample_id"),)


# ===========================================================================
# Phase 4 Task 1: 手工艺人数据模型 (Factory / CraftProduct / RFQ)
# ===========================================================================


class Factory(Base):
    """合作工厂表.

    手工艺人可以对接的加工厂/工作室资源.
    """
    __tablename__ = "factories"

    id = Column(String(32), primary_key=True, default=generate_uuid)
    name = Column(String(200), nullable=False)
    location = Column(String(200), nullable=True)          # 地址/城市
    contact = Column(String(100), nullable=True)            # 联系人
    rating = Column(Float, nullable=True)                   # 评分 (1-5)
    capabilities = Column(JSON, nullable=True)              # 生产能力标签
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index("idx_factory_rating", "rating"),
    )


class CraftProduct(Base):
    """手工艺品表.

    手工艺人上架的具体商品/手作单品.
    """
    __tablename__ = "craft_products"

    id = Column(String(32), primary_key=True, default=generate_uuid)
    work_variant_id = Column(
        String(32), ForeignKey("work_variants.id", ondelete="CASCADE"), nullable=True,
    )
    material = Column(String(200), nullable=True)           # 材质
    dimensions = Column(JSON, nullable=True)                # {length, width, height, weight}
    craft_type = Column(String(50), nullable=True)          # 刺绣/陶瓷/木雕/编织等
    moq = Column(Integer, default=1)                        # 最小起订量
    unit_price = Column(Float, nullable=True)               # 单价
    production_time_days = Column(Integer, nullable=True)   # 生产周期(天)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index("idx_craft_work_variant", "work_variant_id"),
    )


class RFQ(Base):
    """询价单表.

    手工艺场景: 向工厂询价采购特定手工艺品.
    """
    __tablename__ = "rfqs"

    id = Column(String(32), primary_key=True, default=generate_uuid)
    craft_product_id = Column(
        String(32), ForeignKey("craft_products.id", ondelete="CASCADE"), nullable=True,
    )
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    quantity_needed = Column(Integer, nullable=True)
    material_specs = Column(JSON, nullable=True)
    target_price = Column(Float, nullable=True)
    status = Column(String(20), default="open")  # open/quoted/awarded/closed
    quoted_factories = Column(JSON, nullable=True)          # [{"factory_id", "quote"]}
    created_by = Column(String(32), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index("idx_rfq_status", "status"),
    )
