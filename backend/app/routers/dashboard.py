"""经营管理中心 API 路由 — 对应: docs/modules-v3/06-business-management.md
端点: 2 (dashboard)"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import get_db
from app.models.work import Work
from app.models.notary import NotaryRecord
from app.models.monitor import MonitorResult
from app.schemas.common import DashboardStats, ApiResponse

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

    # 最近作品
    recent_works = db.query(Work).filter(
        Work.status == "active"
    ).order_by(Work.imported_at.desc()).limit(10).all()

    stats = DashboardStats(
        total_works=total_works,
        total_notarized=total_notarized,
        infringement_alerts=infringement_alerts,
        monthly_revenue=0.0,
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
