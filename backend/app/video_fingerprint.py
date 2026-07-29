"""视频感知哈希模型 (P3-3)."""

import uuid
from datetime import datetime

from sqlalchemy import Column, String, Integer, Float, DateTime, ForeignKey, JSON, Index
from sqlalchemy.orm import relationship

from app.database import Base


def generate_uuid():
    return uuid.uuid4().hex[:32]


class VideoFingerprintConfig(Base):
    """视频指纹配置表."""
    __tablename__ = "video_fingerprint_config"

    id = Column(String(32), primary_key=True, default=generate_uuid)
    config_name = Column(String(100), nullable=False)
    frame_interval = Column(Integer, default=30)  # seconds between frames
    hash_algorithm = Column(String(20), default="dhash")  # dhash/phash/ahash
    enabled = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.utcnow)


class VideoFrameFingerprint(Base):
    """视频帧感知哈希表."""
    __tablename__ = "video_frame_fingerprints"

    id = Column(String(32), primary_key=True, default=generate_uuid)
    video_work_id = Column(String(32), ForeignKey("works.id", ondelete="CASCADE"), nullable=False)
    frame_number = Column(Integer, nullable=False)
    timestamp = Column(Float, nullable=True)  # seconds from start
    perceptual_hash = Column(String(64), nullable=False)
    hash_type = Column(String(20), default="dhash")  # dhash/phash/ahash/whash
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("idx_vff_video", "video_work_id", "frame_number"),
        Index("idx_vff_hash", "perceptual_hash"),
    )
