# -*- coding: utf-8 -*-
"""公开只读 API 服务层 — 从 public_api.py 提取的业务逻辑."""

from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy import text
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

from app.models.work import Work
from app.models.listing import Listing, ListingStatus
from app.models.contract import ContractInstance
from app.models.system import Notification
from app.models.case_study import CaseStudy
from app.models.private_traffic import FanCommunity


def _safe_query(db, query_fn, fallback=None):
    """Run a DB query safely; return fallback on missing tables."""
    try:
        return query_fn()
    except OperationalError:
        return fallback


# ============================================================================
# 作品相关
# ============================================================================


def get_work_categories(db: Session) -> list:
    """获取作品分类统计."""
    def q():
        return [r[0] for r in db.query(Work.file_type)
                .filter(Work.status == "active").distinct().all() if r[0]]
    return _safe_query(db, q, [])


def list_public_works(db: Session, category: Optional[str] = None,
                      search: Optional[str] = None, limit: int = 20,
                      offset: int = 0) -> list:
    """公开作品列表."""
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


def get_public_work(db: Session, work_id: str) -> Optional[dict]:
    """公开作品详情."""
    work = db.query(Work).filter(
        Work.id == work_id,
        Work.status == "active",
        Work.deleted_at.is_(None),
    ).first()
    return work


# ============================================================================
# 挂牌相关
# ============================================================================


def list_public_listings(db: Session, status: Optional[str] = None,
                         limit: int = 20) -> list:
    """公开挂牌列表."""
    try:
        q = db.query(Work).join(Listing, Work.id == Listing.work_id).filter(
            Work.status == "active",
            Work.thumbnail_path.isnot(None),
            Listing.status == ListingStatus.ACTIVE,
            Work.deleted_at.is_(None),
        )
        if status:
            q = q.filter(Listing.status == status)
        listings = q.order_by(Listing.created_at.desc()).limit(limit).all()
        return listings
    except OperationalError:
        return []


# ============================================================================
# 合约相关
# ============================================================================


def list_public_contracts(db: Session, contract_type: Optional[str] = None,
                          status: Optional[str] = None, recent: bool = False,
                          limit: int = 20) -> list:
    """公开合约列表."""
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
            cutoff = datetime.now(timezone.utc) - timedelta(days=30)
            q = q.filter(ContractInstance.published_at >= cutoff)
        contracts = q.order_by(
            ContractInstance.published_at.desc().nullslast()
        ).limit(limit).all()
        # 转换 Decimal 为 float 以避免 Pydantic 序列化错误
        for c in contracts:
            if hasattr(c, 'total_amount') and isinstance(c.total_amount, Decimal):
                c.total_amount = float(c.total_amount)
        return contracts
    except OperationalError:
        return []


# ============================================================================
# 统计数据
# ============================================================================


def get_dashboard_stats(db: Session) -> dict:
    """平台统计数据."""
    now = datetime.now(timezone.utc)
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

    return {
        "total_works": _safe_query(db, count_works, 0),
        "total_contracts": _safe_query(db, count_contracts, 0),
        "total_listings": _safe_query(db, count_listings, 0),
        "total_users": _safe_query(db, count_users, 0),
        "active_contracts": _safe_query(db, count_active_contracts, 0),
        "monthly_transaction_volume": 0.0,
    }


# ============================================================================
# 通知相关
# ============================================================================


def list_public_notifications(db: Session, limit: int = 20) -> list:
    """公开通知列表."""
    has_is_public = _safe_query(db, lambda: db.execute(text(
        "PRAGMA table_info(notifications)"
    )).fetchall(), [])
    has_pub_col = any(row[1] == 'is_public' for row in has_is_public) if has_is_public else False

    if has_pub_col:
        notifs = db.query(Notification).filter(
            Notification.is_public == True
        ).order_by(Notification.created_at.desc()).limit(limit).all()
    else:
        notifs = db.query(Notification).order_by(
            Notification.created_at.desc()
        ).limit(limit).all()

    return notifs


# ============================================================================
# 市场趋势
# ============================================================================


def get_market_trends(db: Session, period: str) -> list:
    """市场趋势数据."""
    if period != "monthly":
        return []

    def q():
        return db.query(
            text("strftime('%Y-%m', created_at) as period, COUNT(*) as volume")
        ).filter(text("status = 'active'")).group_by(
            text("period")
        ).order_by(text("period")).limit(12).all()

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
            trends.append({
                "period": p,
                "value": int(getattr(r, 'volume', 0) or 0),
                "label": p,
            })
    except OperationalError:
        pass
    return trends


# ============================================================================
# 案例研究
# ============================================================================


def list_public_case_studies(db: Session) -> list:
    """案例研究列表."""
    cases = _safe_query(db, lambda: db.query(CaseStudy).order_by(
        CaseStudy.created_at.desc()
    ).limit(20).all(), [])
    return cases


# ============================================================================
# 合作机会
# ============================================================================


def list_public_opportunities(db: Session) -> list:
    """合作机会曝光."""
    communities = _safe_query(db, lambda: db.query(FanCommunity).filter(
        FanCommunity.is_active == True
    ).order_by(FanCommunity.created_at.desc()).limit(20).all(), [])
    return communities


# ============================================================================
# 画廊分类
# ============================================================================


def get_gallery_categories(db: Session) -> list:
    """画廊分类."""
    cats = _safe_query(db, lambda: [r[0] for r in db.query(Work.file_type)
                                     .filter(Work.status == "active")
                                     .distinct().all() if r[0]], [])
    return cats
