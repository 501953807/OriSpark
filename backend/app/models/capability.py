"""创作者能力评估数据模型."""

import uuid
from datetime import date, datetime
from sqlalchemy import Column, String, DateTime, Float, Boolean, Text, ForeignKey, CheckConstraint, Integer, JSON
from app.database import Base


class CapabilityDimension(Base):
    """能力维度定义表 — 8 维雷达图."""

    __tablename__ = "capability_dimensions"

    id = Column(String(32), primary_key=True, default=lambda: uuid.uuid4().hex)
    dimension_key = Column(String(100), nullable=False, unique=True)  # "artistic_skill", "market_awareness", etc.
    name_zh = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    weight = Column(Float, nullable=False, default=1.0)  # 权重 0-1
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class CreatorAssessment(Base):
    """创作者能力评估记录表."""

    __tablename__ = "creator_assessments"

    id = Column(String(32), primary_key=True, default=lambda: uuid.uuid4().hex)
    user_id = Column(String(32), nullable=False, index=True)
    overall_score = Column(Float, nullable=True)  # 综合评分 0-100
    dimension_scores = Column(JSON, nullable=True)  # {dimension_key: score}
    skill_premium_percent = Column(Float, nullable=True)  # 技能组合溢价
    ai_risk_level = Column(String(20), nullable=True)  # low/medium/high
    ai_risk_description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class LearningPath(Base):
    """学习路径配置表."""

    __tablename__ = "learning_paths"

    id = Column(String(32), primary_key=True, default=lambda: uuid.uuid4().hex)
    stage_key = Column(String(50), nullable=False)  # "beginner", "intermediate", "advanced", "expert"
    stage_name_zh = Column(String(100), nullable=False)
    min_score = Column(Float, nullable=False)  # 该阶段最低分
    max_score = Column(Float, nullable=True)  # 该阶段最高分（None 表示无上限）
    recommended_skills = Column(JSON, nullable=True)  # 推荐提升的技能维度
    milestone_tasks = Column(JSON, nullable=True)  # 阶段里程碑任务
    created_at = Column(DateTime, default=datetime.utcnow)
