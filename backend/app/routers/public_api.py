"""公开只读 API 路由 — OriSpark 宣传门户 + 小程序共用数据源。

所有端点无需认证，返回聚合后的公开数据。
响应字段使用 snake_case（Pydantic 默认），前端已对齐。
"""

from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.work import Work
from app.models.listing import Listing, ListingStatus
from app.models.contract import ContractInstance
from app.models.system import Notification
from app.models.case_study import CaseStudy
from app.models.private_traffic import FanCommunity

router = APIRouter()


# ── Response models (snake_case matching Pydantic defaults) ───────

class PublicWorkOut(BaseModel):
    id: str
    title: str
    description: str = ""
    category: str = ""
    tags: list[str] = []
    thumbnail: Optional[str] = None
    creator_name: str = ""
    is_featured: bool = False
    created_at: Optional[datetime] = None


class PublicContractOut(BaseModel):
    id: str
    title: str
    description: str = ""
    contract_type: str = ""
    total_amount: float = 0.0
    currency: str = "CNY"
    status: str = ""
    scope_usage: str = ""
    scope_geography: str = ""
    created_at: Optional[datetime] = None


class DashboardStatsOut(BaseModel):
    total_works: int = 0
    total_contracts: int = 0
    total_listings: int = 0
    total_users: int = 0
    active_contracts: int = 0
    monthly_transaction_volume: float = 0.0


class MarketTrendOut(BaseModel):
    period: str
    value: int = 0
    label: str = ""


class CaseStudyOut(BaseModel):
    id: str
    title: str
    summary: str = ""
    category: str = ""
    cover_image: Optional[str] = None
    created_at: Optional[datetime] = None


class OpportunityOut(BaseModel):
    id: str
    title: str
    description: str = ""
    type: str = "operator"
    created_by: str = ""
    created_at: Optional[datetime] = None


class PublicNotificationOut(BaseModel):
    id: str
    title: str
    body: str = ""
    type: str = ""
    created_at: Optional[datetime] = None


# ── Helper ────────────────────────────────────────────────────────

