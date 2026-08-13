"""收入多元化分析 API 路由."""

import csv
import io
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user_id
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
from app.utils.audit import AuditLog

router = APIRouter(prefix="/revenue", tags=["revenue"])
@router.post("/records", response_model=RevenueRecordSchema)
def post_record(body: RevenueRecordCreate, actor_id: str = Depends(get_current_user_id), db: Session = Depends(get_db)):
    """记录一笔收入."""
    try:
        record = record_revenue(db, actor_id, body.income_category, body.amount,
                                body.currency, body.platform, body.recorded_date,
                                body.source_description)
        AuditLog.log(db, "record_revenue", f"Recorded revenue by {actor_id}", actor_id)
        return RevenueRecordSchema(
            id=record.id, user_id=record.user_id or "",
            income_category=record.income_category or "", amount=record.amount,
            currency=record.currency, platform=record.platform,
            source_description=record.source_description,
            recorded_date=record.recorded_date, is_verified=record.is_verified,
            created_at=record.created_at,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail="收益操作失败，请稍后重试")


@router.get("/summary/{user_id}", response_model=RevenueSummaryResponse)
def get_summary(user_id: str, months: int = 12, db: Session = Depends(get_db)):
    """获取用户收入汇总统计."""
    summary = get_revenue_summary(db, user_id, months)
    return RevenueSummaryResponse(**summary)


@router.get("/diversity/{user_id}", response_model=DiversityIndexResponse)
def get_diversity(user_id: str, months: int = 12, db: Session = Depends(get_db)):
    """获取用户收入多元化指数."""
    cutoff_months = months
    from datetime import datetime, timedelta, timezone
    cutoff_date = datetime.now(timezone.utc) - timedelta(days=30 * cutoff_months)
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


@router.get("/records/export")
def export_revenue_records(
    user_id: str = Depends(get_current_user_id),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    format: str = Query("csv", pattern="^(csv|json)$"),
    db: Session = Depends(get_db),
):
    """导出收入记录（CSV/JSON）."""
    query = db.query(RevenueRecord).filter(RevenueRecord.user_id == user_id)
    if start_date:
        query = query.filter(RevenueRecord.created_at >= datetime.fromisoformat(start_date.replace(" ", "+")))
    if end_date:
        query = query.filter(RevenueRecord.created_at <= datetime.fromisoformat(end_date.replace(" ", "+")))
    records = query.all()

    if format == "csv":
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["date", "category", "amount", "currency", "platform", "description"])
        for r in records:
            writer.writerow([
                r.created_at.strftime("%Y-%m-%d") if r.created_at else "",
                r.income_category or "",
                r.amount,
                r.currency,
                r.platform or "",
                r.source_description or "",
            ])
        return StreamingResponse(
            io.StringIO(output.getvalue()),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=revenue_export.csv"},
        )
    else:
        items = [
            {
                "id": r.id,
                "date": r.created_at.strftime("%Y-%m-%d") if r.created_at else "",
                "category": r.income_category or "",
                "amount": r.amount,
                "currency": r.currency,
                "platform": r.platform or "",
                "description": r.source_description or "",
            }
            for r in records
        ]
        return {"success": True, "message": f"导出成功，共 {len(items)} 条记录", "data": items}
