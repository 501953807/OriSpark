"""Module 9 v2: AI增长引擎 数据模型."""

import uuid
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field

from app.schemas.common import ApiResponse


# --- Achievement Badge ---

class AchievementBadgeCreate(BaseModel):
    badge_key: str = Field(..., max_length=50)
    badge_name: str = Field(..., max_length=100)
    badge_description: Optional[str] = None
    icon_url: Optional[str] = None
    color_hex: Optional[str] = None
    xp_reward: int = Field(default=100, ge=0)


class AchievementBadgeResponse(BaseModel):
    id: str
    badge_key: str
    badge_name: str
    badge_description: Optional[str] = None
    icon_url: Optional[str] = None
    color_hex: Optional[str] = None
    xp_reward: int
    is_active: bool
    created_at: str

    model_config = {"from_attributes": True}


class UserAchievementResponse(BaseModel):
    id: str
    user_id: str
    badge_id: str
    unlocked_at: str

    model_config = {"from_attributes": True}


class LeaderboardEntryResponse(BaseModel):
    id: str
    user_id: str
    creator_type: str
    rank_position: int
    score: float
    total_xp: int
    period: str
    updated_at: str

    model_config = {"from_attributes": True}


# --- Invoice ---

class InvoiceCreate(BaseModel):
    amount_yuan: float = Field(..., gt=0)
    tax_rate: float = Field(default=0.11, ge=0, le=1)
    description: Optional[str] = None
    payment_method: Optional[str] = None
    due_date: Optional[datetime] = None
    is_auto_renewal: bool = False


class InvoiceUpdate(BaseModel):
    status: Optional[str] = None
    paid_at: Optional[datetime] = None
    payment_proof_path: Optional[str] = None


class InvoiceResponse(BaseModel):
    id: str
    user_id: str
    invoice_number: str
    amount_yuan: float
    tax_rate: float
    subtotal_yuan: float
    tax_amount_yuan: float
    total_yuan: float
    status: str
    due_date: Optional[str] = None
    paid_at: Optional[str] = None
    description: Optional[str] = None
    payment_method: Optional[str] = None
    payment_proof_path: Optional[str] = None
    is_auto_renewal: bool
    created_at: str
    updated_at: Optional[str] = None

    model_config = {"from_attributes": True}


class AutoRenewalUpdate(BaseModel):
    enabled: bool


class AutoRenewalResponse(BaseModel):
    id: str
    subscriber_id: str
    enabled: bool
    last_renewal_attempt: Optional[str] = None
    next_renewal_date: Optional[str] = None
    failed_attempts: int
    max_failed_attempts: int
    created_at: str
    updated_at: Optional[str] = None

    model_config = {"from_attributes": True}


# --- Subtitle Batch ---

class SubtitleBatchCreate(BaseModel):
    work_id: str
    languages: List[str] = Field(..., min_items=1, max_items=20)


class SubtitleTranslateRequest(BaseModel):
    source_lang: str
    target_lang: str
    text: str


class SubtitleBatchResponse(BaseModel):
    id: str
    work_id: str
    language: str
    file_path: str
    format_type: str
    created_at: str
    updated_at: Optional[str] = None

    model_config = {"from_attributes": True}


class SessionComparisonResponse(BaseModel):
    session_a: dict
    session_b: dict
    differences: dict


# --- Responses ---

class AchievementListResponse(BaseModel):
    data: List[AchievementBadgeResponse]


class LeaderboardResponse(BaseModel):
    data: List[LeaderboardEntryResponse]


class InvoiceListResponse(BaseModel):
    data: List[InvoiceResponse]


class SubtitleBatchResultResponse(BaseModel):
    created: int
    skipped: int
    errors: List[str]
