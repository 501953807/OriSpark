"""SCR 信誉系统业务逻辑."""

from decimal import Decimal
from typing import Optional

from sqlalchemy.orm import Session

from app.models.scr_reputation import SCRScore, SCRHistory


RATING_THRESHOLDS = {
    "gold": (90.0, 100.01),
    "silver": (75.0, 90.0),
    "bronze": (55.0, 75.0),
    "starter": (0.0, 55.0),
}

SCORE_DELTA = {
    "fulfillment": 5.0,
    "default": -10.0,
    "late_review": -3.0,
    "complaint": -5.0,
    "cleared": 3.0,
}


def get_or_create_score(db: Session, user_id: str) -> SCRScore:
    """获取或初始化用户的 SCR 评分."""
    score = db.query(SCRScore).filter(SCRScore.user_id == user_id).first()
    if not score:
        score = SCRScore(user_id=user_id, overall_score=Decimal("50.00"))
        db.add(score)
        db.flush()
    return score


def update_score(
    db: Session,
    user_id: str,
    reason: str,
    related_transaction_id: Optional[str] = None,
    description: Optional[str] = None,
) -> SCRScore:
    """根据事件更新用户 SCR 评分并记录历史."""
    delta = SCORE_DELTA.get(reason, 0.0)
    score = get_or_create_score(db, user_id)

    old_score = float(score.overall_score)
    new_score = max(0.0, min(100.0, old_score + delta))
    score.overall_score = Decimal(str(new_score))

    # 更新计数器
    if reason == "fulfillment":
        score.fulfillment_count += 1
    elif reason == "default":
        score.default_count += 1
    elif reason == "late_review":
        score.late_review_count += 1
    elif reason == "complaint":
        score.complaint_count += 1
    elif reason == "cleared":
        score.cleared_count += 1

    # 更新等级
    score.rating_level = _compute_rating(new_score)

    # 记录历史
    hist = SCRHistory(
        user_id=user_id,
        score_delta=Decimal(str(delta)),
        reason=reason,
        related_transaction_id=related_transaction_id,
        description=description,
    )
    db.add(hist)
    db.flush()

    return score


def _compute_rating(score: float) -> str:
    for level, (low, high) in RATING_THRESHOLDS.items():
        if low <= score < high:
            return level
    return "starter"


def get_leaderboard(db: Session, limit: int = 50) -> list[SCRScore]:
    """获取信誉排行榜."""
    return (
        db.query(SCRScore)
        .order_by(SCRScore.overall_score.desc(), SCRScore.fulfillment_count.desc())
        .limit(limit)
        .all()
    )
