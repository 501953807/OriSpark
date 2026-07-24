"""SCR 信誉系统 Pydantic 模型."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class ScoreSchema(BaseModel):
    id: str
    user_id: str
    overall_score: float
    rating_level: str
    fulfillment_count: int
    default_count: int
    late_review_count: int
    complaint_count: int
    cleared_count: int
    avg_response_hours: float
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class HistoryCreate(BaseModel):
    user_id: str
    score_delta: float
    reason: str
    related_transaction_id: Optional[str] = None
    description: Optional[str] = None


class HistorySchema(BaseModel):
    id: str
    user_id: str
    score_delta: float
    reason: str
    related_transaction_id: Optional[str] = None
    description: Optional[str] = None
    created_at: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class LeaderboardEntry(BaseModel):
    user_id: str
    overall_score: float
    rating_level: str
    fulfillment_count: int
    default_count: int

    model_config = ConfigDict(from_attributes=True)
