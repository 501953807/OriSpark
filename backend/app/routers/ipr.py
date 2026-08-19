"""IP 登记指引 API 路由 — 对应: docs/modules-v5/03-ip-registration.md
Phase 0.2: 合规改造(多推荐+置信度+免责声明+律师审核步骤)
端点: 24 (ipr)
"""
import logging

from datetime import date, datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import get_db
from app.models.ipr import (
    IPRegistration, TrademarkClass, CopyrightRegistration,
    TrademarkRegistration, NiceClassification, ApplicationTemplate,
    TrademarkQueryRecord,
)
from app.models.work import Work, WorkTag
from app.models.notary import NotaryRecord
from app.schemas.common import ApiResponse
from app.deps import require_auth
from sqlalchemy.exc import SQLAlchemyError
from app.utils.errors import BusinessException

router = APIRouter()

from app.services.ipr_service import IprService, CreateIPRegistrationPayload, UpdateIPRegistrationPayload, RecommendClassesPayload, PrefillApplicationPayload, ValidateApplicationPayload, GenerateApplicationPayload, ExportApplicationPayload, FeeCalculatorPayload
from app.services.ip_recommendation_service import IPRecommendationService
from app.schemas.ipr import RecommendCategoriesPayload, AdvanceStatusPayload
# ─── 端点实现 ───────────────────────────────────────────────────

@router.get("/ipr/registrations", response_model=ApiResponse[list])
def list_ip_registrations(
    ip_type: Optional[str] = None,
    jurisdiction: Optional[str] = None,
    status: Optional[str] = None,
    work_id: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    user_id: str = Depends(require_auth),
):
    """获取 IP 登记列表 (支持 ip_type/jurisdiction/status/work_id 过滤)."""
    svc = IprService(db)
    return svc.list_ip_registrations(ip_type, jurisdiction, status, user_id=user_id, work_id=work_id)


@router.post("/ipr/registrations", response_model=ApiResponse, dependencies=[Depends(require_auth)])
def create_ip_registration(
    data: CreateIPRegistrationPayload,
    db: Session = Depends(get_db),
):
    """创建 IP 登记记录."""
    svc = IprService(db)
    return svc.create_ip_registration(data)


@router.get("/ipr/registrations/{record_id}", response_model=ApiResponse)
def get_ip_registration(
    record_id: str,
    db: Session = Depends(get_db),
):
    """获取 IP 登记记录详情."""
    svc = IprService(db)
    return svc.get_ip_registration(record_id)


@router.patch("/ipr/registrations/{record_id}", response_model=ApiResponse, dependencies=[Depends(require_auth)])
def update_ip_registration(
    record_id: str,
    data: UpdateIPRegistrationPayload,
    db: Session = Depends(get_db),
    user_id: str = Depends(require_auth),
):
    """更新 IP 登记记录."""
    svc = IprService(db)
    return svc.update_ip_registration(record_id, data, user_id=user_id)


@router.delete("/ipr/registrations/{record_id}", response_model=ApiResponse, dependencies=[Depends(require_auth)])
def delete_ip_registration(
    record_id: str,
    db: Session = Depends(get_db),
):
    """删除 IP 登记记录 (软删除)."""
    svc = IprService(db)
    return svc.delete_ip_registration(record_id)


