"""风险预警 API 路由 — Phase 0."""

from typing import Optional
from datetime import date, datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.work import Work
from app.models.risk_warning import RiskWarning, TaxDeadline, HealthMetric
from app.schemas.common import ApiResponse
from app.services.risk_warning_service import RiskWarningService, detect_burnout_risk
from app.deps import require_auth

router = APIRouter(prefix="/risk-warning", tags=["risk-warning"])


class TaxDeadlineCreate(BaseModel):
    tax_type: str
    due_date: date
    amount_yuan: Optional[float] = None
    notes: Optional[str] = None


class TaxDeadlineResponse(BaseModel):
    id: str
    user_id: str
    tax_type: str
    due_date: str
    amount_yuan: Optional[float] = None
    is_completed: bool
    completed_date: Optional[str] = None
    notes: Optional[str] = None


class HealthMetricCreate(BaseModel):
    daily_work_hours: float
    works_created: int = 0
    has_break_taken: bool = False
    mood_score: Optional[int] = None
    recorded_date: date


class BurnoutRisk(BaseModel):
    risk_level: str  # low, medium, high
    score: float  # 0-100
    factors: list[str]
    recommendation: str


class RiskCheckRequest(BaseModel):
    user_id: Optional[str] = "local"
    work_id: Optional[str] = None
    prompt: Optional[str] = None
    reference_images: Optional[list[str]] = None
    model_name: Optional[str] = None
    work_title: Optional[str] = ""


class BatchCheckItem(BaseModel):
    work_id: Optional[str] = None
    prompt: Optional[str] = None
    work_title: Optional[str] = ""
    model_name: Optional[str] = None
    reference_images: Optional[list[str]] = None


class BatchCheckRequest(BaseModel):
    items: list[BatchCheckItem]
    user_id: str = "local"


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


@router.post("/batch-check", response_model=ApiResponse[list], dependencies=[Depends(require_auth)])
async def batch_check_risk_warning(
    payload: BatchCheckRequest,
    db: Session = Depends(get_db),
):
    """批量侵权检测 — 对多个作品/提示词组合并行检测."""
    service = _get_service()
    items_dict = [item.model_dump() for item in payload.items]
    results = await service.batch_check(
        items=items_dict,
        user_id=payload.user_id,
        db=db,
    )

    total_warnings = sum(r["warning_count"] for r in results)
    return ApiResponse(
        message=f"完成 {len(results)} 个作品的批量检测，共检测到 {total_warnings} 条预警",
        data=results,
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


# --- Tax Deadline Endpoints ---

@router.post("/tax-deadlines", response_model=TaxDeadlineResponse, dependencies=[Depends(require_auth)])
def create_tax_deadline(body: TaxDeadlineCreate, db: Session = Depends(get_db)):
    """添加税务截止日期."""
    deadline = TaxDeadline(
        user_id="local",
        tax_type=body.tax_type,
        due_date=body.due_date,
        amount_yuan=body.amount_yuan,
        notes=body.notes,
    )
    db.add(deadline)
    db.commit()
    db.refresh(deadline)
    return {
        "id": deadline.id,
        "user_id": deadline.user_id,
        "tax_type": deadline.tax_type,
        "due_date": deadline.due_date.isoformat(),
        "amount_yuan": deadline.amount_yuan,
        "is_completed": deadline.is_completed,
        "completed_date": deadline.completed_date.isoformat() if deadline.completed_date else None,
        "notes": deadline.notes,
    }


@router.get("/tax-deadlines", response_model=list[dict])
def list_tax_deadlines(db: Session = Depends(get_db)):
    """获取税务截止日期列表."""
    deadlines = db.query(TaxDeadline).filter(
        TaxDeadline.user_id == "local",
    ).order_by(TaxDeadline.due_date.asc()).all()
    return [
        {
            "id": d.id,
            "tax_type": d.tax_type,
            "due_date": d.due_date.isoformat(),
            "amount_yuan": d.amount_yuan,
            "is_completed": d.is_completed,
            "days_remaining": (d.due_date - date.today()).days,
        }
        for d in deadlines
    ]


@router.patch("/tax-deadlines/{deadline_id}/complete", response_model=ApiResponse, dependencies=[Depends(require_auth)])
def complete_tax_deadline(deadline_id: str, db: Session = Depends(get_db)):
    """标记税务截止日期已完成."""
    deadline = db.query(TaxDeadline).filter(TaxDeadline.id == deadline_id).first()
    if not deadline:
        raise HTTPException(status_code=404, detail="截止日期不存在")
    deadline.is_completed = True
    deadline.completed_date = date.today()
    db.commit()
    return ApiResponse(message="已标记完成")


# --- Health / Burnout Detection Endpoints ---

@router.post("/health-metrics", response_model=ApiResponse, dependencies=[Depends(require_auth)])
def log_health_metric(body: HealthMetricCreate, db: Session = Depends(get_db)):
    """记录健康指标（用于 burnout 预警）."""
    metric = HealthMetric(
        user_id="local",
        daily_work_hours=body.daily_work_hours,
        works_created=body.works_created,
        has_break_taken=body.has_break_taken,
        mood_score=body.mood_score,
        recorded_date=body.recorded_date,
    )
    db.add(metric)
    db.commit()

    # 实时 burnout 检测
    burnout = detect_burnout_risk(db, "local")
    return ApiResponse(
        message="健康指标已记录",
        data={"burnout_risk": burnout},
    )


@router.get("/burnout-risk", response_model=BurnoutRisk)
def get_burnout_risk(db: Session = Depends(get_db)):
    """获取 burnout 风险评估."""
    return detect_burnout_risk(db, "local")
