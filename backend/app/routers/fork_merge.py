"""Fork-Merge 协同创作路由 — Git-style 协作工作流 API."""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.fork_merge import (
    ForkMergeWork,
    ForkMergeBranch,
    ForkMergeCommit,
    ForkMergePullRequest,
    ForkMergeCollaborator,
    ForkMergeSplitLock,
)
from app.schemas.common import ApiResponse
from app.services.fork_merge_service import ForkMergeService


router = APIRouter()


def _work_to_dict(work: ForkMergeWork) -> dict:
    return {
        "id": work.id,
        "original_work_id": work.original_work_id,
        "title": work.title,
        "description": work.description,
        "owner_id": work.owner_id,
        "status": work.status,
        "visibility": work.visibility,
        "base_commit_sha": work.base_commit_sha,
        "created_at": work.created_at.isoformat() if work.created_at else None,
        "updated_at": work.updated_at.isoformat() if work.updated_at else None,
    }


def _branch_to_dict(branch: ForkMergeBranch) -> dict:
    return {
        "id": branch.id,
        "work_id": branch.work_id,
        "name": branch.name,
        "commit_id": branch.commit_id,
        "is_default": branch.is_default,
        "created_at": branch.created_at.isoformat() if branch.created_at else None,
    }


def _commit_to_dict(commit: ForkMergeCommit) -> dict:
    return {
        "id": commit.id,
        "work_id": commit.work_id,
        "branch_id": commit.branch_id,
        "parent_commit_id": commit.parent_commit_id,
        "author_id": commit.author_id,
        "message": commit.message,
        "content_hash": commit.content_hash,
        "metadata_json": commit.metadata_json,
        "committed_at": commit.committed_at.isoformat() if commit.committed_at else None,
    }


def _pr_to_dict(pr: ForkMergePullRequest) -> dict:
    return {
        "id": pr.id,
        "work_id": pr.work_id,
        "title": pr.title,
        "description": pr.description,
        "author_id": pr.author_id,
        "source_branch_id": pr.source_branch_id,
        "target_branch_id": pr.target_branch_id,
        "status": pr.status,
        "merged_at": pr.merged_at.isoformat() if pr.merged_at else None,
        "merge_method": pr.merge_method,
        "conflict_detail": pr.conflict_detail,
        "review_comments": pr.review_comments,
        "created_at": pr.created_at.isoformat() if pr.created_at else None,
        "updated_at": pr.updated_at.isoformat() if pr.updated_at else None,
    }


def _collaborator_to_dict(collab: ForkMergeCollaborator) -> dict:
    return {
        "id": collab.id,
        "work_id": collab.work_id,
        "user_id": collab.user_id,
        "role": collab.role,
        "permissions": collab.permissions,
        "joined_at": collab.joined_at.isoformat() if collab.joined_at else None,
        "left_at": collab.left_at.isoformat() if collab.left_at else None,
    }


def _split_lock_to_dict(lock: ForkMergeSplitLock) -> dict:
    return {
        "id": lock.id,
        "pr_id": lock.pr_id,
        "work_id": lock.work_id,
        "contributor_id": lock.contributor_id,
        "split_pct": lock.split_pct,
        "locked_at": lock.locked_at.isoformat() if lock.locked_at else None,
        "locked_by": lock.locked_by,
        "status": lock.status,
    }


@router.post("/fork-merge/workspaces", response_model=ApiResponse)
async def create_workspace(
    body: dict,
    db: Session = Depends(get_db),
):
    """创建协同仓库."""
    try:
        work = ForkMergeService.create_work(
            db=db,
            original_work_id=body["original_work_id"],
            title=body["title"],
            owner_id=body["owner_id"],
            description=body.get("description"),
            visibility=body.get("visibility", "private"),
        )
        # 自动创建默认分支 main
        ForkMergeService.add_branch(db, work.id, "main", is_default=True)
        db.flush()
        db.refresh(work)
        return ApiResponse(success=True, data=_work_to_dict(work))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/fork-merge/workspaces/{work_id}", response_model=ApiResponse)
