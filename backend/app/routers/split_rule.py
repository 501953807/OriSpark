"""分润规则路由 — 报价竞争、锁定、写入合约."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.split_rule_service import SplitRuleService

router = APIRouter(prefix="/contracts/{contract_id}/split-rules", tags=["split-rules"])


@router.get("/platform-fee")
def get_platform_fee(total_amount: float):
    """计算平台 3‰ 固定费用."""
    fee = SplitRuleService.calculate_platform_fee(total_amount)
    return {"total_amount": total_amount, "platform_fee": fee}


@router.get("")
def get_split_rules(
    contract_id: str,
    db: Session = Depends(get_db),
):
    """获取合约当前分润规则."""
    rules = SplitRuleService.get_contract_split_rules(db, contract_id)
    return {"contract_id": contract_id, "rules": rules}


@router.post("/quotes")
def post_submit_quote(
    contract_id: str,
    participant_id: str,
    role: str,
    percentage: float,
    quote_amount: float,
    db: Session = Depends(get_db),
):
    """参与方提交分润报价."""
    try:
        rule = SplitRuleService.submit_quote(
            db, contract_id, participant_id, role, percentage, quote_amount,
        )
        return {"id": rule.id, "role": rule.role, "percentage": rule.percentage}
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(500, detail=f"Submit quote failed: {e}")


@router.post("/lock")
def post_lock_quotes(contract_id: str, db: Session = Depends(get_db)):
    """锁定各角色最优报价."""
    try:
        locked = SplitRuleService.lock_best_quotes(db, contract_id)
        return {"contract_id": contract_id, "locked_rules": locked}
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(500, detail=f"Lock quotes failed: {e}")


@router.put("/rules")
def put_update_split_rules(
    contract_id: str,
    rules: list[dict],
    db: Session = Depends(get_db),
):
    """将锁定的分润规则写入合约 split_rules_json."""
    try:
        contract = SplitRuleService.update_split_rules_json(db, contract_id, rules)
        return {"id": contract.id, "status": contract.status}
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(500, detail=f"Update split rules failed: {e}")


@router.get("/platform-fee")
def get_platform_fee(total_amount: float):
    """计算平台 3‰ 固定费用."""
    fee = SplitRuleService.calculate_platform_fee(total_amount)
    return {"total_amount": total_amount, "platform_fee": fee}
