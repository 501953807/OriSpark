"""人类贡献度评分 API 路由 — G-01."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.human_contribution_service import (
    calculate_contribution_score,
    save_contribution_score,
)
from app.models.contribution import HumanContributionScore

router = APIRouter(prefix="/contributions", tags=["人类贡献度评分"])


@router.post("/calculate/{work_id}")
def post_calculate_score(work_id: str, db: Session = Depends(get_db)):
    """计算并保存指定作品的贡献度评分."""
    result = calculate_contribution_score(db, work_id, work_id)
    saved = save_contribution_score(db, work_id, work_id, result)
    return {
        "id": saved.id,
        "work_id": saved.work_id,
        "total_score": float(saved.total_score),
        "conclusion": saved.conclusion,
        "defense_tier": saved.defense_tier,
        "dimension_scores": result["dimension_scores"],
        "requires_disclosure": saved.requires_disclosure,
        "eligible_for_registration": saved.eligible_for_registration,
    }


@router.get("/scores/{work_id}")
def get_work_scores(work_id: str, db: Session = Depends(get_db)):
    """获取作品的贡献度评分历史."""
    scores = (
        db.query(HumanContributionScore)
        .filter(HumanContributionScore.work_id == work_id)
        .order_by(HumanContributionScore.created_at.desc())
        .all()
    )
    return [
        {
            "id": s.id,
            "total_score": float(s.total_score),
            "conclusion": s.conclusion,
            "defense_tier": s.defense_tier,
            "ai_session_score": float(s.ai_session_score),
            "mcp_event_score": float(s.mcp_event_score),
            "self_declare_score": float(s.self_declare_score),
            "duration_score": float(s.duration_score),
            "requires_disclosure": s.requires_disclosure,
            "eligible_for_registration": s.eligible_for_registration,
            "created_at": s.created_at.isoformat(),
        }
        for s in scores
    ]
