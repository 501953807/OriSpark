"""数据看板 API 路由 — v6.0 运营者数据洞察.

端点:
  GET /api/operator/data/platform-stats    平台总览数据
  GET /api/operator/data/creator-ranking   创作者排行
  GET /api/operator/data/category-trends   品类热度趋势
  GET /api/operator/data/industry-report   行业报告
"""

from datetime import datetime, timezone, timedelta
from typing import Optional

from fastapi import APIRouter, Depends
from sqlalchemy import func, desc, cast, Float
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.work import Work
from app.models.system import User
from app.models.contract import ContractInstance
from app.models.scr_reputation import SCRScore
from app.deps import require_operator

router = APIRouter(prefix="/operator/data", tags=["data-analytics"])


@router.get("/platform-stats", response_model=dict)
def get_platform_stats(db: Session = Depends(get_db), operator=Depends(require_operator)):
    """平台总览：注册创作者数/作品总数/活跃合约数/月交易额."""
    now = datetime.now(timezone.utc)
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    total_creators = db.query(func.count(User.id)).filter(
        User.creator_type.isnot(None)
    ).scalar() or 0

    total_works = db.query(func.count(Work.id)).filter(
        Work.status == "active"
    ).scalar() or 0

    active_contracts = db.query(func.count(ContractInstance.id)).filter(
        ContractInstance.status.in_(["listed", "active", "executing", "escrow"])
    ).scalar() or 0

    total_contracts = db.query(func.count(ContractInstance.id)).scalar() or 0

    monthly_volume = (
        float(db.query(func.coalesce(func.sum(ContractInstance.total_amount), 0))
        .filter(ContractInstance.created_at >= month_start)
        .scalar() or 0)
    )

    avg_split_rate = 70

    return {
        "total_creators": int(total_creators),
        "total_works": int(total_works),
        "total_contracts": int(total_contracts),
        "active_contracts": int(active_contracts),
        "monthly_transaction_volume": round(monthly_volume, 2),
        "avg_split_rate": avg_split_rate,
    }


@router.get("/creator-ranking", response_model=list[dict])
def get_creator_ranking(
    sort_by: str = "works",
    limit: int = 20,
    db: Session = Depends(get_db),
    operator=Depends(require_operator),
):
    """创作者排行：按作品数/成交额/SCR信誉排行."""
    if sort_by == "transactions":
        subq = (
            db.query(Work.creator_id, func.coalesce(func.sum(ContractInstance.total_amount), 0).label("total"))
            .join(ContractInstance, ContractInstance.work_id == Work.id)
            .group_by(Work.creator_id)
            .subquery()
        )
        ranking = (
            db.query(User.id, User.username, subq.c.total.cast(Float))
            .join(subq, subq.c.creator_id == User.id)
            .filter(User.creator_type.isnot(None))
            .order_by(desc(subq.c.total))
            .limit(limit)
            .all()
        )
        return [
            {
                "user_id": u.id,
                "username": u.username,
                "total_transactions": round(float(u.total) if u.total else 0, 2),
                "work_count": 0,
            }
            for u in ranking
        ]

    elif sort_by == "scr":
        ranking = (
            db.query(SCRScore.user_id, SCRScore.overall_score, SCRScore.rating_level,
                     User.username, User.email)
            .join(User, User.id == SCRScore.user_id)
            .filter(User.creator_type.isnot(None))
            .order_by(desc(SCRScore.overall_score))
            .limit(limit)
            .all()
        )
        return [
            {
                "user_id": s.user_id,
                "username": s.username,
                "email": s.email,
                "scr_score": float(s.overall_score) if s.overall_score else 0,
                "rating_level": s.rating_level,
                "work_count": 0,
            }
            for s in ranking
        ]

    else:  # works (default)
        subq = (
            db.query(Work.creator_id, func.count(Work.id).label("work_count"))
            .filter(Work.status == "active")
            .group_by(Work.creator_id)
            .subquery()
        )
        ranking = (
            db.query(User.id, User.username, User.email, User.creator_type,
                     subq.c.work_count)
            .join(subq, subq.c.creator_id == User.id)
            .filter(User.creator_type.isnot(None))
            .order_by(desc(subq.c.work_count))
            .limit(limit)
            .all()
        )
        return [
            {
                "user_id": u.id,
                "username": u.username,
                "email": u.email,
                "creator_type": u.creator_type,
                "work_count": int(u.work_count) if u.work_count else 0,
                "total_transactions": 0.0,
            }
            for u in ranking
        ]