@router.get("/ipr/guidelines", response_model=ApiResponse)
def get_ipr_guidelines(
    jurisdiction: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """获取 IP 登记指引 (支持 jurisdiction 过滤)."""
    svc = IprService(db)
    return svc.get_ipr_guidelines(jurisdiction)


@router.get("/ipr/guidelines/{ip_type}", response_model=ApiResponse)
def get_ipr_guidelines_by_type(
    ip_type: str,
    jurisdiction: Optional[str] = None,
    version: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """获取指定 IP 类型的详细指引."""
    svc = IprService(db)
    return svc.get_ipr_guidelines_by_type(ip_type, jurisdiction or "cn", version)


@router.get("/ipr/nice-classes", response_model=ApiResponse)
def list_nice_classes(
    search: Optional[str] = None,
    creative_only: bool = Query(False),
    db: Session = Depends(get_db),
):
    """获取尼斯分类列表."""
    svc = IprService(db)
    return svc.list_nice_classes(search, creative_only)


@router.get("/ipr/nice-classes/{class_no}/goods", response_model=ApiResponse)
def get_class_goods(
    class_no: int,
    db: Session = Depends(get_db),
):
    """获取指定类别的商品/服务项目."""
    svc = IprService(db)
    return svc.get_class_goods(class_no)


@router.post("/ipr/recommend/classes", response_model=ApiResponse, dependencies=[Depends(require_auth)])
def recommend_classes(
    data: RecommendClassesPayload,
    db: Session = Depends(get_db),
):
    """基于标签推荐尼斯类别."""
    svc = IprService(db)
    return svc.recommend_classes(data)


@router.get("/ipr/recommend/strategies", response_model=ApiResponse)
def get_recommend_strategies(
    db: Session = Depends(get_db),
):
    """获取创作者策略推荐."""
    svc = IprService(db)
    return svc.get_recommend_strategies()


@router.get("/ipr/templates", response_model=ApiResponse)
def get_application_templates(
    ip_type: Optional[str] = None,
    jurisdiction: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """获取申请模板列表."""
    svc = IprService(db)
    return svc.get_application_templates(ip_type, jurisdiction)


@router.get("/ipr/templates/{template_id}", response_model=ApiResponse)
def get_application_template(
    template_id: str,
    db: Session = Depends(get_db),
):
    """获取申请模板详情."""
    svc = IprService(db)
    return svc.get_application_template(template_id)


@router.post("/ipr/assistant/prefill", response_model=ApiResponse, dependencies=[Depends(require_auth)])
def prefill_application(
    data: PrefillApplicationPayload,
    db: Session = Depends(get_db),
):
    """预填申请表单字段."""
    svc = IprService(db)
    return svc.prefill_application(data)


@router.post("/ipr/assistant/validate", response_model=ApiResponse, dependencies=[Depends(require_auth)])
def validate_application(
    data: ValidateApplicationPayload,
    db: Session = Depends(get_db),
):
    """校验申请表单字段."""
    svc = IprService(db)
    return svc.validate_application(data)


@router.post("/ipr/assistant/generate", response_model=ApiResponse, dependencies=[Depends(require_auth)])
def generate_application(
    data: GenerateApplicationPayload,
    db: Session = Depends(get_db),
):
    """生成申请表单内容."""
    svc = IprService(db)
    return svc.generate_application(data)


@router.post("/ipr/assistant/export", response_model=ApiResponse, dependencies=[Depends(require_auth)])
def export_application(
    data: ExportApplicationPayload,
    db: Session = Depends(get_db),
):
    """导出申请表单."""
    svc = IprService(db)
    return svc.export_application(data)


@router.post("/ipr/registrations/{record_id}/export-package", response_model=ApiResponse, dependencies=[Depends(require_auth)])
def export_application_package(
    record_id: str,
    db: Session = Depends(get_db),
):
    """导出完整申请材料包 (ZIP 格式)."""
    svc = IprService(db)
    return svc.export_application_package(record_id)


@router.get("/ipr/portfolio", response_model=ApiResponse)
def get_ip_portfolio(
    db: Session = Depends(get_db),
):
    """IP 资产组合总览."""
    svc = IprService(db)
    return svc.get_ip_portfolio()


@router.get("/ipr/reminders", response_model=ApiResponse)
def get_reminders(
    db: Session = Depends(get_db),
):
    """获取 IP 续展/到期提醒."""
    svc = IprService(db)
    return svc.get_reminders()


@router.get("/ipr/dashboard", response_model=ApiResponse)
def get_ip_dashboard(
    db: Session = Depends(get_db),
):
    """IP 资产仪表盘."""
    svc = IprService(db)
    return svc.get_ip_dashboard()


@router.get("/ipr/paths", response_model=ApiResponse)
def get_ipr_paths(
    db: Session = Depends(get_db),
):
    """获取 IP 登记全局路径信息."""
    svc = IprService(db)
    return svc.get_ipr_paths()


@router.get("/ipr/gazette/{jurisdiction}", response_model=ApiResponse)
def get_trademark_gazette_info(
    jurisdiction: str,
    db: Session = Depends(get_db),
):
    """获取商标公告监测信息."""
    svc = IprService(db)
    return svc.get_trademark_gazette_info(jurisdiction)


@router.post("/ipr/fee-calculator", response_model=ApiResponse, dependencies=[Depends(require_auth)])
def fee_calculator(
    data: FeeCalculatorPayload,
    db: Session = Depends(get_db),
):
    """费用计算器."""
    svc = IprService(db)
    return svc.fee_calculator(data)


@router.post("/ipr/recommend-categories", response_model=ApiResponse, dependencies=[Depends(require_auth)])
def recommend_categories(
    data: RecommendCategoriesPayload,
    db: Session = Depends(get_db),
):
    """根据作品描述推荐尼斯分类."""
    svc = IPRecommendationService(db)
    return ApiResponse(data=svc.recommend_classes(data.description, data.ip_type))


@router.get("/ipr/registration/{id}/material-list", response_model=ApiResponse)
def get_material_list(
    id: str,
    db: Session = Depends(get_db),
):
    """获取当前状态的材料清单."""
    record = db.query(IPRegistration).filter(IPRegistration.id == id).first()
    if not record:
        raise BusinessException("记录不存在", status_code=404)
    from app.services.ipr_service import _get_material_list_for_status
    return ApiResponse(data=_get_material_list_for_status(record.status, record.ip_type))


@router.post("/ipr/registration/{id}/advance", response_model=ApiResponse, dependencies=[Depends(require_auth)])
def advance_registration_status(
    id: str,
    data: AdvanceStatusPayload,
    db: Session = Depends(get_db),
):
    """推进IP登记状态."""
    from app.services.ipr_service import _VALID_TRANSITIONS, _advance_registration_status
    return _advance_registration_status(db, id, data.status, data.note)




# ── 商标查询端点 ───────────────────────────────────────────────────────

class TrademarkQueryRequest(BaseModel):
    text: str
    jurisdiction: str = "cn"
    class_no: Optional[str] = None
    user_id: Optional[str] = "local"


@router.post("/ipr/trademark/query", response_model=ApiResponse, dependencies=[Depends(require_auth)])
def trademark_query_endpoint(
    body: TrademarkQueryRequest,
    db: Session = Depends(get_db),
):
    """商标查询 — 对接 Gateway ABC 模式."""
    svc = IprService(db)
    return svc.trademark_query(
        text=body.text,
        jurisdiction=body.jurisdiction,
        class_no=body.class_no,
        user_id=body.user_id or "local",
        db=db,
    )


@router.get("/ipr/trademark/history", response_model=ApiResponse)
def trademark_history_endpoint(
    user_id: Optional[str] = "local",
    jurisdiction: Optional[str] = None,
    limit: int = 20,
    db: Session = Depends(get_db),
):
    """获取商标查询历史记录."""
    svc = IprService(db)
    return svc.trademark_history(user_id=user_id, jurisdiction=jurisdiction, limit=limit)


@router.get("/ipr/trademark/sources", response_model=ApiResponse)
def trademark_sources_endpoint(db: Session = Depends(get_db)):
    """返回可用的商标数据库源列表."""
    svc = IprService(db)
    return svc.trademark_sources()
