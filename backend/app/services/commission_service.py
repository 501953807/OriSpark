"""委托管理服务."""

from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session

from app.models.commission import (
    CommissionProject, CommissionOrder, CommissionMessage, VALID_STATUSES,
)


def _apply_update(model: object, data: dict) -> None:
    """将字典中的键值设置到模型实例上."""
    for key, value in data.items():
        if value is not None:
            setattr(model, key, value)


# ============================================================================
# Project CRUD
# ============================================================================

def create_project(db: Session, user_id: str, title: str,
                   description: Optional[str] = None, client_name: Optional[str] = None,
                   status: str = "brief", milestones: Optional[list] = None,
                   payment_terms: Optional[list] = None) -> CommissionProject:
    """创建委托项目."""
    project = CommissionProject(
        user_id=user_id,
        title=title,
        description=description,
        client_name=client_name,
        status=status,
        milestones=milestones if milestones is not None else None,
        payment_terms=payment_terms,
    )


def list_projects(db: Session, user_id: Optional[str] = None,
                  status: Optional[str] = None) -> list[CommissionProject]:
    """列出委托项目."""
    query = db.query(CommissionProject)
    if user_id:
        query = query.filter(CommissionProject.user_id == user_id)
    if status:
        query = query.filter(CommissionProject.status == status)
    return query.order_by(CommissionProject.created_at.desc()).all()


def get_project(db: Session, project_id: str) -> Optional[CommissionProject]:
    """获取委托项目."""
    return db.query(CommissionProject).filter(CommissionProject.id == project_id).first()


def update_project(db: Session, project_id: str, data: dict) -> Optional[CommissionProject]:
    """更新委托项目."""
    project = get_project(db, project_id)
    if not project:
        return None
    updatable = ("title", "description", "client_name", "milestones", "payment_terms")
    for key in updatable:
        if key in data:
            setattr(project, key, data[key])
    db.commit()
    db.refresh(project)
    return project


def delete_project(db: Session, project_id: str) -> bool:
    """删除委托项目."""
    project = get_project(db, project_id)
    if not project:
        return False
    db.delete(project)
    db.commit()
    return True


# ============================================================================
# Order CRUD
# ============================================================================

def create_order(db: Session, project_id: str, order_type: str, amount: float,
                 status: str = "pending") -> CommissionOrder:
    """创建委托订单."""
    if not get_project(db, project_id):
        raise ValueError(f"委托项目不存在: {project_id}")
    order = CommissionOrder(
        project_id=project_id,
        order_type=order_type,
        amount=amount,
        status=status,
    )
    db.add(order)
    db.commit()
    db.refresh(order)
    return order


def list_orders(db: Session, project_id: str) -> list[CommissionOrder]:
    """列出委托项目的订单."""
    return (
        db.query(CommissionOrder)
        .filter(CommissionOrder.project_id == project_id)
        .order_by(CommissionOrder.created_at.desc())
        .all()
    )


def get_order(db: Session, order_id: str) -> Optional[CommissionOrder]:
    """获取委托订单."""
    return db.query(CommissionOrder).filter(CommissionOrder.id == order_id).first()


def update_order(db: Session, order_id: str, data: dict) -> Optional[CommissionOrder]:
    """更新委托订单."""
    order = get_order(db, order_id)
    if not order:
        return None
    for key in ("order_type", "amount", "status"):
        if key in data:
            setattr(order, key, data[key])
    db.commit()
    db.refresh(order)
    return order


def delete_order(db: Session, order_id: str) -> bool:
    """删除委托订单."""
    order = get_order(db, order_id)
    if not order:
        return False
    db.delete(order)
    db.commit()
    return True


# ============================================================================
# Message CRUD
# ============================================================================

def create_message(db: Session, project_id: str, sender_id: str,
                   content: str) -> CommissionMessage:
    """创建沟通消息."""
    if not get_project(db, project_id):
        raise ValueError(f"委托项目不存在: {project_id}")
    message = CommissionMessage(
        project_id=project_id,
        sender_id=sender_id,
        content=content,
    )
    db.add(message)
    db.commit()
    db.refresh(message)
    return message


def list_messages(db: Session, project_id: str) -> list[CommissionMessage]:
    """列出委托项目的消息."""
    return (
        db.query(CommissionMessage)
        .filter(CommissionMessage.project_id == project_id)
        .order_by(CommissionMessage.created_at.asc())
        .all()
    )


# ============================================================================
# State Machine
# ============================================================================

_STATUS_TRANSITIONS = {
    "brief": ["proposal"],
    "proposal": ["production", "brief"],
    "production": ["delivery"],
    "delivery": ["settlement"],
    "settlement": [],  # terminal
}


def transition_project_status(db: Session, project_id: str, new_status: str) -> Optional[CommissionProject]:
    """转换委托项目状态.

    允许的状态流转:
      brief -> proposal
      proposal -> production / brief
      production -> delivery
      delivery -> settlement
    """
    project = get_project(db, project_id)
    if not project:
        return None
    if new_status not in VALID_STATUSES:
        raise ValueError(f"无效的状态: {new_status}")
    allowed = _STATUS_TRANSITIONS.get(project.status, [])
    if new_status not in allowed:
        raise ValueError(
            f"不允许的状态流转: {project.status} -> {new_status}"
        )
    project.status = new_status
    db.commit()
    db.refresh(project)
    return project


# ============================================================================
# Milestone Helpers
# ============================================================================


def add_milestone(db: Session, project_id: str, title: str,
                  description: Optional[str] = None,
                  due_date: Optional[str] = None) -> CommissionProject:
    """向项目的里程碑列表中添加一项."""
    project = get_project(db, project_id)
    if not project:
        return None
    milestones = project.milestones or []
    milestones.append({
        "title": title,
        "description": description,
        "due_date": due_date,
        "completed": False,
        "completed_at": None,
    })
    project.milestones = milestones
    db.commit()
    db.refresh(project)
    return project


def complete_milestone(db: Session, project_id: str, milestone_index: int) -> CommissionProject:
    """标记里程碑为已完成."""
    project = get_project(db, project_id)
    if not project:
        return None
    milestones = project.milestones or []
    if milestone_index < 0 or milestone_index >= len(milestones):
        raise ValueError(f"里程碑索引越界: {milestone_index}")
    milestones[milestone_index]["completed"] = True
    milestones[milestone_index]["completed_at"] = datetime.utcnow().isoformat()
    project.milestones = milestones
    db.commit()
    db.refresh(project)
    return project


def list_project_with_details(db: Session, project_id: str) -> Optional[dict]:
    """获取项目详情 (含订单和消息)."""
    project = get_project(db, project_id)
    if not project:
        return None
    return {
        "id": project.id,
        "user_id": project.user_id,
        "title": project.title,
        "description": project.description,
        "client_name": project.client_name,
        "status": project.status,
        "milestones": project.milestones,
        "payment_terms": project.payment_terms,
        "orders": [
            {
                "id": o.id, "order_type": o.order_type,
                "amount": o.amount, "status": o.status,
                "created_at": o.created_at.isoformat() if o.created_at else None,
            }
            for o in project.orders
        ],
        "messages": [
            {
                "id": m.id, "sender_id": m.sender_id,
                "content": m.content,
                "created_at": m.created_at.isoformat() if m.created_at else None,
            }
            for m in project.messages
        ],
        "created_at": project.created_at.isoformat() if project.created_at else None,
        "updated_at": project.updated_at.isoformat() if project.updated_at else None,
    }
