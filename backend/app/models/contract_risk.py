"""合约风险评估数据模型."""

import uuid
from datetime import datetime

from sqlalchemy import Column, String, Float, Text, DateTime, Boolean, Integer, ForeignKey, Index

from app.database import Base
from app.models.work import generate_uuid


class ContractRiskRule(Base):
    """合约风险评估规则表."""
    __tablename__ = "contract_risk_rules"

    id = Column(String(32), primary_key=True, default=generate_uuid)
    rule_name = Column(String(200), nullable=False, unique=True)
    category = Column(String(50), nullable=False, index=True)  # 'general' | 'transaction'
    clause_type = Column(String(50), nullable=False)  # 条款类别标识
    risk_level = Column(String(20), nullable=False)  # safe/low/medium/high/critical
    weight = Column(Integer, default=1)
    description = Column(Text, nullable=True)
    suggestion = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index("idx_rule_category", "category", "clause_type"),
        Index("idx_rule_active", "is_active"),
    )


class ContractReview(Base):
    """合约审查记录表."""
    __tablename__ = "contract_reviews"

    id = Column(String(32), primary_key=True, default=generate_uuid)
    user_id = Column(String(32), nullable=False, index=True)
    review_type = Column(String(20), nullable=False)  # 'general' | 'transaction'
    target_type = Column(String(50), nullable=True)  # 'listing' / 'auction' / 'rfq' / null
    target_id = Column(String(50), nullable=True)
    contract_text = Column(Text, nullable=False)
    total_score = Column(Float, default=0.0)  # 综合风险分 0-100
    risk_level = Column(String(20), default="safe")  # safe/low/medium/high/critical
    clauses_found = Column(Integer, default=0)
    risk_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("idx_review_user", "user_id", "created_at"),
        Index("idx_review_risk", "risk_level"),
    )


class ContractClause(Base):
    """审查条款明细表."""
    __tablename__ = "contract_clauses"

    id = Column(String(32), primary_key=True, default=generate_uuid)
    review_id = Column(String(32), ForeignKey("contract_reviews.id"), nullable=False)
    clause_index = Column(Integer, nullable=False)
    clause_text = Column(Text, nullable=False)
    clause_category = Column(String(50), nullable=True)
    risk_level = Column(String(20), nullable=True)
    risk_description = Column(Text, nullable=True)
    suggestion = Column(Text, nullable=True)
    is_flagged = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("idx_clause_review", "review_id", "clause_index"),
    )
