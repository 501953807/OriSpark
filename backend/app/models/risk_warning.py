"""风险预警数据模型."""

from datetime import datetime

from sqlalchemy import (
    Column, String, Float, Text, DateTime, Boolean, ForeignKey, Index,
)

from app.database import Base
from app.models.work import generate_uuid


class RiskWarning(Base):
    """风险预警记录表."""
    __tablename__ = "risk_warnings"

    id = Column(String(32), primary_key=True, default=generate_uuid)
    user_id = Column(String(32), nullable=False)
    work_id = Column(String(32), ForeignKey("works.id"), nullable=True)
    warning_type = Column(String(50), nullable=False)
    severity = Column(String(20), nullable=False)
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    matched_entity = Column(String(500), nullable=True)
    confidence = Column(Float, nullable=True)
    suggestion = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    dismissed = Column(Boolean, default=False)
    dismissed_at = Column(DateTime, nullable=True)

    __table_args__ = (
        Index("idx_risk_work", "work_id"),
        Index("idx_risk_type", "warning_type"),
        Index("idx_risk_severity", "severity"),
    )
