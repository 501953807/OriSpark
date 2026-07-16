"""创作者成长阶段数据模型."""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Float, Boolean, Text, Integer, JSON
from app.database import Base


class CreatorGrowthStage(Base):
    """创作者成长阶段记录."""

    __tablename__ = "creator_growth_stages"

    id = Column(String(32), primary_key=True, default=lambda: uuid.uuid4().hex)
    user_id = Column(String(32), nullable=False, index=True)
    stage_key = Column(String(30), nullable=False)  # "beginner", "growing", "scaling", "ecosystem"
    stage_name_zh = Column(String(50), nullable=False)
    monthly_revenue_yuan = Column(Float, default=0)
    total_works = Column(Integer, default=0)
    total_certificates = Column(Integer, default=0)
    credit_score = Column(Float, default=50)
    overall_progress_percent = Column(Float, default=0)  # 当前阶段内进度 0-100
    next_stage_progress_percent = Column(Float, default=0)  # 距下一阶段进度
    evaluated_at = Column(DateTime, default=datetime.utcnow)


class GrowthTask(Base):
    """阶段性任务清单."""

    __tablename__ = "growth_tasks"

    id = Column(String(32), primary_key=True, default=lambda: uuid.uuid4().hex)
    user_id = Column(String(32), nullable=False, index=True)
    stage_key = Column(String(30), nullable=False)
    task_category = Column(String(50), nullable=False)  # "revenue", "works", "certification", "community", "distribution"
    task_title = Column(String(200), nullable=False)
    task_description = Column(Text, nullable=True)
    is_completed = Column(Boolean, default=False)
    completed_at = Column(DateTime, nullable=True)
    priority = Column(Integer, default=5)  # 1=highest
    created_at = Column(DateTime, default=datetime.utcnow)
