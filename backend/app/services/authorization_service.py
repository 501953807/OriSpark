"""授权追踪与收益汇总服务."""

from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from app.models.ai_training_license import AITrainingLicense


def track_authorization(work_id: str, user_id: str, db: Session) -> dict:
    """记录作品被AI训练使用的授权事件，累加使用次数和收入."""
    license_rec = (
        db.query(AITrainingLicense)
        .filter(AITrainingLicense.work_id == work_id)
        .first()
    )
    if not license_rec or not license_rec.enabled:
        return {"error": "Work not licensed for AI training", "status": "rejected"}

    license_rec.total_uses += 1
    db.commit()
    db.refresh(license_rec)

    return {
        "work_id": work_id,
        "user_id": user_id,
        "total_uses": license_rec.total_uses,
        "tracked_at": datetime.now(timezone.utc).isoformat(),
        "status": "recorded",
    }


def get_authorization_summary(user_id: str, db: Session) -> dict:
    """获取创作者AI训练授权统计汇总."""
    now = datetime.now(timezone.utc)
    thirty_days_ago = now - timedelta(days=30)

    licenses = (
        db.query(AITrainingLicense)
        .filter(AITrainingLicense.enabled == True)
        .all()
    )

    total_uses = sum(l.total_uses for l in licenses)
    total_revenue_cents = sum(l.total_revenue_cents for l in licenses)
    total_revenue_yuan = round(total_revenue_cents * 0.07, 2)  # ~0.07 USD/CNY rate

    recent_activities = []
    for lic in licenses:
        recent_activities.append({
            "work_id": lic.work_id,
            "cc_protocol": lic.cc_protocol.value if hasattr(lic.cc_protocol, 'value') else str(lic.cc_protocol),
            "total_uses": lic.total_uses,
            "total_revenue_yuan": round(lic.total_revenue_cents * 0.07, 2),
            "price_per_use_cents": lic.price_per_use_cents,
        })

    return {
        "user_id": user_id,
        "total_authorized_works": len(licenses),
        "total_uses": total_uses,
        "total_revenue_yuan": total_revenue_yuan,
        "recent_activities": sorted(recent_activities, key=lambda x: x["total_uses"], reverse=True)[:5],
    }


def update_authorization(
    work_id: str,
    enabled: bool,
    cc_protocol: str | None,
    price_per_use_cents: int | None,
    db: Session,
) -> dict:
    """更新作品AI训练授权配置."""
    license_rec = (
        db.query(AITrainingLicense)
        .filter(AITrainingLicense.work_id == work_id)
        .first()
    )

    if not license_rec:
        license_rec = AITrainingLicense(
            work_id=work_id,
            enabled=enabled,
            cc_protocol=cc_protocol,
            price_per_use_cents=price_per_use_cents or 5,
        )
        db.add(license_rec)
    else:
        license_rec.enabled = enabled
        if cc_protocol:
            license_rec.cc_protocol = cc_protocol
        if price_per_use_cents is not None:
            license_rec.price_per_use_cents = price_per_use_cents
        license_rec.updated_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(license_rec)

    return {
        "work_id": work_id,
        "enabled": license_rec.enabled,
        "cc_protocol": license_rec.cc_protocol.value if hasattr(license_rec.cc_protocol, 'value') else str(license_rec.cc_protocol),
        "price_per_use_cents": license_rec.price_per_use_cents,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
