"""POD 结算 Pydantic schemas (v2)."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class SettlementItemResponse(BaseModel):
    id: str
    sale_id: Optional[str] = None
    product_id: Optional[str] = None
    sale_amount_yuan: float
    cost_yuan: float
    creator_earning_yuan: float
    platform_fee_yuan: float


class SettlementResponse(BaseModel):
    id: str
    user_id: str
    period: str
    total_sales_yuan: float
    total_cost_yuan: float
    creator_earnings_yuan: float
    platform_fee_yuan: float
    status: str
    confirmed_at: Optional[datetime] = None
    settled_at: Optional[datetime] = None
    notes: Optional[str] = None
    items: list[SettlementItemResponse] = []


class GenerateSettlementRequest(BaseModel):
    period: str  # "2026-07"
    user_id: str


class SalesStatisticsResponse(BaseModel):
    total_sales: float
    total_cost: float
    total_earnings: float
    total_fees: float
    sale_count: int
