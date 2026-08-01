"""微信小程序专用 API 路由."""

from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user_id, require_auth
from app.models.contract import ContractInstance
from app.models.work import Work
from app.models.system import Notification
from app.utils.audit import AuditLog

router = APIRouter(prefix="/api/v1", tags=["mini-program"])


# ── 作品 ──────────────────────────────────────────────────────────

@router.get("/works/my", response_model=list[dict])
def get_my_works(
    limit: int = Query(default=20, le=100),
    offset: int = 0,
    user_id: str = Depends(require_auth),
    db: Session = Depends(get_db),
):
    """获取我的作品列表."""
    works = (
        db.query(Work)
        .filter(Work.created_by == user_id)
        .order_by(Work.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    return [
        {
            "id": w.id,
            "title": w.title,
            "thumbnail": w.thumbnail_path,
            "category": w.file_type or "",
            "created_at": w.created_at.isoformat() if w.created_at else None,
        }
        for w in works
    ]


@router.get("/works/{work_id}", response_model=dict)
def get_work_detail(
    work_id: str,
    user_id: str = Depends(require_auth),
    db: Session = Depends(get_db),
):
    """获取作品详情."""
    work = db.query(Work).filter(Work.id == work_id).first()
    if not work:
        raise HTTPException(status_code=404, detail="作品不存在")
    return {
        "id": work.id,
        "title": work.title,
        "description": work.description or "",
        "thumbnail": work.thumbnail_path,
        "category": work.file_type or "",
        "tags": [t.tag for t in work.tags] if work.tags else [],
        "creator_name": work.created_by or "",
        "created_at": work.created_at.isoformat() if work.created_at else None,
    }


# ── 合约 ──────────────────────────────────────────────────────────

@router.get("/contracts/my", response_model=list[dict])
def get_my_contracts(
    status: str | None = None,
    limit: int = Query(default=20, le=100),
    offset: int = 0,
    actor_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """获取我的合约列表（创建者或交易方）."""
    query = db.query(ContractInstance).filter(
        (ContractInstance.creator_id == actor_id) |
        (ContractInstance.trader_id == actor_id)
    )
    if status:
        query = query.filter(ContractInstance.status == status)
    contracts = query.order_by(ContractInstance.created_at.desc()).offset(offset).limit(limit).all()
    return [
        {
            "id": c.id,
            "title": c.title,
            "contract_type": c.contract_type,
            "total_amount": float(c.total_amount),
            "currency": c.currency,
            "status": c.status,
            "created_at": c.created_at.isoformat() if c.created_at else None,
        }
        for c in contracts
    ]


@router.get("/contracts/{contract_id}", response_model=dict)
def get_contract_detail(
    contract_id: str,
    actor_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """获取合约详情."""
    contract = db.query(ContractInstance).filter(
        ContractInstance.id == contract_id
    ).first()
    if not contract:
        raise HTTPException(status_code=404, detail="合约不存在")
    # 权限校验
    if contract.creator_id != actor_id and contract.trader_id != actor_id:
        raise HTTPException(status_code=403, detail="无权查看此合约")
    return {
        "id": contract.id,
        "title": contract.title,
        "description": contract.description or "",
        "contract_type": contract.contract_type,
        "total_amount": float(contract.total_amount),
        "currency": contract.currency,
        "status": contract.status,
        "scope_usage": contract.scope_usage,
        "scope_geography": contract.scope_geography,
        "created_at": contract.created_at.isoformat() if contract.created_at else None,
    }


# ── 通知 ──────────────────────────────────────────────────────────

@router.get("/notifications", response_model=list[dict])
def get_my_notifications(
    limit: int = Query(default=20, le=50),
    user_id: str = Depends(require_auth),
    db: Session = Depends(get_db),
):
    """获取我的通知."""
    has_type_col = False
    try:
        cols = [r[1] for r in db.execute(
            text("PRAGMA table_info(notifications)")
        ).fetchall()]
        has_type_col = "type" in cols
    except Exception:
        pass

    query = db.query(Notification)
    if has_type_col:
        query = query.filter(Notification.type.in_(["system", "contract", "message"]))
    notifs = query.order_by(Notification.created_at.desc()).limit(limit).all()

    return [
        {
            "id": n.id,
            "title": n.title,
            "body": n.content or "",
            "type": n.type if has_type_col else "system",
            "created_at": n.created_at.isoformat() if n.created_at else None,
        }
        for n in notifs
    ]


@router.get("/notifications/unread-count", response_model=dict)
def get_unread_notification_count(
    user_id: str = Depends(require_auth),
    db: Session = Depends(get_db),
):
    """获取未读通知数量."""
    try:
        count = db.query(Notification).filter(
            Notification.is_read == False,  # noqa: E712
            Notification.target_user_id == user_id
        ).count()
    except Exception:
        count = 0
    return {"count": count}


# ── 聊天 ──────────────────────────────────────────────────────────

@router.get("/messages/sessions", response_model=list[dict])
def get_message_sessions(
    limit: int = Query(default=50, le=100),
    user_id: str = Depends(require_auth),
    db: Session = Depends(get_db),
):
    """获取我的聊天会话列表."""
    # 简化实现：返回系统通知作为消息会话
    return [
        {
            "id": f"system_{i}",
            "other_user_name": "系统通知",
            "last_message": "欢迎使用OriSpark",
            "last_message_at": datetime.now(timezone.utc).isoformat(),
        }
        for i in range(3)
    ]


@router.get("/messages/sessions/{session_id}/messages", response_model=list[dict])
def get_session_messages(
    session_id: str,
    limit: int = Query(default=50, le=100),
    user_id: str = Depends(require_auth),
    db: Session = Depends(get_db),
):
    """获取会话消息列表."""
    # 简化实现：返回空列表
    return []


@router.post("/messages/sessions/{session_id}/messages", response_model=dict)
def send_message(
    session_id: str,
    body: dict,
    user_id: str = Depends(require_auth),
    db: Session = Depends(get_db),
):
    """发送消息."""
    content = body.get("content", "")
    return {
        "id": f"msg_{datetime.now(timezone.utc).timestamp()}",
        "content": content,
        "sender_id": user_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }


# ── 任务 ──────────────────────────────────────────────────────────

@router.get("/tasks/pending", response_model=list[dict])
def get_pending_tasks(
    user_id: str = Depends(require_auth),
    db: Session = Depends(get_db),
):
    """获取待办任务列表."""
    # 简化实现：返回空列表（可根据实际需求扩展）
    return []
