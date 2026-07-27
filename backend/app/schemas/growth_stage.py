"""创作者成长阶段 Pydantic schemas."""

from pydantic import BaseModel
from typing import Optional


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
    unlock_features: list[str] = []
    min_monthly_revenue: Optional[float] = None
    max_monthly_revenue: Optional[float] = None
    min_works: Optional[int] = None
    min_certificates: Optional[int] = None
    description_zh: Optional[str] = None


class NextStageInfo(BaseModel):
    key: str
    name_zh: Optional[str] = None


class RemainingToNext(BaseModel):
    monthly_revenue_gap: float = 0
    works_needed: int = 0
    certs_needed: int = 0


class ProgressDashboard(BaseModel):
    current_stage: StageInfo
    progress_percent: float
    next_stage: Optional[NextStageInfo] = None
    remaining_to_next: RemainingToNext
    completed_tasks: int
    total_tasks: int
    tasks: list[dict]
