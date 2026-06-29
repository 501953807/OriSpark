"""Watermark preset data model.

表:
- watermark_presets: 创作者保存的水印预设配置
"""

from datetime import datetime

from sqlalchemy import (
    Column, String, Text, DateTime, Boolean, Integer, JSON,
    ForeignKey, Index,
)
from sqlalchemy.orm import relationship

from app.database import Base
from app.models.work import generate_uuid


class WatermarkPreset(Base):
    """水印预设配置."""
    __tablename__ = "watermark_presets"

    id = Column(String(32), primary_key=True, default=generate_uuid)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    watermark_type = Column(String(20), nullable=False)  # text / image / tiled
    config = Column(JSON, nullable=False, default=dict)  # 具体配置
    is_default = Column(Boolean, default=False)
    created_by = Column(String(32), ForeignKey("users.id", ondelete="CASCADE"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index("idx_wp_created", "created_at"),
        Index("idx_wp_type", "watermark_type"),
        Index("idx_wp_user", "created_by"),
    )
