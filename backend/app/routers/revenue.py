"""收入多元化分析 API 路由."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.revenue import (
    RevenueRecordCreate,
    RevenueRecordSchema,
    RevenueSummaryResponse,
    DiversityIndexResponse,
)
from app.services.revenue_service import (
    record_revenue,
    get_revenue_summary,
    calculate_diversity_index,
)
from app.models.publish import RevenueRecord

router = APIRouter(prefix="/revenue", tags=["revenue"])


@router.post("/records", response_model=RevenueRecordSchema)
def post_record(body: RevenueRecordCreate, db: Session = Depends(get_db)):
    """记录一笔收入."""
    try:
        record = record_revenue(db, "current_user", body.income_category, body.amount,
                                body.currency, body.platform, body.recorded_date,
                                body.source_description)
        return RevenueRecordSchema(
            id=record.id, user_id=record.user_id or "",
            income_category=record.income_category or "", amount=record.amount,
            currency=record.currency, platform=record.platform,
            source_description=record.source_description,
            recorded_date=record.recorded_date, is_verified=record.is_verified,
            created_at=record.created_at,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/summary/{user_id}", response_model=RevenueSummaryResponse)
def get_summary(user_id: str, months: int = 12, db: Session = Depends(get_db)):
    """获取用户收入汇总统计."""
    summary = get_revenue_summary(db, user_id, months)
    return RevenueSummaryResponse(**summary)


@router.get("/diversity/{user_id}", response_model=DiversityIndexResponse)
def get_diversity(user_id: str, months: int = 12, db: Session = Depends(get_db)):
    """获取用户收入多元化指数."""
    cutoff_months = months
    from datetime import datetime, timedelta
    cutoff_date = datetime.utcnow() - timedelta(days=30 * cutoff_months)
    records = (
        db.query(RevenueRecord)
        .filter(
            RevenueRecord.user_id == user_id,
            RevenueRecord.created_at >= cutoff_date,
        )
        .all()
    )
    diversity = calculate_diversity_index(records)
    return DiversityIndexResponse(**diversity)
