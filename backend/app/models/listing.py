import enum
import uuid
from datetime import datetime

from sqlalchemy import Column, String, DateTime, Float, ForeignKey, Integer, Boolean, JSON
from app.database import Base


class ListingStatus(enum.StrEnum):
    ACTIVE = "active"
    SOLD = "sold"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


class Listing(Base):
    """挂牌记录 — 创作者主动上架作品，买家可直接购买."""
    __tablename__ = "listings"

    id = Column(String(32), primary_key=True, default=lambda: uuid.uuid4().hex)
    work_id = Column(String(32), ForeignKey("works.id"), nullable=False, index=True)
    seller_id = Column(String(32), nullable=False, index=True)
    title = Column(String(200), nullable=False)
    description = Column(String(2000), nullable=True)
    asking_price_yuan = Column(Float, nullable=False)
    original_cost_yuan = Column(Float, nullable=True)  # 成本价，用于计算利润分成
    min_price_yuan = Column(Float, nullable=True)       # 最低接受价
    max_discount_percent = Column(Float, default=10.0)  # 最大议价空间
    quantity_total = Column(Integer, default=1)          # 总数量
    quantity_sold = Column(Integer, default=0)           # 已售数量
    status = Column(String(20), default=ListingStatus.ACTIVE)
    expires_at = Column(DateTime, nullable=True)
    buyer_id = Column(String(32), nullable=True, index=True)
    sold_at = Column(DateTime, nullable=True)
    profit_split_percent = Column(Float, default=70.0)   # 创作者分成比例
    platform_fee_rate_bps = Column(Integer, default=200)  # 平台费率(2%=200bps)
    tags = Column(JSON, nullable=True)                   # 搜索标签
    extra_metadata = Column(JSON, nullable=True)               # 扩展元数据
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
