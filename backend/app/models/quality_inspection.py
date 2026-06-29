"""质检分级表 — 手工艺人 v3 预留 (15.3.4).

Separate from factory.QualityReport (which is for RFQ samples).
This table tracks production batch quality inspections.
v3 激活.
"""

import uuid
from datetime import datetime

from sqlalchemy import Column, String, Integer, Float, Boolean, Text, DateTime, ForeignKey, JSON, Index
from sqlalchemy.orm import relationship

from app.database import Base


def _uid():
    return uuid.uuid4().hex[:32]


class QualityInspection(Base):
    """生产质检分级表.

    对生产批次中的成品进行AQL质检分级.
    v3 激活.
    """
    __tablename__ = "quality_inspections"

    id = Column(String(32), primary_key=True, default=_uid)
    batch_id = Column(String(32), ForeignKey("production_batches.id"), nullable=False)
    inspector_name = Column(String(200), nullable=True)
    aql_level = Column(String(10), default="S-3")
    inspected_count = Column(Integer, default=0)
    passed_count = Column(Integer, default=0)
    failed_count = Column(Integer, default=0)
    grade = Column(String(10), nullable=True)  # A/B/C
    defect_details = Column(JSON, nullable=True)
    inspection_notes = Column(Text, nullable=True)
    inspected_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (Index("idx_qi_batch", "batch_id"),)
