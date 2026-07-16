"""POD (Print-on-Demand) 利润计算器数据模型."""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Float, Boolean, Text, Integer, JSON
from app.database import Base


class PODProduct(Base):
    """POD 产品配置 — 定义各平台/产品的成本结构."""

    __tablename__ = "pod_products"

    id = Column(String(32), primary_key=True, default=lambda: uuid.uuid4().hex)
    user_id = Column(String(32), nullable=False, index=True)
    platform = Column(String(50), nullable=False)  # "redbubble", "printful", "printify"
    product_type = Column(String(50), nullable=False)  # "t-shirt", "phone_case", "poster", "mug", "sticker"
    base_cost_usd = Column(Float, nullable=False)  # 平台基础成本 (USD)
    base_cost_cny = Column(Float, nullable=True)  # 折合人民币
    shipping_cost_usd = Column(Float, default=0)  # 运费
    markup_rate = Column(Float, default=0.2)  # 加价率 (0.2 = 20%)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class PODDesign(Base):
    """POD 设计作品 — 关联到具体作品的 POD 发布."""

    __tablename__ = "pod_designs"

    id = Column(String(32), primary_key=True, default=lambda: uuid.uuid4().hex)
    user_id = Column(String(32), nullable=False, index=True)
    work_id = Column(String(32), nullable=True, index=True)
    title = Column(String(500), nullable=False)
    platforms = Column(JSON, nullable=False)  # [{"platform": "redbubble", "product_types": [...], "markup": 0.2}]
    status = Column(String(20), default="draft")  # draft / published / paused
    total_sales = Column(Integer, default=0)
    total_revenue_cny = Column(Float, default=0)
    total_profit_cny = Column(Float, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)


class PODSale(Base):
    """POD 销售记录 — 追踪每笔交易的利润."""

    __tablename__ = "pod_sales"

    id = Column(String(32), primary_key=True, default=lambda: uuid.uuid4().hex)
    design_id = Column(String(32), nullable=True, index=True)
    user_id = Column(String(32), nullable=False, index=True)
    platform = Column(String(50), nullable=False)
    product_type = Column(String(50), nullable=False)
    sale_price_usd = Column(Float, nullable=False)
    base_cost_usd = Column(Float, nullable=False)
    shipping_cost_usd = Column(Float, default=0)
    platform_fee_pct = Column(Float, default=0)  # 平台手续费比例
    profit_usd = Column(Float, default=0)
    profit_cny = Column(Float, default=0)
    exchange_rate = Column(Float, default=7.2)  # USD/CNY 汇率
    sold_at = Column(DateTime, default=datetime.utcnow)
