"""多平台内容分发流水线服务层."""

from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy.orm import Session

from app.models.content_pipeline import (
    PlatformAccount, ContentTemplate, MultiPlatformSchedule, PublishLog,
)


PLATFORMS = {
    "xiaohongshu": {"name_zh": "小红书", "max_tags": 10, "recommended_cover": "vertical"},
    "bilibili": {"name_zh": "B站", "max_tags": 5, "recommended_cover": "horizontal"},
    "douyin": {"name_zh": "抖音", "max_tags": 10, "recommended_cover": "vertical"},
    "weibo": {"name_zh": "微博", "max_tags": 0, "recommended_cover": "square"},
    "zhihu": {"name_zh": "知乎", "max_tags": 3, "recommended_cover": "horizontal"},
    "kuaishou": {"name_zh": "快手", "max_tags": 10, "recommended_cover": "vertical"},
}


def list_accounts(db: Session, user_id: str) -> list[PlatformAccount]:
    return db.query(PlatformAccount).filter(
        PlatformAccount.user_id == user_id,
        PlatformAccount.is_active == True,
    ).all()


def add_account(db: Session, user_id: str, platform: str, account_name: str,
                account_id: Optional[str] = None, follower_count: int = 0) -> dict:
    existing = db.query(PlatformAccount).filter(
        PlatformAccount.user_id == user_id,
        PlatformAccount.platform == platform,
    ).first()
    if existing:
        existing.account_name = account_name
        existing.account_id = account_id
        existing.follower_count = follower_count
        existing.updated_at = datetime.utcnow()
        db.flush()
        return {"id": existing.id, "action": "updated"}
    acc = PlatformAccount(
        user_id=user_id,
        platform=platform,
        account_name=account_name,
        account_id=account_id,
        follower_count=follower_count,
    )
    db.add(acc)
    db.flush()
    return {"id": acc.id, "action": "created"}


def remove_account(db: Session, user_id: str, platform: str) -> bool:
    acc = db.query(PlatformAccount).filter(
        PlatformAccount.user_id == user_id,
        PlatformAccount.platform == platform,
    ).first()
    if not acc:
        return False
    acc.is_active = False
    db.commit()
    return True


def get_scheduled_publishes(db: Session, user_id: str, status: Optional[str] = None) -> list[MultiPlatformSchedule]:
    q = db.query(MultiPlatformSchedule).filter(
        MultiPlatformSchedule.user_id == user_id,
        MultiPlatformSchedule.status == "scheduled",
    )
    if status:
        q = q.filter(MultiPlatformSchedule.status == status)
    return q.order_by(MultiPlatformSchedule.scheduled_at.asc()).all()


def create_schedule(db: Session, user_id: str, title: str, description: Optional[str],
                    work_id: Optional[str], platforms: list[dict], scheduled_at: datetime,
                    is_recurring: bool = False, recurring_pattern: Optional[str] = None) -> dict:
    schedule = MultiPlatformSchedule(
        user_id=user_id,
        work_id=work_id,
        title=title,
        description=description,
        platforms=platforms,
        scheduled_at=scheduled_at,
        is_recurring=is_recurring,
        recurring_pattern=recurring_pattern,
    )
    db.add(schedule)
    db.flush()
    return {"id": schedule.id, "scheduled_at": schedule.scheduled_at.isoformat()}


def cancel_schedule(db: Session, user_id: str, schedule_id: str) -> bool:
    s = db.query(MultiPlatformSchedule).filter(
        MultiPlatformSchedule.id == schedule_id,
        MultiPlatformSchedule.user_id == user_id,
    ).first()
    if not s:
        return False
    s.status = "cancelled"
    db.flush()
    return True


def simulate_publish(title: str, description: Optional[str], platforms: list[str],
                     tags: Optional[list[str]] = None) -> list[dict]:
    """模拟发布到多个平台，返回各平台的适配建议."""
    results = []
    for p in platforms:
        info = PLATFORMS.get(p)
        if not info:
            continue
        result = {
            "platform": p,
            "platform_name": info["name_zh"],
            "recommended_cover": info["recommended_cover"],
            "max_tags": info["max_tags"],
            "title_adapted": _adapt_title(title, p),
            "tags_count": len(tags or []),
            "tags_ok": (len(tags or []) <= info["max_tags"]) if info["max_tags"] > 0 else True,
        }
        results.append(result)
    return results


def _adapt_title(title: str, platform: str) -> str:
    """根据平台特性给出标题适配建议."""
    hints = {
        "xiaohongshu": f"【{title}】 — 小红书适合加emoji和标签词",
        "bilibili": f"{title} — B站建议保留原标题或加副标题",
        "douyin": f"# {title} # — 抖音适合话题标签格式",
        "weibo": f"[原创]{title} — 微博适合标注原创",
        "zhihu": f"关于{title}的分享 — 知乎适合叙述式标题",
    }
    return hints.get(platform, title)


def get_publish_stats(db: Session, user_id: str) -> dict:
    """获取发布统计: 总计划/已发布/失败/待发布."""
    total = db.query(MultiPlatformSchedule).filter(MultiPlatformSchedule.user_id == user_id).count()
    scheduled = db.query(MultiPlatformSchedule).filter(
        MultiPlatformSchedule.user_id == user_id, MultiPlatformSchedule.status == "scheduled",
    ).count()
    published = db.query(MultiPlatformSchedule).filter(
        MultiPlatformSchedule.user_id == user_id, MultiPlatformSchedule.status == "published",
    ).count()
    failed = db.query(MultiPlatformSchedule).filter(
        MultiPlatformSchedule.user_id == user_id, MultiPlatformSchedule.status == "failed",
    ).count()

    # 近7天发布趋势
    seven_days_ago = datetime.utcnow() - timedelta(days=7)
    recent_published = db.query(PublishLog).filter(
        PublishLog.user_id == user_id,
        PublishLog.status == "success",
        PublishLog.created_at >= seven_days_ago,
    ).count()

    return {
        "total_schedules": total,
        "scheduled": scheduled,
        "published": published,
        "failed": failed,
        "recent_7d_success": recent_published,
    }
