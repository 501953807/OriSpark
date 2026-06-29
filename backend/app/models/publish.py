"""发布变现数据模型."""

from datetime import datetime, date

from sqlalchemy import (
    Column, String, Text, DateTime, Date, Boolean, ForeignKey, Index, Float, Integer, JSON,
)
from sqlalchemy.orm import relationship

from app.database import Base
from app.models.work import generate_uuid


class Product(Base):
    """商品表 (增强 — P1.5 变现引擎)."""
    __tablename__ = "products"

    id = Column(String(32), primary_key=True, default=generate_uuid)
    work_id = Column(String(32), ForeignKey("works.id", ondelete="SET NULL"), nullable=True)
    order_id = Column(String(32), ForeignKey("orders.id", ondelete="SET NULL"), nullable=True)
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    ai_description = Column(Text, nullable=True)  # AI 生成的描述
    price = Column(Float, default=0.0)
    cost = Column(Float, default=0.0)  # ★ 成本(平台费用+制造成本)
    currency = Column(String(10), default="CNY")
    category = Column(String(100), nullable=True)

    # ★ P1.5: 变现引擎增强字段
    monetization_path = Column(String(50), nullable=True)    # pod / crowdfunding / licensing / custom_mfg / digital
    material_category = Column(String(50), nullable=True)    # paper / textile / hard_goods / plastic_3c / metal / wood / leather / toys / digital / special
    platform = Column(String(50), nullable=True)              # printful / redbubble / modian / kickstarter / ...
    platform_product_id = Column(String(100), nullable=True)
    platform_product_url = Column(String(1000), nullable=True)
    platform_status = Column(String(20), default="draft")     # draft / published / reviewing / suspended

    specifications = Column(JSON, nullable=True)
    design_variant_path = Column(String(2000), nullable=True) # ★ 适配后的设计稿路径
    mockup_image_path = Column(String(2000), nullable=True)  # ★ 产品效果图路径
    images = Column(JSON, nullable=True)  # 商品图片路径列表
    csv_export_path = Column(String(2000), nullable=True)

    status = Column(String(20), default="active")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    publishings = relationship("ProductPublishing", back_populates="product", cascade="all, delete-orphan")
    marks = relationship("VerifiedMark", back_populates="product", cascade="all, delete-orphan")
    revenues = relationship("RevenueRecord", back_populates="product", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_product_work", "work_id"),
        Index("idx_product_path", "monetization_path"),
        Index("idx_product_platform", "platform"),
        Index("idx_product_category", "category"),
        Index("idx_product_material", "material_category"),
        Index("idx_product_status", "status"),
    )


class ProductPublishing(Base):
    """发布记录表."""
    __tablename__ = "product_publishings"

    id = Column(String(32), primary_key=True, default=generate_uuid)
    product_id = Column(String(32), ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    listing_id = Column(String(32), ForeignKey("design_listings.id", ondelete="CASCADE"), nullable=True)  # P2: new FK to listing
    platform = Column(String(50), nullable=False)  # taobao/xiaohongshu/douyin/shopify
    listing_url = Column(String(2000), nullable=True)
    status = Column(String(20), default="draft")  # draft/publishing/published/failed
    error_message = Column(Text, nullable=True)
    published_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)

    product = relationship("Product", back_populates="publishings")
    listing = relationship("DesignListing", back_populates="publications")  # P2

    __table_args__ = (
        Index("idx_publish_product", "product_id"),
        Index("idx_publish_platform", "platform"),
        Index("idx_publish_status", "status"),
    )


class VerifiedMark(Base):
    """验证徽章."""
    __tablename__ = "verified_marks"

    id = Column(String(32), primary_key=True, default=generate_uuid)
    product_id = Column(String(32), ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    qr_code = Column(String(2000), nullable=True)  # 验证二维码
    cert_url = Column(String(2000), nullable=True)  # 验证页面 URL
    created_at = Column(DateTime, default=datetime.utcnow)

    product = relationship("Product", back_populates="marks")


class RevenueRecord(Base):
    """收入记录."""
    __tablename__ = "revenue_records"

    id = Column(String(32), primary_key=True, default=generate_uuid)
    product_id = Column(String(32), ForeignKey("products.id", ondelete="SET NULL"), nullable=True)
    listing_id = Column(String(32), ForeignKey("design_listings.id", ondelete="SET NULL"), nullable=True)  # P2
    platform = Column(String(50), nullable=False)
    amount = Column(Float, nullable=False, default=0.0)
    currency = Column(String(10), default="CNY")
    date = Column(Date, default=date.today)
    order_count = Column(Integer, default=1)

    # P1.6.9: Enhanced revenue model fields
    source = Column(String(50), default="manual")  # manual / mcp_api / csv_import / pod_api
    refund_amount = Column(Float, default=0.0)
    platform_fee = Column(Float, default=0.0)
    net_revenue = Column(Float, default=0.0)

    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    product = relationship("Product", back_populates="revenues")
    listing = relationship("DesignListing", back_populates="revenues")  # P2

    __table_args__ = (
        Index("idx_revenue_date", "date"),
        Index("idx_revenue_platform", "platform"),
    )


# ─── Content Distribution Center models (P2) ───


class PublishSchedule(Base):
    """排期发布表."""
    __tablename__ = "publish_schedules"

    id = Column(String(32), primary_key=True, default=generate_uuid)
    product_id = Column(String(32), ForeignKey("products.id", ondelete="SET NULL"), nullable=True)
    listing_id = Column(String(32), ForeignKey("design_listings.id", ondelete="SET NULL"), nullable=True)
    work_id = Column(String(32), ForeignKey("works.id", ondelete="SET NULL"), nullable=True)
    platform = Column(String(50), nullable=False)
    scheduled_time = Column(DateTime, nullable=False)
    status = Column(String(20), default="scheduled")  # scheduled/executing/succeeded/failed/cancelled
    content_preview = Column(Text, nullable=True)  # 文案预览
    executed_at = Column(DateTime, nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index("idx_schedule_platform", "platform"),
        Index("idx_schedule_time", "scheduled_time"),
        Index("idx_schedule_status", "status"),
    )


class PublishContent(Base):
    """发布内容表."""
    __tablename__ = "publish_contents"

    id = Column(String(32), primary_key=True, default=generate_uuid)
    work_id = Column(String(32), ForeignKey("works.id", ondelete="SET NULL"), nullable=True)
    product_id = Column(String(32), ForeignKey("products.id", ondelete="SET NULL"), nullable=True)
    title = Column(String(500), nullable=False)
    content_type = Column(String(20), default="work")  # work / product / pure_text
    text_content = Column(Text, nullable=True)
    image_paths = Column(JSON, nullable=True)  # 图片路径列表
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("idx_content_work", "work_id"),
        Index("idx_content_product", "product_id"),
    )


class PublishAnalytics(Base):
    """影响力分析数据表."""
    __tablename__ = "publish_analytics"

    id = Column(String(32), primary_key=True, default=generate_uuid)
    platform = Column(String(50), nullable=False)
    work_id = Column(String(32), ForeignKey("works.id", ondelete="SET NULL"), nullable=True)
    product_id = Column(String(32), ForeignKey("products.id", ondelete="SET NULL"), nullable=True)
    views = Column(Integer, default=0)
    likes = Column(Integer, default=0)
    comments = Column(Integer, default=0)
    shares = Column(Integer, default=0)
    saves = Column(Integer, default=0)
    date = Column(Date, default=date.today)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("idx_analytics_platform", "platform"),
        Index("idx_analytics_date", "date"),
    )
