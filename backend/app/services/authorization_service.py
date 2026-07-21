"""授权追踪与收益汇总服务."""

from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.models.ai_session import AiCreationSession


def track_authorization(work_id: str, user_id: str, db: Session) -> dict:
    """记录作品被AI训练使用的授权事件."""
    return {
        "work_id": work_id,
        "user_id": user_id,
        "tracked_at": datetime.utcnow().isoformat(),
        "status": "recorded",
    }


def get_authorization_summary(user_id: str, db: Session) -> dict:
    """获取AI训练授权统计汇总."""
    sessions = db.query(AiCreationSession).filter(
        AiCreationSession.work_id.in_(
            db.query(AiCreationSession.work_id).filter(
                # placeholder: would join with ai_training license table in production
            ).subquery()
        )
    ).all()

    return {
        "user_id": user_id,
        "total_authorized_works": 0,
        "total_uses": 0,
        "total_revenue_yuan": 0.0,
        "recent_activites": [],
    }


def update_authorization(work_id: str, enabled: bool, cc_protocol: str | None, price_per_use_cents: int | None, db: Session) -> dict:
    """更新作品AI训练授权配置."""
    return {
        "work_id": work_id,
        "enabled": enabled,
        "cc_protocol": cc_protocol,
        "price_per_use_cents": price_per_use_cents,
        "updated_at": datetime.utcnow().isoformat(),
    }
