"""私域流量路由."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
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

router = APIRouter(prefix="/api/private-traffic", tags=["private-traffic"])

USER_ID = "current_user"


@router.post("/subscriptions", response_model=SubscriptionLinkResponse)
def post_subscription(body: SubscriptionLinkCreate, db: Session = Depends(get_db)):
    """添加付费订阅链接."""
    return create_subscription_link(db, USER_ID, body.model_dump())


@router.get("/subscriptions", response_model=list[dict])
def get_subscriptions(db: Session = Depends(get_db)):
    """获取所有订阅链接."""
    return list_subscription_links(db, USER_ID)


@router.patch("/subscriptions/{link_id}")
def patch_subscription(link_id: str, body: dict, db: Session = Depends(get_db)):
    """更新订阅链接."""
    return update_subscription_count(db, link_id, body.get("subscriber_count", 0))


@router.post("/communities", response_model=FanCommunityResponse)
def post_community(body: FanCommunityCreate, db: Session = Depends(get_db)):
    """创建粉丝社群."""
    return create_community(db, USER_ID, body.model_dump())


@router.get("/communities", response_model=list[FanCommunityResponse])
def get_communities(db: Session = Depends(get_db)):
    """获取所有粉丝社群."""
    return list_communities(db, USER_ID)


@router.post("/funnel", response_model=dict)
def post_funnel(body: FunnelEntryCreate, db: Session = Depends(get_db)):
    """添加漏斗数据."""
    return add_funnel_entry(db, USER_ID, body.model_dump())


@router.get("/funnel-summary", response_model=FunnelSummary)
def get_funnel(db: Session = Depends(get_db)):
    """获取漏斗汇总."""
    return get_funnel_summary(db, USER_ID)
