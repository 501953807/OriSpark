"""视频创作者 (v3) 预留数据模型.

Reserved for future video creator type.
v1: 建表+字段注释 "v3激活".
"""

import uuid
from datetime import datetime

from sqlalchemy import Column, String, Integer, Float, Boolean, Text, DateTime, ForeignKey, JSON, Index
from sqlalchemy.orm import relationship

from app.database import Base


def _uid():
    return uuid.uuid4().hex[:32]


# =============================================================================
# brand_campaigns — 品牌商单工作流 (15.2.1)
# =============================================================================


class BrandCampaign(Base):
    """品牌商单活动表.

    记录品牌方发起的商单项目，含brief/预算/进度.
    v3 激活.
    """
    __tablename__ = "brand_campaigns"

    id = Column(String(32), primary_key=True, default=_uid)
    user_id = Column(String(32), nullable=False)
    brand_name = Column(String(200), nullable=False)
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    budget_min = Column(Float, nullable=True)
    budget_max = Column(Float, nullable=True)
    currency = Column(String(10), default="CNY")
    status = Column(String(20), default="draft")  # draft/negotiating/in_progress/delivered/closed
    deadline = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index("idx_bc_user", "user_id"),
        Index("idx_bc_status", "status"),
    )


class BrandTask(Base):
    """商单任务表.

    商单下的具体交付任务，如初稿/修改/终稿.
    v3 激活.
    """
    __tablename__ = "brand_tasks"

    id = Column(String(32), primary_key=True, default=_uid)
    campaign_id = Column(String(32), ForeignKey("brand_campaigns.id"), nullable=False)
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    deliverable_type = Column(String(50), nullable=True)  # video/image/script
    status = Column(String(20), default="pending")  # pending/in_review/approved/rejected
    due_date = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (Index("idx_bt_campaign", "campaign_id"),)


class BrandMessage(Base):
    """商单沟通消息表.

    品牌方与创作者在商单内的对话.
    v3 激活.
    """
    __tablename__ = "brand_messages"

    id = Column(String(32), primary_key=True, default=_uid)
    campaign_id = Column(String(32), ForeignKey("brand_campaigns.id"), nullable=False)
    sender_id = Column(String(32), nullable=False)
    receiver_id = Column(String(32), nullable=False)
    content = Column(Text, nullable=False)
    attachment_url = Column(String(2000), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (Index("idx_bm_campaign", "campaign_id"),)


# =============================================================================
# platform_earnings — 平台激励追踪 (15.2.2)
# =============================================================================


class PlatformGoal(Base):
    """平台激励目标表.

    创作者设定的平台激励目标，如月播放量/粉丝数.
    v3 激活.
    """
    __tablename__ = "platform_goals"

    id = Column(String(32), primary_key=True, default=_uid)
    user_id = Column(String(32), nullable=False)
    platform = Column(String(50), nullable=False)  # bilibili/douyin/kuaishou
    goal_type = Column(String(50), nullable=False)  # views/followers/revenue
    target_value = Column(Integer, nullable=False)
    period_start = Column(DateTime, nullable=False)
    period_end = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("idx_pg_user", "user_id"),
        Index("idx_pg_period", "platform", "period_start"),
    )


class PlatformEarning(Base):
    """平台收益记录表.

    从各平台拉取的激励/广告/打赏收入.
    v3 激活.
    """
    __tablename__ = "platform_earnings"

    id = Column(String(32), primary_key=True, default=_uid)
    user_id = Column(String(32), nullable=False)
    platform = Column(String(50), nullable=False)
    earning_type = Column(String(50), nullable=True)  # ad_reward/tip/subsidy
    amount = Column(Float, nullable=False)
    currency = Column(String(10), default="CNY")
    period = Column(String(20), nullable=True)  # 2024-01
    recorded_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("idx_pe_user", "user_id"),
        Index("idx_pe_period", "platform", "period"),
    )
