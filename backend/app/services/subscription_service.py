"""订阅系统服务."""

from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.subscription import SubscriptionTier, SubscriptionSubscriber


def create_tier(db: Session, name: str, price: float, period: str = "monthly",
                description: Optional[str] = None, currency: str = "CNY",
                features: Optional[list] = None, is_active: bool = True) -> SubscriptionTier:
    """创建订阅等级."""
    tier = SubscriptionTier(
        name=name,
        description=description,
        price=price,
        currency=currency,
        period=period,
        features=features,
        is_active=is_active,
    )
    db.add(tier)
    db.commit()
    db.refresh(tier)
    return tier


def list_tiers(db: Session, is_active: Optional[bool] = None) -> list[SubscriptionTier]:
    """列出订阅等级."""
    query = db.query(SubscriptionTier)
    if is_active is not None:
        query = query.filter(SubscriptionTier.is_active == is_active)
    return query.order_by(SubscriptionTier.created_at.desc()).all()


def get_tier(db: Session, tier_id: str) -> Optional[SubscriptionTier]:
    """获取单个订阅等级."""
    return db.query(SubscriptionTier).filter(SubscriptionTier.id == tier_id).first()


def update_tier(db: Session, tier_id: str, data: dict) -> Optional[SubscriptionTier]:
    """更新订阅等级."""
    tier = get_tier(db, tier_id)
    if not tier:
        return None
    for key in ("name", "description", "price", "currency", "period", "features", "is_active"):
        if key in data:
            setattr(tier, key, data[key])
    db.commit()
    db.refresh(tier)
    return tier


def delete_tier(db: Session, tier_id: str) -> bool:
    """删除订阅等级."""
    tier = get_tier(db, tier_id)
    if not tier:
        return False
    db.delete(tier)
    db.commit()
    return True


def subscribe(db: Session, user_id: str, tier_id: str) -> SubscriptionSubscriber:
    """订阅某个等级."""
    tier = get_tier(db, tier_id)
    if not tier:
        raise ValueError(f"未知订阅等级: {tier_id}")
    if not tier.is_active:
        raise ValueError("该订阅等级已停用")

    # 检查是否已有活跃订阅
    existing = (
        db.query(SubscriptionSubscriber)
        .filter(
            SubscriptionSubscriber.user_id == user_id,
            SubscriptionSubscriber.tier_id == tier_id,
            SubscriptionSubscriber.status == "active",
        )
        .first()
    )
    if existing:
        raise ValueError("已有活跃订阅")

    subscriber = SubscriptionSubscriber(
        user_id=user_id,
        tier_id=tier_id,
        status="active",
    )
    # Calculate expiry based on tier period
    period_months = 12 if tier.period == "yearly" else 1
    subscriber.expires_at = datetime.now(timezone.utc) + timedelta(days=30 * period_months)
    db.add(subscriber)
    db.commit()
    db.refresh(subscriber)
    return subscriber


def unsubscribe(db: Session, user_id: str, tier_id: str) -> bool:
    """取消订阅."""
    sub = (
        db.query(SubscriptionSubscriber)
        .filter(
            SubscriptionSubscriber.user_id == user_id,
            SubscriptionSubscriber.tier_id == tier_id,
            SubscriptionSubscriber.status == "active",
        )
        .first()
    )
    if not sub:
        return False
    sub.status = "cancelled"
    sub.cancelled_at = datetime.now(timezone.utc)
    db.commit()
    return True


def list_subscribers(db: Session, status: Optional[str] = None) -> list[dict]:
    """获取订阅用户列表（带 tier 关联）."""
    q = db.query(SubscriptionSubscriber).join(SubscriptionTier)
    if status:
        q = q.filter(SubscriptionSubscriber.status == status)
    subs = q.all()
    return [
        {
            "id": s.id,
            "user_id": s.user_id,
            "tier_id": s.tier_id,
            "tier_name": s.tier.name if s.tier else None,
            "status": s.status,
            "subscribed_at": s.subscribed_at.isoformat() if s.subscribed_at else None,
            "cancelled_at": s.cancelled_at.isoformat() if s.cancelled_at else None,
            "expires_at": s.expires_at.isoformat() if s.expires_at else None,
        }
        for s in subs
    ]


def get_user_subscriptions(db: Session, user_id: str) -> list[dict]:
    """获取用户订阅列表."""
    subs = (
        db.query(SubscriptionSubscriber)
        .filter(SubscriptionSubscriber.user_id == user_id)
        .order_by(SubscriptionSubscriber.subscribed_at.desc())
        .all()
    )
    results = []
    for sub in subs:
        tier = sub.tier
        results.append({
            "id": sub.id,
            "user_id": sub.user_id,
            "tier": {
                "id": tier.id,
                "name": tier.name,
                "price": tier.price,
                "currency": tier.currency,
                "period": tier.period,
                "features": tier.features,
            } if tier else None,
            "status": sub.status,
            "subscribed_at": sub.subscribed_at.isoformat() if sub.subscribed_at else None,
            "cancelled_at": sub.cancelled_at.isoformat() if sub.cancelled_at else None,
            "expires_at": sub.expires_at.isoformat() if sub.expires_at else None,
        })
    return results
