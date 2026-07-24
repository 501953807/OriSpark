"""订阅系统 Pydantic 模型."""

from typing import Optional, Any
from datetime import datetime

from pydantic import BaseModel, Field, ConfigDict


class SubscriptionTierCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    price: float = Field(..., ge=0)
    currency: str = Field(default="CNY", max_length=10)
    period: str = Field(default="monthly", pattern="^(monthly|yearly)$")
    features: Optional[list[dict]] = None
    is_active: bool = True


class SubscriptionTierUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = None
    price: Optional[float] = Field(None, ge=0)
    currency: Optional[str] = None
    period: Optional[str] = None
    features: Optional[list[dict]] = None
    is_active: Optional[bool] = None


class SubscriptionTierResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    name: str
    description: Optional[str] = None
    price: float
    currency: str
    period: str
    features: Optional[list[dict]] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime


class SubscriptionSubscriberCreate(BaseModel):
    user_id: str
    tier_id: str


class SubscriptionSubscriberUpdate(BaseModel):
    status: Optional[str] = Field(None, pattern="^(active|cancelled|expired)$")
    cancelled_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None


class SubscriptionSubscriberResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    user_id: str
    tier_id: str
    status: str
    subscribed_at: datetime
    cancelled_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None


class SubscriptionAutoRenewalUpdate(BaseModel):
    enabled: bool


class SubscriptionAutoRenewalResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    subscriber_id: str
    enabled: bool
    last_renewal_attempt: Optional[datetime] = None
    next_renewal_date: Optional[datetime] = None
    failed_attempts: int
    max_failed_attempts: int
    created_at: datetime
    updated_at: datetime
