"""委托项目 Pydantic 模型."""

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict


class MilestoneCreate(BaseModel):
    name: str
    due_date: Optional[str] = None
    description: Optional[str] = None
    order_index: int = 0


class MilestoneUpdate(BaseModel):
    status: Optional[str] = None
    due_date: Optional[str] = None
    description: Optional[str] = None
    name: Optional[str] = None
    order_index: Optional[int] = None


class MilestoneSchema(BaseModel):
    id: str
    commission_id: str
    name: str
    status: str
    due_date: Optional[str] = None
    description: Optional[str] = None
    order_index: int
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class PaymentCreate(BaseModel):
    amount: float
    method: Optional[str] = None
    milestone_id: Optional[str] = None
    notes: Optional[str] = None


class PaymentUpdate(BaseModel):
    status: Optional[str] = None
    paid_at: Optional[str] = None
    amount: Optional[float] = None
    method: Optional[str] = None
    notes: Optional[str] = None


class PaymentSchema(BaseModel):
    id: str
    commission_id: str
    milestone_id: Optional[str] = None
    amount: float
    method: Optional[str] = None
    status: str
    paid_at: Optional[str] = None
    notes: Optional[str] = None
    created_at: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class RevisionCreate(BaseModel):
    description: str
    client_feedback: Optional[str] = None
    files: Optional[list[str]] = None
    created_by: str = "artist"


class RevisionSchema(BaseModel):
    id: str
    commission_id: str
    description: str
    client_feedback: Optional[str] = None
    files: Optional[list[str]] = None
    created_by: str
    created_at: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class TimelineEvent(BaseModel):
    type: str  # milestone | payment | revision
    id: str
    title: str
    description: Optional[str] = None
    date: Optional[str] = None
    status: Optional[str] = None


class CalendarEvent(BaseModel):
    id: str
    title: str
    date: str
    type: str  # milestone_due | payment_received | revision_deadline


class DashboardStats(BaseModel):
    active_count: int = 0
    pending_payment: int = 0
    monthly_revenue: float = 0.0
    avg_ticket: float = 0.0
