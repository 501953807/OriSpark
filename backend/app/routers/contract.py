"""合约市场路由 — 完整 CRUD + 状态机 API."""

from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.contract import ContractInstance
from app.services.contract_state_service import ContractStateService

router = APIRouter(prefix="/contracts", tags=["contract-market"])


@router.post("", response_model=dict)
def post_create_contract(
    body: dict, db: Session = Depends(get_db), actor_id: str = "current_user"
):
    """创建合约草稿."""
    contract = ContractStateService.create_contract(
        db=db,
        title=body["title"],
        description=body.get("description", ""),
        work_id=body.get("work_id"),
        contract_type=body.get("contract_type", "non_exclusive_license"),
        total_amount=float(body["total_amount"]),
        currency=body.get("currency", "CNY"),
        billing_cycle=body.get("billing_cycle", "one_time"),
        scope_usage=body.get("scope_usage", "commercial"),
        scope_geography=body.get("scope_geography", "china"),
        scope_duration=body.get("scope_duration"),
        creator_id=actor_id,
        split_rules_json=body.get("split_rules_json", "[]"),
    )
    return {"id": contract.id, "status": contract.status}


@router.get("", response_model=list[dict])
def get_contracts(
    status: str | None = None,
    creator_id: str | None = None,
    limit: int = Query(default=20, le=100),
    offset: int = 0,
    db: Session = Depends(get_db),
):
    """获取合约列表."""
    query = db.query(ContractInstance)
    if status:
        query = query.filter(ContractInstance.status == status)
    if creator_id:
        query = query.filter(ContractInstance.creator_id == creator_id)
    contracts = query.order_by(ContractInstance.created_at.desc()).offset(offset).limit(limit).all()
    return [
        {
            "id": c.id, "title": c.title, "status": c.status,
            "total_amount": float(c.total_amount), "currency": c.currency,
            "contract_type": c.contract_type, "creator_id": c.creator_id,
            "verified": c.verified, "created_at": c.created_at.isoformat() if c.created_at else None,
        }
        for c in contracts
    ]


@router.get("/transitions")
def get_valid_transitions():
    """获取合法状态流转表."""
    return {"valid_transitions": ContractStateService.get_valid_transitions(), "labels": ContractStateService.get_status_labels()}


@router.get("/{contract_id}", response_model=dict)
def get_contract(contract_id: str, db: Session = Depends(get_db)):
    """获取合约详情."""
    contract = db.query(ContractInstance).filter(ContractInstance.id == contract_id).first()
    if not contract:
        raise HTTPException(404, "Contract not found")
    return {
        "id": contract.id, "title": contract.title, "description": contract.description,
        "work_id": contract.work_id, "contract_type": contract.contract_type,
        "total_amount": float(contract.total_amount), "currency": contract.currency,
        "billing_cycle": contract.billing_cycle, "scope_usage": contract.scope_usage,
        "scope_geography": contract.scope_geography, "scope_duration": contract.scope_duration,
        "status": contract.status, "verified": contract.verified,
        "creator_id": contract.creator_id, "operator_id": contract.operator_id,
        "trader_id": contract.trader_id, "split_rules_json": contract.split_rules_json,
        "published_at": contract.published_at.isoformat() if contract.published_at else None,
        "subscribed_at": contract.subscribed_at.isoformat() if contract.subscribed_at else None,
        "escrowed_at": contract.escrowed_at.isoformat() if contract.escrowed_at else None,
        "executed_at": contract.executed_at.isoformat() if contract.executed_at else None,
        "completed_at": contract.completed_at.isoformat() if contract.completed_at else None,
        "created_at": contract.created_at.isoformat() if contract.created_at else None,
    }


@router.patch("/{contract_id}")
def patch_update_contract(contract_id: str, body: dict, db: Session = Depends(get_db)):
    """更新合约信息（仅草稿状态）."""
    contract = db.query(ContractInstance).filter(ContractInstance.id == contract_id).first()
    if not contract:
        raise HTTPException(404, "Contract not found")
    if contract.status != "draft":
        raise HTTPException(400, "Only draft contracts can be updated")
    for key in ("title", "description", "total_amount", "currency", "billing_cycle",
                "scope_usage", "scope_geography", "scope_duration"):
        if key in body:
            setattr(contract, key, body[key])
    contract.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(contract)
    return {"id": contract.id, "status": contract.status}


