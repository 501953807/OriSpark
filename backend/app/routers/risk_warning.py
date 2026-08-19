"""风险预警 API 路由 — Phase 0.

业务逻辑已提取至 risk_warning_service.py.
"""

from typing import Optional
from datetime import date, datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.common import ApiResponse
from app.services.risk_warning_service import (
    RiskWarningService,
    detect_burnout_risk,
    list_warnings,
    dismiss_warning,
    list_tax_deadlines,
    complete_tax_deadline,
    create_tax_deadline,
    log_health_metric,
    get_work_warnings,
)
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
    risk_level: str
    score: float
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


@router.post("/check", response_model=ApiResponse, dependencies=[Depends(require_auth)])
async def check_risk_warning(
    data: RiskCheckRequest,
    db: Session = Depends(get_db),
):
    """统一风险检测入口."""
    service = _get_service()
    results = await service.check_all(
        db=db,
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


@router.post("/batch-check", response_model=ApiResponse, dependencies=[Depends(require_auth)])
async def batch_check_risk_warning(
    payload: BatchCheckRequest,
    db: Session = Depends(get_db),
):
    """批量侵权检测."""
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


@router.get("/work/{work_id}", response_model=ApiResponse)
def get_work_warnings_endpoint(
    work_id: str,
    dismissed: Optional[bool] = None,
    db: Session = Depends(get_db),
):
    """获取作品的风险预警记录."""
    warnings = get_work_warnings(db, work_id, dismissed)
    if warnings is None:
        raise HTTPException(status_code=404, detail="作品不存在")
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


@router.get("", response_model=ApiResponse)
def list_all_warnings(
    dismissed: Optional[bool] = None,
    severity: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """获取所有风险预警记录."""
    warnings = list_warnings(db, dismissed, severity)
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
def dismiss_warning_endpoint(
    warning_id: str,
    db: Session = Depends(get_db),
):
    """标记预警为已查看."""
    warning = dismiss_warning(db, warning_id)
    if not warning:
        raise HTTPException(status_code=404, detail="预警记录不存在")
    return ApiResponse(message="已标记为查看")


# --- Tax Deadline Endpoints ---

@router.post("/tax-deadlines", response_model=TaxDeadlineResponse, dependencies=[Depends(require_auth)])
def create_tax_deadline_endpoint(body: TaxDeadlineCreate, db: Session = Depends(get_db)):
    """添加税务截止日期."""
    deadline = create_tax_deadline(db, body.tax_type, body.due_date, body.amount_yuan, body.notes)
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
def list_tax_deadlines_endpoint(db: Session = Depends(get_db)):
    """获取税务截止日期列表."""
    deadlines = list_tax_deadlines(db, "local")
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
def complete_tax_deadline_endpoint(deadline_id: str, db: Session = Depends(get_db)):
    """标记税务截止日期已完成."""
    deadline = complete_tax_deadline(db, deadline_id)
    if not deadline:
        raise HTTPException(status_code=404, detail="截止日期不存在")
    return ApiResponse(message="已标记完成")


# --- Health / Burnout Detection Endpoints ---

@router.post("/health-metrics", response_model=ApiResponse, dependencies=[Depends(require_auth)])
def log_health_metric_endpoint(body: HealthMetricCreate, db: Session = Depends(get_db)):
    """记录健康指标（用于 burnout 预警）."""
    log_health_metric(db, "local", body.daily_work_hours, body.works_created,
                      body.has_break_taken, body.mood_score, body.recorded_date)
    burnout = detect_burnout_risk(db, "local")
    return ApiResponse(
        message="健康指标已记录",
        data={"burnout_risk": burnout},
    )


@router.get("/burnout-risk", response_model=BurnoutRisk)
def get_burnout_risk_endpoint(db: Session = Depends(get_db)):
    """获取 burnout 风险评估."""
    return detect_burnout_risk(db, "local")


# ── 2.1 分离检测端点（设计文档 API 契约）────────────────────────────

class PromptCheckRequest(BaseModel):
    prompt: str
    work_title: str = ""
    user_id: Optional[str] = "local"
    work_id: Optional[str] = None


class ReferenceCheckRequest(BaseModel):
    image_hash: str
    work_ids: Optional[list[str]] = None
    user_id: Optional[str] = "local"
    work_id: Optional[str] = None


class TrademarkCheckRequest(BaseModel):
    text: str
    jurisdiction: str = "cn"
    user_id: Optional[str] = "local"
    work_id: Optional[str] = None


class ModelInfoRequest(BaseModel):
    model_name: str
    source: str = "civitai"


@router.post("/check-prompt", response_model=ApiResponse, dependencies=[Depends(require_auth)])
async def check_prompt_endpoint(body: PromptCheckRequest, db: Session = Depends(get_db)):
    """维度 1: 提示词侵权检测."""
    service = _get_service()
    results = service.check_prompt(body.prompt, body.work_title)
    for r in results:
        get_work_warnings(db, body.work_id)  # touch DB
    return ApiResponse(
        message=f"提示词检测完成，发现 {len(results)} 条预警",
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


@router.post("/check-reference", response_model=ApiResponse, dependencies=[Depends(require_auth)])
async def check_reference_endpoint(body: ReferenceCheckRequest, db: Session = Depends(get_db)):
    """维度 2: 参考图相似度检测."""
    from app.models.work import Work
    service = _get_service()
    existing_hashes: list[str] = []
    if db is not None and body.user_id:
        existing_hashes = [
            h[0] for h in db.query(Work.sha256)
            .filter(Work.creator_id == body.user_id, Work.status == "active")
            .distinct().all()
            if h[0]
        ]
    result = service.check_reference_image(body.image_hash, existing_hashes)
    similar_works = []
    external_matches = []
    if result and result.matched_entity and result.matched_entity.startswith("similarity:"):
        similar_works = [{"work_id": "", "title": "（命中本地作品库）", "similarity": float(result.matched_entity.split(":")[-1].rstrip("%"))}]
    return ApiResponse(
        message="参考图检测完成" if result else "未检测到相似作品",
        data={
            "similar_works": similar_works,
            "external_matches": external_matches,
            "warning": {
                "type": result.warning_type,
                "severity": result.severity,
                "title": result.title,
                "confidence": result.confidence,
                "suggestion": result.suggestion,
            } if result else None,
        },
    )


@router.get("/model-info", response_model=ApiResponse, dependencies=[Depends(require_auth)])
async def model_info_endpoint(body: ModelInfoRequest, db: Session = Depends(get_db)):
    """维度 3: LoRA/模型权属信息查询."""
    service = _get_service()
    info = service.model_gateway.query(body.model_name, body.source)
    if info:
        return ApiResponse(data={
            "name": body.model_name,
            "author": getattr(info, "author", None),
            "license": getattr(info, "license_type", None),
            "commercial_use_allowed": getattr(info, "allows_commercial", None),
            "source_url": getattr(info, "source_url", None),
            "requires_attribution": getattr(info, "requires_attribution", False),
        })
    return ApiResponse(
        message="模型来源未知",
        data={
            "name": body.model_name,
            "author": None,
            "license": None,
            "commercial_use_allowed": None,
            "source_url": None,
            "requires_attribution": False,
        },
    )


@router.post("/check-trademark", response_model=ApiResponse, dependencies=[Depends(require_auth)])
async def check_trademark_endpoint(body: TrademarkCheckRequest, db: Session = Depends(get_db)):
    """维度 4: 商标/Logo 碰撞检测."""
    service = _get_service()
    results = await service.check_trademark(body.text, body.jurisdiction)
    return ApiResponse(
        message=f"商标检测完成，发现 {len(results)} 条冲突",
        data=[
            {
                "name": r.matched_entity,
                "class": "",
                "jurisdiction": body.jurisdiction,
                "confidence": r.confidence,
                "action_url": "",
            }
            for r in results
        ],
    )
