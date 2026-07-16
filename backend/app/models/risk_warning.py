"""风险预警数据模型."""

from datetime import datetime, date

from sqlalchemy import (
    Column, String, Float, Text, DateTime, Boolean, ForeignKey, Index, Date, JSON, Integer,
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


class TaxDeadline(Base):
    """税务合规截止日期."""

    __tablename__ = "tax_deadlines"

    id = Column(String(32), primary_key=True, default=generate_uuid)
    user_id = Column(String(32), nullable=False)
    tax_type = Column(String(50), nullable=False)  # quarterly_vat, annual_income, foreign_withholding
    due_date = Column(Date, nullable=False)
    amount_yuan = Column(Float, nullable=True)
    is_completed = Column(Boolean, default=False)
    completed_date = Column(Date, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class HealthMetric(Base):
    """创作者健康指标 — burnout 预警."""

    __tablename__ = "health_metrics"

    id = Column(String(32), primary_key=True, default=generate_uuid)
    user_id = Column(String(32), nullable=False)
    daily_work_hours = Column(Float, nullable=False)
    works_created = Column(Integer, default=0)
    has_break_taken = Column(Boolean, default=False)
    mood_score = Column(Integer, nullable=True)  # 1-10
    recorded_date = Column(Date, nullable=False)
