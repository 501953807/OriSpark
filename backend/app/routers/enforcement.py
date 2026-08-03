# -*- coding: utf-8 -*-
"""维权流水线 API 路由 — 对应: docs/modules-v5/02-rights-protection.md
端点: 14 (enforcement)

所有 DB 操作已提取至 enforcement_manager_service.py.
"""

from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user_id, is_admin
from app.schemas.enforcement import (
    ComplaintSubmitRequest,
    ComplaintSubmitResponse,
    EnforcementActionCreate,
    EnforcementActionResponse,
    EnforcementActionUpdate,
    EnforcementTemplateResponse,
    TransitionRequest,
    ConfirmRequest,
    EvidenceGatherRequest,
    ResolveRequest,
    WorkflowStatusResponse,
)
from app.services.enforcement_manager_service import EnforcementManagerService


router = APIRouter(prefix="/enforcement", tags=["Enforcement"])


# ── 1. POST /actions ────────────────────────────────────────────────


@router.post("/actions", response_model=EnforcementActionResponse, status_code=201)
async def create_action(
    payload: EnforcementActionCreate,
    actor_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """从监测结果创建维权行动."""
    svc = EnforcementManagerService(db)
    return svc.create_action(payload, actor_id)


# ── 2. GET /actions ─────────────────────────────────────────────────


@router.get("/actions", response_model=list[EnforcementActionResponse])
async def list_actions(
    status: Optional[str] = None,
    action_type: Optional[str] = None,
    platform: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    actor_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """获取维权行动列表."""
    svc = EnforcementManagerService(db)
    return svc.list_actions(status, action_type, platform, page, page_size)


# ── 3. GET /actions/{action_id} ─────────────────────────────────────


@router.get("/actions/{action_id}", response_model=EnforcementActionResponse)
async def get_action(
    action_id: str,
    actor_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """获取维权行动详情."""
    svc = EnforcementManagerService(db)
    return svc.get_action(action_id, actor_id, is_admin)


# ── 4. PATCH /actions/{action_id} ───────────────────────────────────


@router.patch("/actions/{action_id}", response_model=EnforcementActionResponse)
async def update_action(
    action_id: str,
    payload: EnforcementActionUpdate,
    actor_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """更新维权行动 (状态机约束)."""
    svc = EnforcementManagerService(db)
    return svc.update_action(action_id, payload, actor_id, is_admin)


# ── 5. POST /actions/{action_id}/gather-evidence ────────────────────


@router.post("/actions/{action_id}/gather-evidence")
async def gather_evidence(
    action_id: str,
    actor_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """收集证据包并创建投诉材料."""
    svc = EnforcementManagerService(db)
    return svc.gather_evidence(action_id, actor_id, is_admin)


# ── 6. POST /actions/{action_id}/submit-complaint ───────────────────


@router.post(
    "/actions/{action_id}/submit-complaint",
    response_model=ComplaintSubmitResponse,
)
async def submit_complaint(
    action_id: str,
    payload: ComplaintSubmitRequest,
    actor_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """使用模板变量提交投诉."""
    svc = EnforcementManagerService(db)
    return svc.submit_complaint(action_id, payload, actor_id, is_admin)


# ── 7. POST /actions/{action_id}/transition ─────────────────────────


@router.post("/actions/{action_id}/transition", response_model=dict)
async def transition_action(
    action_id: str,
    request: TransitionRequest,
    actor_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """转换维权行动状态."""
    svc = EnforcementManagerService(db)
    return svc.transition_action(action_id, request, actor_id, is_admin)


# ── 8. POST /actions/{action_id}/confirm ────────────────────────────


@router.post("/actions/{action_id}/confirm", response_model=dict)
async def confirm_action(
    action_id: str,
    request: ConfirmRequest,
    actor_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """确认复核步骤."""
    svc = EnforcementManagerService(db)
    return svc.confirm_action(action_id, request, actor_id, is_admin)


# ── 9. POST /actions/{action_id}/gather-evidence/step ───────────────


@router.post("/actions/{action_id}/gather-evidence/step", response_model=dict)
async def gather_action_evidence(
    action_id: str,
    request: EvidenceGatherRequest,
    actor_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """收集证据并转换到 evidence_gathered 阶段."""
    svc = EnforcementManagerService(db)
    return svc.gather_action_evidence(action_id, request, actor_id, is_admin)


# ── 10. POST /actions/{action_id}/resolve ───────────────────────────


@router.post("/actions/{action_id}/resolve", response_model=dict)
async def resolve_action(
    action_id: str,
    request: ResolveRequest,
    actor_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """解决维权行动."""
    svc = EnforcementManagerService(db)
    return svc.resolve_action(action_id, request, actor_id, is_admin)


# ── 11. GET /actions/{action_id}/workflow-status ────────────────────


@router.get("/actions/{action_id}/workflow-status", response_model=WorkflowStatusResponse)
async def get_workflow_status(
    action_id: str,
    actor_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """获取当前工作流状态."""
    svc = EnforcementManagerService(db)
    return svc.get_workflow_status(action_id, actor_id, is_admin)


# ── 12. GET /actions/work/{work_id} ─────────────────────────────────


@router.get("/actions/work/{work_id}")
async def list_actions_by_work(
    work_id: str,
    actor_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """列出与指定作品相关的所有维权行动."""
    svc = EnforcementManagerService(db)
    return svc.list_actions_by_work(work_id, actor_id)


# ── 13. GET /templates ──────────────────────────────────────────────


@router.get("/templates", response_model=list[EnforcementTemplateResponse])
async def list_templates(
    platform: Optional[str] = Query(None),
    jurisdiction: Optional[str] = Query(None),
    actor_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """列出维权模板."""
    svc = EnforcementManagerService(db)
    return svc.list_templates(platform, jurisdiction, actor_id)


# ── 14. POST /templates/seed ────────────────────────────────────────


@router.post("/templates/seed")
async def seed_templates(
    actor_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """填充默认维权模板."""
    svc = EnforcementManagerService(db)
    return svc.seed_templates(actor_id, is_admin)


# ── Bridge ──────────────────────────────────────────────────────────


@router.post("/actions/from-work/{work_id}")
async def create_action_from_work_endpoint(
    work_id: str,
    actor_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """从作品直接启动维权流程."""
    svc = EnforcementManagerService(db)
    return svc.create_action_from_work(work_id, actor_id)
