import enum
import uuid
from datetime import datetime

from sqlalchemy import Column, String, DateTime, Float, ForeignKey, Integer, Boolean, JSON, Text
from app.database import Base


class MatchMode(enum.StrEnum):
    AUCTION = "auction"         # 竞价模式
    LICENSING = "licensing"     # 授权撮合


class BidStatus(enum.StrEnum):
    OPEN = "open"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    WITHDRAWN = "withdrawn"


class AuctionRecord(Base):
    """竞价记录 — 创作者挂牌作品，商家竞价."""
    __tablename__ = "auction_records"

    id = Column(String(32), primary_key=True, default=lambda: uuid.uuid4().hex)
    listing_id = Column(String(32), nullable=False, index=True)
    work_id = Column(String(32), ForeignKey("works.id"), nullable=False, index=True)
    seller_id = Column(String(32), nullable=False, index=True)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    starting_price_yuan = Column(Float, nullable=False)
    current_bid_yuan = Column(Float, nullable=False)
    bid_count = Column(Integer, default=0)
    min_increment_yuan = Column(Float, default=10.0)
    ends_at = Column(DateTime, nullable=False, index=True)
    status = Column(String(20), default="active")  # active/closed/extended
    winner_buyer_id = Column(String(32), nullable=True)
    winner_amount_yuan = Column(Float, nullable=True)
    auto_extend_seconds = Column(Integer, default=300)  # 最后5分钟未结束则延长
    created_at = Column(DateTime, default=datetime.utcnow)


class Bid(Base):
    """竞价出价."""
    __tablename__ = "bids"

    id = Column(String(32), primary_key=True, default=lambda: uuid.uuid4().hex)
    auction_id = Column(String(32), ForeignKey("auction_records.id"), nullable=False, index=True)
    buyer_id = Column(String(32), nullable=False, index=True)
    amount_yuan = Column(Float, nullable=False)
    status = Column(String(20), default=BidStatus.OPEN)
    notes = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class LicensingMatch(Base):
    """授权撮合 — 商家向创作者发起授权要约."""
    __tablename__ = "licensing_matches"

    id = Column(String(32), primary_key=True, default=lambda: uuid.uuid4().hex)
    work_id = Column(String(32), ForeignKey("works.id"), nullable=False, index=True)
    seller_id = Column(String(32), nullable=False, index=True)
    buyer_id = Column(String(32), nullable=False, index=True)
    license_type = Column(String(50), nullable=False)  # exclusive/non-exclusive/perpetual/time-limited
    usage_scope = Column(String(200), nullable=True)  # 使用范围描述
    territory = Column(String(100), nullable=True)  # 地域限制
    duration_days = Column(Integer, nullable=True)
    price_per_use_cents = Column(Integer, nullable=True)  # 单次使用费(分)
    minimum_guarantee_yuan = Column(Float, nullable=True)  # 保底金
    royalty_percent = Column(Float, nullable=True)  # 分成比例
    status = Column(String(20), default="pending")  # pending/negotiating/agreed/rejected/terminated
    notes = Column(Text, nullable=True)
    agreed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
