"""创作者能力评估 Pydantic schemas."""

from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class DimensionCreate(BaseModel):
    """创建能力维度."""
    dimension_key: str
    name_zh: str
    description: Optional[str] = None
    weight: float = 1.0


class DimensionSchema(BaseModel):
    """能力维度响应."""
    id: str
    dimension_key: str
    name_zh: str
    description: Optional[str] = None
    weight: float
    is_active: bool


class AssessmentCreate(BaseModel):
    """创建评估请求."""
    dimension_scores: dict[str, float]  # {dimension_key: 0-100}


class AssessmentResponse(BaseModel):
    """评估结果响应."""
    id: str
    user_id: str
    overall_score: Optional[float] = None
    dimension_scores: Optional[dict] = None
    skill_premium_percent: Optional[float] = None
    ai_risk_level: Optional[str] = None
    ai_risk_description: Optional[str] = None
    created_at: datetime


class PremiumRequest(BaseModel):
    """技能溢价计算请求."""
    skills: list[str]
    years_experience: int
    work_count: int


class PremiumResponse(BaseModel):
    """技能溢价响应."""
    premium_percent: float
    breakdown: dict[str, float]


class StageRecommendation(BaseModel):
    """阶段推荐."""
    stage_key: str
    stage_name_zh: str
    recommended_skills: Optional[list[str]] = None
    milestone_tasks: Optional[list[str]] = None


class AIPredictionRequest(BaseModel):
    """AI 替代风险评估请求."""
    current_skills: list[str]
    work_type: str
    experience_years: int


class AIPredictionResponse(BaseModel):
    """AI 替代风险评估响应."""
    risk_level: str  # low / medium / high
    risk_score: float  # 0-100
    vulnerable_skills: list[str]
    moat_building_tips: list[str]
