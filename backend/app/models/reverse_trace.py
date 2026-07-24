"""分发回流引擎数据模型."""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Integer, Float, Boolean, JSON, Text, ForeignKey, Index
from sqlalchemy.orm import relationship
from app.database import Base


class ReverseTraceLink(Base):
    """可信短链 — 为每个分发平台生成带追踪参数的短链."""

    __tablename__ = "reverse_trace_links"

    id = Column(String(32), primary_key=True, default=lambda: uuid.uuid4().hex)
    work_id = Column(String(32), nullable=False, index=True)
    user_id = Column(String(32), nullable=False, index=True)
    platform_code = Column(String(50), nullable=False)  # "weixin", "douyin", "xhs", "youtube"
    short_code = Column(String(12), nullable=False, unique=True, index=True)
    original_url = Column(Text, nullable=False)
    redirect_url = Column(Text, nullable=False)
    is_active = Column(Boolean, default=True)
    click_count = Column(Integer, default=0)
    expire_at = Column(DateTime, nullable=True)
    utm_source = Column(String(50), nullable=True)
    utm_medium = Column(String(50), nullable=True)
    utm_campaign = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    events = relationship(
        "ReverseTraceEvent",
        back_populates="link",
        cascade="all, delete-orphan",
        order_by="ReverseTraceEvent.created_at.desc()",
    )

    __table_args__ = (
        Index("idx_rtl_platform", "platform_code"),
        Index("idx_rtl_user_work", "user_id", "work_id"),
    )


class ReverseTraceEvent(Base):
    """归因事件 — 记录每次短链点击的归因数据."""

    __tablename__ = "reverse_trace_events"

    id = Column(String(32), primary_key=True, default=lambda: uuid.uuid4().hex)
    link_id = Column(String(32), ForeignKey("reverse_trace_links.id"), nullable=False, index=True)
    event_type = Column(String(20), nullable=False)  # "click", "view", "share", "purchase", "signup"
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    referrer = Column(String(500), nullable=True)
    geo_country = Column(String(10), nullable=True)
    geo_region = Column(String(20), nullable=True)
    geo_city = Column(String(100), nullable=True)
    device_type = Column(String(20), nullable=True)  # "mobile", "desktop", "tablet"
    browser = Column(String(50), nullable=True)
    os_name = Column(String(50), nullable=True)
    custom_params = Column(JSON, nullable=True)
    converted = Column(Boolean, default=False)
    conversion_value = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    link = relationship("ReverseTraceLink", back_populates="events")

    __table_args__ = (
        Index("idx_rte_link_time", "link_id", "created_at"),
        Index("idx_rte_event_type", "event_type"),
    )
