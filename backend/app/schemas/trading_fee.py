from pydantic import BaseModel
from typing import Optional
from app.models.trading_fee import FeeTier as TierEnum


class FeeCalcRequest(BaseModel):
    amount_yuan: float
    creator_type: Optional[str] = None
    category: Optional[str] = None
    monthly_volume_yuan: float = 0
    credit_score: int = 0


class FeeCalcResponse(BaseModel):
    amount_yuan: float
    fee_rate_percent: float
    fee_amount_yuan: float
    tier: str
    is_discounted: bool
    discount_reason: Optional[str] = None


class FeeRecordResponse(BaseModel):
    id: str
    transaction_id: str
    amount_yuan: float
    fee_amount_yuan: float
    fee_rate_bps: int
    tier: str
    created_at: Optional[str] = None
