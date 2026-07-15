"""风控系统数据模型."""

from datetime import datetime

from sqlalchemy import (
    Column, String, Float, Text, DateTime, Boolean, Integer, ForeignKey, JSON, Index,
)

from app.database import Base
from app.models.work import generate_uuid


class RiskRule(Base):
    """风控规则配置表."""
    __tablename__ = "risk_rules"

    id = Column(String(32), primary_key=True, default=generate_uuid)
    name = Column(String(200), nullable=False, unique=True)
    description = Column(Text, nullable=True)
    rule_type = Column(String(50), nullable=False)  # price_anomaly, credit_drop, frequency, blacklist, content_match
    condition = Column(JSON, nullable=False)  # {field, operator, value, threshold}
    severity = Column(String(20), nullable=False, default="medium")  # low/medium/high/critical
    action = Column(String(50), nullable=False, default="flag")  # flag/review/block/notify
    weight = Column(Integer, default=1)  # rule weight in composite scoring
    enabled = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index("idx_risk_rule_type", "rule_type"),
        Index("idx_risk_rule_enabled", "enabled"),
    )


class RiskAssessment(Base):
    """风控评估记录表."""
    __tablename__ = "risk_assessments"

    id = Column(String(32), primary_key=True, default=generate_uuid)
    user_id = Column(String(32), nullable=False, index=True)
    target_type = Column(String(50), nullable=False)  # transaction, listing, bid, user_registration
    target_id = Column(String(50), nullable=True)
    risk_score = Column(Float, nullable=False, default=0.0)  # 0-100
    risk_level = Column(String(20), nullable=False, default="low")  # safe/low/medium/high/critical
    triggered_rules = Column(JSON, nullable=True)  # list of rule IDs that fired
    decision = Column(String(50), nullable=False, default="allow")  # allow/review/block/warn
    decision_reason = Column(Text, nullable=True)
    reviewed_by = Column(String(32), nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    review_notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("idx_risk_user", "user_id"),
        Index("idx_risk_level", "risk_level"),
        Index("idx_risk_decision", "decision"),
    )


class BlacklistEntry(Base):
    """黑名单记录表."""
    __tablename__ = "blacklist_entries"

    id = Column(String(32), primary_key=True, default=generate_uuid)
    user_id = Column(String(32), nullable=False, index=True)
    reason = Column(String(200), nullable=False)
    category = Column(String(50), nullable=False)  # fraud, copyright, spam, harassment, policy_violation
    added_by = Column(String(32), nullable=True)
    expires_at = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
