"""商业转化引擎 API 路由 — 对应: docs/modules-v5/04-monetization-engine.md
Phase 1: POD渠道管理、Canvas预览、Printful Mockup
端点: 50 (supply)

⚠️ [已废弃 v5.0] 本模块已被合约市场系统替代，保留供迁移过渡使用。
   新功能请使用 /contract/* 路由。
"""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.common import ApiResponse
from app.schemas.supply import (
    SpecValidateRequest,
    SpecValidateBatchRequest,
    ProductCreate,
    ProductUpdate,
    ChannelCreate,
    CampaignCreate,
    CampaignUpdate,
    LicenseCreate,
    SupplyPartnerCreate,
    SupplyOrderCreate,
    OrderStatusUpdate,
    OrderSampleAction,
    RevenueCreate,
    ReminderCreate,
    PublishToPodRequest,
    FundingGoalRequest,
    FactoryPriceCompareRequest,
    PrintfulMockupRequest,
    ProductMockupRequest,
    DigitalProductValidateRequest,
    MonetizationAdvisorRequest,
    ListingCreate,
    ListingUpdate,
    DesignCompatRequest,
    RemediationRequest,
)
from app.deps import require_auth
from app.services.supply_service import SupplyService

router = APIRouter()


# ─── 产品品类与变现路径 ─────────────────────────────────────────

@router.get("/supply/product-categories", response_model=ApiResponse[dict])
def list_product_categories(material: Optional[str] = None):
    """获取全品类列表 (按材质分类)."""
    svc = SupplyService()
    return svc.list_product_categories(material)


@router.get("/supply/monetization-paths", response_model=ApiResponse[list])
def list_monetization_paths():
    """获取五条变现路径."""
    svc = SupplyService()
    return svc.list_monetization_paths()


@router.get("/supply/platforms", response_model=ApiResponse[list])
def list_platforms():
    """获取支持的变现平台列表."""
    svc = SupplyService()
    return svc.list_platforms()


# ─── 设计规格校验 ──────────────────────────────────────────────

@router.post("/supply/spec-validate", response_model=ApiResponse)
def validate_design_for_category(data: SpecValidateRequest):
    """校验设计稿是否满足指定产品规格."""
    svc = SupplyService()
    return svc.validate_design_spec(data)


@router.post("/supply/spec-validate-batch", response_model=ApiResponse)
def validate_design_for_multiple_categories(data: SpecValidateBatchRequest):
    """批量校验设计稿."""
    svc = SupplyService()
    return svc.validate_design_batch(data)


# ─── Products CRUD ─────────────────────────────────────────────

