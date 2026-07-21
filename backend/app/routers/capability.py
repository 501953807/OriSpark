"""创作者能力评估路由."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.capability import (
    DimensionCreate,
    DimensionSchema,
    AssessmentCreate,
    AssessmentResponse,
    PremiumRequest,
    PremiumResponse,
    AIPredictionRequest,
    AIPredictionResponse,
)
from app.services.capability_service import (
    create_assessment,
    calculate_skill_premium,
    assess_ai_risk,
    get_stage_recommendation,
    AI_VULNERABILITY,
)
from app.models.capability import CapabilityDimension
from app.services.capability_service import AI_VULNERABILITY

router = APIRouter(prefix="/capability", tags=["creator-capability"])


@router.get("/dimensions", response_model=list[DimensionSchema])
def list_dimensions(db: Session = Depends(get_db)):
    """获取所有能力维度."""
    return db.query(CapabilityDimension).filter(
        CapabilityDimension.is_active == True
    ).all()


@router.post("/assessments", response_model=AssessmentResponse)
def post_assessment(req: AssessmentCreate, db: Session = Depends(get_db)):
    """创建能力评估."""
    result = create_assessment(db, "current_user", req.dimension_scores)
    return result


@router.post("/premium", response_model=PremiumResponse)
def calc_premium(req: PremiumRequest):
    """计算技能组合溢价."""
    # 简化：直接用 skills 数量估算
    mock_scores = {s: 60.0 for s in req.skills}
    result = calculate_skill_premium(mock_scores)
    return PremiumResponse(
        premium_percent=result["total"],
        breakdown=result["breakdown"],
    )


@router.post("/ai-risk", response_model=AIPredictionResponse)
def predict_ai_risk(req: AIPredictionRequest):
    """AI 替代风险评估."""
    mock_scores = {s: 50.0 for s in req.current_skills}
    result = assess_ai_risk(mock_scores)
    vuln = AI_VULNERABILITY.get(req.work_type, AI_VULNERABILITY["default"])
    return AIPredictionResponse(
        risk_level=result["risk_level"],
        risk_score=result["risk_score"],
        vulnerable_skills=vuln["high_risk"],
        moat_building_tips=vuln["low_risk"],
    )


@router.get("/stage-recommendation")
def get_stage(score: float):
    """获取阶段推荐."""
    stage = get_stage_recommendation(score)
    if not stage:
        raise HTTPException(404, "Stage not found")
    return stage
