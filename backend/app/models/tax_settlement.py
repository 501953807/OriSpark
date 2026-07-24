"""税务代理和税务报告数据模型."""

from datetime import datetime
from typing import Any

from sqlalchemy import Column, String, Text, DateTime, JSON, Index, Numeric, Integer, ForeignKey
from sqlalchemy.orm import relationship

from app.database import Base
from app.models.work import generate_uuid


class TaxAgent(Base):
    """税务代理入驻信息."""
    __tablename__ = "tax_agents"

    id = Column(String(32), primary_key=True, default=generate_uuid)
    participant_id = Column(String(32), nullable=False, index=True)
    name = Column(String(200), nullable=False)
    license_no = Column(String(100), nullable=True)
    service_areas = Column(JSON, nullable=True)  # ['CN', 'US', 'EU', 'JP']
    fee_rate = Column(Numeric(5, 4), nullable=False)  # 服务费率，如 0.02 = 2%
    avalara_account_id = Column(String(100), nullable=True)
    status = Column(String(20), default="pending", nullable=False)  # pending/approved/suspended/deactivated
    rating = Column(Numeric(3, 2), nullable=True)
    review_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    approved_at = Column(DateTime, nullable=True)

    reports = relationship(
        "TaxReport",
        back_populates="agent",
        cascade="all, delete-orphan",
        order_by="TaxReport.created_at.desc()",
    )

    __table_args__ = (
        Index("idx_ta_status", "status"),
        Index("idx_ta_service_areas", "service_areas"),
    )


class TaxReport(Base):
    """税务报告."""
    __tablename__ = "tax_reports"

    id = Column(String(32), primary_key=True, default=generate_uuid)
    participant_id = Column(String(32), nullable=False, index=True)
    agent_id = Column(String(32), ForeignKey("tax_agents.id"), nullable=True, index=True)
    report_period = Column(String(20), nullable=False)  # '2026-Q3' / '2026-08'
    total_income = Column(Numeric(12, 2), default=0)
    total_tax_withheld = Column(Numeric(12, 2), default=0)
    total_tax_owed = Column(Numeric(12, 2), default=0)
    currency = Column(String(10), default="CNY")
    generated_by = Column(String(50), nullable=True)
    status = Column(String(20), default="draft")  # draft/final/submitted
    file_path = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    finalized_at = Column(DateTime, nullable=True)

    agent = relationship("TaxAgent", back_populates="reports")

    __table_args__ = (
        Index("idx_tr_period", "report_period"),
        Index("idx_tr_status", "status"),
    )
