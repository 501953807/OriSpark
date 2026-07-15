"""工作流变体组模型 (P3-4: Aspect ratio variants).

摄影师 v2 扩展: work_variants 表包含 14 个摄影师专属字段.
"""

import uuid
from datetime import datetime

from sqlalchemy import Column, String, Integer, Float, DateTime, ForeignKey, Index, Text, JSON
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
    """作品变体表 — 变体组内的具体宽高比变体.

    摄影师 v2 扩展字段: camera_model, lens, iso, aperture, shutter_speed,
    focal_length, gps_*, raw_file_path, shot_status, shot_notes, stock_channels.
    """
    __tablename__ = "work_variants"

    id = Column(String(32), primary_key=True, default=generate_uuid)
    group_id = Column(String(32), ForeignKey("work_variant_groups.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(100), nullable=False)
    width = Column(Integer, nullable=False)
    height = Column(Integer, nullable=False)
    aspect_ratio = Column(Float, nullable=False)
    sort_order = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

    # -- 摄影师 v2 扩展字段 --
    camera_model = Column(String(100), nullable=True)       # 相机型号
    lens = Column(String(200), nullable=True)               # 镜头
    iso = Column(Integer, nullable=True)                    # ISO
    aperture = Column(String(20), nullable=True)            # 光圈 (f/2.8)
    shutter_speed = Column(String(30), nullable=True)       # 快门速度 (1/250s)
    focal_length = Column(String(30), nullable=True)        # 焦距 (50mm)
    gps_latitude = Column(Float, nullable=True)             # GPS 纬度
    gps_longitude = Column(Float, nullable=True)            # GPS 经度
    gps_altitude = Column(Float, nullable=True)             # GPS 海拔
    raw_file_path = Column(String(500), nullable=True)      # RAW 原始文件路径
    shot_status = Column(String(20), default="unreviewed")  # 选片状态: unreviewed|pass|hold|reject|shortlist
    shot_notes = Column(Text, nullable=True)                # 选片备注
    stock_channels = Column(JSON, nullable=True)            # 已投放图库渠道

    group = relationship("WorkVariantGroup", back_populates="variants")
    articles = relationship("Article", back_populates="work_variant")

    __table_args__ = (
        Index("idx_wv_group", "group_id"),
        Index("idx_wv_camera", "camera_model"),
        Index("idx_wv_shot_status", "shot_status"),
        Index("idx_wv_raw_path", "raw_file_path"),
    )
