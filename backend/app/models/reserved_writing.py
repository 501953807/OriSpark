"""文字作者 (v4) 预留数据模型.

Reserved for future writing creator type.
v1: 建表+字段注释 "v4激活".
"""

import uuid
from datetime import datetime

from sqlalchemy import Column, String, Integer, Float, Boolean, Text, DateTime, ForeignKey, JSON, Index
from sqlalchemy.orm import relationship

from app.database import Base


def _uid():
    return uuid.uuid4().hex[:32]


# =============================================================================
# chapters — 章节结构 (12.4.1)
# =============================================================================


class Chapter(Base):
    """作品章节表.

    长篇小说/非虚构作品的章节结构.
    v4 激活.
    """
    __tablename__ = "chapters"

    id = Column(String(32), primary_key=True, default=_uid)
    work_id = Column(String(32), ForeignKey("works.id"), nullable=False)
    title = Column(String(500), nullable=False)
    chapter_number = Column(Integer, nullable=False)
    body = Column(Text, nullable=True)  # 章节正文
    word_count = Column(Integer, default=0)
    status = Column(String(20), default="draft")  # draft/published/archived
    published_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index("idx_ch_work", "work_id", "chapter_number"),
    )


class ChapterComment(Base):
    """章节评论表.

    读者对特定章节的评论/段评.
    v4 激活.
    """
    __tablename__ = "chapter_comments"

    id = Column(String(32), primary_key=True, default=_uid)
    chapter_id = Column(String(32), ForeignKey("chapters.id"), nullable=False)
    user_id = Column(String(32), nullable=False)
    body = Column(Text, nullable=False)
    anchor_offset = Column(Integer, nullable=True)  # 正文偏移量，段评定位
    reply_to_id = Column(String(32), nullable=True)  # 回复评论
    likes = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("idx_cc_chapter", "chapter_id"),
        Index("idx_cc_user", "user_id"),
    )


class ChapterRevision(Base):
    """章节修订历史表.

    章节每次修改的版本记录.
    v4 激活.
    """
    __tablename__ = "chapter_revisions"

    id = Column(String(32), primary_key=True, default=_uid)
    chapter_id = Column(String(32), ForeignKey("chapters.id"), nullable=False)
    title = Column(String(500), nullable=False)
    body = Column(Text, nullable=True)
    word_count = Column(Integer, default=0)
    change_summary = Column(Text, nullable=True)
    created_by = Column(String(32), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (Index("idx_cr_chapter", "chapter_id"),)


# =============================================================================
# export_configs — EPUB导出配置 (12.4.2)
# =============================================================================


class ExportConfig(Base):
    """导出配置表.

    用户保存的EPUB/PDF导出模板配置.
    v4 激活.
    """
    __tablename__ = "export_configs"

    id = Column(String(32), primary_key=True, default=_uid)
    user_id = Column(String(32), nullable=False)
    name = Column(String(200), nullable=False)
    format = Column(String(20), nullable=False)  # epub/pdf/mobi
    font_family = Column(String(100), nullable=True)
    font_size = Column(Integer, nullable=True)
    margin_mm = Column(JSON, nullable=True)  # {"top": 20, "bottom": 20, "left": 25, "right": 25}
    include_cover = Column(Boolean, default=True)
    include_toc = Column(Boolean, default=True)
    is_default = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (Index("idx_ec_user", "user_id"),)


# =============================================================================
# ebook_products — 电子书产品 (15.5.1)
# =============================================================================


class EbookProduct(Base):
    """电子书商品表.

    从章节聚合生成的可售卖电子书产品.
    v4 激活.
    """
    __tablename__ = "ebook_products"

    id = Column(String(32), primary_key=True, default=_uid)
    user_id = Column(String(32), nullable=False)
    work_id = Column(String(32), ForeignKey("works.id"), nullable=True)
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    price = Column(Float, nullable=False)
    currency = Column(String(10), default="CNY")
    format = Column(String(20), default="epub")  # epub/pdf/mobi/kfx
    file_size_bytes = Column(Integer, nullable=True)
    page_count = Column(Integer, nullable=True)
    is_active = Column(Boolean, default=True)
    sales_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index("idx_ep_user", "user_id"),
        Index("idx_ep_active", "is_active"),
    )


# =============================================================================
# audiobook_productions — 有声书制作 (15.5.2)
# =============================================================================


class AudiobookProduction(Base):
    """有声书制作项目表.

    将文字作品转化为有声书的制作流程跟踪.
    v4 激活.
    """
    __tablename__ = "audiobook_productions"

    id = Column(String(32), primary_key=True, default=_uid)
    user_id = Column(String(32), nullable=False)
    work_id = Column(String(32), ForeignKey("works.id"), nullable=True)
    title = Column(String(500), nullable=False)
    narrator_id = Column(String(32), nullable=True)  # 配音演员ID
    status = Column(String(20), default="script")  # script/recording/editing/mastering/done
    total_chapters = Column(Integer, default=0)
    completed_chapters = Column(Integer, default=0)
    estimated_duration_minutes = Column(Integer, nullable=True)
    price = Column(Float, nullable=True)
    currency = Column(String(10), default="CNY")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index("idx_abp_user", "user_id"),
        Index("idx_abp_status", "status"),
    )


class AudiobookChapter(Base):
    """有声书章节音频表.

    每章的音频文件与文本对照.
    v4 激活.
    """
    __tablename__ = "audiobook_chapters"

    id = Column(String(32), primary_key=True, default=_uid)
    production_id = Column(String(32), ForeignKey("audiobook_productions.id"), nullable=False)
    chapter_id = Column(String(32), ForeignKey("chapters.id"), nullable=True)
    audio_url = Column(String(2000), nullable=True)
    duration_seconds = Column(Integer, nullable=True)
    word_count = Column(Integer, nullable=True)
    status = Column(String(20), default="pending")  # pending/recording/done
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (Index("idx_abc_prod", "production_id"),)
