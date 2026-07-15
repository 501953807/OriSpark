"""风险预警 API 路由 — Phase 0."""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.work import Work
from app.models.risk_warning import RiskWarning
from app.schemas.common import ApiResponse
from app.services.risk_warning_service import RiskWarningService
from app.deps import require_auth

router = APIRouter(prefix="/api/risk-warning", tags=["risk-warning"])


class RiskCheckRequest(BaseModel):
    user_id: Optional[str] = "local"
    work_id: Optional[str] = None
    prompt: Optional[str] = None
    reference_images: Optional[list[str]] = None
    model_name: Optional[str] = None
    work_title: Optional[str] = ""


def _get_service() -> RiskWarningService:
    return RiskWarningService()


@router.post("/check", response_model=ApiResponse[list], dependencies=[Depends(require_auth)])
async def check_risk_warning(
    data: RiskCheckRequest,
    db: Session = Depends(get_db),
):
    """统一风险检测入口."""
    service = _get_service()
    results = await service.check_all(
        user_id=data.user_id,
        work_id=data.work_id,
        prompt=data.prompt,
        reference_images=data.reference_images,
        model_name=data.model_name,
        work_title=data.work_title,
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


@router.get("", response_model=ApiResponse[list])
def list_all_warnings(
    dismissed: Optional[bool] = None,
    severity: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """获取所有风险预警记录."""
    query = db.query(RiskWarning)
    if dismissed is not None:
        query = query.filter(RiskWarning.dismissed == dismissed)
    if severity:
        query = query.filter(RiskWarning.severity == severity)

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


@router.patch("/{warning_id}/dismiss", response_model=ApiResponse, dependencies=[Depends(require_auth)])
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
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise

    return ApiResponse(message="已标记为查看")
