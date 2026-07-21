"""议价协商 Pydantic schemas (v2)."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class NegotiationCreate(BaseModel):
    buyer_id: str
    seller_id: str
    listing_id: Optional[str] = None
    match_request_id: Optional[str] = None
    description: Optional[str] = None
    initial_price_yuan: Optional[float] = None


class OfferRequest(BaseModel):
    amount_yuan: float = Field(..., gt=0, description="出价金额，必须 > 0")
    message: Optional[str] = None


class NegotiationResponse(BaseModel):
    id: str
    buyer_id: str
    seller_id: str
    listing_id: Optional[str] = None
    match_request_id: Optional[str] = None
    description: Optional[str] = None
    initial_price_yuan: Optional[float] = None
    current_offer_yuan: Optional[float] = None
    final_price_yuan: Optional[float] = None
    status: str
    message_log: list = []
    created_at: datetime
    updated_at: datetime


class NegotiationFilter(BaseModel):
    user_id: Optional[str] = None
    status: Optional[str] = None
    limit: int = 20
    offset: int = 0
