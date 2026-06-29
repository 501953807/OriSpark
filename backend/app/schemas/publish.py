"""发布变现 Pydantic 模型."""

from typing import Optional
from datetime import datetime, date

from pydantic import BaseModel, ConfigDict


class ProductCreate(BaseModel):
    work_id: Optional[str] = None
    title: str
    description: Optional[str] = None
    price: float = 0
    category: Optional[str] = None
    specifications: Optional[dict] = None
    images: Optional[list[str]] = None


class ProductResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    work_id: Optional[str] = None
    title: str
    description: Optional[str] = None
    ai_description: Optional[str] = None
    price: float
    category: Optional[str] = None
    csv_export_path: Optional[str] = None
    created_at: datetime


class PublishRequest(BaseModel):
    platform: str


class RevenueCreate(BaseModel):
    product_id: Optional[str] = None
    platform: str
    amount: float
    date: Optional[date] = None
    order_count: int = 1
    notes: Optional[str] = None


class RevenueResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    product_id: Optional[str] = None
    platform: str
    amount: float
    currency: str
    date: date
    order_count: int
