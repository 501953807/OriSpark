"""私域流量 Pydantic schemas."""

from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class SubscriptionLinkCreate(BaseModel):
    platform: str
    url: str
    subscriber_count: int = 0
    monthly_revenue: float = 0
    currency: str = "CNY"


class SubscriptionLinkResponse(BaseModel):
    id: str
    user_id: str
    platform: str
    url: str
    subscriber_count: int
    monthly_revenue: float
    currency: str
    is_active: bool
    created_at: str


class FanCommunityCreate(BaseModel):
    platform: str
    name: str
    invite_url: Optional[str] = None
    member_count: int = 0
    tags: Optional[list[str]] = None
    description: Optional[str] = None


class FanCommunityResponse(BaseModel):
    id: str
    user_id: str
    platform: str
    name: str
    invite_url: Optional[str] = None
    member_count: int
    tags: Optional[list[str]] = None
    description: Optional[str] = None
    is_active: bool


class FunnelEntryCreate(BaseModel):
    source_platform: str
    public_views: int = 0
    profile_clicks: int = 0
    link_clicks: int = 0
    converted_subscribers: int = 0
    notes: Optional[str] = None


class FunnelSummary(BaseModel):
    total_public_views: int
    total_profile_clicks: int
    total_link_clicks: int
    total_converted: int
    overall_conversion_rate: float
    by_platform: list[dict]
