"""私域流量路由."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user_id
from app.schemas.private_traffic import (
    SubscriptionLinkCreate,
    SubscriptionLinkResponse,
    FanCommunityCreate,
    FanCommunityResponse,
    FunnelEntryCreate,
    FunnelSummary,
)
from app.services.private_traffic_service import (
    create_subscription_link,
    list_subscription_links,
    update_subscription_count,
    create_community,
    list_communities,
    add_funnel_entry,
    get_funnel_summary,
)
from app.utils.audit import AuditLog

router = APIRouter(prefix="/private-traffic", tags=["private-traffic"])


@router.post("/subscriptions", response_model=SubscriptionLinkResponse)
def post_subscription(body: SubscriptionLinkCreate, actor_id: str = Depends(get_current_user_id), db: Session = Depends(get_db)):
    """添加付费订阅链接."""
    result = create_subscription_link(db, actor_id, body.model_dump())
    AuditLog.log(db, "create_subscription_link", f"Created subscription link by {actor_id}", actor_id)
    return result


@router.get("/subscriptions", response_model=list[dict])
def get_subscriptions(actor_id: str = Depends(get_current_user_id), db: Session = Depends(get_db)):
    """获取所有订阅链接."""
    result = list_subscription_links(db, actor_id)
    AuditLog.log(db, "list_subscription_links", f"Listed subscriptions by {actor_id}", actor_id)
    return result


@router.patch("/subscriptions/{link_id}")
def patch_subscription(link_id: str, body: dict, actor_id: str = Depends(get_current_user_id), db: Session = Depends(get_db)):
    """更新订阅链接."""
    from app.services.private_traffic_service import update_subscription_count
    return update_subscription_count(db, link_id, body.get("subscriber_count", 0))


@router.post("/communities", response_model=FanCommunityResponse)
def post_community(body: FanCommunityCreate, actor_id: str = Depends(get_current_user_id), db: Session = Depends(get_db)):
    """创建粉丝社群."""
    result = create_community(db, actor_id, body.model_dump())
    AuditLog.log(db, "create_fan_community", f"Created community by {actor_id}", actor_id)
    return result


@router.get("/communities", response_model=list[FanCommunityResponse])
def get_communities(actor_id: str = Depends(get_current_user_id), db: Session = Depends(get_db)):
    """获取所有粉丝社群."""
    result = list_communities(db, actor_id)
    AuditLog.log(db, "list_communities", f"Listed communities by {actor_id}", actor_id)
    return result


@router.post("/funnel", response_model=dict)
def post_funnel(body: FunnelEntryCreate, actor_id: str = Depends(get_current_user_id), db: Session = Depends(get_db)):
    """添加漏斗数据."""
    result = add_funnel_entry(db, actor_id, body.model_dump())
    AuditLog.log(db, "add_funnel_entry", f"Added funnel entry by {actor_id}", actor_id)
    return result


@router.get("/funnel-summary", response_model=FunnelSummary)
def get_funnel(actor_id: str = Depends(get_current_user_id), db: Session = Depends(get_db)):
    """获取漏斗汇总."""
    result = get_funnel_summary(db, actor_id)
    AuditLog.log(db, "view_funnel_summary", f"Viewed funnel summary by {actor_id}", actor_id)
    return result