def get_public_db():
    """Get a read-only DB session for public endpoints."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _safe_query(db, query_fn, fallback=None):
    """Run a DB query safely; return fallback on missing tables."""
    try:
        return query_fn()
    except OperationalError:
        return fallback


# ── Endpoints ─────────────────────────────────────────────────────

@router.get("/public/work-categories", response_model=list[str])
def get_work_categories(db: Session = Depends(get_public_db)):
    """获取作品分类统计（用于画廊筛选）."""
    def q():
        return [r[0] for r in db.query(Work.file_type)
                .filter(Work.status == "active").distinct().all() if r[0]]
    return _safe_query(db, q, [])


@router.get("/public/works", response_model=list[PublicWorkOut])
def list_public_works(
    category: Optional[str] = Query(None, description="按 file_type 过滤"),
    search: Optional[str] = Query(None, description="标题模糊搜索"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_public_db),
):
    """公开作品列表（仅 active、有缩略图的）."""
    def q():
        return db.query(Work).filter(
            Work.status == "active",
            Work.thumbnail_path.isnot(None),
            Work.deleted_at.is_(None),
        )
    filtered = _safe_query(db, q, db.query(Work))
    if category:
        filtered = filtered.filter(Work.file_type == category)
    if search:
        filtered = filtered.filter(Work.title.ilike(f"%{search}%"))
    works = filtered.order_by(Work.created_at.desc()).offset(offset).limit(limit).all()
    return works


@router.get("/public/works/{work_id}", response_model=PublicWorkOut | dict)
def get_public_work(work_id: str, db: Session = Depends(get_public_db)):
    """公开作品详情."""
    work = db.query(Work).filter(
        Work.id == work_id,
        Work.status == "active",
        Work.deleted_at.is_(None),
    ).first()
    if not work:
        return {"error": "作品不存在或已被删除"}
    return work


@router.get("/public/listings", response_model=list[PublicWorkOut])
def list_public_listings(
    status: Optional[str] = Query(None, description="挂牌状态过滤"),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_public_db),
):
    """公开挂牌列表（关联作品）."""
    try:
        from app.models.work import Work as W
        q = db.query(W).join(Listing, W.id == Listing.work_id).filter(
            W.status == "active",
            W.thumbnail_path.isnot(None),
            Listing.status == ListingStatus.ACTIVE,
            W.deleted_at.is_(None),
        )
        if status:
            q = q.filter(Listing.status == status)
        listings = q.order_by(Listing.created_at.desc()).limit(limit).all()
        return listings
    except OperationalError:
        return []


@router.get("/public/contracts", response_model=list[PublicContractOut])
def list_public_contracts(
    contract_type: Optional[str] = Query(None, description="合约类型过滤"),
    status: Optional[str] = Query(None, description="状态过滤"),
    recent: bool = Query(False, description="仅最近 30 天"),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_public_db),
):
    """公开合约列表（仅 approved + 活跃状态）."""
    try:
        q = db.query(ContractInstance).filter(
            ContractInstance.verified == "approved",
            ContractInstance.status.in_(["listed", "active", "executing"]),
        )
        if contract_type:
            q = q.filter(ContractInstance.contract_type == contract_type)
        if status:
            q = q.filter(ContractInstance.status == status)
        if recent:
            cutoff = datetime.utcnow() - timedelta(days=30)
            q = q.filter(ContractInstance.published_at >= cutoff)
        contracts = q.order_by(
            ContractInstance.published_at.desc().nullslast()
        ).limit(limit).all()
        return contracts
    except OperationalError:
        return []


@router.get("/public/dashboard-stats", response_model=DashboardStatsOut)
def get_dashboard_stats(db: Session = Depends(get_public_db)):
    """平台统计数据（首页仪表盘）."""
    now = datetime.utcnow()
    month_ago = now - timedelta(days=30)

    def count_works():
        return db.query(Work).filter(
            Work.status == "active", Work.deleted_at.is_(None)
        ).count()

    def count_contracts():
        return db.query(ContractInstance).filter(
            ContractInstance.status.in_(["listed", "active", "executing"])
        ).count()

    def count_listings():
        return db.query(Listing).filter(
            Listing.status == ListingStatus.ACTIVE
        ).count()

    def count_users():
        return db.query(ContractInstance.creator_id).distinct().count()

    def count_active_contracts():
        return db.query(ContractInstance).filter(
            ContractInstance.status == "active"
        ).count()

    return DashboardStatsOut(
        total_works=_safe_query(db, count_works, 0),
        total_contracts=_safe_query(db, count_contracts, 0),
        total_listings=_safe_query(db, count_listings, 0),
        total_users=_safe_query(db, count_users, 0),
        active_contracts=_safe_query(db, count_active_contracts, 0),
        monthly_transaction_volume=0.0,
    )


@router.get("/public/notifications", response_model=list[PublicNotificationOut])
def list_public_notifications(
    limit: int = Query(20, ge=1, le=50),
    db: Session = Depends(get_public_db),
):
    """公开通知列表（系统公告等）."""
    # Check if is_public column exists
    has_is_public = _safe_query(db, lambda: db.execute(text(
        "PRAGMA table_info(notifications)"
    )).fetchall(), [])
    has_pub_col = any(row[1] == 'is_public' for row in has_is_public) if has_is_public else False

    if has_pub_col:
        notifs = db.query(Notification).filter(
            Notification.is_public == True  # noqa: E712
        ).order_by(Notification.created_at.desc()).limit(limit).all()
    else:
        notifs = db.query(Notification).order_by(
            Notification.created_at.desc()
        ).limit(limit).all()

    return [
        PublicNotificationOut(
            id=n.id, title=n.title, body=n.content or "",
            type=n.type, created_at=n.created_at
        )
        for n in notifs
    ]


@router.get("/public/market/trends", response_model=list[MarketTrendOut])
def get_market_trends(
    period: str = Query("monthly", description="daily|weekly|monthly"),
    db: Session = Depends(get_public_db),
):
    """市场趋势数据（基于挂牌统计）."""
    if period != "monthly":
        return []

    def q():
        rows = db.query(
            text("strftime('%Y-%m', created_at) as period, COUNT(*) as volume")
        ).filter(text("status = 'active'")).group_by(
            text("period")
        ).order_by(text("period")).limit(12).all()
        return rows

    trends = []
    try:
        rows = db.query(
            text("strftime('%Y-%m', created_at) as period, COUNT(*) as volume")
        ).select_from(Listing).filter(
            Listing.status == ListingStatus.ACTIVE
        ).group_by(
            text("period")
        ).order_by(
            text("period")
        ).limit(12).all()
        for r in rows:
            p = getattr(r, 'period', '') or ''
            trends.append(MarketTrendOut(
                period=p, value=int(getattr(r, 'volume', 0) or 0), label=p
            ))
    except OperationalError:
        pass
    return trends


@router.get("/public/case-studies", response_model=list[CaseStudyOut])
def list_public_case_studies(db: Session = Depends(get_public_db)):
    """案例研究列表."""
    cases = _safe_query(db, lambda: db.query(CaseStudy).order_by(
        CaseStudy.created_at.desc()
    ).limit(20).all(), [])
    return [
        CaseStudyOut(
            id=c.id, title=c.title, category=c.category,
            summary=c.description or "", created_at=c.created_at
        )
        for c in cases
    ]


@router.get("/public/opportunities", response_model=list[OpportunityOut])
def list_public_opportunities(db: Session = Depends(get_public_db)):
    """合作机会曝光（从粉丝社群聚合）."""
    communities = _safe_query(db, lambda: db.query(FanCommunity).filter(
        FanCommunity.is_active == True  # noqa: E712
    ).order_by(FanCommunity.created_at.desc()).limit(20).all(), [])
    return [
        OpportunityOut(
            id=c.id, title=c.name, type=c.platform or "operator",
            description=c.description or "", created_at=c.created_at
        )
        for c in communities
    ]


@router.get("/public/gallery/categories", response_model=list[str])
def get_gallery_categories(db: Session = Depends(get_public_db)):
    """画廊分类（作品类型）."""
    cats = _safe_query(db, lambda: [r[0] for r in db.query(Work.file_type)
                                     .filter(Work.status == "active")
                                     .distinct().all() if r[0]], [])
    return cats
