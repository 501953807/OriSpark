from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class ListingCreate(BaseModel):
    work_id: str
    title: str
    description: Optional[str] = None
    asking_price_yuan: float
    original_cost_yuan: Optional[float] = None
    min_price_yuan: Optional[float] = None
    max_discount_percent: float = 10.0
    quantity_total: int = 1
    expires_days: Optional[int] = 30
    profit_split_percent: float = 70.0
    tags: Optional[list[str]] = None


class ListingUpdate(BaseModel):
    asking_price_yuan: Optional[float] = None
    min_price_yuan: Optional[float] = None
    max_discount_percent: Optional[float] = None
    quantity_total: Optional[int] = None
    status: Optional[str] = None
    profit_split_percent: Optional[float] = None


class ListingResponse(BaseModel):
    id: str
    work_id: str
    seller_id: str
    title: str
    asking_price_yuan: float
    status: str
    quantity_sold: int
    quantity_total: int
    profit_split_percent: float
    platform_fee_rate_bps: int
    created_at: Optional[datetime] = None
