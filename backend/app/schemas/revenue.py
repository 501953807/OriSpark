"""收入多元化分析 Pydantic schemas."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class RevenueRecordCreate(BaseModel):
    income_category: str
    amount: float
    currency: str = "CNY"
    platform: Optional[str] = None
    source_description: Optional[str] = None
    recorded_date: Optional[datetime] = None


class RevenueRecordSchema(BaseModel):
    id: str
    user_id: Optional[str] = None
    income_category: str
    amount: float
    currency: str
    platform: Optional[str]
    source_description: Optional[str]
    recorded_date: Optional[datetime]
    is_verified: bool
    created_at: Optional[datetime] = None


class DiversityIndexResponse(BaseModel):
    diversity_index: float
    total_sources: int
    warnings: list[str]
    category_distribution: dict


class RevenueSummaryResponse(BaseModel):
    user_id: Optional[str] = None
    total_revenue: float
    currency: str
    months: int
    monthly_trend: list[dict]
    diversity: DiversityIndexResponse
