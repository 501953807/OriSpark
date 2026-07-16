"""维权ROI计算器 Pydantic schemas."""

from pydantic import BaseModel
from typing import Optional
from datetime import date


class EnforcementCaseCreate(BaseModel):
    """创建维权案例请求."""
    work_id: Optional[str] = None
    infringement_type: str
    target_platform: str
    estimated_loss_yuan: float
    action_taken: str
    cost_yuan: float = 0
    compensation_received_yuan: float = 0
    outcome: str
    notes: Optional[str] = None


class EnforcementCaseResponse(BaseModel):
    """维权案例响应."""
    id: str
    user_id: str
    work_id: Optional[str] = None
    infringement_type: str
    target_platform: str
    estimated_loss_yuan: float
    cost_yuan: float
    time_to_resolve_days: Optional[int] = None
    compensation_received_yuan: float
    outcome: str
    roi_percent: Optional[float]
    created_at: str


class CaseReferenceSchema(BaseModel):
    """参考案例响应."""
    id: str
    infringement_type: str
    target_platform: str
    typical_cost_range_low: Optional[float] = None
    typical_cost_range_high: Optional[float] = None
    resolution_time_days_low: Optional[int] = None
    resolution_time_days_high: Optional[int] = None
    win_rate_percent: Optional[float] = None
    avg_compensation_yuan: Optional[float] = None
    roi_tier: Optional[str] = None


class DecisionTreeResult(BaseModel):
    """决策树推荐结果."""
    recommended_actions: list[dict]
    primary_recommendation: dict
    reasoning: str


class RoiPredictorRequest(BaseModel):
    """ROI预测器请求."""
    work_value_yuan: float
    infringement_type: str
    target_platform: str
    action_type: str  # "cease_desist" / "platform_complaint" / "civil_lawsuit" / "criminal_report"


class RoiPrediction(BaseModel):
    """ROI预测结果."""
    expected_cost: float
    expected_duration_days: int
    win_probability: float
    expected_compensation: float
    net_return: float
    roi_percent: float
    risk_level: str  # "low" / "medium" / "high"


class DefenseTierSchema(BaseModel):
    """防御预算层级响应."""
    id: str
    tier_key: str
    tier_name_zh: str
    monthly_cost_low: Optional[float] = None
    monthly_cost_high: Optional[float] = None
    annual_cost_low: Optional[float] = None
    annual_cost_high: Optional[float] = None
    features: Optional[list[str]] = None
    description_zh: Optional[str] = None
