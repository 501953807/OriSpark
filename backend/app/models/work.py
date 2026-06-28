"""作品管理数据模型.

表:
- works: 核心作品表
- work_versions: 版本快照
- work_tags: 标签关联
- projects: 项目分组
"""

import uuid
from datetime import datetime

from sqlalchemy import (
    Column, String, Integer, BigInteger, Float, Text, DateTime,
    Boolean, ForeignKey, Index, UniqueConstraint, JSON,
)
from sqlalchemy.orm import relationship

from app.database import Base


def generate_uuid():
    return uuid.uuid4().hex


class Work(Base):
    """作品表."""
    __tablename__ = "works"

    id = Column(String(32), primary_key=True, default=generate_uuid)
    title = Column(String(500), nullable=False, default="未命名作品")
    file_path = Column(String(2000), nullable=False)
    file_name = Column(String(500), nullable=False)
    file_size = Column(BigInteger, nullable=False, default=0)  # bytes
    file_type = Column(String(20), nullable=False, default="image")  # image/audio/video/document/code/design
    file_extension = Column(String(20), nullable=False)
    mime_type = Column(String(100), nullable=True)
    sha256 = Column(String(64), nullable=True, index=True)
    md5 = Column(String(32), nullable=True)
    description = Column(Text, nullable=True)
    project_id = Column(String(32), ForeignKey("projects.id"), nullable=True)
    status = Column(String(20), nullable=False, default="active")  # active/trashed/archived
    is_verified = Column(Boolean, default=False)  # 是否已存证
    thumbnail_path = Column(String(2000), nullable=True)
    width = Column(Integer, nullable=True)
    height = Column(Integer, nullable=True)
    duration = Column(Float, nullable=True)  # 音频/视频时长(秒)
    custom_metadata = Column(JSON, nullable=True)
    exif_data = Column(JSON, nullable=True)
    # P1.1.1-P1.1.3: 导入模式 (full/hash_only/lowres)
    import_mode = Column(String(20), nullable=False, default="full")
    # P1.1.6: Fork 支持
    parent_work_id = Column(String(32), ForeignKey("works.id"), nullable=True)
    # P1.1.8-P1.1.9: 版权管理
    rights = Column(JSON, nullable=True)
    license_type = Column(String(50), nullable=True)
    synopsis = Column(Text, nullable=True)
    completion_date = Column(String(20), nullable=True)
    current_stage = Column(String(30), nullable=True)
    copyright_year = Column(Integer, nullable=True)
    # P3-1: Video project package concept
    is_project_package = Column(Boolean, default=False)
    project_files = Column(JSON, nullable=True)
    # P2-1: RAW format support
    is_raw_original = Column(Boolean, default=False)
    raw_sidecar_path = Column(String(2000), nullable=True)
    raw_processed_variant_id = Column(String(32), nullable=True)
    # P2-3: Culling mode
    cull_status = Column(String(20), default="review")  # review/pass/fail/hold
    cull_rating = Column(Integer, default=0)  # 0-5 stars
    color_label = Column(String(20), default="")  # red/green/blue/yellow
    # Phase 0: AI 创作记录扩展
    ai_assisted = Column(Boolean, default=False)
    ai_tools_used = Column(JSON, nullable=True)
    creator_type = Column(String(30), default="illustrator")
    # P2-2: EXIF advanced search fields (stored in custom_metadata JSON, queried via JSON path)
    created_at = Column(DateTime, default=datetime.utcnow)
    imported_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = Column(DateTime, nullable=True)

    # 关系
    tags = relationship("WorkTag", back_populates="work", cascade="all, delete-orphan")
    versions = relationship("WorkVersion", back_populates="work", cascade="all, delete-orphan")
    project = relationship("Project", back_populates="works")
    notary_records = relationship("NotaryRecord", back_populates="work")
    # Fork 父子关系
    parent = relationship("Work", remote_side="Work.id", backref="forks")

    __table_args__ = (
        Index("idx_works_sha256", "sha256"),
        Index("idx_works_file_type", "file_type"),
        Index("idx_works_status", "status"),
        Index("idx_works_created", "created_at"),
        Index("idx_works_type_status", "file_type", "status"),
        # 复合索引 — 覆盖常用筛选+排序查询模式
        Index("idx_works_query", "file_type", "status", "created_at"),
        Index("idx_works_import_mode", "import_mode"),
        Index("idx_works_parent", "parent_work_id"),
        Index("idx_works_license", "license_type"),
    )


class WorkVersion(Base):
    """作品版本表."""
    __tablename__ = "work_versions"

    id = Column(String(32), primary_key=True, default=generate_uuid)
    work_id = Column(String(32), ForeignKey("works.id", ondelete="CASCADE"), nullable=False)
    version_num = Column(Integer, nullable=False)
    file_hash = Column(String(64), nullable=False)
    file_path = Column(String(2000), nullable=False)
    file_size = Column(BigInteger, nullable=False)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    work = relationship("Work", back_populates="versions")

    __table_args__ = (
        UniqueConstraint("work_id", "version_num", name="uq_work_version"),
        Index("idx_version_work", "work_id"),
    )


class WorkTag(Base):
    """作品标签表."""
    __tablename__ = "work_tags"

    id = Column(String(32), primary_key=True, default=generate_uuid)
    work_id = Column(String(32), ForeignKey("works.id", ondelete="CASCADE"), nullable=False)
    tag = Column(String(100), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    work = relationship("Work", back_populates="tags")

    __table_args__ = (
        UniqueConstraint("work_id", "tag", name="uq_work_tag"),
        Index("idx_work_tags_tag", "tag"),
    )


class Project(Base):
    """项目分组表."""
    __tablename__ = "projects"

    id = Column(String(32), primary_key=True, default=generate_uuid)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    cover_work_id = Column(String(32), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    works = relationship("Work", back_populates="project")
