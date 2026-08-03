"""公开只读 API 路由 — OriSpark 宣传门户 + 小程序共用数据源。

所有端点无需认证，返回聚合后的公开数据。
响应字段使用 snake_case（Pydantic 默认），前端已对齐。

业务逻辑已提取至 public_api_service.py.
"""

from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.work import Work
from app.models.listing import Listing, ListingStatus
from app.models.contract import ContractInstance
from app.models.system import Notification
from app.models.case_study import CaseStudy
from app.models.private_traffic import FanCommunity
from app.services.public_api_service import (
    get_work_categories, list_public_works, get_public_work,
    list_public_listings, list_public_contracts, get_dashboard_stats,
    list_public_notifications, get_market_trends,
    list_public_case_studies, list_public_opportunities, get_gallery_categories,
)

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


# ── Endpoints ───────────────────────────────────────────────────────

@router.get("/public/work-categories", response_model=list[str])
def get_work_categories_endpoint(db: Session = Depends(get_db)):
    """获取作品分类统计（用于画廊筛选）."""
    return get_work_categories(db)


@router.get("/public/works", response_model=list[PublicWorkOut])
def list_public_works_endpoint(
    category: Optional[str] = Query(None, description="按 file_type 过滤"),
    search: Optional[str] = Query(None, description="标题模糊搜索"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    """公开作品列表（仅 active、有缩略图的）."""
    return list_public_works(db, category, search, limit, offset)


@router.get("/public/works/{work_id}", response_model=PublicWorkOut | dict)
def get_public_work_endpoint(work_id: str, db: Session = Depends(get_db)):
    """公开作品详情."""
    work = get_public_work(db, work_id)
    if not work:
        return {"error": "作品不存在或已被删除"}
    return work


@router.get("/public/listings", response_model=list[PublicWorkOut])
def list_public_listings_endpoint(
    status: Optional[str] = Query(None, description="挂牌状态过滤"),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """公开挂牌列表（关联作品）."""
    return list_public_listings(db, status, limit)


@router.get("/public/contracts", response_model=list[PublicContractOut])
def list_public_contracts_endpoint(
    contract_type: Optional[str] = Query(None, description="合约类型过滤"),
    status: Optional[str] = Query(None, description="状态过滤"),
    recent: bool = Query(False, description="仅最近 30 天"),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """公开合约列表（仅 approved + 活跃状态）."""
    return list_public_contracts(db, contract_type, status, recent, limit)


@router.get("/public/dashboard-stats", response_model=DashboardStatsOut)
def get_dashboard_stats_endpoint(db: Session = Depends(get_db)):
    """平台统计数据（首页仪表盘）."""
    return get_dashboard_stats(db)


@router.get("/public/notifications", response_model=list[PublicNotificationOut])
def list_public_notifications_endpoint(
    limit: int = Query(20, ge=1, le=50),
    db: Session = Depends(get_db),
):
    """公开通知列表（系统公告等）."""
    notifs = list_public_notifications(db, limit)
    return [
        PublicNotificationOut(
            id=n.id, title=n.title, body=n.content or "",
            type=n.type, created_at=n.created_at
        )
        for n in notifs
    ]


@router.get("/public/market/trends", response_model=list[MarketTrendOut])
def get_market_trends_endpoint(
    period: str = Query("monthly", description="daily|weekly|monthly"),
    db: Session = Depends(get_db),
):
    """市场趋势数据（基于挂牌统计）."""
    return get_market_trends(db, period)


@router.get("/public/case-studies", response_model=list[CaseStudyOut])
def list_public_case_studies_endpoint(db: Session = Depends(get_db)):
    """案例研究列表."""
    cases = list_public_case_studies(db)
    return [
        CaseStudyOut(
            id=c.id, title=c.title, category=c.category,
            summary=c.description or "", created_at=c.created_at
        )
        for c in cases
    ]


@router.get("/public/opportunities", response_model=list[OpportunityOut])
def list_public_opportunities_endpoint(db: Session = Depends(get_db)):
    """合作机会曝光（从粉丝社群聚合）."""
    communities = list_public_opportunities(db)
    return [
        OpportunityOut(
            id=c.id, title=c.name, type=c.platform or "operator",
            description=c.description or "", created_at=c.created_at
        )
        for c in communities
    ]


@router.get("/public/gallery/categories", response_model=list[str])
def get_gallery_categories_endpoint(db: Session = Depends(get_db)):
    """画廊分类（作品类型）."""
    return get_gallery_categories(db)
