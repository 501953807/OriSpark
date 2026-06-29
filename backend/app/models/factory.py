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
