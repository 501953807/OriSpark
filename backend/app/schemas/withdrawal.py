"""佣金提现 Pydantic schemas (v2)."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class WithdrawalRequest(BaseModel):
    amount_yuan: float = Field(..., gt=0, description="提现金额，必须 > 0")
    method: str = Field(..., pattern="^(bank_transfer|wechat|alipay)$")
    account_info: dict = Field(default_factory=dict, description="收款账户信息")


class WithdrawalResponse(BaseModel):
    id: str
    user_id: str
    amount_yuan: float
    available_balance_yuan: float
    fee_yuan: float
    net_amount_yuan: float
    method: str
    status: str
    created_at: datetime
    updated_at: datetime


class CommissionBalanceResponse(BaseModel):
    available_yuan: float
    frozen_yuan: float
    total_earned_yuan: float


class MonthlyCommissionStats(BaseModel):
    year: int
    month: int
    total_commission: float
    settled_commission: float
    pending_commission: float
    records: list[dict]
