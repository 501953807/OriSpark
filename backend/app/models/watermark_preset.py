"""水印预设数据模型。

表：
- watermark_presets: 创作者保存的水印位置预设配置
"""

import uuid
from enum import Enum
from datetime import datetime, timezone

from sqlalchemy import (
    Column, String, Integer, Text, DateTime, Boolean, Enum as SAEnum, Index,
)
from sqlalchemy.orm import relationship

from app.database import Base
from app.models.work import generate_uuid


class PositionEnum(str, Enum):
    """水印位置枚举."""

    TOP_LEFT = "top-left"
    TOP_RIGHT = "top-right"
    BOTTOM_LEFT = "bottom-left"
    BOTTOM_RIGHT = "bottom-right"


class WatermarkPreset(Base):
    """水印预设配置."""

    __tablename__ = "watermark_presets"

    id = Column(String(32), primary_key=True, default=generate_uuid)
    name = Column(String(100), nullable=False)
    position = Column(
        SAEnum(PositionEnum, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        default=PositionEnum.TOP_RIGHT,
    )
    opacity = Column(Integer, nullable=False, default=100)  # 0-100
    text = Column(Text, nullable=True)  # 可选水印文本
    image_path = Column(Text, nullable=True)  # 可选水印图片路径
    created_at = Column(DateTime, default=datetime.now(timezone.utc))

    # 索引优化
    __table_args__ = (
        Index("idx_wp_name", "name"),
        Index("idx_wp_position", "position"),
        Index("idx_wp_created", "created_at"),
    )

    def to_dict(self) -> dict:
        """转换为字典格式."""
        return {
            "id": self.id,
            "name": self.name,
            "position": self.position.value,
            "opacity": self.opacity,
            "text": self.text,
            "image_path": self.image_path,
            "updated_at": None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


# 导出到 models/__init__.py
__all__ = ["WatermarkPreset", "PositionEnum"]