"""Enhanced monetization models — P1.5 supply chain enhancements.

Adds: ProductTemplate, Campaign, License, MonetizationChannel, RevenueRecord (enhanced)
Extends: Partner with manufacturing capabilities, Order with order_type and sample mgmt.
"""

from datetime import datetime, date

from sqlalchemy import (
    Column, String, Text, DateTime, Date, Boolean, ForeignKey, Index, Float, Integer, JSON,
)
from sqlalchemy.orm import relationship

from app.database import Base
from app.models.work import generate_uuid


# ---------------------------------------------------------------------------
# ProductTemplate — design-to-product spec adapter rules
# ---------------------------------------------------------------------------
class ProductTemplate(Base):
    """产品规格模板 — per-platform + per-category design requirements."""
    __tablename__ = "product_templates"

    id = Column(String(32), primary_key=True, default=generate_uuid)
    platform = Column(String(50), nullable=False)           # printful / printify / redbubble / yingge
    product_category = Column(String(100), nullable=False)   # t_shirt / mug / poster / phone_case

    # design spec
    print_area_width_mm = Column(Float, nullable=True)
    print_area_height_mm = Column(Float, nullable=True)
    dpi_required = Column(Integer, default=300)
    file_format = Column(String(20), default="PNG")          # PNG / JPEG / PDF
    color_mode = Column(String(20), default="sRGB")           # sRGB / CMYK
    transparent_bg = Column(Integer, default=1)              # 1=required, 0=no
    bleed_mm = Column(Float, default=0)

    # pricing reference
    base_cost_cny = Column(Float, nullable=True)
    recommended_price_range = Column(JSON, nullable=True)    # [min, max]

    # metadata
    production_time_days = Column(Integer, nullable=True)
    shipping_regions = Column(JSON, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index("idx_pt_platform_cat", "platform", "product_category"),
    )


# ---------------------------------------------------------------------------
# MonetizationChannel — connected monetization channels (stores / accounts)
# ---------------------------------------------------------------------------
class MonetizationChannel(Base):
    """变现渠道."""
    __tablename__ = "monetization_channels"

    id = Column(String(32), primary_key=True, default=generate_uuid)
    name = Column(String(200), nullable=False)
    channel_type = Column(String(50), nullable=False)        # pod / crowdfunding / licensing / ecommerce / digital
    platform = Column(String(50), nullable=False)             # printful / redbubble / shopify / etsy / ...
    platform_store_id = Column(String(200), nullable=True)
    platform_store_url = Column(String(1000), nullable=True)
    credentials_encrypted = Column(Text, nullable=True)      # AES-encrypted API keys (if any)
    connected_at = Column(DateTime, nullable=True)
    last_sync_at = Column(DateTime, nullable=True)
    status = Column(String(20), default="active")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index("idx_mc_platform", "platform"),
        Index("idx_mc_type", "channel_type"),
    )


# ---------------------------------------------------------------------------
# Campaign — crowdfunding projects
# ---------------------------------------------------------------------------
class Campaign(Base):
    """众筹项目."""
    __tablename__ = "campaigns"

    id = Column(String(32), primary_key=True, default=generate_uuid)
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)

    platform = Column(String(50), nullable=False)            # modian / kickstarter / indiegogo / patreon
    platform_campaign_id = Column(String(100), nullable=True)
    platform_url = Column(String(1000), nullable=True)

    goal_amount = Column(Float, nullable=False)
    currency = Column(String(10), default="CNY")
    raised_amount = Column(Float, default=0)
    backer_count = Column(Integer, default=0)

    reward_tiers = Column(JSON, nullable=False)              # [{name, price, description, limit, sold}]

    launch_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)
    estimated_delivery_date = Column(Date, nullable=True)
    actual_delivery_date = Column(Date, nullable=True)

    status = Column(String(20), default="draft")             # draft/launching/funded/successful/failed/fulfilling/completed

    related_product_ids = Column(JSON, nullable=True)        # legacy: JSON array of old product IDs
    related_work_ids = Column(JSON, nullable=True)
    listing_id = Column(String(32), ForeignKey("design_listings.id", ondelete="SET NULL"), nullable=True)  # P2: FK to listing

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    listing = relationship("DesignListing", back_populates="campaigns")  # P2

    __table_args__ = (
        Index("idx_campaign_status", "status"),
        Index("idx_campaign_platform", "platform"),
        Index("idx_campaign_listing", "listing_id"),
    )


# ---------------------------------------------------------------------------
# License — IP licensing records
# ---------------------------------------------------------------------------
class License(Base):
    """IP授权记录."""
    __tablename__ = "licenses"

    id = Column(String(32), primary_key=True, default=generate_uuid)
    work_id = Column(String(32), ForeignKey("works.id", ondelete="SET NULL"), nullable=True)
    listing_id = Column(String(32), ForeignKey("design_listings.id", ondelete="SET NULL"), nullable=True)  # P2
    license_type = Column(String(50), nullable=False)       # single_use / multi_use / commercial_extended / buyout
    platform = Column(String(50), nullable=True)             # creative_fabrica / creative_market / envato / gumroad

    allowed_uses = Column(JSON, nullable=True)               # [personal, commercial, resale, modification]
    restrictions = Column(JSON, nullable=True)               # [no_resale, attribution_required, print_limit]

    price = Column(Float, nullable=False)
    currency = Column(String(10), default="CNY")

    platform_listing_id = Column(String(100), nullable=True)
    platform_listing_url = Column(String(1000), nullable=True)
    sales_count = Column(Integer, default=0)
    total_revenue = Column(Float, default=0)

    status = Column(String(20), default="active")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    listing = relationship("DesignListing", back_populates="licenses")  # P2

    __table_args__ = (
        Index("idx_license_type", "license_type"),
        Index("idx_license_platform", "platform"),
        Index("idx_license_listing", "listing_id"),
    )


# ---------------------------------------------------------------------------
# Product (enhanced) — extends publish.Product with monetization fields
#   Migrates existing "products" table by adding columns.
#   Using a separate model class for clarity; columns are added via migration.
#   For MVP, we add columns directly to the existing Product model.
# ---------------------------------------------------------------------------
# NOTE: We enhance publish.Product directly rather than creating a separate model.
# See app/models/publish.py — add monetization_path, material, etc. columns.


# ---------------------------------------------------------------------------
# Partner (enhanced) — add manufacturing capabilities fields
# ---------------------------------------------------------------------------
# NOTE: Enhance supply.Partner directly. Add:
#   - product_categories (JSON)
#   - material_capabilities (JSON)
#   - moq_per_category (JSON)
#   - typical_lead_time_days (Integer)
#   - price_range (JSON)
# See app/models/supply.py


# ---------------------------------------------------------------------------
# Order (enhanced) — add order_type and sample management
# ---------------------------------------------------------------------------
# NOTE: Enhance supply.Order directly. Add:
#   - order_type (String) — custom_mfg / pod_bulk / crowdfunding_fulfillment / sample
#   - product_category (String)
#   - design_file_path (String)
#   - shipping_cost (Float)
#   - campaign_id (String / FK)
#   - sample_requested, sample_received, sample_approved (Integer)
# See app/models/supply.py
