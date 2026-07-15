import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.trading_fee import FeeCalcRequest, FeeCalcResponse, FeeRecordResponse
from app.services.trading_fee_service import calculate_fee, record_transaction

router = APIRouter(prefix="/api/trading-fees", tags=["trading-fees"])


@router.post("/calculate", response_model=FeeCalcResponse)
def post_calculate_fee(req: FeeCalcRequest):
    result = calculate_fee(
        amount_yuan=req.amount_yuan,
        monthly_volume_yuan=req.monthly_volume_yuan,
        credit_score=req.credit_score,
        creator_type=req.creator_type,
        category=req.category,
    )
    return FeeCalcResponse(**result)


@router.post("/record", response_model=FeeRecordResponse)
def post_record_transaction(transaction_id: str | None = None, req: FeeCalcRequest = ...):
    if transaction_id is None:
        transaction_id = uuid.uuid4().hex[:32]
    calc = calculate_fee(
        amount_yuan=req.amount_yuan,
        monthly_volume_yuan=req.monthly_volume_yuan,
        credit_score=req.credit_score,
    )
    return FeeRecordResponse(
        id=transaction_id,
        transaction_id=transaction_id,
        amount_yuan=calc["amount_yuan"],
        fee_amount_yuan=calc["fee_amount_yuan"],
        fee_rate_bps=calc["rate_bps"],
        tier=calc["tier"],
    )


@router.get("/estimator")
def get_estimator(amount_yuan: float, monthly_volume_yuan: float = 0,
                  credit_score: int = 50):
    """费用估算器 — 前端用."""
    result = calculate_fee(
        amount_yuan=amount_yuan,
        monthly_volume_yuan=monthly_volume_yuan,
        credit_score=credit_score,
    )
    return {
        "amount_yuan": result["amount_yuan"],
        "fee_yuan": result["fee_amount_yuan"],
        "rate_percent": round(result["rate_bps"] / 100, 2),
        "tier": result["tier"],
        "is_discounted": result["is_discounted"],
    }
