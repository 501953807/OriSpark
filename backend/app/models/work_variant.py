"""工作流变体组模型 (P3-4: Aspect ratio variants)."""

import uuid
from datetime import datetime

from sqlalchemy import Column, String, Integer, Float, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship

from app.database import Base


def generate_uuid():
    return uuid.uuid4().hex[:32]


class WorkVariantGroup(Base):
    """作品变体组表 — 管理同一作品的不同宽高比版本 (16:9, 9:16, 1:1)."""
    __tablename__ = "work_variant_groups"

    id = Column(String(32), primary_key=True, default=generate_uuid)
    work_id = Column(String(32), ForeignKey("works.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(100), nullable=False, default="默认变体组")
    description = Column(String(500), nullable=True, default=None)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    variants = relationship("WorkVariant", back_populates="group", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_wvg_work", "work_id"),
    )


class WorkVariant(Base):
    """作品变体表 — 变体组内的具体宽高比变体."""
    __tablename__ = "work_variants"

    id = Column(String(32), primary_key=True, default=generate_uuid)
    group_id = Column(String(32), ForeignKey("work_variant_groups.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(100), nullable=False)
    width = Column(Integer, nullable=False)
    height = Column(Integer, nullable=False)
    aspect_ratio = Column(Float, nullable=False)
    sort_order = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

    group = relationship("WorkVariantGroup", back_populates="variants")

    __table_args__ = (
        Index("idx_wv_group", "group_id"),
    )
