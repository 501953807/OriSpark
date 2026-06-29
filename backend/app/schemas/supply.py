"""供应链 Pydantic 模型."""

from typing import Optional
from datetime import datetime, date

from pydantic import BaseModel, ConfigDict


class PartnerCreate(BaseModel):
    name: str
    company_name: Optional[str] = None
    contact_person: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    website: Optional[str] = None
    categories: Optional[list[str]] = None
    moq: Optional[int] = None
    rating: int = 0
    tags: Optional[list[str]] = None
    notes: Optional[str] = None


class PartnerResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    name: str
    company_name: Optional[str] = None
    contact_person: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    categories: Optional[list] = None
    rating: int
    status: str
    created_at: datetime


class OrderCreate(BaseModel):
    partner_id: Optional[str] = None
    product_name: str
    quantity: int = 1
    specifications: Optional[str] = None
    unit_price: float = 0
    total_amount: float = 0
    deposit_percent: float = 30
    deposit_paid: float = 0
    status: str = "draft"
    expected_date: Optional[date] = None
    notes: Optional[str] = None


class OrderResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    order_number: str
    partner_id: Optional[str] = None
    product_name: str
    quantity: int
    total_amount: float
    deposit_paid: float
    balance_due: float
    status: str
    expected_date: Optional[date] = None
    actual_date: Optional[date] = None
    created_at: datetime
