"""合约市场路由 — 完整 CRUD + 状态机 API."""

from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query, Header
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.contract import ContractInstance
from app.services.contract_state_service import ContractStateService
from app.deps import get_current_user_id
from app.utils.audit import AuditLog

router = APIRouter(prefix="/contracts", tags=["contract-market"])


@router.post("", response_model=dict)
def post_create_contract(
    body: dict,
    db: Session = Depends(get_db),
    actor_id: str = Depends(get_current_user_id)
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
    # 🔑 Log creation
    AuditLog.log(db, "create_contract", f"Created contract {contract.id} by {actor_id}", actor_id)
    return {"id": contract.id, "status": contract.status}


@router.get("", response_model=list[dict])
def get_contracts(
    status: str | None = None,
    creator_id: str | None = None,
    limit: int = Query(default=20, le=100),
    offset: int = 0,
    actor_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """获取合约列表."""
    query = db.query(ContractInstance)
    if status:
        query = query.filter(ContractInstance.status == status)
    if creator_id:
        query = query.filter(ContractInstance.creator_id == creator_id)
    contracts = query.order_by(ContractInstance.created_at.desc()).offset(offset).limit(limit).all()
    # 🔑 Log listing
    AuditLog.log(db, "list_contracts", f"Listed {len(contracts)} contracts by {actor_id}", actor_id)
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


@router.get("/platform-fee")
def get_platform_fee(total_amount: float, db: Session = Depends(get_db)):
    """计算平台 3‰ 固定费用."""
    from app.services.split_rule_service import SplitRuleService
    fee = SplitRuleService.calculate_platform_fee(total_amount)
    return {"total_amount": total_amount, "platform_fee": fee}


@router.get("/{contract_id}", response_model=dict)
def get_contract(contract_id: str, actor_id: str = Depends(get_current_user_id), db: Session = Depends(get_db)):
    """获取合约详情."""
    contract = db.query(ContractInstance).filter(ContractInstance.id == contract_id).first()
    if not contract:
        raise HTTPException(404, "Contract not found")
    # 🔑 权限校验：只有合约创建者或交易方可查看
    if contract.creator_id != actor_id and contract.trader_id != actor_id:
        raise HTTPException(403, "Forbidden: You do not have access to this contract")
    # 🔑 Log view
    AuditLog.log(db, "view_contract", f"Viewed contract {contract_id} by {actor_id}", actor_id)
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
def patch_update_contract(contract_id: str, body: dict, actor_id: str = Depends(get_current_user_id), db: Session = Depends(get_db)):
    """更新合约信息（仅草稿状态）."""
    contract = db.query(ContractInstance).filter(ContractInstance.id == contract_id).first()
    # 🔑 权限校验：只有合约创建者或授权交易方可修改
    if contract.creator_id != actor_id and contract.trader_id != actor_id:
        raise HTTPException(403, "Forbidden: You are not authorized to modify this contract")
    if not contract:
        raise HTTPException(404, "Contract not found")
    if contract.status != "draft":
        raise HTTPException(400, "Only draft contracts can be updated")
    for key in ("title", "description", "total_amount", "currency", "billing_cycle",
                "scope_usage", "scope_geography", "scope_duration"):
        if key in body:
            setattr(contract, key, body[key])
    contract.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(contract)
    # 🔑 Log update
    AuditLog.log(db, "update_contract", f"Updated contract {contract_id} by {actor_id}", actor_id)
    return {"id": contract.id, "status": contract.status}


@router.post("/{contract_id}/publish")
def post_publish_contract(
    contract_id: str,
    actor_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """发布合约挂牌."""
    contract = ContractStateService.publish_contract(db, contract_id, actor_id)
    # 🔑 Log publish
    AuditLog.log(db, "publish_contract", f"Published contract {contract_id} by {actor_id}", actor_id)
    return {"id": contract.id, "status": contract.status}


@router.post("/{contract_id}/activate")
def post_activate_contract(contract_id: str, actor_id: str = Depends(get_current_user_id), db: Session = Depends(get_db)):
    """激活合约（平台审核通过）."""
    contract = ContractStateService.activate_contract(db, contract_id, actor_id)
    # 🔑 Log activate
    AuditLog.log(db, "activate_contract", f"Activated contract {contract_id} by {actor_id}", actor_id)
    return {"id": contract.id, "status": contract.status}


@router.post("/{contract_id}/subscribe")
def post_subscribe_contract(contract_id: str, subscriber_id: str, actor_id: str = Depends(get_current_user_id), db: Session = Depends(get_db)):
    """认购合约."""
    contract = ContractStateService.subscribe_contract(db, contract_id, subscriber_id, actor_id)
    # 🔑 Log subscribe
    AuditLog.log(db, "subscribe_contract", f"Subscribed contract {contract_id} by {actor_id}", actor_id)
    return {"id": contract.id, "status": contract.status}


@router.post("/{contract_id}/escrow/initiate")
def post_initiate_escrow(contract_id: str, provider: str, actor_id: str = Depends(get_current_user_id), db: Session = Depends(get_db)):
    """发起资金托管."""
    contract = ContractStateService.initiate_escrow(db, contract_id, provider, actor_id)
    # 🔑 Log initiate escrow
    AuditLog.log(db, "initiate_escrow", f"Initiated escrow for contract {contract_id} by {actor_id}", actor_id)
    return {"id": contract.id, "status": contract.status}


@router.post("/{contract_id}/escrow/confirm")
def post_confirm_escrow(contract_id: str, transaction_id: str, actor_id: str = Depends(get_current_user_id), db: Session = Depends(get_db)):
    """确认托管到账."""
    contract = ContractStateService.confirm_escrow(db, contract_id, transaction_id, actor_id)
    # 🔑 Log confirm escrow
    AuditLog.log(db, "confirm_escrow", f"Confirmed escrow for contract {contract_id} by {actor_id}", actor_id)
    return {"id": contract.id, "status": contract.status}


@router.post("/{contract_id}/insurance/activate")
def post_activate_insurance(contract_id: str, insurance_product_id: str | None = None, policy_no: str | None = None, premium: float | None = None, actor_id: str = Depends(get_current_user_id), db: Session = Depends(get_db)):
    """激活保险."""
    contract = ContractStateService.activate_insurance(db, contract_id, insurance_product_id, policy_no, premium, actor_id)
    # 🔑 Log activate insurance
    AuditLog.log(db, "activate_insurance", f"Activated insurance for contract {contract_id} by {actor_id}", actor_id)
    return {"id": contract.id, "status": contract.status}


@router.post("/{contract_id}/execute/start")
def post_start_execution(contract_id: str, actor_id: str = Depends(get_current_user_id), db: Session = Depends(get_db)):
    """开始履约."""
    contract = ContractStateService.start_execution(db, contract_id, actor_id)
    # 🔑 Log start execution
    AuditLog.log(db, "start_execution", f"Started execution for contract {contract_id} by {actor_id}", actor_id)
    return {"id": contract.id, "status": contract.status}


@router.post("/{contract_id}/complete")
def post_complete_contract(contract_id: str, actor_id: str = Depends(get_current_user_id), db: Session = Depends(get_db)):
    """完成合约."""
    contract = ContractStateService.complete_contract(db, contract_id, actor_id)
    # 🔑 Log complete contract
    AuditLog.log(db, "complete_contract", f"Completed contract {contract_id} by {actor_id}", actor_id)
    return {"id": contract.id, "status": contract.status}


@router.post("/{contract_id}/dispute")
def post_dispute_contract(contract_id: str, reason: str, actor_id: str = Depends(get_current_user_id), db: Session = Depends(get_db)):
    """拒绝验收/发起争议."""
    contract = ContractStateService.reject_inspection(db, contract_id, reason, actor_id)
    # 🔑 Log dispute contract
    AuditLog.log(db, "dispute_contract", f"Disputed contract {contract_id} by {actor_id} - reason={reason}", actor_id)
    return {"id": contract.id, "status": contract.status}


@router.post("/{contract_id}/resolve")
def post_resolve_dispute(contract_id: str, resolution: str, actor_id: str = Depends(get_current_user_id), db: Session = Depends(get_db)):
    """解决争议."""
    contract = ContractStateService.resolve_dispute(db, contract_id, resolution, actor_id)
    # 🔑 Log resolve dispute
    AuditLog.log(db, "resolve_dispute", f"Resolved dispute for contract {contract_id} by {actor_id}", actor_id)
    return {"id": contract.id, "status": contract.status}


@router.post("/{contract_id}/refund")
def post_refund_contract(contract_id: str, reason: str, actor_id: str = Depends(get_current_user_id), db: Session = Depends(get_db)):
    """退款."""
    contract = ContractStateService.refund_contract(db, contract_id, reason, actor_id)
    # 🔑 Log refund
    AuditLog.log(db, "refund_contract", f"Refunded contract {contract_id} by {actor_id} - reason={reason}", actor_id)
    return {"id": contract.id, "status": contract.status}


@router.post("/{contract_id}/cancel")
def post_cancel_contract(contract_id: str, reason: str, actor_id: str = Depends(get_current_user_id), db: Session = Depends(get_db)):
    """取消合约."""
    contract = ContractStateService.cancel_contract(db, contract_id, reason, actor_id)
    # 🔑 Log cancel contract
    AuditLog.log(db, "cancel_contract", f"Canceled contract {contract_id} by {actor_id} - reason={reason}", actor_id)
    return {"id": contract.id, "status": contract.status}


@router.get("/{contract_id}/timeline")
def get_timeline(contract_id: str, actor_id: str = Depends(get_current_user_id), db: Session = Depends(get_db)):
    """获取合约时间线."""
    # 🔑 权限校验：只有合约相关方可查看时间线
    contract = db.query(ContractInstance).filter(ContractInstance.id == contract_id).first()
    if not contract:
        raise HTTPException(404, "Contract not found")
    if contract.creator_id != actor_id and contract.trader_id != actor_id:
        raise HTTPException(403, "Forbidden: You do not have access to this contract's timeline")
    # 🔑 Log view timeline
    AuditLog.log(db, "view_timeline", f"Viewed timeline for contract {contract_id} by {actor_id}", actor_id)
    timeline = ContractStateService.get_contract_timeline(db, contract_id)
    return {"contract_id": contract_id, "timeline": timeline}


@router.post("/{contract_id}/escrow/release")
def post_release_escrow(contract_id: str, actor_id: str = Depends(get_current_user_id), db: Session = Depends(get_db)):
    """释放托管资金到各方分润账户."""
    from app.services.payment_gateway import PaymentGatewayService
    result = PaymentGatewayService.release_escrow(
        db=db, contract_id=contract_id, actor_id=actor_id
    )
    # 🔑 Log release escrow
    AuditLog.log(db, "release_escrow", f"Released escrow for contract {contract_id} by {actor_id}", actor_id)
    return result


@router.post("/{contract_id}/escrow/refund")
def post_escrow_refund(
    contract_id: str,
    reason: str = "",
    actor_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """退款至付款方（托管中合约）."""
    from app.services.payment_gateway import PaymentGatewayService
    result = PaymentGatewayService.refund_escrow(
        db=db, contract_id=contract_id, reason=reason or "用户申请退款", actor_id=actor_id
    )
    # 🔑 Log escrow refund
    AuditLog.log(db, "escrow_refund", f"Escrow refunded for contract {contract_id} by {actor_id} - reason={reason}", actor_id)
    return result


@router.get("/{contract_id}/status")
def get_status(contract_id: str, actor_id: str = Depends(get_current_user_id), db: Session = Depends(get_db)):
    """获取合约状态摘要."""
    # 🔑 权限校验：只有合约相关方可查看状态
    contract = db.query(ContractInstance).filter(ContractInstance.id == contract_id).first()
    if not contract:
        raise HTTPException(404, "Contract not found")
    if contract.creator_id != actor_id and contract.trader_id != actor_id:
        raise HTTPException(403, "Forbidden: You do not have access to this contract's status")
    # 🔑 Log view status
    AuditLog.log(db, "view_status", f"Viewed status for contract {contract_id} by {actor_id}", actor_id)
    summary = ContractStateService.get_contract_status_summary(db, contract_id)
    return summary


@router.delete("/{contract_id}")
def delete_contract(contract_id: str, actor_id: str = Depends(get_current_user_id), db: Session = Depends(get_db)):
    """删除合约（仅草稿状态）."""
    contract = db.query(ContractInstance).filter(ContractInstance.id == contract_id).first()
    if not contract:
        raise HTTPException(404, "Contract not found")
    if contract.creator_id != actor_id:
        raise HTTPException(403, "Forbidden: Only the creator can delete a contract")
    if contract.status != "draft":
        raise HTTPException(400, "Only draft contracts can be deleted")
    db.delete(contract)
    db.commit()
    AuditLog.log(db, "delete_contract", f"Deleted contract {contract_id} by {actor_id}", actor_id)
    return {"id": contract_id, "deleted": True}


@router.post("/{contract_id}/confirm-subscribe")
def post_confirm_subscribe(contract_id: str, actor_id: str = Depends(get_current_user_id), db: Session = Depends(get_db)):
    """创作者确认认购 — 由 creator 在 subscribe 后确认，进入托管阶段."""
    contract = db.query(ContractInstance).filter(ContractInstance.id == contract_id).first()
    if not contract:
        raise HTTPException(404, "Contract not found")
    if contract.creator_id != actor_id:
        raise HTTPException(403, "Forbidden: Only the creator can confirm subscription")
    if contract.status != "subscribed":
        raise HTTPException(400, f"Contract is not in subscribed state, current status: {contract.status}")
    from app.services.contract_state_service import ContractStateService
    contract = ContractStateService.confirm_subscribe(db, contract_id, actor_id)
    AuditLog.log(db, "confirm_subscribe", f"Creator confirmed subscribe for contract {contract_id} by {actor_id}", actor_id)
    return {"id": contract.id, "status": contract.status}

