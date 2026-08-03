"""订阅系统 API 路由 — 对应: docs/modules-v5/04-monetization-engine.md
Phase 2: 创作者订阅层级
端点: 7 (subscription)

业务逻辑已提取至 subscription_service.py.
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from typing import Optional

from app.database import get_db
from app.schemas.common import ApiResponse, SuccessResponse
from app.deps import require_auth
from app.services.subscription_service import (
    list_tiers, create_tier, get_tier, update_tier, delete_tier,
    subscribe, unsubscribe, get_user_subscriptions, list_subscribers,
)

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


def _tier_to_dict(tier) -> dict:
    return {
        "id": tier.id,
        "name": tier.name,
        "description": tier.description,
        "price": tier.price,
        "currency": tier.currency,
        "period": tier.period,
        "features": tier.features or [],
        "is_active": tier.is_active,
        "subscriber_count": len(tier.subscribers) if hasattr(tier, "subscribers") else 0,
        "created_at": tier.created_at.isoformat() if tier.created_at else None,
        "updated_at": tier.updated_at.isoformat() if tier.updated_at else None,
    }


def _sub_to_dict(sub) -> dict:
    return {
        "id": sub.id,
        "user_id": sub.user_id,
        "tier_id": sub.tier_id,
        "status": sub.status,
        "subscribed_at": sub.subscribed_at.isoformat() if sub.subscribed_at else None,
        "cancelled_at": sub.cancelled_at.isoformat() if sub.cancelled_at else None,
        "expires_at": sub.expires_at.isoformat() if sub.expires_at else None,
    }


# ============================================================================
# 9.x 订阅等级管理
# ============================================================================


@router.get("/subscription/tiers", response_model=ApiResponse)
def list_tiers_endpoint(
    is_active: Optional[bool] = None,
    db: Session = Depends(get_db),
):
    """获取所有订阅等级列表."""
    tiers = list_tiers(db, is_active)
    return ApiResponse(data=[_tier_to_dict(t) for t in tiers])


@router.post("/subscription/tiers", response_model=ApiResponse, dependencies=[Depends(require_auth)])
def create_tier_endpoint(payload: CreateTierPayload, db: Session = Depends(get_db)):
    """创建订阅等级."""
    tier = create_tier(
        db, payload.name, payload.price, payload.period,
        payload.description, payload.currency, payload.features, payload.is_active,
    )
    return ApiResponse(data=_tier_to_dict(tier), message="等级创建成功")


@router.put("/subscription/tiers/{tier_id}", response_model=ApiResponse, dependencies=[Depends(require_auth)])
@router.patch("/subscription/tiers/{tier_id}", response_model=ApiResponse, dependencies=[Depends(require_auth)])
def update_tier_endpoint(tier_id: str, payload: UpdateTierPayload, db: Session = Depends(get_db)):
    """更新订阅等级."""
    result = update_tier(db, tier_id, payload.model_dump(exclude_unset=True))
    if not result:
        raise HTTPException(status_code=404, detail="等级不存在")
    return ApiResponse(data=_tier_to_dict(result), message="等级更新成功")


@router.delete("/subscription/tiers/{tier_id}", response_model=ApiResponse, dependencies=[Depends(require_auth)])
def delete_tier_endpoint(tier_id: str, db: Session = Depends(get_db)):
    """删除订阅等级."""
    deleted = delete_tier(db, tier_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="等级不存在")
    return ApiResponse(data={"success": True, "message": "等级已删除"})


# ============================================================================
# 9.x 订阅用户管理
# ============================================================================


@router.get("/subscription/subscribers", response_model=ApiResponse, dependencies=[Depends(require_auth)])
def list_subscribers_endpoint(
    user_id: Optional[str] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """获取订阅用户列表."""
    if user_id:
        subs = get_user_subscriptions(db, user_id)
    else:
        # 全量查询 (需鉴权)
        subs = list_subscribers(db, status=status)
    return ApiResponse(data=subs)


@router.post("/subscription/subscribe", response_model=ApiResponse, dependencies=[Depends(require_auth)])
def subscribe_endpoint(payload: SubscribePayload, db: Session = Depends(get_db)):
    """订阅某个等级."""
    try:
        sub = subscribe(db, payload.user_id, payload.tier_id)
        return ApiResponse(data=_sub_to_dict(sub), message="订阅成功")
    except ValueError as e:
        detail = str(e)
        raise HTTPException(status_code=409 if "已有" in detail else 404, detail=detail)


@router.post("/subscription/cancel", response_model=ApiResponse, dependencies=[Depends(require_auth)])
def cancel_subscription_endpoint(payload: CancelSubscriptionPayload, db: Session = Depends(get_db)):
    """取消订阅."""
    try:
        deleted = unsubscribe(db, payload.user_id, None)
        if not deleted:
            raise HTTPException(status_code=404, detail="无活跃订阅")
        return ApiResponse(message="订阅已取消")
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))