@router.get("/category-trends", response_model=list[dict])
def get_category_trends(
    period: str = "monthly",
    limit: int = 10,
    db: Session = Depends(get_db),
    operator=Depends(require_operator),
):
    """品类热度趋势：按 IP 类型统计的热门品类."""
    if period == "quarterly":
        cutoff = datetime.now(timezone.utc) - timedelta(days=90)
        period_label = "quarterly"
    else:
        cutoff = datetime.now(timezone.utc) - timedelta(days=30)
        period_label = "monthly"

    trends = (
        db.query(User.creator_type, func.count(Work.id).label("work_count"))
        .join(Work, Work.creator_id == User.id)
        .filter(
            User.creator_type.isnot(None),
            Work.status == "active",
            Work.created_at >= cutoff,
        )
        .group_by(User.creator_type)
        .order_by(desc("work_count"))
        .limit(limit)
        .all()
    )

    return [
        {
            "category": t.creator_type or "unknown",
            "work_count": int(t.work_count),
            "period": period_label,
        }
        for t in trends
    ]


@router.get("/industry-report", response_model=dict)
def get_industry_report(
    month: Optional[str] = None,
    db: Session = Depends(get_db),
    operator=Depends(require_operator),
):
    """行业报告：月度创作者经济报告."""
    if month is None:
        now = datetime.now(timezone.utc)
        if now.month == 1:
            month_date = now.replace(year=now.year - 1, month=12, day=1)
        else:
            month_date = now.replace(month=now.month - 1, day=1)
        month_str = month_date.strftime("%Y-%m")
    else:
        month_str = month
        month_date = datetime.strptime(month, "%Y-%m").replace(day=1)

    month_end = month_date.replace(day=28) + timedelta(days=4)
    month_end = month_end.replace(day=1) - timedelta(days=1)

    total_creators = db.query(func.count(User.id)).filter(
        User.creator_type.isnot(None),
        User.created_at >= month_date,
        User.created_at <= month_end,
    ).scalar() or 0

    total_works = db.query(func.count(Work.id)).filter(
        Work.status == "active",
        Work.created_at >= month_date,
        Work.created_at <= month_end,
    ).scalar() or 0

    total_contracts = db.query(func.count(ContractInstance.id)).filter(
        ContractInstance.created_at >= month_date,
        ContractInstance.created_at <= month_end,
    ).scalar() or 0

    transaction_volume = (
        float(db.query(func.coalesce(func.sum(ContractInstance.total_amount), 0))
        .filter(
            ContractInstance.created_at >= month_date,
            ContractInstance.created_at <= month_end,
        )
        .scalar() or 0)
    )

    categories = (
        db.query(User.creator_type, func.count(User.id).label("cnt"))
        .filter(
            User.creator_type.isnot(None),
            User.created_at >= month_date,
            User.created_at <= month_end,
        )
        .group_by(User.creator_type)
        .order_by(desc("cnt"))
        .limit(5)
        .all()
    )

    top_categories = [c.creator_type for c in categories if c.creator_type]

    summary = (
        f"{month_str} 创作者经济报告：新增创作者 {total_creators} 人，"
        f"新增作品 {total_works} 件，合约 {total_contracts} 个，"
        f"交易额 ¥{transaction_volume:,.2f}。"
    )

    return {
        "report_month": month_str,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "summary": summary,
        "total_creators": int(total_creators),
        "total_works": int(total_works),
        "total_contracts": int(total_contracts),
        "transaction_volume": round(transaction_volume, 2),
        "top_categories": top_categories,
    }