async def get_workspace(work_id: str, db: Session = Depends(get_db)):
    """获取协同仓库详情."""
    work = ForkMergeService.get_work(db, work_id)
    if not work:
        raise HTTPException(status_code=404, detail="协同仓库不存在")
    return ApiResponse(success=True, data=_work_to_dict(work))


@router.get("/fork-merge/workspaces", response_model=ApiResponse)
async def list_workspaces(
    owner_id: str = Query(..., description="所有者用户 ID"),
    status: Optional[str] = Query(None, description="状态过滤"),
    limit: int = Query(default=20, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    """按所有者查询协同仓库列表."""
    works = ForkMergeService.get_works_by_owner(
        db=db, owner_id=owner_id, status=status, limit=limit, offset=offset
    )
    return ApiResponse(
        success=True,
        data={"items": [_work_to_dict(w) for w in works], "total": len(works)},
    )


@router.patch("/fork-merge/workspaces/{work_id}/close", response_model=ApiResponse)
async def close_workspace(work_id: str, db: Session = Depends(get_db)):
    """关闭协同仓库."""
    try:
        work = ForkMergeService.close_work(db, work_id)
        return ApiResponse(success=True, data=_work_to_dict(work))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# --- Branches ---

@router.post("/fork-merge/workspaces/{work_id}/branches", response_model=ApiResponse)
async def create_branch(
    work_id: str,
    body: dict,
    db: Session = Depends(get_db),
):
    """添加分支."""
    try:
        branch = ForkMergeService.add_branch(
            db=db,
            work_id=work_id,
            name=body["name"],
            is_default=body.get("is_default", False),
        )
        db.flush()
        db.refresh(branch)
        return ApiResponse(success=True, data=_branch_to_dict(branch))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/fork-merge/workspaces/{work_id}/branches", response_model=ApiResponse)
async def list_branches(work_id: str, db: Session = Depends(get_db)):
    """获取分支列表."""
    branches = ForkMergeService.get_branches(db, work_id)
    return ApiResponse(
        success=True,
        data={"items": [_branch_to_dict(b) for b in branches]},
    )


# --- Commits ---

@router.post("/fork-merge/workspaces/{work_id}/commits", response_model=ApiResponse)
async def create_commit(
    work_id: str,
    body: dict,
    db: Session = Depends(get_db),
):
    """添加提交记录."""
    try:
        commit = ForkMergeService.add_commit(
            db=db,
            work_id=work_id,
            author_id=body["author_id"],
            message=body.get("message", ""),
            branch_id=body.get("branch_id"),
            parent_commit_id=body.get("parent_commit_id"),
            content_hash=body.get("content_hash"),
            metadata_json=body.get("metadata_json"),
        )
        db.flush()
        db.refresh(commit)
        return ApiResponse(success=True, data=_commit_to_dict(commit))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/fork-merge/workspaces/{work_id}/commits", response_model=ApiResponse)
async def list_commits(
    work_id: str,
    author_id: Optional[str] = Query(None),
    limit: int = Query(default=50, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    """获取提交记录列表."""
    commits = ForkMergeService.get_commits(
        db=db, work_id=work_id, author_id=author_id, limit=limit, offset=offset
    )
    return ApiResponse(
        success=True,
        data={"items": [_commit_to_dict(c) for c in commits]},
    )


# --- Pull Requests ---

@router.post("/fork-merge/workspaces/{work_id}/pull-requests", response_model=ApiResponse)
async def create_pull_request(
    work_id: str,
    body: dict,
    db: Session = Depends(get_db),
):
    """创建 Merge Request."""
    try:
        pr = ForkMergeService.create_pull_request(
            db=db,
            work_id=work_id,
            title=body["title"],
            author_id=body["author_id"],
            source_branch_id=body["source_branch_id"],
            target_branch_id=body.get("target_branch_id"),
            description=body.get("description"),
        )
        db.flush()
        db.refresh(pr)
        return ApiResponse(success=True, data=_pr_to_dict(pr))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/fork-merge/workspaces/{work_id}/pull-requests", response_model=ApiResponse)
async def list_pull_requests(
    work_id: str,
    status: Optional[str] = Query(None),
    author_id: Optional[str] = Query(None),
    limit: int = Query(default=20, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    """获取 Merge Request 列表."""
    prs = ForkMergeService.get_pull_requests(
        db=db, work_id=work_id, status=status, author_id=author_id,
        limit=limit, offset=offset,
    )
    return ApiResponse(
        success=True,
        data={"items": [_pr_to_dict(p) for p in prs]},
    )


@router.post("/fork-merge/pull-requests/{pr_id}/merge", response_model=ApiResponse)
async def merge_pull_request(
    pr_id: str,
    body: dict = {},
    db: Session = Depends(get_db),
):
    """合并 Merge Request."""
    try:
        pr = ForkMergeService.merge_pull_request(
            db=db,
            pr_id=pr_id,
            merge_method=body.get("merge_method", "merge"),
            locked_by=body.get("locked_by"),
        )
        db.flush()
        db.refresh(pr)
        return ApiResponse(success=True, data=_pr_to_dict(pr))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/fork-merge/pull-requests/{pr_id}/reject", response_model=ApiResponse)
async def reject_pull_request(pr_id: str, db: Session = Depends(get_db)):
    """拒绝 Merge Request."""
    try:
        pr = ForkMergeService.reject_pull_request(db, pr_id)
        db.flush()
        db.refresh(pr)
        return ApiResponse(success=True, data=_pr_to_dict(pr))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# --- Collaborators ---

@router.post("/fork-merge/workspaces/{work_id}/collaborators", response_model=ApiResponse)
async def add_collaborator(
    work_id: str,
    body: dict,
    db: Session = Depends(get_db),
):
    """添加协作者."""
    try:
        collab = ForkMergeService.add_collaborator(
            db=db,
            work_id=work_id,
            user_id=body["user_id"],
            role=body.get("role", "contributor"),
            permissions=body.get("permissions"),
        )
        db.flush()
        db.refresh(collab)
        return ApiResponse(success=True, data=_collaborator_to_dict(collab))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/fork-merge/workspaces/{work_id}/collaborators/{user_id}", response_model=ApiResponse)
async def remove_collaborator(
    work_id: str,
    user_id: str,
    db: Session = Depends(get_db),
):
    """移除协作者."""
    try:
        collab = ForkMergeService.remove_collaborator(db, work_id, user_id)
        db.flush()
        db.refresh(collab)
        return ApiResponse(success=True, data=_collaborator_to_dict(collab))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/fork-merge/workspaces/{work_id}/collaborators", response_model=ApiResponse)
async def list_collaborators(work_id: str, db: Session = Depends(get_db)):
    """获取协作者列表."""
    collaborators = ForkMergeService.get_collaborators(db, work_id)
    return ApiResponse(
        success=True,
        data={"items": [_collaborator_to_dict(c) for c in collaborators]},
    )


# --- Split Locks ---

@router.post("/fork-merge/pull-requests/{pr_id}/split-locks", response_model=ApiResponse)
async def lock_split(
    pr_id: str,
    body: dict,
    db: Session = Depends(get_db),
):
    """锁定分润比例."""
    try:
        split_lock = ForkMergeService.lock_split(
            db=db,
            pr_id=pr_id,
            work_id=body["work_id"],
            contributor_id=body["contributor_id"],
            split_pct=body["split_pct"],
            locked_by=body["locked_by"],
        )
        db.flush()
        db.refresh(split_lock)
        return ApiResponse(success=True, data=_split_lock_to_dict(split_lock))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/fork-merge/pull-requests/{pr_id}/split-locks", response_model=ApiResponse)
async def list_split_locks(pr_id: str, db: Session = Depends(get_db)):
    """获取分润锁定列表."""
    locks = ForkMergeService.get_split_locks(db, pr_id)
    return ApiResponse(
        success=True,
        data={"items": [_split_lock_to_dict(l) for l in locks]},
    )


@router.post("/fork-merge/split-locks/{split_lock_id}/release", response_model=ApiResponse)
async def release_split_lock(split_lock_id: str, db: Session = Depends(get_db)):
    """释放分润锁定."""
    try:
        split_lock = ForkMergeService.release_split_lock(db, split_lock_id)
        db.flush()
        db.refresh(split_lock)
        return ApiResponse(success=True, data=_split_lock_to_dict(split_lock))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
