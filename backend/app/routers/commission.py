# -*- coding: utf-8 -*-
"""委托项目管理 API 路由 — 对应: docs/modules-v5/06-business-management.md
端点: 9 (commission)

所有 DB 操作已提取至 commission_manager_service.py.
"""

from typing import Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import require_auth
from app.schemas.common import ApiResponse, PaginationParams
from app.schemas.commission import (
    MilestoneCreate,
    MilestoneUpdate,
    PaymentCreate,
    PaymentUpdate,
    RevisionCreate,
)
from app.services.commission_manager_service import CommissionManagerService


router = APIRouter(prefix="/commission", tags=["Commission"])


# ── 请求体模型（与原始代码保持一致）─────────────────────────────────────


class CreateProjectPayload(BaseModel):
    title: str
    user_id: str = ""
    description: Optional[str] = None
    client_name: Optional[str] = None
    status: str = "brief"
    payment_terms: list = Field(default_factory=list)


class UpdateProjectPayload(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    client_name: Optional[str] = None
    status: Optional[str] = None


class CreateOrderPayload(BaseModel):
    order_type: str
    amount: float
    status: str = "pending"


class CreateMessagePayload(BaseModel):
    sender_id: str = ""
    content: str


# ============================================================================
# 10.x 委托项目 CRUD
# ============================================================================


@router.get("/projects", response_model=ApiResponse)
def list_projects(
    params: PaginationParams = Query(PaginationParams()),
    user_id: Optional[str] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """获取委托项目列表 (分页)."""
    svc = CommissionManagerService(db)
    return svc.list_projects(params, user_id=user_id, status=status)


@router.post("/projects", response_model=ApiResponse[dict], dependencies=[Depends(require_auth)])
def create_project(payload: CreateProjectPayload, db: Session = Depends(get_db)):
    """创建委托项目."""
    svc = CommissionManagerService(db)
    return svc.create_project(
        payload.title, payload.user_id, payload.description,
        payload.client_name, payload.status, payload.payment_terms,
    )


@router.get("/projects/{project_id}", response_model=ApiResponse[dict])
def get_project(project_id: str, db: Session = Depends(get_db)):
    """获取单个委托项目详情."""
    svc = CommissionManagerService(db)
    return svc.get_project(project_id)


@router.put("/projects/{project_id}", response_model=ApiResponse[dict], dependencies=[Depends(require_auth)])
def update_project(project_id: str, payload: UpdateProjectPayload, db: Session = Depends(get_db)):
    """更新委托项目."""
    svc = CommissionManagerService(db)
    return svc.update_project(project_id, payload.title, payload.description, payload.client_name, payload.status)


@router.delete("/projects/{project_id}", response_model=ApiResponse[dict], dependencies=[Depends(require_auth)])
def delete_project(project_id: str, db: Session = Depends(get_db)):
    """删除委托项目 (级联删除订单、消息、里程碑、收款、修改记录)."""
    svc = CommissionManagerService(db)
    return svc.delete_project(project_id)


# ============================================================================
# 10.x 委托订单 CRUD
# ============================================================================


@router.get("/projects/{project_id}/orders", response_model=ApiResponse[list])
def list_orders(project_id: str, status: Optional[str] = None, db: Session = Depends(get_db)):
    """获取项目下的订单列表."""
    svc = CommissionManagerService(db)
    return svc.list_orders(project_id, status)


@router.post("/projects/{project_id}/orders", response_model=ApiResponse[dict], dependencies=[Depends(require_auth)])
def create_order(project_id: str, payload: CreateOrderPayload, db: Session = Depends(get_db)):
    """创建委托订单."""
    svc = CommissionManagerService(db)
    return svc.create_order(project_id, payload.order_type, payload.amount, payload.status)


# ============================================================================
# 10.x 委托沟通消息
# ============================================================================


@router.get("/projects/{project_id}/messages", response_model=ApiResponse[list])
def list_messages(project_id: str, db: Session = Depends(get_db)):
    """获取项目沟通消息列表."""
    svc = CommissionManagerService(db)
    return svc.list_messages(project_id)


@router.post("/projects/{project_id}/messages", response_model=ApiResponse[dict], dependencies=[Depends(require_auth)])
def create_message(project_id: str, payload: CreateMessagePayload, db: Session = Depends(get_db)):
    """发送沟通消息."""
    svc = CommissionManagerService(db)
    return svc.create_message(project_id, payload.sender_id, payload.content)


# ============================================================================
# 10.x 里程碑 CRUD
# ============================================================================


@router.get("/projects/{id}/milestones", response_model=ApiResponse[list])
def list_milestones(id: str, db: Session = Depends(get_db)):
    """获取项目里程碑列表."""
    svc = CommissionManagerService(db)
    return svc.list_milestones(id)


@router.post("/projects/{id}/milestones", response_model=ApiResponse[dict], dependencies=[Depends(require_auth)])
def create_milestone(id: str, payload: MilestoneCreate, db: Session = Depends(get_db)):
    """创建里程碑."""
    svc = CommissionManagerService(db)
    return svc.create_milestone(id, payload)


@router.patch("/projects/{id}/milestones/{mid}", response_model=ApiResponse[dict], dependencies=[Depends(require_auth)])
def update_milestone(id: str, mid: str, payload: MilestoneUpdate, db: Session = Depends(get_db)):
    """更新里程碑."""
    svc = CommissionManagerService(db)
    return svc.update_milestone(id, mid, payload)


@router.delete("/projects/{id}/milestones/{mid}", response_model=ApiResponse[dict], dependencies=[Depends(require_auth)])
def delete_milestone(id: str, mid: str, db: Session = Depends(get_db)):
    """删除里程碑."""
    svc = CommissionManagerService(db)
    return svc.delete_milestone(id, mid)


# ============================================================================
# 10.x 收款记录 CRUD
# ============================================================================


@router.get("/projects/{id}/payments", response_model=ApiResponse[list])
def list_payments(id: str, db: Session = Depends(get_db)):
    """获取项目收款记录列表."""
    svc = CommissionManagerService(db)
    return svc.list_payments(id)


@router.post("/projects/{id}/payments", response_model=ApiResponse[dict], dependencies=[Depends(require_auth)])
def create_payment(id: str, payload: PaymentCreate, db: Session = Depends(get_db)):
    """记录收款."""
    svc = CommissionManagerService(db)
    return svc.create_payment(id, payload)


@router.patch("/projects/{id}/payments/{pid}", response_model=ApiResponse[dict], dependencies=[Depends(require_auth)])
def update_payment(id: str, pid: str, payload: PaymentUpdate, db: Session = Depends(get_db)):
    """更新收款记录."""
    svc = CommissionManagerService(db)
    return svc.update_payment(id, pid, payload)


@router.delete("/projects/{id}/payments/{pid}", response_model=ApiResponse[dict], dependencies=[Depends(require_auth)])
def delete_payment(id: str, pid: str, db: Session = Depends(get_db)):
    """删除收款记录."""
    svc = CommissionManagerService(db)
    return svc.delete_payment(id, pid)


# ============================================================================
# 10.x 修改/反馈记录 CRUD
# ============================================================================


@router.get("/projects/{id}/revisions", response_model=ApiResponse[list])
def list_revisions(id: str, db: Session = Depends(get_db)):
    """获取项目修改记录."""
    svc = CommissionManagerService(db)
    return svc.list_revisions(id)


@router.post("/projects/{id}/revisions", response_model=ApiResponse[dict], dependencies=[Depends(require_auth)])
def create_revision(id: str, payload: RevisionCreate, db: Session = Depends(get_db)):
    """记录修改."""
    svc = CommissionManagerService(db)
    return svc.create_revision(id, payload)


@router.delete("/projects/{id}/revisions/{rid}", response_model=ApiResponse[dict], dependencies=[Depends(require_auth)])
def delete_revision(id: str, rid: str, db: Session = Depends(get_db)):
    """删除修改记录."""
    svc = CommissionManagerService(db)
    return svc.delete_revision(id, rid)


# ============================================================================
# 10.x 时间线聚合
# ============================================================================


@router.get("/projects/{id}/timeline", response_model=ApiResponse[list])
def get_timeline(id: str, db: Session = Depends(get_db)):
    """获取项目完整时间线 (里程碑+收款+修改)."""
    svc = CommissionManagerService(db)
    return svc.get_timeline(id)


# ============================================================================
# 10.x 约稿日历
# ============================================================================


@router.get("/calendar", response_model=ApiResponse[dict])
def get_calendar(
    from_date: str = Query(default=None, alias="from"),
    to_date: str = Query(default=None),
    db: Session = Depends(get_db),
):
    """获取约稿日历事件."""
    svc = CommissionManagerService(db)
    return svc.get_calendar(from_date, to_date)


# ============================================================================
# 10.x 仪表盘统计
# ============================================================================


@router.get("/dashboard", response_model=ApiResponse[dict], dependencies=[Depends(require_auth)])
def get_dashboard(db: Session = Depends(get_db)):
    """获取委托项目仪表盘统计."""
    svc = CommissionManagerService(db)
    return svc.get_dashboard()


# ============================================================================
# v2: 佣金余额 + 提现 + 对账单
# ============================================================================


@router.get("/balance", response_model=ApiResponse[dict], dependencies=[Depends(require_auth)])
def get_commission_balance(user_id: str = Depends(require_auth), db: Session = Depends(get_db)):
    """获取可用佣金余额."""
    svc = CommissionManagerService(db)
    return svc.get_commission_balance()


@router.post("/withdraw", response_model=ApiResponse[dict], dependencies=[Depends(require_auth)])
def post_withdraw(data: dict, user_id: str = Depends(require_auth), db: Session = Depends(get_db)):
    """申请佣金提现."""
    svc = CommissionManagerService(db)
    return svc.withdraw(user_id, data.get("amount_yuan", 0), data.get("method", "bank_transfer"), data.get("account_info"))


@router.get("/withdrawals", response_model=ApiResponse[list], dependencies=[Depends(require_auth)])
def get_withdrawals(
    user_id: str = Depends(require_auth),
    status: str = Query(default=None),
    limit: int = Query(default=20),
    db: Session = Depends(get_db),
):
    """提现记录列表."""
    svc = CommissionManagerService(db)
    return svc.get_withdrawals(user_id, status, limit)


@router.get("/statistics/monthly", response_model=ApiResponse[dict], dependencies=[Depends(require_auth)])
def get_monthly_stats(
    user_id: str = Depends(require_auth),
    year: int = Query(default=None),
    db: Session = Depends(get_db),
):
    """月度佣金汇总（对账单）."""
    svc = CommissionManagerService(db)
    return svc.get_monthly_stats(user_id, year)


@router.get("/statistics/yearly", response_model=ApiResponse[dict], dependencies=[Depends(require_auth)])
def get_yearly_stats(
    user_id: str = Depends(require_auth),
    year: int = Query(default=None),
    db: Session = Depends(get_db),
):
    """年度佣金汇总."""
    svc = CommissionManagerService(db)
    return svc.get_yearly_stats(user_id, year)