@router.post("/{contract_id}/publish")
def post_publish_contract(contract_id: str, actor_id: str = "current_user", db: Session = Depends(get_db)):
    """发布合约挂牌."""
    contract = ContractStateService.publish_contract(db, contract_id, actor_id)
    return {"id": contract.id, "status": contract.status}


@router.post("/{contract_id}/activate")
def post_activate_contract(contract_id: str, actor_id: str = "current_user", db: Session = Depends(get_db)):
    """激活合约（平台审核通过）."""
    contract = ContractStateService.activate_contract(db, contract_id, actor_id)
    return {"id": contract.id, "status": contract.status}


@router.post("/{contract_id}/subscribe")
def post_subscribe_contract(contract_id: str, subscriber_id: str, actor_id: str = "current_user", db: Session = Depends(get_db)):
    """认购合约."""
    contract = ContractStateService.subscribe_contract(db, contract_id, subscriber_id, actor_id)
    return {"id": contract.id, "status": contract.status}


@router.post("/{contract_id}/escrow/initiate")
def post_initiate_escrow(contract_id: str, provider: str, actor_id: str = "current_user", db: Session = Depends(get_db)):
    """发起资金托管."""
    contract = ContractStateService.initiate_escrow(db, contract_id, provider, actor_id)
    return {"id": contract.id, "status": contract.status}


@router.post("/{contract_id}/escrow/confirm")
def post_confirm_escrow(contract_id: str, transaction_id: str, actor_id: str = "current_user", db: Session = Depends(get_db)):
    """确认托管到账."""
    contract = ContractStateService.confirm_escrow(db, contract_id, transaction_id, actor_id)
    return {"id": contract.id, "status": contract.status}


@router.post("/{contract_id}/insurance/activate")
def post_activate_insurance(contract_id: str, insurance_product_id: str | None = None, policy_no: str | None = None, premium: float | None = None, actor_id: str = "current_user", db: Session = Depends(get_db)):
    """激活保险."""
    contract = ContractStateService.activate_insurance(db, contract_id, insurance_product_id, policy_no, premium, actor_id)
    return {"id": contract.id, "status": contract.status}


@router.post("/{contract_id}/execute/start")
def post_start_execution(contract_id: str, actor_id: str = "current_user", db: Session = Depends(get_db)):
    """开始履约."""
    contract = ContractStateService.start_execution(db, contract_id, actor_id)
    return {"id": contract.id, "status": contract.status}


@router.post("/{contract_id}/complete")
def post_complete_contract(contract_id: str, actor_id: str = "current_user", db: Session = Depends(get_db)):
    """完成合约."""
    contract = ContractStateService.complete_contract(db, contract_id, actor_id)
    return {"id": contract.id, "status": contract.status}


@router.post("/{contract_id}/dispute")
def post_dispute_contract(contract_id: str, reason: str, actor_id: str = "current_user", db: Session = Depends(get_db)):
    """拒绝验收/发起争议."""
    contract = ContractStateService.reject_inspection(db, contract_id, reason, actor_id)
    return {"id": contract.id, "status": contract.status}


@router.post("/{contract_id}/resolve")
def post_resolve_dispute(contract_id: str, resolution: str, actor_id: str = "current_user", db: Session = Depends(get_db)):
    """解决争议."""
    contract = ContractStateService.resolve_dispute(db, contract_id, resolution, actor_id)
    return {"id": contract.id, "status": contract.status}


@router.post("/{contract_id}/refund")
def post_refund_contract(contract_id: str, reason: str, actor_id: str = "current_user", db: Session = Depends(get_db)):
    """退款."""
    contract = ContractStateService.refund_contract(db, contract_id, reason, actor_id)
    return {"id": contract.id, "status": contract.status}


@router.post("/{contract_id}/cancel")
def post_cancel_contract(contract_id: str, reason: str, actor_id: str = "current_user", db: Session = Depends(get_db)):
    """取消合约."""
    contract = ContractStateService.cancel_contract(db, contract_id, reason, actor_id)
    return {"id": contract.id, "status": contract.status}


@router.get("/{contract_id}/timeline")
def get_timeline(contract_id: str, db: Session = Depends(get_db)):
    """获取合约时间线."""
    timeline = ContractStateService.get_contract_timeline(db, contract_id)
    return {"contract_id": contract_id, "timeline": timeline}


@router.get("/{contract_id}/status")
def get_status(contract_id: str, db: Session = Depends(get_db)):
    """获取合约状态摘要."""
    summary = ContractStateService.get_contract_status_summary(db, contract_id)
    return summary
