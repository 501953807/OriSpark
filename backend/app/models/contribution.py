"""人类贡献度评分数据模型 — G-01."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, String, Float, Boolean, DateTime, Index, ForeignKey
from sqlalchemy.orm import relationship

from app.database import Base


class HumanContributionScore(Base):
    """人类贡献度评分表."""
    __tablename__ = "human_contribution_scores"

    id = Column(String(32), primary_key=True, default=lambda: uuid.uuid4().hex)
    work_id = Column(String(32), ForeignKey("works.id", ondelete="CASCADE"), nullable=False, index=True, comment="作品 ID")
    author_id = Column(String(32), nullable=False, index=True, comment="作者 ID")

    # 维度评分 (0-1)
    ai_session_score = Column(Float, nullable=False, default=1.0, comment="AI会话交叉验证分")
    mcp_event_score = Column(Float, nullable=False, default=0.8, comment="MCP事件流分析分")
    self_declare_score = Column(Float, nullable=False, default=0.5, comment="自声明验证分")
    duration_score = Column(Float, nullable=False, default=1.0, comment="创作时长模式分")

    # 总分与结论
    total_score = Column(Float, nullable=False, default=0.0, comment="加权总分 0-1")
    conclusion = Column(String(20), nullable=False, default="pass", comment="pass/declare/reject")
    defense_tier = Column(String(10), nullable=False, default="L1", comment="推荐防御层级 L1/L2/L3")
    requires_disclosure = Column(Boolean, nullable=False, default=False, comment="是否需要声明AI参与")
    eligible_for_registration = Column(Boolean, nullable=False, default=True, comment="是否可进入确权")

    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index("ix_contribution_work_author", "work_id", "author_id"),
    )

    work = relationship("Work", back_populates="contribution_scores", foreign_keys=[work_id])
