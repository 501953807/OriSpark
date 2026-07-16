"""私域流量管理服务层."""

from datetime import datetime, date
from typing import Optional

from sqlalchemy.orm import Session

from app.models.private_traffic import SubscriptionLink, FanCommunity, ConversionFunnel


def create_subscription_link(db: Session, user_id: str, data: dict) -> dict:
    """添加付费订阅链接."""
    link = SubscriptionLink(
        user_id=user_id,
        platform=data["platform"],
        url=data["url"],
        subscriber_count=data.get("subscriber_count", 0),
        monthly_revenue=data.get("monthly_revenue", 0),
        currency=data.get("currency", "CNY"),
    )
    db.add(link)
    db.commit()
    db.refresh(link)
    return {
        "id": link.id,
        "user_id": link.user_id,
        "platform": link.platform,
        "url": link.url,
        "subscriber_count": link.subscriber_count,
        "monthly_revenue": link.monthly_revenue,
        "currency": link.currency,
        "is_active": link.is_active,
        "created_at": link.created_at.isoformat(),
    }


def list_subscription_links(db: Session, user_id: str) -> list[dict]:
    """获取所有订阅链接."""
    links = db.query(SubscriptionLink).filter(
        SubscriptionLink.user_id == user_id,
        SubscriptionLink.is_active == True,
    ).all()
    return [
        {
            "id": l.id,
            "platform": l.platform,
            "url": l.url,
            "subscriber_count": l.subscriber_count,
            "monthly_revenue": l.monthly_revenue,
            "currency": l.currency,
            "total_monthly": sum(
                l2.monthly_revenue for l2 in links if l2.is_active
            ),
        }
        for l in links
    ]


def update_subscription_count(db: Session, link_id: str, count: int) -> dict:
    """更新订阅者数量."""
    link = db.query(SubscriptionLink).filter(
        SubscriptionLink.id == link_id
    ).first()
    if not link:
        raise ValueError("Link not found")
    link.subscriber_count = count
    db.commit()
    db.refresh(link)
    return {"id": link.id, "subscriber_count": link.subscriber_count}


def create_community(db: Session, user_id: str, data: dict) -> dict:
    """创建粉丝社群."""
    community = FanCommunity(
        user_id=user_id,
        platform=data["platform"],
        name=data["name"],
        invite_url=data.get("invite_url"),
        member_count=data.get("member_count", 0),
        tags=data.get("tags"),
        description=data.get("description"),
    )
    db.add(community)
    db.commit()
    db.refresh(community)
    return {
        "id": community.id,
        "user_id": community.user_id,
        "platform": community.platform,
        "name": community.name,
        "invite_url": community.invite_url,
        "member_count": community.member_count,
        "tags": community.tags,
        "description": community.description,
        "is_active": community.is_active,
    }


def list_communities(db: Session, user_id: str) -> list[dict]:
    """获取所有粉丝社群."""
    communities = db.query(FanCommunity).filter(
        FanCommunity.user_id == user_id,
        FanCommunity.is_active == True,
    ).all()
    return [
        {
            "id": c.id,
            "platform": c.platform,
            "name": c.name,
            "invite_url": c.invite_url,
            "member_count": c.member_count,
            "tags": c.tags,
            "description": c.description,
        }
        for c in communities
    ]


def add_funnel_entry(db: Session, user_id: str, data: dict) -> dict:
    """添加漏斗数据点."""
    entry = ConversionFunnel(
        user_id=user_id,
        source_platform=data["source_platform"],
        public_views=data.get("public_views", 0),
        profile_clicks=data.get("profile_clicks", 0),
        link_clicks=data.get("link_clicks", 0),
        converted_subscribers=data.get("converted_subscribers", 0),
        tracked_date=datetime.utcnow(),
        notes=data.get("notes"),
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return {
        "id": entry.id,
        "source_platform": entry.source_platform,
        "public_views": entry.public_views,
        "profile_clicks": entry.profile_clicks,
        "link_clicks": entry.link_clicks,
        "converted_subscribers": entry.converted_subscribers,
        "tracked_date": entry.tracked_date.isoformat(),
    }


def get_funnel_summary(db: Session, user_id: str) -> dict:
    """获取漏斗汇总统计."""
    entries = db.query(ConversionFunnel).filter(
        ConversionFunnel.user_id == user_id,
    ).all()

    total_views = sum(e.public_views for e in entries)
    total_clicks = sum(e.profile_clicks for e in entries)
    total_link = sum(e.link_clicks for e in entries)
    total_conv = sum(e.converted_subscribers for e in entries)

    by_platform: dict[str, dict] = {}
    for e in entries:
        if e.source_platform not in by_platform:
            by_platform[e.source_platform] = {
                "platform": e.source_platform,
                "views": 0, "clicks": 0, "links": 0, "converted": 0,
            }
        by_platform[e.source_platform]["views"] += e.public_views
        by_platform[e.source_platform]["clicks"] += e.profile_clicks
        by_platform[e.source_platform]["links"] += e.link_clicks
        by_platform[e.source_platform]["converted"] += e.converted_subscribers

    for p in by_platform.values():
        p["profile_ctr"] = round(p["clicks"] / p["views"] * 100, 1) if p["views"] > 0 else 0
        p["link_ctr"] = round(p["links"] / p["clicks"] * 100, 1) if p["clicks"] > 0 else 0
        p["conv_rate"] = round(p["converted"] / p["links"] * 100, 1) if p["links"] > 0 else 0

    return {
        "total_public_views": total_views,
        "total_profile_clicks": total_clicks,
        "total_link_clicks": total_link,
        "total_converted": total_conv,
        "overall_conversion_rate": round(total_conv / total_views * 100, 2) if total_views > 0 else 0,
        "by_platform": list(by_platform.values()),
    }
