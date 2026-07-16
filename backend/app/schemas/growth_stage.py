"""创作者成长阶段 Pydantic schemas."""

from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class GrowthStageResponse(BaseModel):
    id: str
    user_id: str
    stage_key: str
    stage_name_zh: str
    monthly_revenue_yuan: float
    total_works: int
    total_certificates: int
    credit_score: float
    overall_progress_percent: float
    next_stage_progress_percent: float
    evaluated_at: str


class GrowthTaskResponse(BaseModel):
    id: str
    user_id: str
    stage_key: str
    task_category: str
    task_title: str
    task_description: Optional[str] = None
    is_completed: bool
    completed_at: Optional[str] = None
    priority: int


class StageInfo(BaseModel):
    key: str
    name_zh: str
    min_monthly_revenue: float
    max_monthly_revenue: float
    min_works: int
    min_certificates: int
    description_zh: str
    unlock_features: list[str]


class ProgressDashboard(BaseModel):
    current_stage: StageInfo
    progress_percent: float
    next_stage: Optional[StageInfo] = None
    remaining_to_next: dict
    completed_tasks: int
    total_tasks: int
