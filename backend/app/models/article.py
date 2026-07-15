"""文章数据模型 (P4: 文字作者).

表: articles — 文字创作者的文章管理.
"""

import uuid
from datetime import datetime

from sqlalchemy import (
    Column, String, Integer, Text, DateTime,
    ForeignKey, Index, JSON,
)
from sqlalchemy.orm import relationship

from app.database import Base


def generate_uuid():
    return uuid.uuid4().hex[:32]


class Article(Base):
    """文章表 — 文字创作者的单篇文章/博客内容.

    支持 Markdown/HTML 格式正文，可按分类、标签、状态筛选.
    """
    __tablename__ = "articles"

    id = Column(String(32), primary_key=True, default=generate_uuid)
    title = Column(String(300), nullable=False)
    subtitle = Column(String(300), nullable=True)
    content = Column(Text, nullable=True)  # Markdown/HTML
    excerpt = Column(String(1000), nullable=True)
    author_id = Column(String(32), ForeignKey("users.id"), nullable=True)
    work_variant_id = Column(String(32), ForeignKey("work_variants.id"), nullable=True)
    category = Column(String(50), nullable=True)  # 科技/文学/历史/艺术
    tags = Column(JSON, nullable=True)  # ["Python", "AI", "教程"]
    word_count = Column(Integer, nullable=True)
    reading_time_minutes = Column(Integer, nullable=True)
    status = Column(String(20), default="draft")  # draft/published/archived
    published_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    author = relationship("User", backref="articles")
    work_variant = relationship("WorkVariant", back_populates="articles")

    __table_args__ = (
        Index("idx_article_status", "status"),
        Index("idx_article_category", "category"),
    )
