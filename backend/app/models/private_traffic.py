"""私域流量管理数据模型."""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Float, Boolean, Text, Integer, JSON
from app.database import Base


class SubscriptionLink(Base):
    """付费订阅链接管理 — Patreon/爱发电/知识星球等."""

    __tablename__ = "subscription_links"

    id = Column(String(32), primary_key=True, default=lambda: uuid.uuid4().hex)
    user_id = Column(String(32), nullable=False, index=True)
    platform = Column(String(50), nullable=False)  # "patreon", "aidian", "zsxq", "other"
    url = Column(Text, nullable=False)
    subscriber_count = Column(Integer, default=0)
    monthly_revenue = Column(Float, default=0)
    currency = Column(String(10), default="CNY")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class FanCommunity(Base):
    """粉丝社群标签管理 — Discord/微信群/Telegram等."""

    __tablename__ = "fan_communities"

    id = Column(String(32), primary_key=True, default=lambda: uuid.uuid4().hex)
    user_id = Column(String(32), nullable=False, index=True)
    platform = Column(String(50), nullable=False)  # "discord", "wechat", "telegram", "qq"
    name = Column(String(200), nullable=False)
    invite_url = Column(Text, nullable=True)
    member_count = Column(Integer, default=0)
    tags = Column(JSON, nullable=True)  # ["核心粉", "付费用户", "活跃"]
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class ConversionFunnel(Base):
    """公域→私域漏斗追踪."""

    __tablename__ = "conversion_funnels"

    id = Column(String(32), primary_key=True, default=lambda: uuid.uuid4().hex)
    user_id = Column(String(32), nullable=False, index=True)
    source_platform = Column(String(50), nullable=False)  # "xiaohongshu", "douyin", "youtube"
    public_views = Column(Integer, default=0)  # 公域曝光量
    profile_clicks = Column(Integer, default=0)  # 主页点击
    link_clicks = Column(Integer, default=0)  # 链接点击
    converted_subscribers = Column(Integer, default=0)  # 实际转化数
    tracked_date = Column(DateTime, nullable=False)
    notes = Column(Text, nullable=True)
