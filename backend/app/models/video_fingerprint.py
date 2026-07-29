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
    name = Column(String(100), nullable=False)  # renamed from config_name
    algorithm = Column(String(20), default="pHash")  # renamed from hash_algorithm
    frame_interval = Column(Integer, default=30)  # seconds between frames
    threshold = Column(Float, default=0.85)  # new field for similarity threshold
    is_active = Column(Integer, default=1)  # renamed from enabled, using integer as boolean storage
    settings = Column(JSON, default={})  # new field for additional configuration
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class VideoFrameFingerprint(Base):
    """视频帧感知哈希表."""
    __tablename__ = "video_frame_fingerprints"

    id = Column(String(32), primary_key=True, default=generate_uuid)
    work_id = Column(String(32), ForeignKey("works.id", ondelete="CASCADE"), nullable=False)  # renamed from video_work_id
    config_id = Column(String(32), ForeignKey("video_fingerprint_config.id", ondelete="SET_NULL"), nullable=True)  # new foreign key
    frame_hash = Column(String(64), nullable=False)  # renamed from perceptual_hash
    frame_number = Column(Integer, nullable=False)  # kept existing frame_number
    timestamp_ms = Column(Float, default=0.0)  # renamed from timestamp, in ms
    similarity_score = Column(Float, nullable=True)  # new field for match score
    matched_work_id = Column(String(32), nullable=True)  # new field for referenced work ID
    hash_type = Column(String(20), default="dhash")  # dhash/phash/ahash/whash
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index("idx_vff_work", "work_id", "frame_number"),
        Index("idx_vff_hash", "frame_hash"),
        Index("idx_vff_config", "config_id"),
    )
