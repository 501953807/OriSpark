"""专辑管理模型.

Musician v4: Albums — 专辑/EP/单曲管理.
"""

import uuid
from datetime import datetime

from sqlalchemy import Column, String, Integer, DateTime, Index

from app.database import Base


def _uid():
    return uuid.uuid4().hex[:32]


class Album(Base):
    """专辑表.

    音乐人发布的专辑/EP/单曲集合.
    """
    __tablename__ = "albums"

    id = Column(String(32), primary_key=True, default=_uid)
    title = Column(String(200), nullable=False)
    album_type = Column(String(20), default="single")  # single/ep/album/compilation
    release_date = Column(DateTime, nullable=True)
    cover_art_path = Column(String(500), nullable=True)
    label = Column(String(200), nullable=True)  # 唱片公司
    total_tracks = Column(Integer, nullable=True)
    duration_seconds = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index("idx_album_type", "album_type"),
    )
