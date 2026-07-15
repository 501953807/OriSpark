from sqlalchemy.orm import Session

from app.models.credit import (
    CreditRating, CreditBehavior, BEHAVIOR_SCORES, apply_behavior,
)


def get_or_create_rating(db: Session, user_id: str, user_type: str) -> CreditRating:
    """获取或创建信用评级."""
    rating = db.query(CreditRating).filter(
        CreditRating.user_id == user_id,
        CreditRating.user_type == user_type,
    ).first()
    if not rating:
        rating = CreditRating(user_id=user_id, user_type=user_type)
        db.add(rating)
        # Don't commit here — let record_behavior handle the single commit
    return rating


def record_behavior(db: Session, req: dict) -> tuple[CreditRating, CreditBehavior]:
    """记录一条信用行为并更新评分."""
    rating = get_or_create_rating(db, req["user_id"], req.get("user_type", "creator"))

    behavior_type = req["behavior_type"]
    score_delta = req.get("score_delta", BEHAVIOR_SCORES.get(behavior_type, 0))

    behavior = CreditBehavior(
        rating_id=rating.id,
        user_id=req["user_id"],
        behavior_type=behavior_type,
        score_delta=score_delta,
        related_transaction_id=req.get("related_transaction_id"),
        description=req.get("description"),
    )
    db.add(behavior)

    rating = apply_behavior(rating, behavior_type, score_delta)

    db.commit()
    db.refresh(rating)
    db.refresh(behavior)
    return rating, behavior


def get_rating_by_user(db: Session, user_id: str) -> CreditRating | None:
    """按用户ID查询信用评级."""
    return db.query(CreditRating).filter(CreditRating.user_id == user_id).first()


def get_behaviors(db: Session, user_id: str, limit: int = 50) -> list[CreditBehavior]:
    """查询用户信用行为记录."""
    return (db.query(CreditBehavior)
            .filter(CreditBehavior.user_id == user_id)
            .order_by(CreditBehavior.created_at.desc())
            .limit(limit)
            .all())
