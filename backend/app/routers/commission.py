"""委托项目管理 API 路由 — 对应: docs/modules-v3/06-business-management.md
端点: 9 (commission)"""

from datetime import datetime, date, timedelta
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.database import get_db
from app.schemas.common import ApiResponse, PaginatedResponse, PaginationParams
from app.models.commission import (
    CommissionProject,
    CommissionOrder,
    CommissionMessage,
    CommissionMilestone,
    CommissionPayment,
    CommissionRevision,
)
from app.schemas.common import ApiResponse
from app.schemas.commission import (
    MilestoneCreate,
    MilestoneUpdate,
    MilestoneSchema,
    PaymentCreate,
    PaymentUpdate,
    PaymentSchema,
    RevisionCreate,
    RevisionSchema,
    TimelineEvent,
    CalendarEvent,
    DashboardStats,
)
from app.deps import require_auth

router = APIRouter()


# ============================================================================
# Helper functions
# ============================================================================


def _milestone_to_dict(m: CommissionMilestone) -> dict:
    return {
        "id": m.id,
        "commission_id": m.commission_id,
        "name": m.name,
        "status": m.status,
        "due_date": m.due_date.isoformat() if m.due_date else None,
        "description": m.description,
        "order_index": m.order_index,
        "created_at": m.created_at.isoformat() if m.created_at else None,
        "updated_at": m.updated_at.isoformat() if m.updated_at else None,
    }


def _payment_to_dict(p: CommissionPayment) -> dict:
    return {
        "id": p.id,
        "commission_id": p.commission_id,
        "milestone_id": p.milestone_id,
        "amount": float(p.amount) if isinstance(p.amount, Decimal) else p.amount,
        "method": p.method,
        "status": p.status,
        "paid_at": p.paid_at.isoformat() if p.paid_at else None,
        "notes": p.notes,
        "created_at": p.created_at.isoformat() if p.created_at else None,
    }


def _revision_to_dict(r: CommissionRevision) -> dict:
    return {
        "id": r.id,
        "commission_id": r.commission_id,
        "description": r.description,
        "client_feedback": r.client_feedback,
        "files": r.files or [],
        "created_by": r.created_by,
        "created_at": r.created_at.isoformat() if r.created_at else None,
    }


def _order_to_dict(o: CommissionOrder) -> dict:
    return {
        "id": o.id,
        "project_id": o.project_id,
        "order_type": o.order_type,
        "amount": o.amount,
        "status": o.status,
        "created_at": o.created_at.isoformat() if o.created_at else None,
    }


def _msg_to_dict(m: CommissionMessage) -> dict:
    return {
        "id": m.id,
        "project_id": m.project_id,
        "sender_id": m.sender_id,
        "content": m.content,
        "created_at": m.created_at.isoformat() if m.created_at else None,
    }


def _project_to_dict(p: CommissionProject) -> dict:
    """Convert CommissionProject to dict using ORM relationships."""
    return {
        "id": p.id,
        "user_id": p.user_id,
        "title": p.title,
        "description": p.description,
        "client_name": p.client_name,
        "status": p.status,
        "milestones": [_milestone_to_dict(m) for m in (p.milestones or [])],
        "payment_terms": p.payment_terms or [],
        "orders": [_order_to_dict(o) for o in (p.orders or [])],
        "messages": [_msg_to_dict(m) for m in (p.messages or [])],
        "created_at": p.created_at.isoformat() if p.created_at else None,
        "updated_at": p.updated_at.isoformat() if p.updated_at else None,
    }


# ============================================================================
# 10.x 委托项目 CRUD
# ============================================================================


from pydantic import BaseModel, Field


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


