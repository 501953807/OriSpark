"""分润规则路由 — 报价竞争、锁定、写入合约、执行分润."""

from typing import Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.split_rule_service import SplitRuleService

router = APIRouter(prefix="/contracts/{contract_id}/split-rules", tags=["split-rules"])


class ExecuteSplitRequest(BaseModel):
    total_amount: Optional[float] = None
    batch_id: Optional[str] = None


class RefundSplitRequest(BaseModel):
    reason: str


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
    rule = SplitRuleService.submit_quote(
        db, contract_id, participant_id, role, percentage, quote_amount,
    )
    return {"id": rule.id, "role": rule.role, "percentage": rule.percentage}


@router.post("/lock")
def post_lock_quotes(contract_id: str, db: Session = Depends(get_db)):
    """锁定各角色最优报价."""
    locked = SplitRuleService.lock_best_quotes(db, contract_id)
    return {"contract_id": contract_id, "locked_rules": locked}


@router.put("/rules")
def put_update_split_rules(
    contract_id: str,
    rules: list[dict],
    db: Session = Depends(get_db),
):
    """将锁定的分润规则写入合约 split_rules_json."""
    contract = SplitRuleService.update_split_rules_json(db, contract_id, rules)
    return {"id": contract.id, "status": contract.status}


@router.get("/calculate")
def get_calculate_split(
    contract_id: str,
    total_amount: Optional[float] = Query(default=None),
    db: Session = Depends(get_db),
):
    """计算分润方案 — 按 split_rules_json 分配金额."""
    result = SplitRuleService.calculate_split(db, contract_id, total_amount)
    return result


@router.post("/execute")
def post_execute_split(
    contract_id: str,
    body: ExecuteSplitRequest,
    db: Session = Depends(get_db),
):
    """执行分润 — 创建执行日志，调用支付网关释放资金."""
    result = SplitRuleService.execute_split(
        db,
        contract_id,
        total_amount=body.total_amount,
        batch_id=body.batch_id,
    )
    return result


@router.post("/refund")
def post_refund_split(
    contract_id: str,
    body: RefundSplitRequest,
    db: Session = Depends(get_db),
):
    """退款分润 — 将最近的成功执行记录标记为 refunded."""
    result = SplitRuleService.refund_split(
        db, contract_id, reason=body.reason,
    )
    return result
