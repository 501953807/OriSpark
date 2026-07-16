"""创作者导航数据模型."""

import uuid
from datetime import datetime

from sqlalchemy import Column, String, Float, Text, DateTime, Boolean, Integer, JSON, Index

from app.database import Base
from app.models.work import generate_uuid


class NavigationTask(Base):
    """导航任务配置表."""
    __tablename__ = "navigation_tasks"

    id = Column(String(32), primary_key=True, default=generate_uuid)
    task_key = Column(String(50), nullable=False, unique=True, index=True)
    category = Column(String(20), nullable=False, index=True)  # 'onboarding' | 'compliance' | 'growth'
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    priority = Column(Integer, default=0)  # 数值越小越优先
    check_expression = Column(Text, nullable=True)  # Python 表达式检查完成条件
    auto_complete = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("idx_nav_category", "category", "priority"),
    )


class CreatorNavigation(Base):
    """创作者导航进度表 — 每个用户一条记录."""
    __tablename__ = "creator_navigations"

    id = Column(String(32), primary_key=True, default=generate_uuid)
    user_id = Column(String(32), nullable=False, unique=True, index=True)
    active_path = Column(String(20), nullable=False, default="onboarding")
    completed_tasks = Column(JSON, default=list)  # 已完成的任务 key 列表
    current_task_key = Column(String(50), nullable=True)
    progress_percent = Column(Float, default=0.0)
    last_completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index("idx_nav_user", "user_id"),
    )
