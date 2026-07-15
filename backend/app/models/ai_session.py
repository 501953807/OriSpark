"""AI 创作会话记录数据模型."""

from datetime import datetime

from sqlalchemy import (
    Column, String, Integer, Text, DateTime, ForeignKey, Index, JSON,
)

from app.database import Base
from app.models.work import generate_uuid


class AiCreationSession(Base):
    """AI 创作会话记录表."""
    __tablename__ = "ai_creation_sessions"

    id = Column(String(32), primary_key=True, default=generate_uuid)
    work_id = Column(String(32), ForeignKey("works.id", ondelete="CASCADE"), nullable=False)
    tool_name = Column(String(100), nullable=False)
    tool_version = Column(String(50), nullable=True)
    prompt = Column(Text, nullable=True)
    prompt_history = Column(JSON, nullable=True)
    seed = Column(Integer, nullable=True)
    parameters = Column(JSON, nullable=True)
    negative_prompt = Column(Text, nullable=True)
    model_name = Column(String(500), nullable=True)
    lora_names = Column(JSON, nullable=True)
    output_images = Column(JSON, nullable=True)
    human_interventions = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index("idx_ai_session_work", "work_id"),
    )
