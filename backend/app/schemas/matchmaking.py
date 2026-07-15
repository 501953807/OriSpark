from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class MatchRequestCreate(BaseModel):
    buyer_id: str
    title: str
    description: Optional[str] = None
    category: Optional[str] = None
    style_tags: Optional[list[str]] = None
    budget_min_yuan: Optional[float] = None
    budget_max_yuan: Optional[float] = None
    delivery_deadline: Optional[datetime] = None


class MatchRequestSchema(BaseModel):
    id: str
    buyer_id: str
    title: str
    category: Optional[str] = None
    status: str
    matched_seller_ids: Optional[list[str]] = None
    created_at: Optional[datetime] = None


class MatchTransactionSchema(BaseModel):
    id: str
    match_request_id: str
    buyer_id: str
    seller_id: str
    agreed_amount_yuan: float
    payment_status: str
    delivery_status: str
    created_at: Optional[datetime] = None
