"""Fork-Merge 协同创作服务 — Git-style 协作工作流."""

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session

from app.models.fork_merge import (
    ForkMergeWork,
    ForkMergeBranch,
    ForkMergeCommit,
    ForkMergePullRequest,
    ForkMergeCollaborator,
    ForkMergeSplitLock,
)


class ForkMergeService:
    """Fork-Merge 协同创作服务."""

    @classmethod
    def create_work(
        cls,
        db: Session,
        original_work_id: str,
        title: str,
        owner_id: str,
        description: Optional[str] = None,
        visibility: str = "private",
    ) -> ForkMergeWork:
        """创建协同仓库."""
        work = ForkMergeWork(
            id=str(uuid.uuid4().hex[:32]),
            original_work_id=original_work_id,
            title=title,
            description=description,
            owner_id=owner_id,
            visibility=visibility,
            base_commit_sha=str(uuid.uuid4().hex[:16]),
        )
        db.add(work)
        db.commit()
        db.refresh(work)
        return work

    @classmethod
    def get_work(cls, db: Session, work_id: str) -> Optional[ForkMergeWork]:
        """获取协同仓库."""
        return db.query(ForkMergeWork).filter(
            ForkMergeWork.id == work_id
        ).first()

    @classmethod
    def get_works_by_owner(
        cls,
        db: Session,
        owner_id: str,
        status: Optional[str] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> list[ForkMergeWork]:
        """按所有者查询协同仓库列表."""
        query = db.query(ForkMergeWork).filter(
            ForkMergeWork.owner_id == owner_id
        )
        if status:
            query = query.filter(ForkMergeWork.status == status)
        return query.order_by(
            ForkMergeWork.created_at.desc()
        ).offset(offset).limit(limit).all()

    @classmethod
    def close_work(cls, db: Session, work_id: str) -> ForkMergeWork:
        """关闭协同仓库."""
        work = cls.get_work(db, work_id)
        if not work:
            raise ValueError("协同仓库不存在")
        work.status = "closed"
        work.updated_at = datetime.utcnow()
        db.flush()
        db.refresh(work)
        return work

    @classmethod
    def add_branch(
        cls,
        db: Session,
        work_id: str,
        name: str,
        is_default: bool = False,
    ) -> ForkMergeBranch:
        """添加分支."""
        work = cls.get_work(db, work_id)
        if not work:
            raise ValueError("协同仓库不存在")

        branch = ForkMergeBranch(
            id=str(uuid.uuid4().hex[:32]),
            work_id=work_id,
            name=name,
            is_default=is_default,
        )
        db.add(branch)
        db.commit()
        db.refresh(branch)
        return branch

    @classmethod
    def get_branches(cls, db: Session, work_id: str) -> list[ForkMergeBranch]:
        """获取协同仓库的所有分支."""
        return db.query(ForkMergeBranch).filter(
            ForkMergeBranch.work_id == work_id
        ).order_by(
            ForkMergeBranch.created_at.desc()
        ).all()

    @classmethod
    def add_commit(
        cls,
        db: Session,
        work_id: str,
        author_id: str,
        message: str,
        branch_id: Optional[str] = None,
        parent_commit_id: Optional[str] = None,
        content_hash: Optional[str] = None,
        metadata_json: Optional[dict] = None,
    ) -> ForkMergeCommit:
        """添加提交记录."""
        work = cls.get_work(db, work_id)
        if not work:
            raise ValueError("协同仓库不存在")

        commit = ForkMergeCommit(
            id=str(uuid.uuid4().hex[:32]),
            work_id=work_id,
            branch_id=branch_id,
            parent_commit_id=parent_commit_id,
            author_id=author_id,
            message=message,
            content_hash=content_hash,
            metadata_json=metadata_json,
        )
        db.add(commit)
        db.commit()
        db.refresh(commit)

        # Update branch HEAD pointer
        if branch_id:
            branch = db.query(ForkMergeBranch).filter(
                ForkMergeBranch.id == branch_id
            ).first()
            if branch:
                branch.commit_id = commit.id
                db.commit()

        return commit

    @classmethod
    def get_commits(
        cls,
        db: Session,
        work_id: str,
        author_id: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[ForkMergeCommit]:
        """获取协同仓库的提交记录."""
        query = db.query(ForkMergeCommit).filter(
            ForkMergeCommit.work_id == work_id
        )
        if author_id:
            query = query.filter(ForkMergeCommit.author_id == author_id)
        return query.order_by(
            ForkMergeCommit.committed_at.desc()
        ).offset(offset).limit(limit).all()

    @classmethod
    def create_pull_request(
        cls,
        db: Session,
        work_id: str,
        title: str,
        author_id: str,
        source_branch_id: str,
        target_branch_id: Optional[str] = None,
        description: Optional[str] = None,
    ) -> ForkMergePullRequest:
        """创建 Merge Request."""
        work = cls.get_work(db, work_id)
        if not work:
            raise ValueError("协同仓库不存在")

        pr = ForkMergePullRequest(
            id=str(uuid.uuid4().hex[:32]),
            work_id=work_id,
            title=title,
            description=description,
            author_id=author_id,
            source_branch_id=source_branch_id,
            target_branch_id=target_branch_id or source_branch_id,
        )
        db.add(pr)
        db.commit()
        db.refresh(pr)
        return pr

    @classmethod
    def get_pull_requests(
        cls,
        db: Session,
        work_id: str,
        status: Optional[str] = None,
        author_id: Optional[str] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> list[ForkMergePullRequest]:
        """获取协同仓库的 Merge Request 列表."""
        query = db.query(ForkMergePullRequest).filter(
            ForkMergePullRequest.work_id == work_id
        )
        if status:
            query = query.filter(ForkMergePullRequest.status == status)
        if author_id:
            query = query.filter(ForkMergePullRequest.author_id == author_id)
        return query.order_by(
            ForkMergePullRequest.created_at.desc()
        ).offset(offset).limit(limit).all()

    @classmethod
    def merge_pull_request(
        cls,
        db: Session,
        pr_id: str,
        merge_method: str = "merge",
        locked_by: Optional[str] = None,
    ) -> ForkMergePullRequest:
        """合并 Merge Request."""
        pr = db.query(ForkMergePullRequest).filter(
            ForkMergePullRequest.id == pr_id
        ).first()
        if not pr:
            raise ValueError("Merge Request 不存在")
        if pr.status != "open":
            raise ValueError("只能合并开放的 Merge Request")

        pr.status = "merged"
        pr.merged_at = datetime.utcnow()
        pr.merge_method = merge_method
        db.flush()
        db.refresh(pr)
        return pr

    @classmethod
    def reject_pull_request(
        cls,
        db: Session,
        pr_id: str,
    ) -> ForkMergePullRequest:
        """拒绝 Merge Request."""
        pr = db.query(ForkMergePullRequest).filter(
            ForkMergePullRequest.id == pr_id
        ).first()
        if not pr:
            raise ValueError("Merge Request 不存在")
        if pr.status != "open":
            raise ValueError("只能拒绝开放的 Merge Request")

        pr.status = "rejected"
        db.flush()
        db.refresh(pr)
        return pr

    @classmethod
    def add_collaborator(
        cls,
        db: Session,
        work_id: str,
        user_id: str,
        role: str = "contributor",
        permissions: Optional[dict] = None,
    ) -> ForkMergeCollaborator:
        """添加协作者."""
        work = cls.get_work(db, work_id)
        if not work:
            raise ValueError("协同仓库不存在")

        collaborator = ForkMergeCollaborator(
            id=str(uuid.uuid4().hex[:32]),
            work_id=work_id,
            user_id=user_id,
            role=role,
            permissions=permissions,
        )
        db.add(collaborator)
        db.commit()
        db.refresh(collaborator)
        return collaborator

    @classmethod
    def remove_collaborator(
        cls,
        db: Session,
        work_id: str,
        user_id: str,
    ) -> ForkMergeCollaborator:
        """移除协作者."""
        collaborator = db.query(ForkMergeCollaborator).filter(
            ForkMergeCollaborator.work_id == work_id,
            ForkMergeCollaborator.user_id == user_id,
        ).first()
        if not collaborator:
            raise ValueError("协作者不存在")

        collaborator.left_at = datetime.utcnow()
        db.flush()
        db.refresh(collaborator)
        return collaborator

    @classmethod
    def get_collaborators(cls, db: Session, work_id: str) -> list[ForkMergeCollaborator]:
        """获取协同仓库的协作者列表."""
        return db.query(ForkMergeCollaborator).filter(
            ForkMergeCollaborator.work_id == work_id,
            ForkMergeCollaborator.left_at.is_(None),
        ).all()

    @classmethod
    def lock_split(
        cls,
        db: Session,
        pr_id: str,
        work_id: str,
        contributor_id: str,
        split_pct: float,
        locked_by: str,
    ) -> ForkMergeSplitLock:
        """锁定分润比例."""
        pr = db.query(ForkMergePullRequest).filter(
            ForkMergePullRequest.id == pr_id
        ).first()
        if not pr:
            raise ValueError("Merge Request 不存在")

        split_lock = ForkMergeSplitLock(
            id=str(uuid.uuid4().hex[:32]),
            pr_id=pr_id,
            work_id=work_id,
            contributor_id=contributor_id,
            split_pct=split_pct,
            locked_by=locked_by,
        )
        db.add(split_lock)
        db.commit()
        db.refresh(split_lock)
        return split_lock

    @classmethod
    def get_split_locks(
        cls,
        db: Session,
        pr_id: str,
    ) -> list[ForkMergeSplitLock]:
        """获取 Merge Request 的分润锁定列表."""
        return db.query(ForkMergeSplitLock).filter(
            ForkMergeSplitLock.pr_id == pr_id
        ).all()

    @classmethod
    def release_split_lock(
        cls,
        db: Session,
        split_lock_id: str,
    ) -> ForkMergeSplitLock:
        """释放分润锁定."""
        split_lock = db.query(ForkMergeSplitLock).filter(
            ForkMergeSplitLock.id == split_lock_id
        ).first()
        if not split_lock:
            raise ValueError("分润锁定不存在")

        split_lock.status = "released"
        db.flush()
        db.refresh(split_lock)
        return split_lock
