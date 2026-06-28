"""风险预警 API 路由 — Phase 0."""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.work import Work
from app.models.risk_warning import RiskWarning
from app.schemas.common import ApiResponse
from app.services.risk_warning_service import RiskWarningService

router = APIRouter(prefix="/api/risk-warning", tags=["risk-warning"])


def _get_service() -> RiskWarningService:
    return RiskWarningService()


@router.post("/check", response_model=ApiResponse[list])
async def check_risk_warning(
    data: dict,
    db: Session = Depends(get_db),
):
    """统一风险检测入口."""
    service = _get_service()
    user_id = data.get("user_id", "local")
    results = await service.check_all(
        user_id=user_id,
        work_id=data.get("work_id"),
        prompt=data.get("prompt"),
        reference_images=data.get("reference_images"),
        model_name=data.get("model_name"),
        work_title=data.get("work_title", ""),
    )

    return ApiResponse(
        message=f"检测到 {len(results)} 条风险预警",
        data=[
            {
                "warning_type": r.warning_type,
                "severity": r.severity,
                "title": r.title,
                "description": r.description,
                "matched_entity": r.matched_entity,
                "confidence": r.confidence,
                "suggestion": r.suggestion,
            }
            for r in results
        ],
    )


@router.get("/work/{work_id}", response_model=ApiResponse[list])
def get_work_warnings(
    work_id: str,
    dismissed: Optional[bool] = None,
    db: Session = Depends(get_db),
):
    """获取作品的风险预警记录."""
    work = db.query(Work).filter(Work.id == work_id).first()
    if not work:
        raise HTTPException(status_code=404, detail="作品不存在")

    query = db.query(RiskWarning).filter(RiskWarning.work_id == work_id)
    if dismissed is not None:
        query = query.filter(RiskWarning.dismissed == dismissed)

    warnings = query.order_by(RiskWarning.created_at.desc()).all()

    return ApiResponse(
        data=[
            {
                "id": w.id,
                "warning_type": w.warning_type,
                "severity": w.severity,
                "title": w.title,
                "matched_entity": w.matched_entity,
                "confidence": w.confidence,
                "dismissed": w.dismissed,
                "created_at": w.created_at.isoformat() if w.created_at else None,
            }
            for w in warnings
        ],
    )


@router.patch("/{warning_id}/dismiss", response_model=ApiResponse)
def dismiss_warning(
    warning_id: str,
    db: Session = Depends(get_db),
):
    """标记预警为已查看."""
    warning = db.query(RiskWarning).filter(RiskWarning.id == warning_id).first()
    if not warning:
        raise HTTPException(status_code=404, detail="预警记录不存在")

    warning.dismissed = True
    from datetime import datetime
    warning.dismissed_at = datetime.utcnow()
    db.commit()

    return ApiResponse(message="已标记为查看")
