"""议价协商数据模型."""

from datetime import datetime

from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Numeric, Index
from sqlalchemy.orm import relationship

from app.database import Base
from app.models.work import generate_uuid


class TradeNegotiation(Base):
    """多轮议价协商记录."""
    __tablename__ = "trade_negotiations"

    id = Column(String(32), primary_key=True, default=generate_uuid)
    buyer_id = Column(String(32), ForeignKey("users.id"), nullable=False, index=True)
    seller_id = Column(String(32), ForeignKey("users.id"), nullable=False, index=True)
    listing_id = Column(String(32), ForeignKey("listings.id"), nullable=True, index=True)
    match_request_id = Column(String(32), ForeignKey("match_requests.id"), nullable=True, index=True)
    description = Column(Text, nullable=True)
    initial_price_yuan = Column(Numeric(12, 2), nullable=True)
    current_offer_yuan = Column(Numeric(12, 2), nullable=True)
    final_price_yuan = Column(Numeric(12, 2), nullable=True)
    status = Column(String(20), default="pending", index=True)
    message_log = Column(Text, nullable=True)  # JSON string
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index("idx_nego_buyer", "buyer_id"),
        Index("idx_nego_seller", "seller_id"),
        Index("idx_nego_status", "status"),
        Index("idx_nego_created", "created_at"),
    )
