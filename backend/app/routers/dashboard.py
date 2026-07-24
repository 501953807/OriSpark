"""经营管理中心 API 路由 — 对应: docs/modules-v5/06-business-management.md
端点: 4 (dashboard/stats, dashboard/recent, dashboard/revenue, dashboard/trends)"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta

from app.database import get_db
from app.models.work import Work
from app.models.notary import NotaryRecord
from app.models.monitor import MonitorResult
from app.models.photographer_v2 import StockSale
from app.models.etsy import EtsyOrder
from app.models.commission import CommissionOrder
from app.schemas.common import (
    DashboardStats,
    ApiResponse,
    RevenueByMonth,
    WorkTrend,
    RevenueSummary,
    TrendsSummary,
)

router = APIRouter()


@router.get("/dashboard/stats", response_model=ApiResponse[DashboardStats])
def get_dashboard_stats(db: Session = Depends(get_db)):
    """获取工作台统计数据."""
    total_works = db.query(func.count(Work.id)).filter(
        Work.status == "active"
    ).scalar() or 0

    total_notarized = db.query(func.count(NotaryRecord.id)).filter(
        NotaryRecord.status == "confirmed"
    ).scalar() or 0

    infringement_alerts = db.query(func.count(MonitorResult.id)).filter(
        MonitorResult.status == "pending_review"
    ).scalar() or 0

    # Monthly revenue — aggregate from all revenue tables
    now = datetime.utcnow()
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    monthly_rev = 0.0

    for model, amt_col, date_col in [
        (StockSale, 'sale_amount', 'sale_date'),
        (EtsyOrder, 'order_total', 'order_date'),
        (CommissionOrder, 'amount', 'created_at'),
    ]:
        val = (
            db.query(func.coalesce(func.sum(getattr(model, amt_col)), 0))
            .filter(getattr(model, date_col) >= month_start)
            .scalar()
        )
        monthly_rev += float(val)

    # 最近作品
    recent_works = db.query(Work).filter(
        Work.status == "active"
    ).order_by(Work.imported_at.desc()).limit(10).all()

    stats = DashboardStats(
        total_works=total_works,
        total_notarized=total_notarized,
        infringement_alerts=infringement_alerts,
        monthly_revenue=round(monthly_rev, 2),
        recent_works=[
            {
                "id": w.id,
                "title": w.title,
                "file_type": w.file_type,
                "thumbnail_path": w.thumbnail_path,
                "imported_at": w.imported_at.isoformat() if w.imported_at else None,
                "is_verified": w.is_verified,
            }
            for w in recent_works
        ],
    )

    return ApiResponse(data=stats)


@router.get("/dashboard/recent")
def get_recent_works(limit: int = 10, db: Session = Depends(get_db)):
    """获取最近导入的作品."""
    works = db.query(Work).filter(
        Work.status == "active"
    ).order_by(Work.imported_at.desc()).limit(limit).all()

    return ApiResponse(data=[
        {
            "id": w.id,
            "title": w.title,
            "file_type": w.file_type,
            "file_extension": w.file_extension,
            "thumbnail_path": w.thumbnail_path,
            "file_size": w.file_size,
            "sha256": w.sha256,
            "is_verified": w.is_verified,
            "imported_at": w.imported_at.isoformat() if w.imported_at else None,
        }
        for w in works
    ])


@router.get("/dashboard/revenue", response_model=ApiResponse[RevenueSummary])
def get_dashboard_revenue(db: Session = Depends(get_db)):
    """获取收入数据 — 聚合 stock_sales / etsy_orders / commission_orders, 返回近 12 个月收入趋势."""
    now = datetime.utcnow()
    twelve_months_ago = now.replace(day=1) - timedelta(days=365)

    # --- monthly revenue breakdown ---
    revenue_by_month: dict[str, float] = {}

    def _aggregate(model, amount_col, date_col):
        rows = (
            db.query(
                func.strftime('%Y-%m', date_col).label('month'),
                func.coalesce(func.sum(getattr(model, amount_col)), 0).label('total'),
            )
            .filter(getattr(model, date_col) >= twelve_months_ago)
            .group_by('month')
            .all()
        )
        for month_str, total in rows:
            revenue_by_month[month_str] = revenue_by_month.get(month_str, 0) + float(total)

    # stock_sales.sale_amount / sale_date
    _aggregate(StockSale, 'sale_amount', 'sale_date')

    # etsy_orders.order_total / order_date
    _aggregate(EtsyOrder, 'order_total', 'order_date')

    # commission_orders.amount / created_at (approximate)
    _aggregate(CommissionOrder, 'amount', 'created_at')

    monthly = [
        RevenueByMonth(
            month=m,
            revenue=round(revenue_by_month.get(m, 0), 2),
        )
        for m in sorted(revenue_by_month.keys())
    ]

    total_revenue = sum(r.revenue for r in monthly)

    return ApiResponse(data=RevenueSummary(
        total_revenue=round(total_revenue, 2),
        revenue_by_month=monthly,
    ))


@router.get("/dashboard/trends", response_model=ApiResponse[TrendsSummary])
def get_dashboard_trends(db: Session = Depends(get_db)):
    """获取作品创建趋势 — 近 30 天每日新增作品数."""
    now = datetime.utcnow()
    thirty_days_ago = now - timedelta(days=30)

    rows = (
        db.query(
            func.strftime('%Y-%m-%d', Work.created_at).label('day'),
            func.count(Work.id).label('cnt'),
        )
        .filter(Work.created_at >= thirty_days_ago)
        .group_by('day')
        .all()
    )

    daily_counts = {r.day: r.cnt for r in rows}

    # Fill gaps so chart axes are continuous
    daily_trends: list[WorkTrend] = []
    total_works_30d = 0
    for i in range(30):
        d = (now - timedelta(days=29 - i)).strftime('%Y-%m-%d')
        cnt = daily_counts.get(d, 0)
        total_works_30d += cnt
        daily_trends.append(WorkTrend(date=d, count=cnt))

    avg_daily = round(total_works_30d / 30, 2) if total_works_30d > 0 else 0.0

    return ApiResponse(data=TrendsSummary(
        daily_trends=daily_trends,
        total_works_30d=total_works_30d,
        avg_daily=avg_daily,
    ))
