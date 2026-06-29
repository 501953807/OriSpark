"""委托项目管理 API 路由 — 对应: docs/modules-v3/06-business-management.md
端点: 9 (commission)"""

from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional

from app.database import get_db
from app.models.commission import CommissionProject, CommissionOrder, CommissionMessage
from app.schemas.common import ApiResponse
from app.deps import require_auth

router = APIRouter()


# ============================================================================
# 10.x 委托项目 CRUD
# ============================================================================


@router.get("/commission/projects", response_model=ApiResponse[list])
def list_projects(
    user_id: Optional[str] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """获取委托项目列表."""
    q = db.query(CommissionProject)
    if user_id:
        q = q.filter(CommissionProject.user_id == user_id)
    if status:
        q = q.filter(CommissionProject.status == status)
    projects = q.order_by(CommissionProject.created_at.desc()).all()
    return ApiResponse(data=[
        {
            "id": p.id,
            "title": p.title,
            "description": p.description,
            "client_name": p.client_name,
            "status": p.status,
            "milestones": p.milestones or [],
            "payment_terms": p.payment_terms or [],
            "order_count": len(p.orders),
            "message_count": len(p.messages),
            "created_at": p.created_at.isoformat() if p.created_at else None,
            "updated_at": p.updated_at.isoformat() if p.updated_at else None,
        }
        for p in projects
    ])


@router.post("/commission/projects", response_model=ApiResponse[dict], dependencies=[Depends(require_auth)])
def create_project(payload: dict, db: Session = Depends(get_db)):
    """创建委托项目."""
    title = payload.get("title")
    if not title:
        raise HTTPException(status_code=400, detail="title is required")
    project = CommissionProject(
        user_id=payload.get("user_id", ""),
        title=title,
        description=payload.get("description"),
        client_name=payload.get("client_name"),
        status=payload.get("status", "brief"),
        milestones=payload.get("milestones", []),
        payment_terms=payload.get("payment_terms", []),
    )
    db.add(project)
    db.commit()
    db.refresh(project)
    return ApiResponse(data=_project_to_dict(project), message="项目创建成功")


@router.get("/commission/projects/{project_id}", response_model=ApiResponse[dict])
def get_project(project_id: str, db: Session = Depends(get_db)):
    """获取单个委托项目详情."""
    project = db.query(CommissionProject).filter(CommissionProject.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    return ApiResponse(data=_project_to_dict(project))


@router.put("/commission/projects/{project_id}", response_model=ApiResponse[dict], dependencies=[Depends(require_auth)])
def update_project(project_id: str, payload: dict, db: Session = Depends(get_db)):
    """更新委托项目."""
    project = db.query(CommissionProject).filter(CommissionProject.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    for key in ("title", "description", "client_name", "status", "milestones", "payment_terms"):
        if key in payload:
            setattr(project, key, payload[key])
    db.commit()
    db.refresh(project)
    return ApiResponse(data=_project_to_dict(project), message="项目更新成功")


@router.delete("/commission/projects/{project_id}", response_model=ApiResponse[dict], dependencies=[Depends(require_auth)])
def delete_project(project_id: str, db: Session = Depends(get_db)):
    """删除委托项目 (级联删除订单和消息)."""
    project = db.query(CommissionProject).filter(CommissionProject.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    db.delete(project)
    db.commit()
    return ApiResponse(data={"success": True}, message="项目已删除")


# ============================================================================
# 10.x 委托订单 CRUD
# ============================================================================


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
def create_order(project_id: str, payload: dict, db: Session = Depends(get_db)):
    """创建委托订单."""
    project = db.query(CommissionProject).filter(CommissionProject.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    order_type = payload.get("order_type")
    amount = payload.get("amount")
    if not order_type or amount is None:
        raise HTTPException(status_code=400, detail="order_type and amount are required")
    order = CommissionOrder(
        project_id=project_id,
        order_type=order_type,
        amount=float(amount),
        status=payload.get("status", "pending"),
    )
    db.add(order)
    db.commit()
    db.refresh(order)
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


@router.post("/commission/projects/{project_id}/messages", response_model=ApiResponse[dict], dependencies=[Depends(require_auth)])
def create_message(project_id: str, payload: dict, db: Session = Depends(get_db)):
    """发送沟通消息."""
    project = db.query(CommissionProject).filter(CommissionProject.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    sender_id = payload.get("sender_id", "")
    content = payload.get("content")
    if not content:
        raise HTTPException(status_code=400, detail="content is required")
    msg = CommissionMessage(
        project_id=project_id,
        sender_id=sender_id,
        content=content,
    )
    db.add(msg)
    db.commit()
    db.refresh(msg)
    return ApiResponse(data=_msg_to_dict(msg), message="消息发送成功")


def _project_to_dict(p: CommissionProject) -> dict:
    return {
        "id": p.id,
        "user_id": p.user_id,
        "title": p.title,
        "description": p.description,
        "client_name": p.client_name,
        "status": p.status,
        "milestones": p.milestones or [],
        "payment_terms": p.payment_terms or [],
        "orders": [_order_to_dict(o) for o in p.orders],
        "messages": [_msg_to_dict(m) for m in p.messages],
        "created_at": p.created_at.isoformat() if p.created_at else None,
        "updated_at": p.updated_at.isoformat() if p.updated_at else None,
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
