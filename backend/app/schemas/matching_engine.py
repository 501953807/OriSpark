from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class AuctionCreate(BaseModel):
    listing_id: str
    work_id: str
    seller_id: str
    title: str
    description: Optional[str] = None
    starting_price_yuan: float
    min_increment_yuan: float = 10.0
    ends_at: datetime
    auto_extend_seconds: int = 300


class AuctionBidRequest(BaseModel):
    buyer_id: str
    amount_yuan: float
    notes: Optional[str] = None


class AuctionResponse(BaseModel):
    id: str
    listing_id: str
    work_id: str
    current_bid_yuan: float
    bid_count: int
    ends_at: datetime
    status: str
    winner_buyer_id: Optional[str] = None


class LicensingMatchCreate(BaseModel):
    work_id: str
    seller_id: str
    buyer_id: str
    license_type: str
    usage_scope: Optional[str] = None
    territory: Optional[str] = None
    duration_days: Optional[int] = None
    price_per_use_cents: Optional[int] = None
    minimum_guarantee_yuan: Optional[float] = None
    royalty_percent: Optional[float] = None
