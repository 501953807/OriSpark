"""维权ROI路由."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.enforcement_roi import (
    EnforcementCaseCreate,
    EnforcementCaseResponse,
    CaseReferenceSchema,
    DecisionTreeResult,
    RoiPredictorRequest,
    RoiPrediction,
    DefenseTierSchema,
)
from app.services.enforcement_roi_service import (
    get_decision_tree,
    predict_roi,
    get_all_defense_tiers,
    list_case_references,
    get_case_reference,
    save_enforcement_case,
    get_user_cases,
)

router = APIRouter(prefix="/enforcement-roi", tags=["enforcement-roi"])


@router.get("/decision-tree")
def show_decision_tree(
    infringement_type: str = Query(..., description="侵权类型"),
    loss_amount: float = Query(..., description="预估损失金额"),
):
    """维权路径决策树 — 根据侵权类型和损失金额推荐维权方案."""
    return get_decision_tree(infringement_type, loss_amount)


@router.post("/predict", response_model=RoiPrediction)
def roi_predict(req: RoiPredictorRequest):
    """ROI预测器 — 预测维权投入产出比."""
    return predict_roi(
        req.work_value_yuan,
        req.infringement_type,
        req.target_platform,
        req.action_type,
    )


@router.get("/defense-tiers", response_model=list[DefenseTierSchema])
def list_defense_tiers():
    """获取四层防御预算配置."""
    return get_all_defense_tiers()


@router.get("/cases-reference", response_model=list[CaseReferenceSchema])
def list_references(
    infringement_type: str = Query(None, description="按侵权类型筛选"),
    db: Session = Depends(get_db),
):
    """获取参考案例库."""
    return list_case_references(db, infringement_type)


@router.get("/cases-reference/{case_id}", response_model=CaseReferenceSchema)
def get_reference_detail(case_id: str, db: Session = Depends(get_db)):
    """获取单个参考案例详情."""
    from app.models.enforcement_roi import CaseReference
    case = db.query(CaseReference).filter(CaseReference.id == case_id).first()
    if not case:
        raise HTTPException(404, "Case reference not found")
    return {
        "id": case.id,
        "infringement_type": case.infringement_type,
        "target_platform": case.target_platform,
        "typical_cost_range_low": case.typical_cost_range_low,
        "typical_cost_range_high": case.typical_cost_range_high,
        "resolution_time_days_low": case.resolution_time_days_low,
        "resolution_time_days_high": case.resolution_time_days_high,
        "win_rate_percent": case.win_rate_percent,
        "avg_compensation_yuan": case.avg_compensation_yuan,
        "roi_tier": case.roi_tier,
    }


@router.post("/cases", response_model=EnforcementCaseResponse)
def save_case(req: EnforcementCaseCreate, db: Session = Depends(get_db)):
    """保存维权案例记录."""
    result = save_enforcement_case(db, "current_user", req.model_dump())
    return result


@router.get("/my-cases", response_model=dict)
def my_cases(db: Session = Depends(get_db)):
    """获取我的维权案例和统计汇总."""
    return get_user_cases(db, "current_user")
