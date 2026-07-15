"""订阅系统 API 路由 — 对应: docs/modules-v3/04-monetization-engine.md
Phase 2: 创作者订阅层级
端点: 7 (subscription)"""

from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from typing import Optional

from app.database import get_db
from app.models.subscription import SubscriptionTier, SubscriptionSubscriber
from app.schemas.common import ApiResponse, PaginatedResponse, PaginationParams, SuccessResponse
from app.deps import require_auth

router = APIRouter()


class CreateTierPayload(BaseModel):
    name: str
    price: float
    description: Optional[str] = None
    currency: str = "CNY"
    period: str = "monthly"
    features: list = Field(default_factory=list)
    is_active: bool = True


class UpdateTierPayload(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    currency: Optional[str] = None
    period: Optional[str] = None
    features: Optional[list] = None
    is_active: Optional[bool] = None


class SubscribePayload(BaseModel):
    user_id: str
    tier_id: str


class CancelSubscriptionPayload(BaseModel):
    user_id: str


# ============================================================================
# 9.x 订阅等级管理
# ============================================================================


@router.get("/subscription/tiers", response_model=ApiResponse[list])
def list_tiers(
    is_active: Optional[bool] = None,
    db: Session = Depends(get_db),
):
    """获取所有订阅等级列表."""
    q = db.query(SubscriptionTier)
    if is_active is not None:
        q = q.filter(SubscriptionTier.is_active == is_active)
    tiers = q.order_by(SubscriptionTier.price).all()
    return ApiResponse(data=[
        {
            "id": t.id,
            "name": t.name,
            "description": t.description,
            "price": t.price,
            "currency": t.currency,
            "period": t.period,
            "features": t.features or [],
            "is_active": t.is_active,
            "created_at": t.created_at.isoformat() if t.created_at else None,
        }
        for t in tiers
    ])


@router.post("/subscription/tiers", response_model=ApiResponse[dict], dependencies=[Depends(require_auth)])
def create_tier(payload: CreateTierPayload, db: Session = Depends(get_db)):
    """创建订阅等级."""
    tier = SubscriptionTier(
        name=payload.name,
        description=payload.description,
        price=float(payload.price),
        currency=payload.currency,
        period=payload.period,
        features=payload.features or [],
        is_active=payload.is_active,
    )
    db.add(tier)
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise
    db.refresh(tier)
    return ApiResponse(data=_tier_to_dict(tier), message="等级创建成功")


@router.put("/subscription/tiers/{tier_id}", response_model=ApiResponse[dict], dependencies=[Depends(require_auth)])
@router.patch("/subscription/tiers/{tier_id}", response_model=ApiResponse[dict], dependencies=[Depends(require_auth)])
def update_tier(tier_id: str, payload: UpdateTierPayload, db: Session = Depends(get_db)):
    """更新订阅等级."""
    tier = db.query(SubscriptionTier).filter(SubscriptionTier.id == tier_id).first()
    if not tier:
        raise HTTPException(status_code=404, detail="等级不存在")
    update_data = payload.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(tier, key, value)
    tier.updated_at = datetime.utcnow()
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise
    db.refresh(tier)
    return ApiResponse(data=_tier_to_dict(tier), message="等级更新成功")


@router.delete("/subscription/tiers/{tier_id}", response_model=ApiResponse[SuccessResponse], dependencies=[Depends(require_auth)])
def delete_tier(tier_id: str, db: Session = Depends(get_db)):
    """删除订阅等级."""
    tier = db.query(SubscriptionTier).filter(SubscriptionTier.id == tier_id).first()
    if not tier:
        raise HTTPException(status_code=404, detail="等级不存在")
    db.delete(tier)
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise
    return ApiResponse(data={"success": True, "message": "等级已删除"})


# ============================================================================
# 9.x 订阅用户管理
# ============================================================================


@router.get("/subscription/subscribers", response_model=ApiResponse[list], dependencies=[Depends(require_auth)])
def list_subscribers(
    user_id: Optional[str] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """获取订阅用户列表."""
    q = db.query(SubscriptionSubscriber).join(SubscriptionTier)
    if user_id:
        q = q.filter(SubscriptionSubscriber.user_id == user_id)
    if status:
        q = q.filter(SubscriptionSubscriber.status == status)
    subs = q.all()
    return ApiResponse(data=[
        {
            "id": s.id,
            "user_id": s.user_id,
            "tier_id": s.tier_id,
            "tier_name": tier.name if (tier := db.query(SubscriptionTier).filter(SubscriptionTier.id == s.tier_id).first()) else None,
            "status": s.status,
            "subscribed_at": s.subscribed_at.isoformat() if s.subscribed_at else None,
            "cancelled_at": s.cancelled_at.isoformat() if s.cancelled_at else None,
            "expires_at": s.expires_at.isoformat() if s.expires_at else None,
        }
        for s in subs
    ])


@router.post("/subscription/subscribe", response_model=ApiResponse[dict], dependencies=[Depends(require_auth)])
def subscribe(payload: SubscribePayload, db: Session = Depends(get_db)):
    """订阅某个等级."""
    user_id = payload.user_id
    tier_id = payload.tier_id
    tier = db.query(SubscriptionTier).filter(
        SubscriptionTier.id == tier_id, SubscriptionTier.is_active == True
    ).first()
    if not tier:
        raise HTTPException(status_code=404, detail="订阅等级不存在或未激活")
    # Check if already subscribed
    existing = db.query(SubscriptionSubscriber).filter(
        SubscriptionSubscriber.user_id == user_id,
        SubscriptionSubscriber.tier_id == tier_id,
        SubscriptionSubscriber.status == "active",
    ).first()
    if existing:
        raise HTTPException(status_code=409, detail="已有活跃订阅")
    sub = SubscriptionSubscriber(
        user_id=user_id,
        tier_id=tier_id,
        status="active",
        subscribed_at=datetime.utcnow(),
        expires_at=datetime.utcnow() + (
            datetime(9999, 12, 31) if tier.period == "yearly"
            else datetime.utcnow().replace(year=datetime.utcnow().year + 1)
        ),
    )
    # Cancel previous subscriptions
    db.query(SubscriptionSubscriber).filter(
        SubscriptionSubscriber.user_id == user_id,
        SubscriptionSubscriber.status == "active",
    ).update({"status": "cancelled", "cancelled_at": datetime.utcnow()})
    db.add(sub)
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise
    db.refresh(sub)
    return ApiResponse(data=_sub_to_dict(sub), message="订阅成功")


@router.post("/subscription/cancel", response_model=ApiResponse[dict], dependencies=[Depends(require_auth)])
def cancel_subscription(payload: CancelSubscriptionPayload, db: Session = Depends(get_db)):
    """取消订阅."""
    user_id = payload.user_id
    sub = db.query(SubscriptionSubscriber).filter(
        SubscriptionSubscriber.user_id == user_id,
        SubscriptionSubscriber.status == "active",
    ).first()
    if not sub:
        raise HTTPException(status_code=404, detail="无活跃订阅")
    sub.status = "cancelled"
    sub.cancelled_at = datetime.utcnow()
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise
    return ApiResponse(data=_sub_to_dict(sub), message="订阅已取消")


def _tier_to_dict(t: SubscriptionTier) -> dict:
    return {
        "id": t.id,
        "name": t.name,
        "description": t.description,
        "price": t.price,
        "currency": t.currency,
        "period": t.period,
        "features": t.features or [],
        "is_active": t.is_active,
        "subscriber_count": len(t.subscribers) if hasattr(t, "subscribers") else 0,
        "created_at": t.created_at.isoformat() if t.created_at else None,
        "updated_at": t.updated_at.isoformat() if t.updated_at else None,
    }


def _sub_to_dict(s: SubscriptionSubscriber) -> dict:
    return {
        "id": s.id,
        "user_id": s.user_id,
        "tier_id": s.tier_id,
        "status": s.status,
        "subscribed_at": s.subscribed_at.isoformat() if s.subscribed_at else None,
        "cancelled_at": s.cancelled_at.isoformat() if s.cancelled_at else None,
        "expires_at": s.expires_at.isoformat() if s.expires_at else None,
    }
