"""运营合作路由 — 运营者发起合作要约 / 创作者接受或拒绝."""

from datetime import datetime, timezone, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Header
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.operation_cooperation import OperationCooperation
from app.models.system import User as UserModel
from app.models.work import Work
from app.deps import require_operator, require_creator
from app.utils.audit import AuditLog

router = APIRouter(prefix="/operator/operations", tags=["operation-cooperation"])


class ProposeRequest(BaseModel):
    work_id: str
    scope: dict
    notes: Optional[str] = None


@router.post("/propose", response_model=dict)
def propose_cooperation(
    body: ProposeRequest,
    db: Session = Depends(get_db),
    operator: UserModel = Depends(require_operator),
):
    """运营者向创作者发起合作要约."""
    from app.models.work import Work
    work = db.query(Work).filter(Work.id == body.work_id).first()
    if not work:
        raise HTTPException(404, "作品不存在")
    if work.creator_id == operator.id:
        raise HTTPException(400, "不能对自己拥有的作品发起合作")

    # 检查是否已有 pending 要约
    existing = db.query(OperationCooperation).filter(
        OperationCooperation.work_id == body.work_id,
        OperationCooperation.creator_id == work.creator_id,
        OperationCooperation.status == "pending"
    ).first()
    if existing:
        raise HTTPException(400, "该作品已有待处理的合作要约")

    expires_at = datetime.now(timezone.utc) + timedelta(days=30)
    coop = OperationCooperation(
        work_id=body.work_id,
        operator_id=operator.id,
        creator_id=work.creator_id,
        scope=body.scope,
        notes=body.notes,
        expires_at=expires_at,
    )
    db.add(coop)
    db.commit()
    db.refresh(coop)
    AuditLog.log(db, "propose_cooperation", f"Operator {operator.id} proposed to creator {coop.creator_id} on work {coop.work_id}", operator.id)
    return {
        "id": coop.id,
        "work_id": coop.work_id,
        "creator_id": coop.creator_id,
        "status": coop.status,
        "scope": coop.scope,
        "expires_at": coop.expires_at.isoformat() if coop.expires_at else None,
        "created_at": coop.created_at.isoformat(),
    }


@router.get("", response_model=list[dict])
def list_operator_operations(
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    operator: UserModel = Depends(require_operator),
):
    """运营者查看我的合作要约列表."""
    query = db.query(OperationCooperation).filter(OperationCooperation.operator_id == operator.id)
    if status:
        query = query.filter(OperationCooperation.status == status)
    operations = query.order_by(OperationCooperation.created_at.desc()).all()
    return [
        {
            "id": o.id,
            "work_id": o.work_id,
            "creator_id": o.creator_id,
            "status": o.status,
            "scope": o.scope,
            "notes": o.notes,
            "created_at": o.created_at.isoformat() if o.created_at else None,
            "expires_at": o.expires_at.isoformat() if o.expires_at else None,
        }
        for o in operations
    ]


# -- 创作者接受/拒绝 --

@router.get("/creator/pending", response_model=list[dict])
def list_creator_pending(
    db: Session = Depends(get_db),
    creator: UserModel = Depends(require_creator),
):
    """创作者查看待处理的合作请求."""
    operations = (
        db.query(OperationCooperation)
        .filter(
            OperationCooperation.creator_id == creator.id,
            OperationCooperation.status == "pending",
        )
        .order_by(OperationCooperation.created_at.desc())
        .all()
    )
    return [
        {
            "id": o.id,
            "work_id": o.work_id,
            "operator_id": o.operator_id,
            "operator_name": o.operator.username if o.operator else "未知",
            "status": o.status,
            "scope": o.scope,
            "notes": o.notes,
            "created_at": o.created_at.isoformat() if o.created_at else None,
            "expires_at": o.expires_at.isoformat() if o.expires_at else None,
        }
        for o in operations
    ]


@router.post("/creator/accept/{id}", response_model=dict)
def accept_cooperation(
    id: str,
    db: Session = Depends(get_db),
    creator: UserModel = Depends(require_creator),
):
    """创作者接受合作要约 → 自动创建 ContractInstance."""
    coop = (
        db.query(OperationCooperation)
        .filter(
            OperationCooperation.id == id,
            OperationCooperation.creator_id == creator.id,
            OperationCooperation.status == "pending",
        )
        .first()
    )
    if not coop:
        raise HTTPException(404, "合作要约不存在或已处理")

    # 检查是否已过期
    if coop.expires_at and coop.expires_at < datetime.now(timezone.utc):
        coop.status = "expired"
        db.commit()
        raise HTTPException(400, "合作要约已过期")

    coop.status = "accepted"
    coop.accepted_at = datetime.now(timezone.utc)
    db.commit()
    AuditLog.log(db, "accept_cooperation", f"Creator {creator.id} accepted cooperation {id}", creator.id)

    return {
        "id": coop.id,
        "work_id": coop.work_id,
        "status": coop.status,
        "accepted_at": coop.accepted_at.isoformat(),
        "message": "合作要约已接受，合约将在后续流程中生成",
    }


@router.post("/creator/reject/{id}", response_model=dict)
def reject_cooperation(
    id: str,
    db: Session = Depends(get_db),
    creator: UserModel = Depends(require_creator),
):
    """创作者拒绝合作要约."""
    coop = (
        db.query(OperationCooperation)
        .filter(
            OperationCooperation.id == id,
            OperationCooperation.creator_id == creator.id,
            OperationCooperation.status == "pending",
        )
        .first()
    )
    if not coop:
        raise HTTPException(404, "合作要约不存在或已处理")

    coop.status = "rejected"
    coop.rejected_at = datetime.now(timezone.utc)
    db.commit()
    AuditLog.log(db, "reject_cooperation", f"Creator {creator.id} rejected cooperation {id}", creator.id)

    return {"id": coop.id, "status": coop.status}
