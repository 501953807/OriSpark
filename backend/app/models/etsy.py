"""Etsy 平台集成数据模型.

手工艺人 (v3b) — Etsy OAuth + Listing/Order/Shop 管理.
"""

import uuid
from datetime import datetime

from sqlalchemy import (
    Column, String, Text, DateTime, Boolean, ForeignKey,
    Index, Float, Integer, JSON,
)
from sqlalchemy.orm import relationship

from app.database import Base


def _uid():
    return uuid.uuid4().hex[:32]


# =============================================================================
# EtsyListing — Etsy 商品发布记录 (15.3.4)
# =============================================================================


class EtsyListing(Base):
    """Etsy listing 同步表.

    将 OriStudio 本地产品发布到 Etsy 店铺并追踪状态.
    v3b 激活.
    """

    __tablename__ = "etsy_listings"

    id = Column(String(32), primary_key=True, default=_uid)
    user_id = Column(String(32), nullable=False)
    product_id = Column(
        String(32), ForeignKey("physical_products.id"), nullable=True,
    )  # link to local product
    etsy_listing_id = Column(String(100), nullable=False)  # Etsy-side listing ID
    etsy_shop_id = Column(String(100), nullable=False)
    title = Column(String(140), nullable=False)
    description = Column(Text, nullable=True)
    price = Column(Float, nullable=False)
    currency = Column(String(10), default="USD")
    quantity = Column(Integer, default=1)
    etsy_category_id = Column(String(50), nullable=True)
    tags = Column(JSON, nullable=True)  # max 13 tags
    materials = Column(JSON, nullable=True)
    shipping_profile_id = Column(String(100), nullable=True)
    processing_time_days = Column(Integer, nullable=True)
    ships_from_country = Column(String(10), default="CN")
    shipping_cost = Column(Float, nullable=True)
    free_shipping = Column(Boolean, default=False)
    variations = Column(JSON, nullable=True)  # size/color options
    status = Column(String(20), default="draft")  # draft/active/inactive/sold_out
    etsy_status = Column(String(20), default="active")  # active/inactive/expired
    views_count = Column(Integer, default=0)
    favorites_count = Column(Integer, default=0)
    sales_count = Column(Integer, default=0)
    revenue = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index("idx_etsy_listing_user", "user_id"),
        Index("idx_etsy_listing_etsy", "etsy_listing_id"),
        Index("idx_etsy_listing_shop", "etsy_shop_id"),
        Index("idx_etsy_listing_status", "status"),
    )

    orders = relationship("EtsyOrder", back_populates="listing", cascade="all, delete-orphan")


# =============================================================================
# EtsyOrder — Etsy 订单记录 (15.3.5)
# =============================================================================


class EtsyOrder(Base):
    """Etsy 订单同步表.

    从 Etsy 拉取订单并在本地持久化.
    v3b 激活.
    """

    __tablename__ = "etsy_orders"

    id = Column(String(32), primary_key=True, default=_uid)
    user_id = Column(String(32), nullable=False)
    listing_id = Column(
        String(32), ForeignKey("etsy_listings.id"), nullable=True,
    )
    etsy_order_id = Column(String(100), nullable=False, unique=True)
    buyer_name = Column(String(200), nullable=True)
    buyer_country = Column(String(100), nullable=True)
    order_total = Column(Float, nullable=False)
    shipping_cost = Column(Float, nullable=True)
    tax = Column(Float, nullable=True)
    order_date = Column(DateTime, nullable=False)
    shipping_deadline = Column(DateTime, nullable=True)
    status = Column(String(20), default="paid")  # paid/shipped/completed/cancelled
    tracking_number = Column(String(100), nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index("idx_etsy_order_user", "user_id"),
        Index("idx_etsy_order_etsy", "etsy_order_id"),
        Index("idx_etsy_order_status", "status"),
    )

    listing = relationship("EtsyListing", back_populates="orders")


# =============================================================================
# EtsyShop — Etsy 店铺连接 (15.3.6)
# =============================================================================


class EtsyShop(Base):
    """Etsy 店铺连接表.

    存储 OAuth 凭证和店铺信息.
    v3b 激活.
    """

    __tablename__ = "etsy_shops"

    id = Column(String(32), primary_key=True, default=_uid)
    user_id = Column(String(32), nullable=False)
    shop_name = Column(String(100), nullable=False)
    shop_id = Column(String(100), nullable=False)  # Etsy shop ID
    access_token = Column(String(500), nullable=False)  # encrypted
    refresh_token = Column(String(500), nullable=True)  # encrypted
    token_expires_at = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index("idx_etsy_shop_user", "user_id"),
        Index("idx_etsy_shop_id", "shop_id"),
    )