@router.get("/supply/products", response_model=ApiResponse[list])
def list_products(
    monetization_path: Optional[str] = None,
    platform: Optional[str] = None,
    material_category: Optional[str] = None,
    status: Optional[str] = None,
    work_id: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """产品列表."""
    svc = SupplyService(db)
    return svc.list_products(monetization_path, platform, material_category, status, work_id)


@router.post("/supply/products", response_model=ApiResponse, dependencies=[Depends(require_auth)])
def create_product(data: ProductCreate, db: Session = Depends(get_db)):
    """创建商品."""
    svc = SupplyService(db)
    return svc.create_product(data)


@router.get("/supply/products/{product_id}", response_model=ApiResponse)
def get_product(product_id: str, db: Session = Depends(get_db)):
    """获取商品详情."""
    svc = SupplyService(db)
    return svc.get_product(product_id)


@router.patch("/supply/products/{product_id}", response_model=ApiResponse, dependencies=[Depends(require_auth)])
def update_product(product_id: str, data: ProductUpdate, db: Session = Depends(get_db)):
    """更新商品."""
    svc = SupplyService(db)
    return svc.update_product(product_id, data)


# ─── 变现渠道 ──────────────────────────────────────────────────

@router.get("/supply/channels", response_model=ApiResponse[list])
def list_channels(
    channel_type: Optional[str] = None,
    status: Optional[str] = "active",
    db: Session = Depends(get_db),
):
    """变现渠道列表."""
    svc = SupplyService(db)
    return svc.list_channels(channel_type, status)


@router.post("/supply/channels", response_model=ApiResponse, dependencies=[Depends(require_auth)])
def create_channel(data: ChannelCreate, db: Session = Depends(get_db)):
    """添加变现渠道."""
    svc = SupplyService(db)
    return svc.create_channel(data)


# ─── 众筹项目 ──────────────────────────────────────────────────

@router.get("/supply/campaigns", response_model=ApiResponse[list])
def list_campaigns(
    platform: Optional[str] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """众筹项目列表."""
    svc = SupplyService(db)
    return svc.list_campaigns(platform, status)


@router.post("/supply/campaigns", response_model=ApiResponse, dependencies=[Depends(require_auth)])
def create_campaign(data: CampaignCreate, db: Session = Depends(get_db)):
    """创建众筹项目."""
    svc = SupplyService(db)
    return svc.create_campaign(data)


@router.patch("/supply/campaigns/{campaign_id}", response_model=ApiResponse, dependencies=[Depends(require_auth)])
def update_campaign(campaign_id: str, data: CampaignUpdate, db: Session = Depends(get_db)):
    """更新众筹项目."""
    svc = SupplyService(db)
    return svc.update_campaign(campaign_id, data)


@router.get("/supply/campaigns/{campaign_id}/report", response_model=ApiResponse)
def export_campaign_report(campaign_id: str, db: Session = Depends(get_db)):
    """导出众筹项目报表."""
    svc = SupplyService(db)
    return svc.export_campaign_report(campaign_id)


@router.get("/supply/campaigns/reward-templates", response_model=ApiResponse[list])
def list_reward_tier_templates():
    """获取众筹奖励档位模板."""
    svc = SupplyService()
    return svc.list_reward_tier_templates()


@router.post("/supply/campaigns/calculate-goal", response_model=ApiResponse, dependencies=[Depends(require_auth)])
def calculate_funding_goal(data: FundingGoalRequest, db: Session = Depends(get_db)):
    """计算建议众筹目标金额."""
    svc = SupplyService(db)
    return svc.calculate_funding_goal(data)


# ─── IP 授权 ───────────────────────────────────────────────────

@router.get("/supply/licenses", response_model=ApiResponse[list])
def list_licenses(
    license_type: Optional[str] = None,
    status: Optional[str] = "active",
    db: Session = Depends(get_db),
):
    """授权记录列表."""
    svc = SupplyService(db)
    return svc.list_licenses(license_type, status)


@router.get("/supply/licenses/templates", response_model=ApiResponse[list])
def list_license_templates():
    """授权条款模板."""
    svc = SupplyService()
    return svc.list_license_templates()


@router.post("/supply/licenses", response_model=ApiResponse, dependencies=[Depends(require_auth)])
def create_license(data: LicenseCreate, db: Session = Depends(get_db)):
    """创建授权条款."""
    svc = SupplyService(db)
    return svc.create_license(data)


@router.get("/supply/licenses/{license_id}/export", response_model=ApiResponse)
def export_license(license_id: str, format: str = "creative_fabrica", db: Session = Depends(get_db)):
    """导出授权为第三方平台格式."""
    svc = SupplyService(db)
    return svc.export_license(license_id, format)


# ─── Partners ──────────────────────────────────────────────────

@router.get("/supply/partners", response_model=ApiResponse[list])
def list_partners(
    status: Optional[str] = "active",
    partner_type: Optional[str] = None,
    product_category: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """获取合作伙伴列表."""
    svc = SupplyService(db)
    return svc.list_partners(status, partner_type, product_category)


@router.post("/supply/partners", response_model=ApiResponse, dependencies=[Depends(require_auth)])
def create_partner(data: SupplyPartnerCreate, db: Session = Depends(get_db)):
    """创建合作伙伴."""
    svc = SupplyService(db)
    return svc.create_partner(data)


# ─── Orders ────────────────────────────────────────────────────

@router.get("/supply/orders", response_model=ApiResponse[list])
def list_orders(
    status: Optional[str] = None,
    partner_id: Optional[str] = None,
    order_type: Optional[str] = None,
    campaign_id: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """获取订单列表."""
    svc = SupplyService(db)
    return svc.list_orders(status, partner_id, order_type, campaign_id)


@router.post("/supply/orders", response_model=ApiResponse, dependencies=[Depends(require_auth)])
def create_order(data: SupplyOrderCreate, db: Session = Depends(get_db)):
    """创建订单."""
    svc = SupplyService(db)
    return svc.create_order(data)


@router.patch("/supply/orders/{order_id}/status", response_model=ApiResponse, dependencies=[Depends(require_auth)])
def update_order_status(order_id: str, data: OrderStatusUpdate, db: Session = Depends(get_db)):
    """更新订单状态."""
    svc = SupplyService(db)
    return svc.update_order_status(order_id, data)


@router.post("/supply/orders/{order_id}/sample", response_model=ApiResponse, dependencies=[Depends(require_auth)])
def manage_order_sample(order_id: str, data: OrderSampleAction, db: Session = Depends(get_db)):
    """样品管理."""
    svc = SupplyService(db)
    return svc.manage_order_sample(order_id, data)


# ─── Revenue ───────────────────────────────────────────────────

@router.get("/supply/revenue", response_model=ApiResponse[list])
def list_revenue(
    platform: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """收入列表."""
    svc = SupplyService(db)
    return svc.list_revenue(platform)


@router.post("/supply/revenue", response_model=ApiResponse, dependencies=[Depends(require_auth)])
def create_revenue(data: RevenueCreate, db: Session = Depends(get_db)):
    """手动录入收入."""
    svc = SupplyService(db)
    return svc.create_revenue(data)


@router.get("/supply/revenue/summary", response_model=ApiResponse[dict])
def revenue_summary(db: Session = Depends(get_db)):
    """收入汇总."""
    svc = SupplyService(db)
    return svc.revenue_summary()


@router.get("/supply/dashboard", response_model=ApiResponse[dict])
def supply_dashboard(db: Session = Depends(get_db)):
    """变现仪表盘."""
    svc = SupplyService(db)
    return svc.supply_dashboard()


@router.get("/supply/revenue/aggregated", response_model=ApiResponse[dict])
def aggregated_revenue(db: Session = Depends(get_db)):
    """聚合收入分析."""
    svc = SupplyService(db)
    return svc.aggregated_revenue()


# ─── Reminders ─────────────────────────────────────────────────

@router.get("/supply/reminders", response_model=ApiResponse[list])
def list_reminders(
    status: Optional[str] = "pending",
    db: Session = Depends(get_db),
):
    """获取提醒列表."""
    svc = SupplyService(db)
    return svc.list_reminders(status)


@router.post("/supply/reminders", response_model=ApiResponse, dependencies=[Depends(require_auth)])
def create_reminder(data: ReminderCreate, db: Session = Depends(get_db)):
    """创建提醒."""
    svc = SupplyService(db)
    return svc.create_reminder(data)


# ─── POD 发布 ──────────────────────────────────────────────────

@router.post("/supply/publish-to-pod", response_model=ApiResponse, dependencies=[Depends(require_auth)])
async def publish_to_pod(data: PublishToPodRequest, db: Session = Depends(get_db)):
    """发布设计到 POD 平台."""
    svc = SupplyService(db)
    return await svc.publish_to_pod(data)


# ─── 中国 POD 平台 ─────────────────────────────────────────────

@router.get("/supply/chinese-pod-platforms", response_model=ApiResponse[list])
def list_chinese_pod_platforms():
    """获取中国 POD 平台列表."""
    svc = SupplyService()
    return svc.list_chinese_pod_platforms()


@router.get("/supply/chinese-pod-platforms/{platform_id}", response_model=ApiResponse)
def get_chinese_pod_platform_detail(platform_id: str):
    """获取中国 POD 平台详情."""
    svc = SupplyService()
    return svc.get_chinese_pod_platform_detail(platform_id)


# ─── 工厂比价 ──────────────────────────────────────────────────

@router.post("/supply/factory-price-compare", response_model=ApiResponse, dependencies=[Depends(require_auth)])
def factory_price_compare(data: FactoryPriceCompareRequest, db: Session = Depends(get_db)):
    """工厂报价对比工具."""
    svc = SupplyService(db)
    return svc.factory_price_compare(data)


# ─── Mockup 生成 ───────────────────────────────────────────────

@router.post("/supply/mockup/printful", response_model=ApiResponse)
async def generate_printful_mockup(data: PrintfulMockupRequest):
    """Printful Mockup API 照片级效果图."""
    svc = SupplyService()
    return await svc.generate_printful_mockup(
        data.product_id, data.design_file_id, data.colors
    )


@router.post("/supply/generate-mockup", response_model=ApiResponse)
async def generate_product_mockup(data: ProductMockupRequest):
    """AI 产品效果图生成."""
    svc = SupplyService()
    return await svc.generate_product_mockup(
        data.category_id, data.prompt or "", data.style or ""
    )


# ─── 数字产品格式化 ────────────────────────────────────────────

@router.get("/supply/digital-product-formats", response_model=ApiResponse[list])
def list_digital_product_formats():
    """获取数字产品格式元数据."""
    svc = SupplyService()
    return svc.list_digital_product_formats()


@router.post("/supply/digital-product/validate", response_model=ApiResponse)
def validate_digital_product(data: DigitalProductValidateRequest):
    """校验数字产品是否符合目标平台要求."""
    svc = SupplyService()
    formats_resp = svc.list_digital_product_formats()
    formats = formats_resp.data

    product_type = data.product_type
    target_platform = data.target_platform
    file_formats = data.file_formats
    file_count = data.file_count
    file_size_mb = data.file_size_mb
    has_preview = data.has_preview

    matching_format = None
    for f_info in formats:
        if f_info["product_type"] == product_type:
            if target_platform in f_info.get("platforms", {}):
                matching_format = f_info["platforms"][target_platform]
                break

    if not matching_format:
        raise HTTPException(status_code=400, detail=f"未知产品类型或目标平台: {product_type}/{target_platform}")

    checks = []
    errors = 0
    warnings = 0

    required = matching_format.get("required_formats", [])
    format_match = any(rf in file_formats for rf in required)
    checks.append({
        "check": "file_format",
        "status": "pass" if format_match else "error",
        "message": f"文件格式: {file_formats}",
        "requirement": f"需要包含 {required} 之一",
    })
    if not format_match:
        errors += 1

    max_size = matching_format.get("max_file_size_mb", 100)
    if file_size_mb <= max_size:
        checks.append({"check": "file_size", "status": "pass", "message": f"{file_size_mb}MB <= {max_size}MB"})
    else:
        checks.append({"check": "file_size", "status": "error", "message": f"{file_size_mb}MB > {max_size}MB"})
        errors += 1

    preview_required = matching_format.get("preview_required", False)
    if preview_required:
        if has_preview:
            checks.append({"check": "preview", "status": "pass", "message": "已提供预览"})
        else:
            checks.append({"check": "preview", "status": "error", "message": "缺少预览图"})
            errors += 1

    min_previews = matching_format.get("min_preview_count", 0)
    if min_previews > 0:
        if file_count >= min_previews:
            checks.append({"check": "preview_count", "status": "pass", "message": f"预览数量 {file_count} >= {min_previews}"})
        else:
            checks.append({"check": "preview_count", "status": "warning", "message": f"预览数量 {file_count} < {min_previews}"})
            warnings += 1

    if matching_format.get("help_file_required"):
        checks.append({"check": "help_file", "status": "warning", "message": "建议包含说明文件"})
        warnings += 1

    return ApiResponse(data={
        "product_type": product_type,
        "target_platform": target_platform,
        "requirements": matching_format,
        "checks": checks,
        "passed": errors == 0,
        "error_count": errors,
        "warning_count": warnings,
    })


# ─── Monetization Advisor ──────────────────────────────────────

@router.post("/supply/monetization-advisor", response_model=ApiResponse)
async def monetization_advisor(data: MonetizationAdvisorRequest):
    """AI 变现策略顾问."""
    svc = SupplyService()
    return await svc.monetization_advisor(
        data.work_title, data.work_type, data.creator_type, data.current_paths
    )


# ─── Design Listing CRUD ───────────────────────────────────────

@router.get("/supply/listings", response_model=ApiResponse[list])
def list_listings(
    monetization_path: Optional[str] = None,
    platform: Optional[str] = None,
    material_category: Optional[str] = None,
    status: Optional[str] = None,
    work_id: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """商品列表."""
    svc = SupplyService(db)
    return svc.list_listings(monetization_path, platform, material_category, status, work_id)


@router.post("/supply/listings", response_model=ApiResponse, dependencies=[Depends(require_auth)])
def create_listing(data: ListingCreate, db: Session = Depends(get_db)):
    """创建商品."""
    svc = SupplyService(db)
    return svc.create_listing(data)


@router.get("/supply/listings/{listing_id}", response_model=ApiResponse)
def get_listing_detail(listing_id: str, db: Session = Depends(get_db)):
    """商品详情."""
    svc = SupplyService(db)
    return svc.get_listing_detail(listing_id)


@router.patch("/supply/listings/{listing_id}", response_model=ApiResponse, dependencies=[Depends(require_auth)])
def update_listing(listing_id: str, data: ListingUpdate, db: Session = Depends(get_db)):
    """更新商品信息."""
    svc = SupplyService(db)
    return svc.update_listing(listing_id, data)


@router.delete("/supply/listings/{listing_id}", response_model=ApiResponse, dependencies=[Depends(require_auth)])
def delete_listing(listing_id: str, db: Session = Depends(get_db)):
    """软删除商品."""
    svc = SupplyService(db)
    return svc.delete_listing(listing_id)


# ─── Spec Validation Compatibility & Remediation ──────────────

@router.post("/supply/spec-validate-compat", response_model=ApiResponse)
def validate_design_compatibility(data: DesignCompatRequest):
    """兼容产品推荐."""
    svc = SupplyService()
    return svc.validate_design_compatibility(
        {"dpi": data.dpi, "width_px": data.width_px, "height_px": data.height_px,
         "color_mode": data.color_mode, "file_format": data.file_format,
         "has_transparency": data.has_transparency},
        data.exclude_category_id,
        data.limit,
    )


@router.post("/supply/spec-validate-remediation", response_model=ApiResponse)
def get_remediation_suggestions(data: RemediationRequest):
    """修复建议."""
    svc = SupplyService()
    return svc.get_remediation_suggestions(
        data.category_id,
        {"dpi": data.dpi, "width_px": data.width_px, "height_px": data.height_px,
         "color_mode": data.color_mode, "file_format": data.file_format,
         "has_transparency": data.has_transparency},
    )
