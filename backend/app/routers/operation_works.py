"""作品公开可运营状态路由 — v6.0 Issue #62.

端点:
- GET  /api/creator/works/{id}/operation-public    — 创作者获取公开状态
- PATCH /api/creator/works/{id}/operation-public   — 创作者切换公开状态
- GET  /api/operator/works/available               — 运营者发现公开作品
- GET  /api/operator/works/available/{id}          — 运营者查看单个公开作品详情
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.work import WorkResponse
from app.deps import require_creator, require_operator
from app.models.system import User as UserModel
from app.services.work_operation_service import WorkOperationService

router = APIRouter(prefix="/creator/works", tags=["operation-work"])

# 运营者专用路由（与 creator 路由分开，归属同一 router 但前缀不同）
operator_router = APIRouter(prefix="/operator/works", tags=["operation-work"])


# ==================== 创作者端 ====================

@router.get("/{work_id}/operation-public", response_model=dict)
def get_operation_public_status(
    work_id: str,
    db: Session = Depends(get_db),
    creator: UserModel = Depends(require_creator),
):
    """创作者查询自己作品的公开可运营状态."""
    from app.models.work import Work
    work_obj = db.query(Work).filter(Work.id == work_id).first()
    if not work_obj:
        raise HTTPException(status_code=404, detail="作品不存在")
    if work_obj.creator_id != creator.id:
        raise HTTPException(status_code=403, detail="无权访问该作品")
    return {
        "work_id": work_obj.id,
        "work_operation_public": work_obj.work_operation_public,
        "operation_agreement_id": work_obj.operation_agreement_id,
    }


@router.patch("/{work_id}/operation-public", response_model=WorkResponse)
def toggle_operation_public(
    work_id: str,
    db: Session = Depends(get_db),
    creator: UserModel = Depends(require_creator),
):
    """创作者切换作品的公开可运营状态."""
    try:
        work = WorkOperationService.toggle_operation_public(db, work_id, creator.id)
    except ValueError as e:
        detail = str(e)
        if detail == "作品不存在":
            raise HTTPException(status_code=404, detail=detail)
        raise HTTPException(status_code=403, detail=detail)
    return work


# ==================== 运营者端 ====================

@operator_router.get("/available", response_model=dict)
def list_available_works(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    operator: UserModel = Depends(require_operator),
):
    """运营者发现公开可运营作品列表."""
    result = WorkOperationService.list_operation_public_works(db, page=page, limit=limit)
    return {
        "items": [WorkResponse.model_validate(w) for w in result["items"]],
        "total": result["total"],
        "page": result["page"],
        "page_size": result["page_size"],
        "total_pages": result["total_pages"],
    }


@operator_router.get("/available/{work_id}", response_model=WorkResponse)
def get_available_work(
    work_id: str,
    db: Session = Depends(get_db),
    operator: UserModel = Depends(require_operator),
):
    """运营者查看单个公开作品详情."""
    work = WorkOperationService.get_operation_public_work(db, work_id)
    if not work:
        raise HTTPException(status_code=404, detail="作品不存在或未公开可运营")
    return work
