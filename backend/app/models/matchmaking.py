import uuid
from datetime import datetime

from sqlalchemy import Column, String, DateTime, Float, ForeignKey, Integer, Text, JSON
from app.database import Base


class MatchRequest(Base):
    """撮合请求 — 商家发布需求，系统推荐创作者."""
    __tablename__ = "match_requests"

    id = Column(String(32), primary_key=True, default=lambda: uuid.uuid4().hex)
    buyer_id = Column(String(32), nullable=False, index=True)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    category = Column(String(50), nullable=True)  # illustration/music/photo/video
    style_tags = Column(JSON, nullable=True)  # ["minimalist", "vintage"]
    budget_min_yuan = Column(Float, nullable=True)
    budget_max_yuan = Column(Float, nullable=True)
    delivery_deadline = Column(DateTime, nullable=True)
    status = Column(String(20), default="pending")  # pending/matching/awarded/closed
    matched_seller_ids = Column(JSON, nullable=True)  # recommended seller IDs
    awarded_to = Column(String(32), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class MatchTransaction(Base):
    """撮合成交记录 — 记录撮合成功后的交易."""
    __tablename__ = "match_transactions"

    id = Column(String(32), primary_key=True, default=lambda: uuid.uuid4().hex)
    match_request_id = Column(String(32), ForeignKey("match_requests.id"), nullable=False, index=True)
    buyer_id = Column(String(32), nullable=False, index=True)
    seller_id = Column(String(32), nullable=False, index=True)
    work_id = Column(String(32), ForeignKey("works.id"), nullable=True, index=True)
    agreed_amount_yuan = Column(Float, nullable=False)
    payment_status = Column(String(20), default="pending")  # pending/paid/refunded
    delivery_status = Column(String(20), default="pending")  # pending/delivered/accepted/rejected
    delivery_date = Column(DateTime, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
