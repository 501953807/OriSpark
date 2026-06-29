"""字幕管理数据模型 (P3-2)."""

import uuid
from datetime import datetime

from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship

from app.database import Base


def generate_uuid():
    return uuid.uuid4().hex[:32]


class Subtitle(Base):
    """作品字幕表."""
    __tablename__ = "subtitles"

    id = Column(String(32), primary_key=True, default=generate_uuid)
    work_id = Column(String(32), ForeignKey("works.id", ondelete="CASCADE"), nullable=False)
    language = Column(String(10), nullable=False)  # zh, en, ja, etc.
    file_path = Column(String(2000), nullable=False)
    format_type = Column(String(10), default="srt")  # srt/ass/vtt
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    work = relationship("Work", backref="subtitles")

    __table_args__ = (
        Index("idx_subtitles_work", "work_id"),
        Index("idx_subtitles_lang", "language"),
    )


class ProjectFileFormat(Base):
    """项目文件格式表 (P3-1)."""
    __tablename__ = "project_file_formats"

    id = Column(String(32), primary_key=True, default=generate_uuid)
    name = Column(String(100), nullable=False)
    extension = Column(String(10), nullable=False)
    mime_type = Column(String(100), nullable=True)
    description = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (Index("idx_pff_ext", "extension"),)
