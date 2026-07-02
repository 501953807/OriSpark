"""音乐发行模型.

Musician v4: Music Releases — 音频发行与分发管理.
"""

import uuid
from datetime import datetime

from sqlalchemy import Column, String, Integer, Float, DateTime, ForeignKey, Index

from app.database import Base


def _uid():
    return uuid.uuid4().hex[:32]


class MusicRelease(Base):
    """音乐发行表.

    具体的音频发行记录，关联到专辑和工作变体.
    """
    __tablename__ = "music_releases"

    id = Column(String(32), primary_key=True, default=_uid)
    album_id = Column(String(32), ForeignKey("albums.id"), nullable=True)
    work_variant_id = Column(String(32), ForeignKey("work_variants.id"), nullable=True)
    title = Column(String(200), nullable=False)
    isrc = Column(String(12), nullable=True)  # 国际标准录音代码
    audio_file_path = Column(String(500), nullable=True)
    duration_seconds = Column(Integer, nullable=True)
    bitrate = Column(Integer, nullable=True)
    format = Column(String(10), default="mp3")  # mp3/flac/wav
    genre = Column(String(50), nullable=True)
    mood = Column(String(50), nullable=True)
    bpm = Column(Integer, nullable=True)
    distribution_status = Column(String(20), default="pending")  # pending/distributing/distributed
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index("idx_release_isrc", "isrc"),
        Index("idx_release_album", "album_id"),
    )
