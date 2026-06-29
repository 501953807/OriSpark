"""Design Listing data models — P2 monetization engine restructuring.

Replaces the flat `products` table with a proper hierarchy:
  Design File (work) → Product Template → Listing → Publication

New tables:
- DesignListing: the sellable combination of a design + product template + pricing
- DesignTemplateCompatibility: tracks which templates each design passes/warns/errors on

This enables:
- One design → multiple listings (same art on T-shirt, mug, sticker)
- Spec validation failure → compatible product recommendations
- Cross-path product relationship (one listing → POD + crowdfunding + IP license)
"""

from datetime import datetime

from sqlalchemy import (
    Column, String, Text, DateTime, Boolean, ForeignKey, Index, Float, Integer, JSON,
)
from sqlalchemy.orm import relationship

from app.database import Base
from app.models.work import generate_uuid


# ---------------------------------------------------------------------------
# DesignListing — the sellable entity (design + template + pricing)
# ---------------------------------------------------------------------------
class DesignListing(Base):
    """商品 — 设计稿 × 产品模板 × 定价的组合。"""
    __tablename__ = "design_listings"

    id = Column(String(32), primary_key=True, default=generate_uuid)

    # Foreign keys
    work_id = Column(
        String(32), ForeignKey("works.id", ondelete="SET NULL"), nullable=True
    )
    product_template_id = Column(
        String(32),
        ForeignKey("product_templates.id", ondelete="RESTRICT"),
        nullable=False,
    )

    # Product info
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    ai_description = Column(Text, nullable=True)  # AI generated

    # Pricing
    price = Column(Float, default=0.0)
    cost = Column(Float, default=0.0)
    currency = Column(String(10), default="CNY")

    # Spec validation snapshot (stored at creation time)
    spec_validation = Column(JSON, nullable=True)  # Full SpecValidationReport
    spec_validated_at = Column(DateTime, nullable=True)

    # Variant info (basic size/color)
    variant_sku = Column(String(100), nullable=True)
    variant_name = Column(String(200), nullable=True)

    # Monetization path
    monetization_path = Column(
        String(50), nullable=True
    )  # pod / crowdfunding / licensing / custom_mfg / digital

    # Status
    status = Column(String(20), default="draft")  # draft / active / discontinued

    # Mockup / preview
    mockup_image_path = Column(String(2000), nullable=True)
    design_file_path = Column(String(2000), nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    publications = relationship(
        "ProductPublishing", back_populates="listing", cascade="all, delete-orphan"
    )
    revenues = relationship(
        "RevenueRecord", back_populates="listing", cascade="all, delete-orphan"
    )
    orders = relationship("Order", back_populates="listing")
    campaigns = relationship("Campaign", back_populates="listing")
    licenses = relationship("License", back_populates="listing")

    __table_args__ = (
        Index("idx_dl_work", "work_id"),
        Index("idx_dl_template", "product_template_id"),
        Index("idx_dl_path", "monetization_path"),
        Index("idx_dl_status", "status"),
    )


# ---------------------------------------------------------------------------
# DesignTemplateCompatibility — tracks which templates accept a design
# ---------------------------------------------------------------------------
class DesignTemplateCompatibility(Base):
    """设计稿与产品模板的兼容性记录。

    当设计稿通过 spec-validate-compat API 校验时，自动写入此表。
    用于"兼容产品推荐"功能 — 当某品类失败时，查询此表找到可通过的品类。
    """

    __tablename__ = "design_template_compatibility"

    id = Column(String(32), primary_key=True, default=generate_uuid)

    work_id = Column(
        String(32), ForeignKey("works.id", ondelete="CASCADE"), nullable=False
    )
    product_template_id = Column(
        String(32), ForeignKey("product_templates.id", ondelete="CASCADE"),
        nullable=False,
    )

    compatibility_score = Column(Float, default=0.0)  # 0.00 to 1.00
    spec_result = Column(String(20), default="error")  # pass / warning / error
    error_count = Column(Integer, default=0)
    warning_count = Column(Integer, default=0)
    compatible = Column(Boolean, default=False)  # True when spec_result == "pass"

    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("idx_dtc_work", "work_id"),
        Index("idx_dtc_template", "product_template_id"),
        Index("idx_dtc_compatible", "work_id", "compatible"),
        # One check per work+template pair
        Index("uq_dtc", "work_id", "product_template_id", unique=True),
    )


# ---------------------------------------------------------------------------
# Extend existing relationships in publish.py models
# ---------------------------------------------------------------------------
# ProductPublishing.listing relationship is added in the router migration
# Campaign.listing relationship is added in the router migration
# License.listing relationship is added in the router migration
# Order.listing relationship is added in the router migration
