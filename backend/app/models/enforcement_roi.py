"""维权ROI计算器数据模型."""

import uuid
from datetime import date, datetime
from sqlalchemy import Column, String, DateTime, Float, Boolean, Text, Integer, ForeignKey, JSON, CheckConstraint
from app.database import Base


class EnforcementCase(Base):
    """维权案例记录表."""

    __tablename__ = "enforcement_cases"
    __table_args__ = (
        CheckConstraint("infringement_type IN ('platform_copy', 'commercial_use', 'ai_training', 'social_share', 'reverse_image')", name="check_infringement_type"),
        CheckConstraint("action_taken IN ('cease_desist', 'platform_complaint', 'civil_lawsuit', 'criminal_report', 'none')", name="check_action_taken"),
        CheckConstraint("outcome IN ('successful', 'partial', 'no_response', 'lost', 'settled')", name="check_outcome"),
    )

    id = Column(String(32), primary_key=True, default=lambda: uuid.uuid4().hex)
    user_id = Column(String(32), nullable=False, index=True)
    work_id = Column(String(32), nullable=True)
    infringement_type = Column(String(30), nullable=False)
    target_platform = Column(String(100), nullable=False)
    estimated_loss_yuan = Column(Float, nullable=False)
    action_taken = Column(String(20), nullable=False)
    cost_yuan = Column(Float, default=0)  # 律师费/诉讼费/时间成本
    time_to_resolve_days = Column(Integer, nullable=True)
    compensation_received_yuan = Column(Float, default=0)
    outcome = Column(String(20), nullable=False)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class CaseReference(Base):
    """参考案例库 — 用于相似案例匹配."""

    __tablename__ = "case_references"

    id = Column(String(32), primary_key=True, default=lambda: uuid.uuid4().hex)
    infringement_type = Column(String(30), nullable=False)
    target_platform = Column(String(100), nullable=False)
    typical_cost_range_low = Column(Float, nullable=True)
    typical_cost_range_high = Column(Float, nullable=True)
    resolution_time_days_low = Column(Integer, nullable=True)
    resolution_time_days_high = Column(Integer, nullable=True)
    win_rate_percent = Column(Float, nullable=True)  # 成功率
    avg_compensation_yuan = Column(Float, nullable=True)
    roi_tier = Column(String(20), nullable=True)  # "high" / "medium" / "low_negative"
    description_zh = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)


class DefenseBudgetTier(Base):
    """四层防御预算配置."""

    __tablename__ = "defense_budget_tiers"

    id = Column(String(32), primary_key=True, default=lambda: uuid.uuid4().hex)
    tier_key = Column(String(30), nullable=False, unique=True)  # "zero", "low", "mid", "high"
    tier_name_zh = Column(String(50), nullable=False)
    monthly_cost_low = Column(Float, nullable=True)
    monthly_cost_high = Column(Float, nullable=True)
    annual_cost_low = Column(Float, nullable=True)
    annual_cost_high = Column(Float, nullable=True)
    features = Column(JSON, nullable=True)  # ["水印", "C2PA存证", "监控扫描"]
    description_zh = Column(Text, nullable=True)
    recommended_for = Column(String(200), nullable=True)
