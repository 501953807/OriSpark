"""多平台内容分发流水线数据模型."""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Float, Boolean, Text, Integer, JSON
from app.database import Base


class PlatformAccount(Base):
    """创作者绑定的第三方平台账号."""

    __tablename__ = "platform_accounts"

    id = Column(String(32), primary_key=True, default=lambda: uuid.uuid4().hex)
    user_id = Column(String(32), nullable=False, index=True)
    platform = Column(String(30), nullable=False)  # "xiaohongshu", "bilibili", "douyin", etc.
    account_name = Column(String(200), nullable=False)
    account_id = Column(String(200), nullable=True)  # 平台返回的账号ID
    follower_count = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ContentTemplate(Base):
    """内容模板 — 用于批量发布时的标准化格式."""

    __tablename__ = "content_templates"

    id = Column(String(32), primary_key=True, default=lambda: uuid.uuid4().hex)
    user_id = Column(String(32), nullable=False, index=True)
    platform = Column(String(30), nullable=False)
    title_template = Column(String(500), nullable=False)
    description_template = Column(Text, nullable=True)
    tags_template = Column(JSON, default=list)  # ["tag1", "tag2"]
    cover_style = Column(String(50), default="auto")  # "auto", "square", "vertical", "horizontal"
    created_at = Column(DateTime, default=datetime.utcnow)


class MultiPlatformSchedule(Base):
    """多平台定时发布计划."""

    __tablename__ = "multi_platform_schedules"

    id = Column(String(32), primary_key=True, default=lambda: uuid.uuid4().hex)
    user_id = Column(String(32), nullable=False, index=True)
    work_id = Column(String(32), nullable=True, index=True)  # 关联作品
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    platforms = Column(JSON, nullable=False)  # [{"platform": "xiaohongshu", "account_id": "...", "status": "pending"}]
    scheduled_at = Column(DateTime, nullable=False)
    is_recurring = Column(Boolean, default=False)
    recurring_pattern = Column(String(50), nullable=True)  # "daily", "weekly", "biweekly"
    status = Column(String(20), default="scheduled")  # "scheduled", "published", "failed", "cancelled"
    published_at = Column(DateTime, nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class PublishLog(Base):
    """发布日志 — 记录每次发布的实际结果."""

    __tablename__ = "publish_logs"

    id = Column(String(32), primary_key=True, default=lambda: uuid.uuid4().hex)
    schedule_id = Column(String(32), nullable=True, index=True)
    user_id = Column(String(32), nullable=False, index=True)
    platform = Column(String(30), nullable=False)
    work_id = Column(String(32), nullable=True)
    post_url = Column(String(500), nullable=True)
    status = Column(String(20), nullable=False)  # "success", "failed"
    response_data = Column(JSON, nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
