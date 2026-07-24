"""SCR 分布式信誉系统 API 路由."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.common import ApiResponse
from app.schemas.scr_reputation import (
    ScoreSchema,
    HistoryCreate,
    HistorySchema,
    LeaderboardEntry,
)
from app.services.scr_reputation_service import (
    update_score,
    get_or_create_score,
    get_leaderboard,
)
from app.deps import require_auth
from app.models.scr_reputation import SCRScore as SCRScoreModel, SCRHistory as SCRHistoryModel

router = APIRouter()


def _score_to_dict(s: SCRScoreModel) -> dict:
    return {
        "id": s.id,
        "user_id": s.user_id,
        "overall_score": float(s.overall_score),
        "rating_level": s.rating_level,
        "fulfillment_count": s.fulfillment_count,
        "default_count": s.default_count,
        "late_review_count": s.late_review_count,
        "complaint_count": s.complaint_count,
        "cleared_count": s.cleared_count,
        "avg_response_hours": float(s.avg_response_hours) if s.avg_response_hours else 24.0,
        "created_at": s.created_at.isoformat() if s.created_at else None,
        "updated_at": s.updated_at.isoformat() if s.updated_at else None,
    }


def _history_to_dict(h: SCRHistoryModel) -> dict:
    return {
        "id": h.id,
        "user_id": h.user_id,
        "score_delta": float(h.score_delta),
        "reason": h.reason,
        "related_transaction_id": h.related_transaction_id,
        "description": h.description,
        "created_at": h.created_at.isoformat() if h.created_at else None,
    }


@router.get("/scr/score/{user_id}", response_model=ApiResponse)
def get_score(user_id: str, db: Session = Depends(get_db)):
    """获取用户 SCR 评分."""
    score = get_or_create_score(db, user_id)
    return ApiResponse(data=_score_to_dict(score))


@router.post("/scr/report", response_model=ApiResponse)
def submit_report(body: HistoryCreate, db: Session = Depends(get_db), _auth=Depends(require_auth)):
    """提交评价，触发评分更新."""
    score = update_score(
        db,
        user_id=body.user_id,
        reason=body.reason,
        related_transaction_id=body.related_transaction_id,
        description=body.description,
    )
    return ApiResponse(data=_score_to_dict(score), message="评分已更新")


@router.get("/scr/history/{user_id}", response_model=ApiResponse)
def get_history(user_id: str, db: Session = Depends(get_db)):
    """获取评分历史."""
    records = (
        db.query(SCRHistoryModel)
        .filter(SCRHistoryModel.user_id == user_id)
        .order_by(SCRHistoryModel.created_at.desc())
        .limit(50)
        .all()
    )
    return ApiResponse(data=[_history_to_dict(r) for r in records])


@router.get("/scr/leaderboard", response_model=ApiResponse)
def leaderboard(limit: int = 50, db: Session = Depends(get_db)):
    """获取信誉排行榜."""
    scores = get_leaderboard(db, limit)
    return ApiResponse(data=[_score_to_dict(s) for s in scores])
