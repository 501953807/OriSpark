from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.credit import CreditRatingCreate, CreditBehaviorRecord, CreditRatingSchema, CreditBehaviorSchema
from app.services.credit_service import record_behavior, get_rating_by_user, get_behaviors, get_improvement_suggestions

router = APIRouter(prefix="/credit", tags=["credit"])


@router.post("/behavior", response_model=dict)
def post_record_behavior(body: CreditBehaviorRecord, db: Session = Depends(get_db)):
    """记录一条信用行为."""
    rating, behavior = record_behavior(db, body.model_dump())
    return {
        "rating": {
            "id": rating.id, "total_score": rating.total_score,
            "tier": rating.tier, "transaction_count": rating.transaction_count,
            "successful_transactions": rating.successful_transactions,
            "dispute_count": rating.dispute_count,
        },
        "behavior": {"id": behavior.id, "score_delta": behavior.score_delta},
    }


@router.get("/rating/{user_id}", response_model=CreditRatingSchema)
def get_rating(user_id: str, db: Session = Depends(get_db)):
    """查询用户信用评级."""
    rating = get_rating_by_user(db, user_id)
    if not rating:
        raise HTTPException(status_code=404, detail="Credit rating not found")
    return CreditRatingSchema(
        id=rating.id, user_id=rating.user_id, user_type=rating.user_type,
        total_score=rating.total_score, tier=rating.tier,
        transaction_count=rating.transaction_count,
        successful_transactions=rating.successful_transactions,
        dispute_count=rating.dispute_count,
        tier_history=rating.tier_history,
        created_at=rating.created_at,
    )


@router.get("/behaviors/{user_id}", response_model=list[CreditBehaviorSchema])
def get_user_behaviors(user_id: str, limit: int = 50, db: Session = Depends(get_db)):
    """查询用户信用行为历史."""
    behaviors = get_behaviors(db, user_id, limit)
    return [CreditBehaviorSchema(id=b.id, user_id=b.user_id, behavior_type=b.behavior_type,
                                 score_delta=b.score_delta, created_at=b.created_at)
            for b in behaviors]


@router.get("/improvement-suggestions/{user_id}", response_model=dict)
def get_improvements(user_id: str, db: Session = Depends(get_db)):
    """获取信用提升建议."""
    suggestions = get_improvement_suggestions(user_id, db)
    return {"data": suggestions}
