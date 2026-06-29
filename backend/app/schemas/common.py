"""通用 Pydantic 模型."""

from typing import Any, Generic, TypeVar, Optional
from datetime import datetime

from pydantic import BaseModel, ConfigDict

T = TypeVar("T")


class ApiResponse(BaseModel, Generic[T]):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    success: bool = True
    message: str = "ok"
    data: Optional[T] = None


class PaginatedResponse(BaseModel, Generic[T]):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    items: list[T]
    total: int
    page: int
    page_size: int
    total_pages: int


class PaginationParams(BaseModel):
    page: int = 1
    page_size: int = 20


class DashboardStats(BaseModel):
    total_works: int = 0
    total_notarized: int = 0
    infringement_alerts: int = 0
    monthly_revenue: float = 0.0
    recent_works: list[dict] = []
    upcoming_reminders: list[dict] = []


class ErrorResponse(BaseModel):
    success: bool = False
    message: str
    detail: Optional[str] = None


class SuccessResponse(BaseModel):
    success: bool = True
    message: str = "ok"
