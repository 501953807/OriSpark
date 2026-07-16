"""案例知识库数据模型."""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Float, Boolean, Text, Integer, JSON
from app.database import Base


class CaseStudy(Base):
    """成功案例/失败教训记录."""

    __tablename__ = "case_studies"

    id = Column(String(32), primary_key=True, default=lambda: uuid.uuid4().hex)
    user_id = Column(String(32), nullable=False, index=True)
    title = Column(String(500), nullable=False)
    category = Column(String(50), nullable=False)  # "monetization", "copyright", "platform_growth", "brand_collab", "failure_lesson"
    case_type = Column(String(20), default="success")  # "success", "lesson"
    description = Column(Text, nullable=True)
    key_metrics = Column(JSON, nullable=True)  # {"revenue": 50000, "followers": 10000, "timeline_days": 90}
    tags = Column(JSON, default=list)  # ["pod", "redbubble", "t-shirt"]
    source_url = Column(String(500), nullable=True)
    creator_role = Column(String(200), nullable=True)  # 创作者角色/行业
    takeaways = Column(JSON, default=list)  # ["关键经验点1", "关键经验点2"]
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class CaseTag(Base):
    """案例标签系统."""

    __tablename__ = "case_tags"

    id = Column(String(32), primary_key=True, default=lambda: uuid.uuid4().hex)
    name = Column(String(50), nullable=False, unique=True)
    count = Column(Integer, default=0)
