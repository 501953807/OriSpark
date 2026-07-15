"""手稿数据模型 (P4: 文字作者).

表: manuscripts — 书籍章节/段落的手稿管理.
"""

import uuid
from datetime import datetime

from sqlalchemy import (
    Column, String, Integer, Text, DateTime,
    ForeignKey, Index,
)
from sqlalchemy.orm import relationship

from app.database import Base


def generate_uuid():
    return uuid.uuid4().hex[:32]


class Manuscript(Base):
    """手稿表 — 书籍中的章节/段落手写内容.

    支持版本管理 (version)，每章可以有多个修订版本.
    """
    __tablename__ = "manuscripts"

    id = Column(String(32), primary_key=True, default=generate_uuid)
    title = Column(String(300), nullable=False)
    book_id = Column(String(32), ForeignKey("books.id"), nullable=True)
    chapter_number = Column(Integer, nullable=True)
    content = Column(Text, nullable=True)
    word_count = Column(Integer, nullable=True)
    status = Column(String(20), default="draft")  # draft/revising/final
    version = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    book = relationship("Book", back_populates="manuscripts")

    __table_args__ = (
        Index("idx_manuscript_book", "book_id"),
    )
