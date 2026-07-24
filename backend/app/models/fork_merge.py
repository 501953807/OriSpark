"""Fork-Merge 协同创作数据模型.

表:
- fork_merge_works: 协同仓库（半成品的 Git-style 工作空间）
- fork_merge_branches: 分支
- fork_merge_commits: 提交记录
- fork_merge_pull_requests: Merge Request
- fork_merge_collaborators: 协作者
- fork_merge_split_locks: 分润锁定
"""

import uuid
from datetime import datetime

from sqlalchemy import (
    Column, String, Integer, Float, Text, DateTime,
    Boolean, ForeignKey, Index, JSON,
)
from sqlalchemy.orm import relationship

from app.database import Base


def generate_uuid():
    return uuid.uuid4().hex[:32]


class ForkMergeWork(Base):
    """协同仓库表 — 半成品的 Git-style 工作空间."""
    __tablename__ = "fork_merge_works"

    id = Column(String(32), primary_key=True, default=generate_uuid)
    original_work_id = Column(String(32), nullable=False, comment="源作品 ID")
    title = Column(String(500), nullable=False, default="未命名协同仓库")
    description = Column(Text, nullable=True)
    owner_id = Column(String(32), nullable=False, index=True, comment="创建者/所有者用户 ID")
    status = Column(String(20), nullable=False, default="active", comment="active/closed/archived")
    visibility = Column(String(20), nullable=False, default="private", comment="public/private")
    base_commit_sha = Column(String(64), nullable=True, comment="初始基线提交 SHA")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    branches = relationship("ForkMergeBranch", back_populates="work", cascade="all, delete-orphan")
    commits = relationship("ForkMergeCommit", back_populates="work", cascade="all, delete-orphan")
    pull_requests = relationship("ForkMergePullRequest", back_populates="work", cascade="all, delete-orphan")
    collaborators = relationship("ForkMergeCollaborator", back_populates="work", cascade="all, delete-orphan")
    split_locks = relationship("ForkMergeSplitLock", back_populates="work", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_fmw_owner", "owner_id"),
        Index("idx_fmw_status", "status"),
    )


class ForkMergeBranch(Base):
    """分支表."""
    __tablename__ = "fork_merge_branches"

    id = Column(String(32), primary_key=True, default=generate_uuid)
    work_id = Column(String(32), ForeignKey("fork_merge_works.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(100), nullable=False, default="main", comment="分支名，默认 main")
    commit_id = Column(String(32), ForeignKey("fork_merge_commits.id", ondelete="SET NULL", use_alter=True), nullable=True, comment="当前 HEAD 提交 ID")
    is_default = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    work = relationship("ForkMergeWork", back_populates="branches")
    commit = relationship("ForkMergeCommit", foreign_keys=[commit_id])

    __table_args__ = (
        Index("idx_fmb_work", "work_id"),
        Index("idx_fmb_name", "name"),
    )


class ForkMergeCommit(Base):
    """提交记录表 — Git-style commit."""
    __tablename__ = "fork_merge_commits"

    id = Column(String(32), primary_key=True, default=generate_uuid)
    work_id = Column(String(32), ForeignKey("fork_merge_works.id", ondelete="CASCADE"), nullable=False)
    branch_id = Column(String(32), ForeignKey("fork_merge_branches.id", ondelete="SET NULL", use_alter=True), nullable=True)
    parent_commit_id = Column(String(32), ForeignKey("fork_merge_commits.id", ondelete="SET NULL"), nullable=True, comment="父提交 ID")
    author_id = Column(String(32), nullable=False, index=True, comment="提交者用户 ID")
    message = Column(Text, nullable=False, default="")
    content_hash = Column(String(64), nullable=True, comment="内容 SHA256")
    metadata_json = Column(JSON, nullable=True, comment="扩展元数据（文件变更、AI 工具使用等）")
    committed_at = Column(DateTime, default=datetime.utcnow)

    work = relationship("ForkMergeWork", back_populates="commits")
    branch = relationship("ForkMergeBranch", foreign_keys=[branch_id])

    __table_args__ = (
        Index("idx_fmc_work", "work_id"),
        Index("idx_fmc_author", "author_id"),
    )


class ForkMergePullRequest(Base):
    """Merge Request 表."""
    __tablename__ = "fork_merge_pull_requests"

    id = Column(String(32), primary_key=True, default=generate_uuid)
    work_id = Column(String(32), ForeignKey("fork_merge_works.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    author_id = Column(String(32), nullable=False, index=True, comment="发起人用户 ID")
    source_branch_id = Column(String(32), ForeignKey("fork_merge_branches.id", ondelete="SET NULL"), nullable=True, comment="源分支 ID")
    target_branch_id = Column(String(32), ForeignKey("fork_merge_branches.id", ondelete="SET NULL"), nullable=True, comment="目标分支 ID")
    status = Column(String(20), nullable=False, default="open", comment="open/merged/closed/rejected")
    merged_at = Column(DateTime, nullable=True)
    merge_method = Column(String(20), nullable=True, comment="merge/squash/rebase")
    conflict_detail = Column(JSON, nullable=True, comment="冲突详情")
    review_comments = Column(JSON, nullable=True, comment="评审意见列表")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    work = relationship("ForkMergeWork", back_populates="pull_requests")

    __table_args__ = (
        Index("idx_fmpr_work", "work_id"),
        Index("idx_fmpr_author", "author_id"),
        Index("idx_fmpr_status", "status"),
    )


class ForkMergeCollaborator(Base):
    """协作者表."""
    __tablename__ = "fork_merge_collaborators"

    id = Column(String(32), primary_key=True, default=generate_uuid)
    work_id = Column(String(32), ForeignKey("fork_merge_works.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(String(32), nullable=False, index=True, comment="协作用户 ID")
    role = Column(String(20), nullable=False, default="contributor", comment="owner/collaborator/contributor/viewer")
    permissions = Column(JSON, nullable=True, comment="细粒度权限")
    joined_at = Column(DateTime, default=datetime.utcnow)
    left_at = Column(DateTime, nullable=True)

    work = relationship("ForkMergeWork", back_populates="collaborators")

    __table_args__ = (
        Index("idx_fmcol_work", "work_id"),
        Index("idx_fmcol_user", "user_id"),
        Index("idx_fmcol_unique", "work_id", "user_id", unique=True),
    )


class ForkMergeSplitLock(Base):
    """分润锁定表 — 联合确权时锁定各参与方的分润比例."""
    __tablename__ = "fork_merge_split_locks"

    id = Column(String(32), primary_key=True, default=generate_uuid)
    pr_id = Column(String(32), ForeignKey("fork_merge_pull_requests.id", ondelete="CASCADE"), nullable=False, comment="关联 Merge Request")
    work_id = Column(String(32), ForeignKey("fork_merge_works.id", ondelete="CASCADE"), nullable=False)
    contributor_id = Column(String(32), nullable=False, index=True, comment="贡献者用户 ID")
    split_pct = Column(Float, nullable=False, default=0.0, comment="分润比例百分比")
    locked_at = Column(DateTime, default=datetime.utcnow)
    locked_by = Column(String(32), nullable=False, comment="锁定操作者 ID")
    status = Column(String(20), nullable=False, default="locked", comment="locked/released/modified")

    pr = relationship("ForkMergePullRequest")
    work = relationship("ForkMergeWork", back_populates="split_locks")

    __table_args__ = (
        Index("idx_fmsl_pr", "pr_id"),
        Index("idx_fmsl_contributor", "contributor_id"),
    )
