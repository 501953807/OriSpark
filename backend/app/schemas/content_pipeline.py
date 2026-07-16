"""多平台内容分发流水线 Pydantic schemas."""

from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class PlatformAccountCreate(BaseModel):
    platform: str
    account_name: str
    account_id: Optional[str] = None
    follower_count: int = 0


class PlatformAccountResponse(BaseModel):
    id: str
    platform: str
    account_name: str
    account_id: Optional[str] = None
    follower_count: int
    is_active: bool
    created_at: str
    updated_at: str


class ScheduleCreate(BaseModel):
    title: str
    description: Optional[str] = None
    work_id: Optional[str] = None
    platforms: list[dict]
    scheduled_at: str
    is_recurring: bool = False
    recurring_pattern: Optional[str] = None


class PublishScheduleResponse(BaseModel):
    id: str
    title: str
    description: Optional[str] = None
    platforms: list[dict]
    scheduled_at: str
    is_recurring: bool
    recurring_pattern: Optional[str] = None
    status: str
    published_at: Optional[str] = None
    error_message: Optional[str] = None


class SimulateResult(BaseModel):
    platform: str
    platform_name: str
    recommended_cover: str
    max_tags: int
    title_adapted: str
    tags_count: int
    tags_ok: bool


class PublishStats(BaseModel):
    total_schedules: int
    scheduled: int
    published: int
    failed: int
    recent_7d_success: int
