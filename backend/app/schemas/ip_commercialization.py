from pydantic import BaseModel
from typing import Optional
from app.models.ip_commercialization import IPEvaluationStage


class IPAssessmentCreate(BaseModel):
    work_id: str
    ip_name: str
    originality_score: float
    market_demand_score: float
    competition_density: float
    monetization_potential: float


class IPAssessmentResponse(BaseModel):
    id: str
    work_id: str
    ip_name: str
    overall_score: Optional[float]
    current_stage: IPEvaluationStage
    brand_premium_estimate: Optional[float]
    trademark_classes: Optional[list[str]]
