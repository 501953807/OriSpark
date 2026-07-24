"""分发回流引擎 Pydantic 模型."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class TraceLinkCreate(BaseModel):
    work_id: str
    platform_code: str
    original_url: str
    redirect_url: Optional[str] = None
    utm_source: Optional[str] = None
    utm_medium: Optional[str] = None
    utm_campaign: Optional[str] = None
    expire_at: Optional[datetime] = None


class TraceLinkUpdate(BaseModel):
    is_active: Optional[bool] = None
    utm_source: Optional[str] = None
    utm_medium: Optional[str] = None
    utm_campaign: Optional[str] = None


class TraceLinkSchema(BaseModel):
    id: str
    work_id: str
    user_id: str
    platform_code: str
    short_code: str
    original_url: str
    redirect_url: str
    is_active: bool
    click_count: int
    expire_at: Optional[datetime] = None
    utm_source: Optional[str] = None
    utm_medium: Optional[str] = None
    utm_campaign: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class TraceEventCreate(BaseModel):
    link_id: str
    event_type: str
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    referrer: Optional[str] = None
    geo_country: Optional[str] = None
    geo_region: Optional[str] = None
    geo_city: Optional[str] = None
    device_type: Optional[str] = None
    browser: Optional[str] = None
    os_name: Optional[str] = None
    custom_params: Optional[dict] = None
    converted: bool = False
    conversion_value: Optional[float] = None


class TraceEventSchema(BaseModel):
    id: str
    link_id: str
    event_type: str
    ip_address: Optional[str] = None
    geo_country: Optional[str] = None
    geo_region: Optional[str] = None
    geo_city: Optional[str] = None
    device_type: Optional[str] = None
    converted: bool
    conversion_value: Optional[float] = None
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class AttributionSummary(BaseModel):
    link_id: str
    total_clicks: int
    unique_visitors: int
    event_breakdown: dict[str, int]
    top_countries: list[dict[str, int]]
    conversion_rate: float
    total_conversions: int
    total_conversion_value: float