@router.get("/commission/projects", response_model=ApiResponse[PaginatedResponse])
def list_projects(
    params: PaginationParams = Query(PaginationParams()),
    user_id: Optional[str] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """获取委托项目列表 (分页)."""
    q = db.query(CommissionProject)
    if user_id:
        q = q.filter(CommissionProject.user_id == user_id)
    if status:
        q = q.filter(CommissionProject.status == status)
    total = q.count()
    projects = (
        q.order_by(CommissionProject.created_at.desc())
        .limit(params.page_size)
        .offset((params.page - 1) * params.page_size)
        .all()
    )
    return ApiResponse(data={
        "items": [
            {
                "id": p.id,
                "title": p.title,
                "description": p.description,
                "client_name": p.client_name,
                "status": p.status,
                "milestones": [_milestone_to_dict(m) for m in (p.milestones or [])],
                "payment_terms": p.payment_terms or [],
                "order_count": len(p.orders) if p.orders else 0,
                "message_count": len(p.messages) if p.messages else 0,
                "created_at": p.created_at.isoformat() if p.created_at else None,
                "updated_at": p.updated_at.isoformat() if p.updated_at else None,
            }
            for p in projects
        ],
        "total": total,
        "page": params.page,
        "page_size": params.page_size,
        "total_pages": (total + params.page_size - 1) // params.page_size if params.page_size else 0,
    })


@router.post("/commission/projects", response_model=ApiResponse[dict], dependencies=[Depends(require_auth)])
def create_project(payload: CreateProjectPayload, db: Session = Depends(get_db)):
    """创建委托项目."""
    project = CommissionProject(
        user_id=payload.user_id,
        title=payload.title,
        description=payload.description,
        client_name=payload.client_name,
        status=payload.status,
        payment_terms=payload.payment_terms or [],
    )
    try:
        db.add(project)
        db.commit()
        db.refresh(project)
    except Exception:
        db.rollback()
        raise
    return ApiResponse(data=_project_to_dict(project), message="项目创建成功")


@router.get("/commission/projects/{project_id}", response_model=ApiResponse[dict])
def get_project(project_id: str, db: Session = Depends(get_db)):
    """获取单个委托项目详情."""
    project = db.query(CommissionProject).filter(CommissionProject.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    return ApiResponse(data=_project_to_dict(project))


@router.put("/commission/projects/{project_id}", response_model=ApiResponse[dict], dependencies=[Depends(require_auth)])
def update_project(project_id: str, payload: UpdateProjectPayload, db: Session = Depends(get_db)):
    """更新委托项目."""
    project = db.query(CommissionProject).filter(CommissionProject.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    update_data = payload.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(project, key, value)
    try:
        db.commit()
        db.refresh(project)
    except Exception:
        db.rollback()
        raise
    return ApiResponse(data=_project_to_dict(project), message="项目更新成功")


@router.delete("/commission/projects/{project_id}", response_model=ApiResponse[dict], dependencies=[Depends(require_auth)])
def delete_project(project_id: str, db: Session = Depends(get_db)):
    """删除委托项目 (级联删除订单、消息、里程碑、收款、修改记录)."""
    project = db.query(CommissionProject).filter(CommissionProject.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    try:
        db.delete(project)
        db.commit()
    except Exception:
        db.rollback()
        raise
    return ApiResponse(data={"success": True}, message="项目已删除")


# ============================================================================
# 10.x 委托订单 CRUD
# ============================================================================


class CreateOrderPayload(BaseModel):
    order_type: str
    amount: float
    status: str = "pending"


@router.get("/commission/projects/{project_id}/orders", response_model=ApiResponse[list])
def list_orders(project_id: str, status: Optional[str] = None, db: Session = Depends(get_db)):
    """获取项目下的订单列表."""
    q = db.query(CommissionOrder).filter(CommissionOrder.project_id == project_id)
    if status:
        q = q.filter(CommissionOrder.status == status)
    orders = q.all()
    return ApiResponse(data=[
        {
            "id": o.id,
            "order_type": o.order_type,
            "amount": o.amount,
            "status": o.status,
            "created_at": o.created_at.isoformat() if o.created_at else None,
        }
        for o in orders
    ])


@router.post("/commission/projects/{project_id}/orders", response_model=ApiResponse[dict], dependencies=[Depends(require_auth)])
def create_order(project_id: str, payload: CreateOrderPayload, db: Session = Depends(get_db)):
    """创建委托订单."""
    project = db.query(CommissionProject).filter(CommissionProject.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    order = CommissionOrder(
        project_id=project_id,
        order_type=payload.order_type,
        amount=payload.amount,
        status=payload.status,
    )
    db.add(order)
    try:
        db.commit()
        db.refresh(order)
    except Exception:
        db.rollback()
        raise
    return ApiResponse(data=_order_to_dict(order), message="订单创建成功")


# ============================================================================
# 10.x 委托沟通消息
# ============================================================================


@router.get("/commission/projects/{project_id}/messages", response_model=ApiResponse[list])
def list_messages(project_id: str, db: Session = Depends(get_db)):
    """获取项目沟通消息列表."""
    msgs = db.query(CommissionMessage).filter(
        CommissionMessage.project_id == project_id
    ).order_by(CommissionMessage.created_at).all()
    return ApiResponse(data=[
        {
            "id": m.id,
            "sender_id": m.sender_id,
            "content": m.content,
            "created_at": m.created_at.isoformat() if m.created_at else None,
        }
        for m in msgs
    ])


class CreateMessagePayload(BaseModel):
    sender_id: str = ""
    content: str


@router.post("/commission/projects/{project_id}/messages", response_model=ApiResponse[dict], dependencies=[Depends(require_auth)])
def create_message(project_id: str, payload: CreateMessagePayload, db: Session = Depends(get_db)):
    """发送沟通消息."""
    project = db.query(CommissionProject).filter(CommissionProject.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    msg = CommissionMessage(
        project_id=project_id,
        sender_id=payload.sender_id,
        content=payload.content,
    )
    db.add(msg)
    try:
        db.commit()
        db.refresh(msg)
    except Exception:
        db.rollback()
        raise
    return ApiResponse(data=_msg_to_dict(msg), message="消息发送成功")


# ============================================================================
# 10.x 里程碑 CRUD
# ============================================================================


@router.get("/commission/projects/{id}/milestones", response_model=ApiResponse[list])
def list_milestones(id: str, db: Session = Depends(get_db)):
    """获取项目里程碑列表."""
    project = db.query(CommissionProject).filter(CommissionProject.id == id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    milestones = (
        db.query(CommissionMilestone)
        .filter(CommissionMilestone.commission_id == id)
        .order_by(CommissionMilestone.order_index)
        .all()
    )
    return ApiResponse(data=[_milestone_to_dict(m) for m in milestones])


@router.post("/commission/projects/{id}/milestones", response_model=ApiResponse[dict], dependencies=[Depends(require_auth)])
def create_milestone(id: str, payload: MilestoneCreate, db: Session = Depends(get_db)):
    """创建里程碑."""
    project = db.query(CommissionProject).filter(CommissionProject.id == id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    due_date = None
    if payload.due_date:
        try:
            due_date = datetime.fromisoformat(payload.due_date)
        except ValueError:
            due_date = datetime.strptime(payload.due_date, "%Y-%m-%d")
    milestone = CommissionMilestone(
        commission_id=id,
        name=payload.name,
        status="pending",
        due_date=due_date,
        description=payload.description,
        order_index=payload.order_index,
    )
    db.add(milestone)
    try:
        db.commit()
        db.refresh(milestone)
    except Exception:
        db.rollback()
        raise
    return ApiResponse(data=_milestone_to_dict(milestone), message="里程碑创建成功")


@router.patch("/commission/projects/{id}/milestones/{mid}", response_model=ApiResponse[dict], dependencies=[Depends(require_auth)])
def update_milestone(id: str, mid: str, payload: MilestoneUpdate, db: Session = Depends(get_db)):
    """更新里程碑."""
    milestone = (
        db.query(CommissionMilestone)
        .filter(CommissionMilestone.id == mid, CommissionMilestone.commission_id == id)
        .first()
    )
    if not milestone:
        raise HTTPException(status_code=404, detail="里程碑不存在")
    for key, value in payload.model_dump(exclude_unset=True).items():
        if key == "due_date" and value:
            try:
                value = datetime.fromisoformat(value)
            except ValueError:
                value = datetime.strptime(value, "%Y-%m-%d")
        setattr(milestone, key, value)
    try:
        db.commit()
        db.refresh(milestone)
    except Exception:
        db.rollback()
        raise
    return ApiResponse(data=_milestone_to_dict(milestone), message="里程碑更新成功")


@router.delete("/commission/projects/{id}/milestones/{mid}", response_model=ApiResponse[dict], dependencies=[Depends(require_auth)])
def delete_milestone(id: str, mid: str, db: Session = Depends(get_db)):
    """删除里程碑."""
    milestone = (
        db.query(CommissionMilestone)
        .filter(CommissionMilestone.id == mid, CommissionMilestone.commission_id == id)
        .first()
    )
    if not milestone:
        raise HTTPException(status_code=404, detail="里程碑不存在")
    try:
        db.delete(milestone)
        db.commit()
    except Exception:
        db.rollback()
        raise
    return ApiResponse(data={"success": True}, message="里程碑已删除")


# ============================================================================
# 10.x 收款记录 CRUD
# ============================================================================


@router.get("/commission/projects/{id}/payments", response_model=ApiResponse[list])
def list_payments(id: str, db: Session = Depends(get_db)):
    """获取项目收款记录列表."""
    project = db.query(CommissionProject).filter(CommissionProject.id == id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    payments = (
        db.query(CommissionPayment)
        .filter(CommissionPayment.commission_id == id)
        .order_by(CommissionPayment.created_at.desc())
        .all()
    )
    return ApiResponse(data=[_payment_to_dict(p) for p in payments])


@router.post("/commission/projects/{id}/payments", response_model=ApiResponse[dict], dependencies=[Depends(require_auth)])
def create_payment(id: str, payload: PaymentCreate, db: Session = Depends(get_db)):
    """记录收款."""
    project = db.query(CommissionProject).filter(CommissionProject.id == id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    payment = CommissionPayment(
        commission_id=id,
        milestone_id=payload.milestone_id,
        amount=Decimal(str(payload.amount)),
        method=payload.method,
        status=payload.status or "pending",
        notes=payload.notes,
    )
    db.add(payment)
    try:
        db.commit()
        db.refresh(payment)
    except Exception:
        db.rollback()
        raise
    return ApiResponse(data=_payment_to_dict(payment), message="收款记录创建成功")


@router.patch("/commission/projects/{id}/payments/{pid}", response_model=ApiResponse[dict], dependencies=[Depends(require_auth)])
def update_payment(id: str, pid: str, payload: PaymentUpdate, db: Session = Depends(get_db)):
    """更新收款记录."""
    payment = (
        db.query(CommissionPayment)
        .filter(CommissionPayment.id == pid, CommissionPayment.commission_id == id)
        .first()
    )
    if not payment:
        raise HTTPException(status_code=404, detail="收款记录不存在")
    data = payload.model_dump(exclude_unset=True)
    if "paid_at" in data and data["paid_at"]:
        try:
            data["paid_at"] = datetime.fromisoformat(data["paid_at"])
        except ValueError:
            data["paid_at"] = datetime.strptime(data["paid_at"], "%Y-%m-%d")
    if "amount" in data and data["amount"] is not None:
        data["amount"] = Decimal(str(data["amount"]))
    for key, value in data.items():
        setattr(payment, key, value)
    try:
        db.commit()
        db.refresh(payment)
    except Exception:
        db.rollback()
        raise
    return ApiResponse(data=_payment_to_dict(payment), message="收款记录更新成功")


@router.delete("/commission/projects/{id}/payments/{pid}", response_model=ApiResponse[dict], dependencies=[Depends(require_auth)])
def delete_payment(id: str, pid: str, db: Session = Depends(get_db)):
    """删除收款记录."""
    payment = (
        db.query(CommissionPayment)
        .filter(CommissionPayment.id == pid, CommissionPayment.commission_id == id)
        .first()
    )
    if not payment:
        raise HTTPException(status_code=404, detail="收款记录不存在")
    try:
        db.delete(payment)
        db.commit()
    except Exception:
        db.rollback()
        raise
    return ApiResponse(data={"success": True}, message="收款记录已删除")


# ============================================================================
# 10.x 修改/反馈记录 CRUD
# ============================================================================


@router.get("/commission/projects/{id}/revisions", response_model=ApiResponse[list])
def list_revisions(id: str, db: Session = Depends(get_db)):
    """获取项目修改记录."""
    project = db.query(CommissionProject).filter(CommissionProject.id == id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    revisions = (
        db.query(CommissionRevision)
        .filter(CommissionRevision.commission_id == id)
        .order_by(CommissionRevision.created_at.desc())
        .all()
    )
    return ApiResponse(data=[_revision_to_dict(r) for r in revisions])


@router.post("/commission/projects/{id}/revisions", response_model=ApiResponse[dict], dependencies=[Depends(require_auth)])
def create_revision(id: str, payload: RevisionCreate, db: Session = Depends(get_db)):
    """记录修改."""
    project = db.query(CommissionProject).filter(CommissionProject.id == id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    revision = CommissionRevision(
        commission_id=id,
        description=payload.description,
        client_feedback=payload.client_feedback,
        files=payload.files,
        created_by=payload.created_by,
    )
    db.add(revision)
    try:
        db.commit()
        db.refresh(revision)
    except Exception:
        db.rollback()
        raise
    return ApiResponse(data=_revision_to_dict(revision), message="修改记录创建成功")


@router.delete("/commission/projects/{id}/revisions/{rid}", response_model=ApiResponse[dict], dependencies=[Depends(require_auth)])
def delete_revision(id: str, rid: str, db: Session = Depends(get_db)):
    """删除修改记录."""
    revision = (
        db.query(CommissionRevision)
        .filter(CommissionRevision.id == rid, CommissionRevision.commission_id == id)
        .first()
    )
    if not revision:
        raise HTTPException(status_code=404, detail="修改记录不存在")
    try:
        db.delete(revision)
        db.commit()
    except Exception:
        db.rollback()
        raise
    return ApiResponse(data={"success": True}, message="修改记录已删除")


# ============================================================================
# 10.x 时间线聚合
# ============================================================================


@router.get("/commission/projects/{id}/timeline", response_model=ApiResponse[list])
def get_timeline(id: str, db: Session = Depends(get_db)):
    """获取项目完整时间线 (里程碑+收款+修改)."""
    project = db.query(CommissionProject).filter(CommissionProject.id == id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    events: list[dict] = []

    milestones = (
        db.query(CommissionMilestone)
        .filter(CommissionMilestone.commission_id == id)
        .order_by(CommissionMilestone.created_at)
        .all()
    )
    for m in milestones:
        events.append({
            "type": "milestone",
            "id": m.id,
            "title": m.name,
            "description": m.description,
            "date": (m.due_date or m.created_at).isoformat() if (m.due_date or m.created_at) else None,
            "status": m.status,
        })

    payments = (
        db.query(CommissionPayment)
        .filter(CommissionPayment.commission_id == id)
        .order_by(CommissionPayment.created_at)
        .all()
    )
    for p in payments:
        events.append({
            "type": "payment",
            "id": p.id,
            "title": f"收款 ¥{float(p.amount)}",
            "description": p.notes,
            "date": (p.paid_at or p.created_at).isoformat() if (p.paid_at or p.created_at) else None,
            "status": p.status,
        })

    revisions = (
        db.query(CommissionRevision)
        .filter(CommissionRevision.commission_id == id)
        .order_by(CommissionRevision.created_at)
        .all()
    )
    for r in revisions:
        events.append({
            "type": "revision",
            "id": r.id,
            "title": "修改记录",
            "description": r.description,
            "date": r.created_at.isoformat() if r.created_at else None,
            "status": r.created_by,
        })

    events.sort(key=lambda e: e["date"] or "", reverse=False)
    return ApiResponse(data=events)


# ============================================================================
# 10.x 约稿日历
# ============================================================================


@router.get("/commission/calendar", response_model=ApiResponse[dict])
def get_calendar(
    from_date: str = Query(default=None, alias="from"),
    to_date: str = Query(default=None),
    db: Session = Depends(get_db),
):
    """获取约稿日历事件."""
    start = datetime.strptime(from_date, "%Y-%m-%d").date() if from_date else date.today() - timedelta(days=30)
    end = datetime.strptime(to_date, "%Y-%m-%d").date() if to_date else date.today() + timedelta(days=30)

    projects = (
        db.query(CommissionProject)
        .filter(CommissionProject.status != "settlement")
        .all()
    )

    events: list[dict] = []
    for p in projects:
        milestones = (
            db.query(CommissionMilestone)
            .filter(CommissionMilestone.commission_id == p.id)
            .all()
        )
        for m in milestones:
            if m.due_date and m.due_date.date() >= start and m.due_date.date() <= end:
                events.append({
                    "id": m.id,
                    "title": f"{p.title} - {m.name}",
                    "date": m.due_date.isoformat(),
                    "type": "milestone_due",
                })

        payments = (
            db.query(CommissionPayment)
            .filter(CommissionPayment.commission_id == p.id)
            .all()
        )
        for pay in payments:
            if pay.paid_at and pay.paid_at.date() >= start and pay.paid_at.date() <= end:
                events.append({
                    "id": pay.id,
                    "title": f"{p.title} - 收款 ¥{float(pay.amount)}",
                    "date": pay.paid_at.isoformat(),
                    "type": "payment_received",
                })

    return ApiResponse(data={"events": events})


# ============================================================================
# 10.x 仪表盘统计
# ============================================================================


@router.get("/commission/dashboard", response_model=ApiResponse[dict], dependencies=[Depends(require_auth)])
def get_dashboard(db: Session = Depends(get_db)):
    """获取委托项目仪表盘统计."""
    active_projects = (
        db.query(CommissionProject)
        .filter(CommissionProject.status.in_(["proposal", "production", "delivery"]))
        .all()
    )
    active_count = len(active_projects)

    pending_payments = (
        db.query(CommissionPayment)
        .filter(CommissionPayment.status.in_(["pending", "partial"]))
        .all()
    )
    pending_payment_count = len(pending_payments)

    now = datetime.utcnow()
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    received = (
        db.query(CommissionPayment)
        .filter(CommissionPayment.status == "received")
        .all()
    )
    monthly_revenue = sum(float(p.amount) for p in received if p.paid_at and p.paid_at >= month_start)

    total_amount = sum(
        float(p.amount)
        for p in received
    )
    avg_ticket = total_amount / len(received) if received else 0.0

    return ApiResponse(data={
        "active_count": active_count,
        "pending_payment": pending_payment_count,
        "monthly_revenue": round(monthly_revenue, 2),
        "avg_ticket": round(avg_ticket, 2),
    })
