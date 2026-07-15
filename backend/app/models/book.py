"""书籍数据模型 (P4: 文字作者).

表: books — 文字创作者的书籍项目管理.
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


class Book(Base):
    """书籍表 — 文字创作者的书籍/长篇项目.

    支持小说/散文/诗歌/学术等体裁，管理封面、出版社、ISBN 等信息.
    """
    __tablename__ = "books"

    id = Column(String(32), primary_key=True, default=generate_uuid)
    title = Column(String(300), nullable=False)
    author_id = Column(String(32), ForeignKey("users.id"), nullable=True)
    cover_path = Column(String(500), nullable=True)
    description = Column(Text, nullable=True)
    genre = Column(String(50), nullable=True)  # 小说/散文/诗歌/学术
    publisher = Column(String(200), nullable=True)
    isbn = Column(String(13), nullable=True)
    total_chapters = Column(Integer, nullable=True)
    total_word_count = Column(Integer, nullable=True)
    publication_date = Column(DateTime, nullable=True)
    status = Column(String(20), default="writing")  # writing/published/archived
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    author = relationship("User", backref="books")
    manuscripts = relationship("Manuscript", back_populates="book", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_book_status", "status"),
        Index("idx_book_genre", "genre"),
    )
