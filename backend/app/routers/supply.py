"""商业转化引擎 API 路由 — 对应: docs/modules-v3/04-monetization-engine.md
Phase 1: POD渠道管理、Canvas预览、Printful Mockup
端点: 50 (supply)

Features:
  - 增强 Products CRUD (含变现路径/材质/平台)
  - 变现渠道管理
  - 众筹项目管理
  - IP 授权管理
  - 增强 Partners CRUD (含制造能力)
  - 增强 Orders CRUD (含订单类型/样品管理)
  - 变现仪表盘
"""

from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.database import get_db
from app.models.supply import Partner, Order, OrderPayment, OrderCommunication, Reminder
from app.models.publish import Product, RevenueRecord, ProductPublishing
from app.models.monetization import ProductTemplate, MonetizationChannel, Campaign, License
from app.models.listings import DesignListing, DesignTemplateCompatibility
from app.schemas.common import ApiResponse
from app.utils.crypto import encrypt, decrypt
from app.services.seed_data import (
    PRODUCT_CATEGORIES, MATERIAL_CATEGORIES, MONETIZATION_PATHS, PLATFORMS,
    get_categories_by_material, get_category_by_id, get_monetization_path,
)
from app.services.spec_checker import validate_design_spec, validate_for_multiple_categories

router = APIRouter()


# ============================================================================
# 9.1 产品品类与变现路径 (Seed Data)
# ============================================================================

@router.get("/supply/product-categories", response_model=ApiResponse[dict])
def list_product_categories(
    material: Optional[str] = None,
):
    """获取全品类列表(按材质分类) — P1.5.1."""
    categories = PRODUCT_CATEGORIES
    if material:
        categories = [c for c in categories if c["material_category"] == material]

    # Group by material
    grouped = {}
    for c in categories:
        mat = c["material_category"]
        if mat not in grouped:
            grouped[mat] = {
                "material_id": mat,
                "material_label_zh": c["material_label_zh"],
                "categories": [],
            }
        grouped[mat]["categories"].append(c)

    return ApiResponse(data={
        "materials": MATERIAL_CATEGORIES,
        "categories_by_material": grouped,
        "total_categories": len(PRODUCT_CATEGORIES),
    })


@router.get("/supply/monetization-paths", response_model=ApiResponse[list])
def list_monetization_paths():
    """获取五条变现路径."""
    return ApiResponse(data=MONETIZATION_PATHS)


@router.get("/supply/platforms", response_model=ApiResponse[list])
def list_platforms():
    """获取支持的变现平台列表."""
    return ApiResponse(data=PLATFORMS)


# ============================================================================
# 9.2 设计规格校验
# ============================================================================

@router.post("/supply/spec-validate", response_model=ApiResponse)
def validate_design_for_category(data: dict):
    """校验设计稿是否满足指定产品规格 — P1.5.3-P1.5.4.

    Body:
        category_id: str — 产品品类 ID (from seed data)
        dpi: int (optional) — 设计稿 DPI
        width_px: int (optional) — 宽度(像素)
        height_px: int (optional) — 高度(像素)
        color_mode: str (optional) — 'sRGB' / 'CMYK'
        file_format: str (optional) — 'PNG' / 'JPEG' / 'PDF'
        has_transparency: bool (optional) — 是否有透明背景
    """
    category_id = data.get("category_id")
    if not category_id:
        raise HTTPException(status_code=400, detail="缺少 category_id")

    template = get_category_by_id(category_id)
    if not template:
        raise HTTPException(status_code=400, detail=f"未知品类: {category_id}")

    design_spec = {
        "dpi": data.get("dpi"),
        "width_px": data.get("width_px"),
        "height_px": data.get("height_px"),
        "color_mode": data.get("color_mode"),
        "file_format": data.get("file_format"),
        "has_transparency": data.get("has_transparency"),
    }

    report = validate_design_spec(template, **{k: v for k, v in design_spec.items() if v is not None})

    # P2: Also return compatible categories for remediation
    compatible = get_compatible_templates(
        design_spec, PRODUCT_CATEGORIES,
        exclude_category_id=category_id,
        limit=10,
    )

    return ApiResponse(data={
        "product_category": template["name_zh"],
        "category_id": template["id"],
        "overall_status": report.overall_status,
        "passed": report.passed,
        "error_count": report.error_count,
        "warning_count": report.warning_count,
        "checks": [
            {
                "check": c.check,
                "status": c.status,
                "message": c.message,
                "suggestion": c.suggestion,
            }
            for c in report.checks
        ],
        "compatible_categories": [
            {
                "template_id": c.template_id,
                "name_zh": c.name_zh,
                "compatibility_score": c.compatibility_score,
                "spec_result": c.spec_result,
                "error_count": c.error_count,
                "warning_count": c.warning_count,
                "min_required": c.min_required_px,
                "current_meets": c.current_meets,
            }
            for c in compatible
        ],
    })


@router.post("/supply/spec-validate-batch", response_model=ApiResponse)
def validate_design_for_multiple_categories(data: dict):
    """校验设计稿是否满足多个产品品类规格 — P1.5.4.

    Body:
        category_ids: list[str] — 产品品类 ID 列表
        dpi, width_px, height_px, color_mode, file_format, has_transparency (optional)
    """
    category_ids = data.get("category_ids", [])
    if not category_ids:
        raise HTTPException(status_code=400, detail="缺少 category_ids")

    templates = [get_category_by_id(cid) for cid in category_ids]
    templates = [t for t in templates if t is not None]
    if not templates:
        raise HTTPException(status_code=400, detail="找不到任何有效品类")

    design_spec = {
        "dpi": data.get("dpi"),
        "width_px": data.get("width_px"),
        "height_px": data.get("height_px"),
        "color_mode": data.get("color_mode"),
        "file_format": data.get("file_format"),
        "has_transparency": data.get("has_transparency"),
    }
    clean_spec = {k: v for k, v in design_spec.items() if v is not None}

    reports = validate_for_multiple_categories(clean_spec, templates)
    return ApiResponse(data={
        "results": [
            {
                "product_category": r.product_name,
                "category_id": r.product_category_id,
                "overall_status": r.overall_status,
                "passed": r.passed,
                "error_count": r.error_count,
                "warning_count": r.warning_count,
                "checks": [{"check": c.check, "status": c.status, "message": c.message, "suggestion": c.suggestion} for c in r.checks],
            }
            for r in reports
        ],
        "overall_passed": all(r.passed for r in reports),
        "total_errors": sum(r.error_count for r in reports),
        "total_warnings": sum(r.warning_count for r in reports),
    })


# ============================================================================
# 9.3 Products CRUD (Enhanced — P1.5.2)
# ============================================================================

# @deprecated: Use /supply/listings instead. Scheduled for removal in v3.
@router.get("/supply/products", response_model=ApiResponse[list])
def list_products(
    monetization_path: Optional[str] = None,
    platform: Optional[str] = None,
    material_category: Optional[str] = None,
    status: Optional[str] = None,
    work_id: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """产品列表 — P1.5.2 增强 (支持多维度过滤)."""
    query = db.query(Product)
    if monetization_path:
        query = query.filter(Product.monetization_path == monetization_path)
    if platform:
        query = query.filter(Product.platform == platform)
    if material_category:
        query = query.filter(Product.material_category == material_category)
    if status:
        query = query.filter(Product.status == status)
    if work_id:
        query = query.filter(Product.work_id == work_id)

    products = query.order_by(Product.created_at.desc()).all()

    return ApiResponse(data=[
        {
            "id": p.id, "work_id": p.work_id, "title": p.title,
            "description": p.description, "price": p.price, "cost": p.cost,
            "currency": p.currency, "category": p.category,
            "monetization_path": p.monetization_path,
            "material_category": p.material_category,
            "platform": p.platform, "platform_product_id": p.platform_product_id,
            "platform_product_url": p.platform_product_url,
            "platform_status": p.platform_status,
            "specifications": p.specifications,
            "design_variant_path": p.design_variant_path,
            "mockup_image_path": p.mockup_image_path,
            "images": p.images, "status": p.status,
            "created_at": p.created_at.isoformat() if p.created_at else None,
            "updated_at": p.updated_at.isoformat() if p.updated_at else None,
        }
        for p in products
    ])


@router.post("/supply/products", response_model=ApiResponse)
def create_product(data: dict, db: Session = Depends(get_db)):
    """创建商品 — P1.5.2 增强 (关联作品+变现路径+品类+平台)."""
    product = Product(
        work_id=data.get("work_id"),
        title=data.get("title"),
        description=data.get("description"),
        price=data.get("price", 0),
        cost=data.get("cost", 0),
        currency=data.get("currency", "CNY"),
        category=data.get("category"),
        monetization_path=data.get("monetization_path"),
        material_category=data.get("material_category"),
        platform=data.get("platform"),
        specifications=data.get("specifications"),
        design_variant_path=data.get("design_variant_path"),
        mockup_image_path=data.get("mockup_image_path"),
        images=data.get("images"),
        platform_status=data.get("platform_status", "draft"),
        status=data.get("status", "active"),
    )
    db.add(product)
    db.commit()
    db.refresh(product)

    return ApiResponse(message="商品已创建", data={"id": product.id})


@router.get("/supply/products/{product_id}", response_model=ApiResponse)
def get_product(product_id: str, db: Session = Depends(get_db)):
    """获取商品详情 — P1.5.2."""
    p = db.query(Product).filter(Product.id == product_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="商品不存在")

    # Gather revenue records too
    revenues = db.query(RevenueRecord).filter(RevenueRecord.product_id == product_id).all()

    return ApiResponse(data={
        "id": p.id, "work_id": p.work_id, "title": p.title,
        "description": p.description, "price": p.price, "cost": p.cost,
        "currency": p.currency, "category": p.category,
        "monetization_path": p.monetization_path,
        "material_category": p.material_category,
        "platform": p.platform, "platform_product_id": p.platform_product_id,
        "platform_product_url": p.platform_product_url,
        "platform_status": p.platform_status,
        "specifications": p.specifications,
        "design_variant_path": p.design_variant_path,
        "mockup_image_path": p.mockup_image_path,
        "images": p.images, "status": p.status,
        "revenues": [
            {"id": r.id, "amount": r.amount, "currency": r.currency,
             "date": r.date.isoformat() if r.date else None,
             "platform": r.platform, "order_count": r.order_count,
             "source": getattr(r, 'source', 'manual'),
             "refund_amount": getattr(r, 'refund_amount', 0),
             "platform_fee": getattr(r, 'platform_fee', 0),
             "net_revenue": getattr(r, 'net_revenue', 0),
             "notes": r.notes}
            for r in revenues
        ],
        "total_revenue": sum(r.amount for r in revenues),
        "created_at": p.created_at.isoformat() if p.created_at else None,
        "updated_at": p.updated_at.isoformat() if p.updated_at else None,
    })


@router.patch("/supply/products/{product_id}", response_model=ApiResponse)
def update_product(product_id: str, data: dict, db: Session = Depends(get_db)):
    """更新商品 — P1.5.2."""
    p = db.query(Product).filter(Product.id == product_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="商品不存在")

    updatable = [
        "title", "description", "price", "cost", "category",
        "monetization_path", "material_category", "platform",
        "specifications", "design_variant_path", "mockup_image_path",
        "images", "platform_status", "platform_product_id",
        "platform_product_url", "status",
    ]
    for key in updatable:
        if key in data:
            setattr(p, key, data[key])

    db.commit()
    return ApiResponse(message="商品已更新")


# ============================================================================
# 9.4 变现渠道
# ============================================================================

@router.get("/supply/channels", response_model=ApiResponse[list])
def list_channels(
    channel_type: Optional[str] = None,
    status: Optional[str] = "active",
    db: Session = Depends(get_db),
):
    """变现渠道列表."""
    query = db.query(MonetizationChannel)
    if channel_type:
        query = query.filter(MonetizationChannel.channel_type == channel_type)
    if status:
        query = query.filter(MonetizationChannel.status == status)

    channels = query.order_by(MonetizationChannel.created_at.desc()).all()
    return ApiResponse(data=[
        {
            "id": c.id, "name": c.name, "channel_type": c.channel_type,
            "platform": c.platform, "platform_store_id": c.platform_store_id,
            "platform_store_url": c.platform_store_url,
            "connected_at": c.connected_at.isoformat() if c.connected_at else None,
            "last_sync_at": c.last_sync_at.isoformat() if c.last_sync_at else None,
            "status": c.status,
        }
        for c in channels
    ])


@router.post("/supply/channels", response_model=ApiResponse)
def create_channel(data: dict, db: Session = Depends(get_db)):
    """添加变现渠道."""
    channel = MonetizationChannel(
        name=data.get("name"),
        channel_type=data.get("channel_type"),
        platform=data.get("platform"),
        platform_store_id=data.get("platform_store_id"),
        platform_store_url=data.get("platform_store_url"),
        credentials_encrypted=encrypt(data["credentials"]) if data.get("credentials") else None,
        status=data.get("status", "active"),
    )
    db.add(channel)
    db.commit()
    db.refresh(channel)

    return ApiResponse(message="渠道已添加", data={"id": channel.id})


# ============================================================================
# 9.5 众筹项目
# ============================================================================

@router.get("/supply/campaigns", response_model=ApiResponse[list])
def list_campaigns(
    platform: Optional[str] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """众筹项目列表."""
    query = db.query(Campaign)
    if platform:
        query = query.filter(Campaign.platform == platform)
    if status:
        query = query.filter(Campaign.status == status)

    campaigns = query.order_by(Campaign.created_at.desc()).all()
    return ApiResponse(data=[
        {
            "id": c.id, "title": c.title, "description": c.description,
            "platform": c.platform, "platform_campaign_id": c.platform_campaign_id,
            "platform_url": c.platform_url,
            "goal_amount": c.goal_amount, "currency": c.currency,
            "raised_amount": c.raised_amount, "backer_count": c.backer_count,
            "progress_pct": round(c.raised_amount / c.goal_amount * 100, 1) if c.goal_amount > 0 else 0,
            "reward_tiers": c.reward_tiers,
            "launch_date": c.launch_date.isoformat() if c.launch_date else None,
            "end_date": c.end_date.isoformat() if c.end_date else None,
            "status": c.status,
            "created_at": c.created_at.isoformat() if c.created_at else None,
        }
        for c in campaigns
    ])


@router.post("/supply/campaigns", response_model=ApiResponse)
def create_campaign(data: dict, db: Session = Depends(get_db)):
    """创建众筹项目."""
    campaign = Campaign(
        title=data.get("title"),
        description=data.get("description"),
        platform=data.get("platform"),
        platform_campaign_id=data.get("platform_campaign_id"),
        platform_url=data.get("platform_url"),
        goal_amount=data.get("goal_amount", 0),
        currency=data.get("currency", "CNY"),
        raised_amount=data.get("raised_amount", 0),
        backer_count=data.get("backer_count", 0),
        reward_tiers=data.get("reward_tiers", []),
        launch_date=data.get("launch_date"),
        end_date=data.get("end_date"),
        estimated_delivery_date=data.get("estimated_delivery_date"),
        related_product_ids=data.get("related_product_ids"),
        related_work_ids=data.get("related_work_ids"),
        status=data.get("status", "draft"),
    )
    db.add(campaign)
    db.commit()
    db.refresh(campaign)

    return ApiResponse(message="众筹项目已创建", data={"id": campaign.id})


@router.patch("/supply/campaigns/{campaign_id}", response_model=ApiResponse)
def update_campaign(campaign_id: str, data: dict, db: Session = Depends(get_db)):
    """更新众筹进度."""
    c = db.query(Campaign).filter(Campaign.id == campaign_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="众筹项目不存在")

    updatable = [
        "title", "description", "raised_amount", "backer_count",
        "status", "actual_delivery_date", "platform_url",
    ]
    for key in updatable:
        if key in data:
            setattr(c, key, data[key])

    db.commit()
    return ApiResponse(message="众筹项目已更新")


# ============================================================================
# 9.6 IP 授权
# ============================================================================

@router.get("/supply/licenses", response_model=ApiResponse[list])
def list_licenses(
    license_type: Optional[str] = None,
    status: Optional[str] = "active",
    db: Session = Depends(get_db),
):
    """授权记录列表."""
    query = db.query(License)
    if license_type:
        query = query.filter(License.license_type == license_type)
    if status:
        query = query.filter(License.status == status)

    licenses = query.order_by(License.created_at.desc()).all()
    return ApiResponse(data=[
        {
            "id": l.id, "work_id": l.work_id, "license_type": l.license_type,
            "platform": l.platform,
            "allowed_uses": l.allowed_uses, "restrictions": l.restrictions,
            "price": l.price, "currency": l.currency,
            "platform_listing_id": l.platform_listing_id,
            "platform_listing_url": l.platform_listing_url,
            "sales_count": l.sales_count, "total_revenue": l.total_revenue,
            "status": l.status,
            "created_at": l.created_at.isoformat() if l.created_at else None,
        }
        for l in licenses
    ])


@router.get("/supply/licenses/templates", response_model=ApiResponse[list])
def list_license_templates():
    """授权条款模板."""
    templates = [
        {"id": "single_use", "name_zh": "单次使用授权", "name_en": "Single Use License",
         "description": "买方获得一次使用权利，不包含转售/再授权",
         "suggested_price_range": "35-350 CNY",
         "allowed_uses": ["personal"], "restrictions": ["no_resale", "no_modification"]},
        {"id": "multi_use", "name_zh": "多次使用授权", "name_en": "Multi-Use License",
         "description": "买方可在多个项目中使用，不包含转售",
         "suggested_price_range": "350-3500 CNY",
         "allowed_uses": ["personal", "commercial"], "restrictions": ["no_resale"]},
        {"id": "commercial_extended", "name_zh": "商业扩展授权", "name_en": "Commercial Extended License",
         "description": "可用于转售产品(如T恤上印图案)，可修改/衍生",
         "suggested_price_range": "700-7000 CNY",
         "allowed_uses": ["personal", "commercial", "resale", "modification"], "restrictions": []},
        {"id": "buyout", "name_zh": "买断授权", "name_en": "Buyout License",
         "description": "创作者转让全部权利，买方独家使用",
         "suggested_price_range": "7000+ CNY",
         "allowed_uses": ["all"], "restrictions": []},
    ]
    return ApiResponse(data=templates)


@router.post("/supply/licenses", response_model=ApiResponse)
def create_license(data: dict, db: Session = Depends(get_db)):
    """创建授权条款."""
    license_record = License(
        work_id=data.get("work_id"),
        license_type=data.get("license_type"),
        platform=data.get("platform"),
        allowed_uses=data.get("allowed_uses"),
        restrictions=data.get("restrictions"),
        price=data.get("price", 0),
        currency=data.get("currency", "CNY"),
        platform_listing_id=data.get("platform_listing_id"),
        platform_listing_url=data.get("platform_listing_url"),
        status=data.get("status", "active"),
    )
    db.add(license_record)
    db.commit()
    db.refresh(license_record)

    return ApiResponse(message="授权已创建", data={"id": license_record.id})


# ============================================================================
# 9.7 Partners (Enhanced — P1.5.9)
# ============================================================================

@router.get("/supply/partners", response_model=ApiResponse[list])
def list_partners(
    status: Optional[str] = "active",
    partner_type: Optional[str] = None,
    product_category: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """获取合作伙伴列表 — P1.5.9 增强 (支持 type/product_category/material 过滤)."""
    query = db.query(Partner)
    if status:
        query = query.filter(Partner.status == status)
    if partner_type:
        query = query.filter(Partner.type == partner_type)

    partners = query.order_by(Partner.created_at.desc()).all()

    # Post-filter for JSON fields (SQLite limitation)
    from sqlalchemy import cast, String

    def _filter_output(partners_list):
        results = []
        for p in partners_list:
            pdata = {
                "id": p.id, "name": p.name, "company_name": p.company_name,
                "type": p.type,
                "contact_person": p.contact_person, "phone": decrypt(p.phone) if p.phone else None,
                "email": p.email, "address": p.address, "website": p.website,
                "categories": p.categories,
                "product_categories": p.product_categories,
                "material_capabilities": p.material_capabilities,
                "moq_per_category": p.moq_per_category,
                "typical_lead_time_days": p.typical_lead_time_days,
                "price_range": p.price_range,
                "moq": p.moq, "rating": p.rating,
                "tags": p.tags, "status": p.status, "notes": p.notes,
                "created_at": p.created_at.isoformat() if p.created_at else None,
            }
            if product_category:
                pc = p.product_categories or []
                if product_category not in pc:
                    continue
            results.append(pdata)
        return results

    return ApiResponse(data=_filter_output(partners))


@router.post("/supply/partners", response_model=ApiResponse)
def create_partner(data: dict, db: Session = Depends(get_db)):
    """创建合作伙伴 — P1.5.9 增强 (含制造能力)."""
    partner = Partner(
        name=data.get("name"),
        company_name=data.get("company_name"),
        type=data.get("type", "manufacturer"),
        contact_person=data.get("contact_person"),
        phone=encrypt(data["phone"]) if data.get("phone") else None,
        email=data.get("email"),
        address=data.get("address"),
        website=data.get("website"),
        categories=data.get("categories", []),
        product_categories=data.get("product_categories"),
        material_capabilities=data.get("material_capabilities"),
        moq_per_category=data.get("moq_per_category"),
        typical_lead_time_days=data.get("typical_lead_time_days"),
        price_range=data.get("price_range"),
        moq=data.get("moq"),
        rating=data.get("rating", 0),
        tags=data.get("tags", []),
        notes=data.get("notes"),
    )
    db.add(partner)
    db.commit()
    db.refresh(partner)

    return ApiResponse(message="联系人已创建", data={"id": partner.id})


# ============================================================================
# 9.8 Orders (Enhanced — P1.5.10)
# ============================================================================

@router.get("/supply/orders", response_model=ApiResponse[list])
def list_orders(
    status: Optional[str] = None,
    partner_id: Optional[str] = None,
    order_type: Optional[str] = None,
    campaign_id: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """获取订单列表 — P1.5.10 增强."""
    query = db.query(Order)
    if status:
        query = query.filter(Order.status == status)
    if partner_id:
        query = query.filter(Order.partner_id == partner_id)
    if order_type:
        query = query.filter(Order.order_type == order_type)
    if campaign_id:
        query = query.filter(Order.campaign_id == campaign_id)

    orders = query.order_by(Order.created_at.desc()).all()

    return ApiResponse(data=[
        {
            "id": o.id, "order_number": o.order_number,
            "order_type": o.order_type,
            "partner_id": o.partner_id, "campaign_id": o.campaign_id,
            "product_id": o.product_id, "product_name": o.product_name,
            "product_category": o.product_category,
            "quantity": o.quantity,
            "specifications": o.specifications,
            "design_file_path": o.design_file_path,
            "unit_price": o.unit_price,
            "total_amount": o.total_amount,
            "deposit_percent": o.deposit_percent,
            "deposit_paid": o.deposit_paid,
            "balance_due": o.balance_due,
            "shipping_cost": o.shipping_cost,
            "status": o.status,
            "expected_date": o.expected_date.isoformat() if o.expected_date else None,
            "actual_date": o.actual_date.isoformat() if o.actual_date else None,
            "sample_requested": bool(o.sample_requested),
            "sample_received": bool(o.sample_received),
            "sample_approved": bool(o.sample_approved),
            "notes": o.notes,
            "created_at": o.created_at.isoformat() if o.created_at else None,
        }
        for o in orders
    ])


@router.post("/supply/orders", response_model=ApiResponse)
def create_order(data: dict, db: Session = Depends(get_db)):
    """创建订单 — P1.5.10 增强 (含 order_type + 样品管理)."""
    import uuid
    order_number = f"ORD-{uuid.uuid4().hex[:8].upper()}"

    total = data.get("total_amount", 0)
    deposit_percent = data.get("deposit_percent", 30)
    deposit_paid = data.get("deposit_paid", 0)
    shipping_cost = data.get("shipping_cost", 0)

    order = Order(
        order_number=order_number,
        order_type=data.get("order_type", "custom_mfg"),
        partner_id=data.get("partner_id"),
        campaign_id=data.get("campaign_id"),
        product_id=data.get("product_id"),
        product_name=data.get("product_name"),
        product_category=data.get("product_category"),
        quantity=data.get("quantity", 1),
        specifications=data.get("specifications"),
        design_file_path=data.get("design_file_path"),
        unit_price=data.get("unit_price", 0),
        total_amount=total,
        deposit_percent=deposit_percent,
        deposit_paid=deposit_paid,
        balance_due=total - deposit_paid,
        shipping_cost=shipping_cost,
        status=data.get("status", "draft"),
        expected_date=data.get("expected_date"),
        sample_requested=data.get("sample_requested", 0),
        notes=data.get("notes"),
    )
    db.add(order)
    db.commit()
    db.refresh(order)

    return ApiResponse(message="订单已创建", data={"id": order.id, "order_number": order_number})


@router.patch("/supply/orders/{order_id}/status", response_model=ApiResponse)
def update_order_status(order_id: str, data: dict, db: Session = Depends(get_db)):
    """更新订单状态 — P1.5.10."""
    o = db.query(Order).filter(Order.id == order_id).first()
    if not o:
        raise HTTPException(status_code=404, detail="订单不存在")

    if "status" in data:
        o.status = data["status"]
    if "tracking_number" in data:
        o.tracking_number = data["tracking_number"]
    if "actual_date" in data:
        o.actual_date = data["actual_date"]
    if "notes" in data:
        o.notes = data["notes"]

    db.commit()
    return ApiResponse(message="订单状态已更新")


@router.post("/supply/orders/{order_id}/sample", response_model=ApiResponse)
def manage_order_sample(order_id: str, data: dict, db: Session = Depends(get_db)):
    """样品管理 — P1.5.10.

    Body: { action: "request" / "receive" / "approve" / "reject" }
    """
    o = db.query(Order).filter(Order.id == order_id).first()
    if not o:
        raise HTTPException(status_code=404, detail="订单不存在")

    action = data.get("action", "request")
    if action == "request":
        o.sample_requested = 1
    elif action == "receive":
        o.sample_received = 1
    elif action == "approve":
        o.sample_approved = 1
        o.status = "confirmed"
    elif action == "reject":
        o.sample_approved = 0
        o.sample_received = 0

    db.commit()
    return ApiResponse(message=f"样品状态已更新 (action={action})")


# ============================================================================
# 9.9 变现仪表盘 (P1.5.11)
# ============================================================================

@router.get("/supply/revenue", response_model=ApiResponse[list])
def list_revenue(
    platform: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """收入列表."""
    query = db.query(RevenueRecord)
    if platform:
        query = query.filter(RevenueRecord.platform == platform)

    records = query.order_by(RevenueRecord.date.desc()).all()
    return ApiResponse(data=[
        {
            "id": r.id, "product_id": r.product_id, "platform": r.platform,
            "amount": r.amount, "currency": r.currency,
            "date": r.date.isoformat() if r.date else None,
            "order_count": r.order_count,
            "source": getattr(r, 'source', 'manual'),
            "refund_amount": getattr(r, 'refund_amount', 0),
            "platform_fee": getattr(r, 'platform_fee', 0),
            "net_revenue": getattr(r, 'net_revenue', 0),
            "notes": r.notes,
        }
        for r in records
    ])


@router.post("/supply/revenue", response_model=ApiResponse)
def create_revenue(data: dict, db: Session = Depends(get_db)):
    """手动录入收入 (P1.6.9: 支持 source/refund_amount/platform_fee/net_revenue)."""
    from datetime import date as date_type
    revenue = RevenueRecord(
        product_id=data.get("product_id"),
        platform=data.get("platform"),
        amount=data.get("amount", 0),
        currency=data.get("currency", "CNY"),
        date=data.get("date", date_type.today()),
        order_count=data.get("order_count", 1),
        source=data.get("source", "manual"),
        refund_amount=data.get("refund_amount", 0),
        platform_fee=data.get("platform_fee", 0),
        net_revenue=data.get("net_revenue", 0),
        notes=data.get("notes"),
    )
    db.add(revenue)
    db.commit()
    db.refresh(revenue)

    return ApiResponse(message="收入已记录", data={"id": revenue.id})


@router.get("/supply/revenue/summary", response_model=ApiResponse[dict])
def revenue_summary(db: Session = Depends(get_db)):
    """收入汇总 (总/按路径)."""
    from sqlalchemy import func

    # Total
    total_row = db.query(func.sum(RevenueRecord.amount), func.count(RevenueRecord.id)).first()
    total_amount = total_row[0] or 0
    total_orders = total_row[1] or 0

    # By platform
    by_platform_rows = db.query(
        RevenueRecord.platform, func.sum(RevenueRecord.amount), func.count(RevenueRecord.id)
    ).group_by(RevenueRecord.platform).all()

    by_platform = [
        {"platform": row[0], "amount": row[1] or 0, "order_count": row[2] or 0}
        for row in by_platform_rows
    ]

    # Products count
    product_count = db.query(func.count(Product.id)).scalar()

    # Channels count
    channel_count = db.query(func.count(MonetizationChannel.id)).filter(
        MonetizationChannel.status == "active"
    ).scalar()

    return ApiResponse(data={
        "total_revenue": round(total_amount, 2),
        "total_orders": total_orders,
        "active_products": product_count,
        "active_channels": channel_count,
        "by_platform": by_platform,
    })


@router.get("/supply/dashboard", response_model=ApiResponse[dict])
def supply_dashboard(db: Session = Depends(get_db)):
    """变现仪表盘 — P1.5.11.

    Returns aggregated data for the monetization dashboard:
    - Revenue by monetization path
    - Revenue by platform
    - Product counts by path
    - Channel breakdown
    """
    from sqlalchemy import func

    # Revenue summary
    total_rev = db.query(func.sum(RevenueRecord.amount)).scalar() or 0
    total_order_count = db.query(func.sum(RevenueRecord.order_count)).scalar() or 0

    # Product counts by monetization path
    path_counts = db.query(
        Product.monetization_path, func.count(Product.id)
    ).filter(Product.status == "active").group_by(Product.monetization_path).all()

    by_path = [
        {"path": row[0] or "unknown", "product_count": row[1]}
        for row in path_counts
    ]

    # Product counts by material
    mat_counts = db.query(
        Product.material_category, func.count(Product.id)
    ).filter(Product.status == "active").group_by(Product.material_category).all()

    by_material = [
        {"material": row[0] or "unknown", "product_count": row[1]}
        for row in mat_counts
    ]

    # Revenue by platform
    rev_by_platform = db.query(
        RevenueRecord.platform, func.sum(RevenueRecord.amount)
    ).group_by(RevenueRecord.platform).all()

    # Active channels
    channel_count = db.query(func.count(MonetizationChannel.id)).filter(
        MonetizationChannel.status == "active"
    ).scalar()

    # Partner count
    partner_count = db.query(func.count(Partner.id)).filter(
        Partner.status == "active"
    ).scalar()

    # Campaign stats
    campaign_count = db.query(func.count(Campaign.id)).scalar()
    active_campaigns = db.query(func.count(Campaign.id)).filter(
        Campaign.status.in_(["launching", "funded", "fulfilling"])
    ).scalar()

    # Total products
    total_products = db.query(func.count(Product.id)).scalar()

    return ApiResponse(data={
        "summary": {
            "total_revenue": round(total_rev, 2),
            "total_orders": total_order_count,
            "total_products": total_products,
            "active_channels": channel_count,
            "partners": partner_count,
            "campaigns": campaign_count,
            "active_campaigns": active_campaigns,
        },
        "revenue_by_platform": [
            {"platform": row[0], "amount": round(row[1] or 0, 2)}
            for row in rev_by_platform
        ],
        "products_by_path": by_path,
        "products_by_material": by_material,
        # Preset monetization paths for the dashboard chart (with 0-revenue for unused paths)
        "monetization_path_slots": [
            {"id": path["id"], "name_zh": path["name_zh"], "icon": path["icon"]}
            for path in MONETIZATION_PATHS
        ],
    })


# ============================================================================
# 9.10 提醒 (保留)
# ============================================================================

@router.get("/supply/reminders", response_model=ApiResponse[list])
def list_reminders(
    status: Optional[str] = "pending",
    db: Session = Depends(get_db),
):
    """获取提醒列表."""
    query = db.query(Reminder)
    if status:
        query = query.filter(Reminder.status == status)

    reminders = query.order_by(Reminder.remind_at.asc()).all()

    return ApiResponse(data=[
        {
            "id": r.id, "type": r.type, "related_id": r.related_id,
            "title": r.title, "remind_at": r.remind_at.isoformat() if r.remind_at else None,
            "status": r.status,
        }
        for r in reminders
    ])


@router.post("/supply/reminders", response_model=ApiResponse)
def create_reminder(data: dict, db: Session = Depends(get_db)):
    """创建提醒."""
    reminder = Reminder(
        type=data.get("type", "order"),
        related_id=data.get("related_id", ""),
        title=data.get("title"),
        remind_at=data.get("remind_at"),
    )
    db.add(reminder)
    db.commit()
    db.refresh(reminder)

    return ApiResponse(message="提醒已创建", data={"id": reminder.id})


# ============================================================================
# 9.11 POD 平台发布 — P2.5.1-P2.5.2
# ============================================================================

@router.post("/supply/publish-to-pod", response_model=ApiResponse)
async def publish_to_pod(data: dict, db: Session = Depends(get_db)):
    """发布设计到 POD 平台 — P2.5.1-P2.5.2.

    支持的平台: printful, redbubble, yingge, yunda

    Body:
        platform: str — 目标平台 ID
        product_data: {title, description, design_file_path, category, price}
        action: str — 'publish' / 'preview' / 'cost_estimate'
    """
    from app.gateway.printful import PrintfulGateway
    from app.gateway.redbubble import RedbubbleGateway

    platform = data.get("platform", "")
    product_data = data.get("product_data", {})
    action = data.get("action", "publish")

    if platform == "printful":
        gw = PrintfulGateway()
        if action == "publish":
            result = await gw.create_product(product_data)
        elif action == "cost_estimate":
            result = await gw.get_shipping_rates(
                product_data.get("platform_product_id", "mock"),
                product_data.get("country_code", "CN"),
            )
        else:
            result = await gw.get_product(product_data.get("platform_product_id", "mock"))
        return ApiResponse(data={"platform": platform, "platform_name": gw.get_platform_name(), "action": action, "result": result})

    elif platform == "redbubble":
        gw = RedbubbleGateway()
        if action == "publish":
            result = await gw.upload_design(
                design_file_path=product_data.get("design_file_path", ""),
                title=product_data.get("title", ""),
                description=product_data.get("description", ""),
                tags=product_data.get("tags", []),
            )
        elif action == "stats":
            result = await gw.get_sales_stats()
        elif action == "csv_template":
            csv_data = gw.generate_csv_template(product_data.get("designs", []))
            return ApiResponse(data={"platform": platform, "action": action, "csv_content": csv_data})
        else:
            result = await gw.upload_design(
                design_file_path=product_data.get("design_file_path", "mock.png"),
                title=product_data.get("title", "Mock Product"),
            )
        return ApiResponse(data={"platform": platform, "platform_name": gw.get_platform_name(), "action": action, "result": result})

    # Chinese POD platforms
    elif platform in ("yingge", "yunda", "dingzhilian", "shanyin"):
        from app.services.chinese_pod import (
            get_chinese_pod_platform,
            get_chinese_pod_categories,
            get_chinese_pod_specs,
        )
        plat_info = get_chinese_pod_platform(platform)
        cats = get_chinese_pod_categories(platform)
        specs = get_chinese_pod_specs(platform)
        return ApiResponse(data={
            "platform": platform,
            "platform_info": plat_info,
            "categories": cats,
            "design_specs": specs,
            "action": action,
            "note": "中国 POD 平台通过手动上传或 API 对接；当前为规格参考模式",
            "matched_product": {
                "category": product_data.get("category", ""),
                "found": product_data.get("category", "") in cats,
                "spec_check": specs,
            },
        })

    else:
        raise HTTPException(status_code=400, detail=f"不支持的 POD 平台: {platform}")


# ============================================================================
# 9.12 中国 POD 平台模板查询 — P2.5.13
# ============================================================================

@router.get("/supply/chinese-pod-platforms", response_model=ApiResponse[list])
def list_chinese_pod_platforms():
    """获取中国 POD 平台列表 — P2.5.13."""
    from app.services.chinese_pod import CHINESE_POD_PLATFORMS
    return ApiResponse(data=CHINESE_POD_PLATFORMS)


@router.get("/supply/chinese-pod-platforms/{platform_id}", response_model=ApiResponse)
def get_chinese_pod_platform_detail(platform_id: str):
    """获取中国 POD 平台详情（含品类、规格）— P2.5.13."""
    from app.services.chinese_pod import (
        get_chinese_pod_platform,
        get_chinese_pod_categories,
        get_chinese_pod_specs,
    )
    plat = get_chinese_pod_platform(platform_id)
    if not plat:
        raise HTTPException(status_code=404, detail=f"未知平台: {platform_id}")
    return ApiResponse(data={
        "platform": plat,
        "categories": get_chinese_pod_categories(platform_id),
        "specs": get_chinese_pod_specs(platform_id),
    })


# ============================================================================
# 9.13 众筹管理增强 — P2.5.3-P2.5.4
# ============================================================================

@router.get("/supply/campaigns/{campaign_id}/report", response_model=ApiResponse)
def export_campaign_report(campaign_id: str, db: Session = Depends(get_db)):
    """导出众筹项目报表 — P2.5.4.

    返回结构化报告数据，包含：
    - 项目基本信息
    - 进度与资金汇总
    - 奖励档位状态
    - 关联订单履约进度
    """
    c = db.query(Campaign).filter(Campaign.id == campaign_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="众筹项目不存在")

    # Reward tier analysis
    tiers = c.reward_tiers or []
    tier_stats = []
    for t in tiers:
        sold = t.get("sold", 0)
        limit_val = t.get("limit", 0)
        price = t.get("price", 0)
        tier_stats.append({
            "name": t.get("name", ""),
            "price": price,
            "sold": sold,
            "limit": limit_val,
            "available": limit_val - sold if limit_val > 0 else None,
            "revenue": sold * price,
            "sold_out": limit_val > 0 and sold >= limit_val,
        })

    # Total revenue from tiers
    tier_revenue = sum(ts["revenue"] for ts in tier_stats)

    # Related orders
    related_orders = db.query(Order).filter(
        Order.campaign_id == campaign_id
    ).all()

    order_stats = {
        "total": len(related_orders),
        "by_status": {},
    }
    for o in related_orders:
        order_stats["by_status"][o.status] = order_stats["by_status"].get(o.status, 0) + 1

    funding_pct = round(c.raised_amount / c.goal_amount * 100, 1) if c.goal_amount > 0 else 0

    return ApiResponse(data={
        "campaign": {
            "id": c.id,
            "title": c.title,
            "platform": c.platform,
            "status": c.status,
            "launch_date": c.launch_date.isoformat() if c.launch_date else None,
            "end_date": c.end_date.isoformat() if c.end_date else None,
            "estimated_delivery_date": c.estimated_delivery_date.isoformat() if c.estimated_delivery_date else None,
        },
        "funding": {
            "goal_amount": c.goal_amount,
            "raised_amount": c.raised_amount,
            "currency": c.currency,
            "backer_count": c.backer_count,
            "funding_pct": funding_pct,
            "tier_revenue": tier_revenue,
        },
        "reward_tiers": tier_stats,
        "orders": order_stats,
        "export_time": __import__("datetime").datetime.utcnow().isoformat(),
    })


@router.get("/supply/campaigns/reward-templates", response_model=ApiResponse[list])
def list_reward_tier_templates():
    """获取众筹奖励档位模板 — P2.5.3.

    提供常用奖励档位结构模板，帮助创作者快速搭建众筹项目。
    """
    templates = [
        {
            "id": "rt_basic_3",
            "name_zh": "基础三档",
            "description": "入门档 + 标准档 + 豪华档",
            "tiers": [
                {"name": "早鸟支持", "price_suggestions": {"min": 1, "max": 49}, "type": "support", "digital_only": True},
                {"name": "标准档", "price_suggestions": {"min": 49, "max": 199}, "type": "product", "includes_product": True},
                {"name": "豪华档", "price_suggestions": {"min": 199, "max": 599}, "type": "bundle", "includes_product": True, "extras": ["签名", "限量编号"]},
            ],
        },
        {
            "id": "rt_pod",
            "name_zh": "POD预定模式",
            "description": "适合按需打印产品，T恤/海报/周边",
            "tiers": [
                {"name": "单品档", "price_suggestions": {"min": 59, "max": 159}, "type": "single_product", "includes_product": True},
                {"name": "组合档", "price_suggestions": {"min": 159, "max": 359}, "type": "bundle", "includes_product": True, "item_count": 2},
                {"name": "全套档", "price_suggestions": {"min": 359, "max": 999}, "type": "full_set", "includes_product": True, "item_count": "all"},
            ],
        },
        {
            "id": "rt_digital",
            "name_zh": "数字产品模式",
            "description": "适合笔刷/素材/模板等数字产品众筹",
            "tiers": [
                {"name": "基础包", "price_suggestions": {"min": 9, "max": 49}, "type": "digital_basic", "file_count": "5-10"},
                {"name": "完整包", "price_suggestions": {"min": 49, "max": 149}, "type": "digital_full", "file_count": "20-50"},
                {"name": "终身会员", "price_suggestions": {"min": 149, "max": 499}, "type": "digital_lifetime", "includes_future_updates": True},
            ],
        },
        {
            "id": "rt_fan_builder",
            "name_zh": "粉丝建设模式",
            "description": "Patreon风格，按月支持+独家内容",
            "tiers": [
                {"name": "关注者", "price_suggestions": {"min": 5, "max": 15}, "type": "monthly", "recurring": True, "perks": ["幕后内容"]},
                {"name": "支持者", "price_suggestions": {"min": 15, "max": 49}, "type": "monthly", "recurring": True, "perks": ["投票权", "独家内容"]},
                {"name": "赞助者", "price_suggestions": {"min": 49, "max": 199}, "type": "monthly", "recurring": True, "perks": ["署名", "定制内容", "1v1沟通"]},
            ],
        },
        {
            "id": "rt_stretch_goals",
            "name_zh": "解锁目标模式",
            "description": "含解锁目标的众筹结构，适合创意玩具/桌游/艺术书",
            "tiers": [
                {"name": "标准支持", "price_suggestions": {"min": 39, "max": 149}, "type": "product", "includes_product": True},
                {"name": "收藏版", "price_suggestions": {"min": 149, "max": 449}, "type": "collectors", "includes_product": True, "extras": ["特殊包装", "编号证书"]},
                {"name": "终极版", "price_suggestions": {"min": 449, "max": 1499}, "type": "ultimate", "includes_product": True, "extras": ["创作者签名", "定制内容", "视频感谢"]},
            ],
            "stretch_goal_examples": [
                {"target": 150, "unlock": "新配色版本解锁"},
                {"target": 200, "unlock": "附赠贴纸套装"},
                {"target": 300, "unlock": "升级材质/工艺"},
                {"target": 500, "unlock": "创作者直播/线上见面会"},
            ],
        },
    ]
    return ApiResponse(data=templates)


@router.post("/supply/campaigns/calculate-goal", response_model=ApiResponse)
def calculate_funding_goal(data: dict, db: Session = Depends(get_db)):
    """计算建议众筹目标金额 — P2.5.3.

    Body:
        tiers: list[{name, price, estimated_backers}]
        manufacturing_cost: float
        shipping_cost: float
        platform_fee_pct: float (default 8.0)
        buffer_pct: float (default 15.0)
    """
    tiers = data.get("tiers", [])
    manufacturing_cost = data.get("manufacturing_cost", 0)
    shipping_cost = data.get("shipping_cost", 0)
    platform_fee_pct = data.get("platform_fee_pct", 8.0)
    buffer_pct = data.get("buffer_pct", 15.0)

    total_estimated_revenue = 0
    tier_projection = []
    for t in tiers:
        price = t.get("price", 0)
        backers = t.get("estimated_backers", 0)
        rev = price * backers
        total_estimated_revenue += rev
        tier_projection.append({
            "name": t.get("name", ""),
            "price": price,
            "estimated_backers": backers,
            "estimated_revenue": rev,
        })

    # Platform fee
    platform_fee = total_estimated_revenue * (platform_fee_pct / 100)

    # Net after fees
    net_revenue = total_estimated_revenue - platform_fee

    # Total costs
    total_costs = manufacturing_cost + shipping_cost

    # Break-even
    break_even = total_costs / (1 - platform_fee_pct / 100) if total_costs > 0 else 0

    # Suggested goal (with buffer)
    suggested_goal = break_even * (1 + buffer_pct / 100)

    return ApiResponse(data={
        "tier_projection": tier_projection,
        "total_estimated_revenue": round(total_estimated_revenue, 2),
        "platform_fee": round(platform_fee, 2),
        "net_revenue": round(net_revenue, 2),
        "total_costs": round(total_costs, 2),
        "break_even": round(break_even, 2),
        "suggested_goal": round(max(suggested_goal, break_even * 1.1), 2),
        "profit_at_suggested_goal": round(suggested_goal - total_costs - suggested_goal * (platform_fee_pct / 100), 2),
        "currency": data.get("currency", "CNY"),
        "parameters": {
            "platform_fee_pct": platform_fee_pct,
            "buffer_pct": buffer_pct,
        },
    })


# ============================================================================
# 9.14 IP 授权市场对接 — P2.5.5-P2.5.6
# ============================================================================

@router.get("/supply/licenses/{license_id}/export", response_model=ApiResponse)
def export_license(license_id: str, format: str = "creative_fabrica", db: Session = Depends(get_db)):
    """导出授权为第三方平台格式 — P2.5.5-P2.5.6.

    支持的导出格式:
    - creative_fabrica: Creative Fabrica 上传格式
    - creative_market: Creative Market 产品 CSV
    - gumroad: Gumroad 产品描述
    - envato: Envato Market 格式
    """
    lic = db.query(License).filter(License.id == license_id).first()
    if not lic:
        raise HTTPException(status_code=404, detail="授权记录不存在")

    # Get associated work/product
    product = None
    if lic.work_id:
        product = db.query(Product).filter(Product.work_id == lic.work_id).first()

    base_info = {
        "license_id": lic.id,
        "license_type": lic.license_type,
        "price": lic.price,
        "currency": lic.currency,
        "allowed_uses": lic.allowed_uses or [],
        "restrictions": lic.restrictions or [],
        "platform": lic.platform or "",
        "work_id": lic.work_id,
    }

    if format == "creative_fabrica":
        # Creative Fabrica: structured listing
        result = {
            "format": "creative_fabrica",
            "listing_data": {
                "title": product.title if product else f"License-{lic.id[:8]}",
                "description": product.description if product else "",
                "price": lic.price,
                "license_type": _map_license_to_cf(lic.license_type),
                "tags": ["design", "illustration"],
                "file_format": "PNG",
                "commercial_use": "commercial" in (lic.allowed_uses or []),
            },
            "exported_at": __import__("datetime").datetime.utcnow().isoformat(),
        }

    elif format == "creative_market":
        # Creative Market: CSV-like structured product
        result = {
            "format": "creative_market",
            "listing_data": {
                "product_name": product.title if product else f"License-{lic.id[:8]}",
                "product_description": product.description if product else "",
                "category": "Graphics / Illustrations",
                "price": f"${lic.price:.2f}" if lic.currency != "CNY" else f"¥{lic.price:.2f}",
                "license_type": _map_license_to_cm(lic.license_type),
                "tags": ["illustration", "design"],
            },
            "exported_at": __import__("datetime").datetime.utcnow().isoformat(),
        }

    elif format == "gumroad":
        # Gumroad: simple product description
        result = {
            "format": "gumroad",
            "listing_data": {
                "name": product.title if product else f"Design License - {lic.id[:8]}",
                "description": _generate_gumroad_description(lic, product),
                "price": int(lic.price * 100),  # Gumroad uses cents
                "currency": lic.currency.lower(),
                "discoverable": True,
            },
            "exported_at": __import__("datetime").datetime.utcnow().isoformat(),
        }

    elif format == "envato":
        result = {
            "format": "envato",
            "listing_data": {
                "title": product.title if product else f"License-{lic.id[:8]}",
                "description": product.description if product else "",
                "category": "graphics/illustrations",
                "regular_price": lic.price,
                "extended_price": lic.price * 5,
                "tags": ["design", "illustration", "art"],
            },
            "exported_at": __import__("datetime").datetime.utcnow().isoformat(),
        }

    else:
        raise HTTPException(status_code=400, detail=f"不支持的导出格式: {format}")

    result["base_license"] = base_info
    return ApiResponse(data=result)


def _map_license_to_cf(license_type: str) -> str:
    """Map internal license type to Creative Fabrica format."""
    mapping = {
        "single_use": "Standard",
        "multi_use": "Standard",
        "commercial_extended": "Commercial",
        "buyout": "Exclusive",
    }
    return mapping.get(license_type, "Standard")


def _map_license_to_cm(license_type: str) -> str:
    """Map internal license type to Creative Market format."""
    mapping = {
        "single_use": "Personal Use",
        "multi_use": "Commercial Use",
        "commercial_extended": "Extended Commercial",
        "buyout": "Full Buyout",
    }
    return mapping.get(license_type, "Personal Use")


def _generate_gumroad_description(lic, product) -> str:
    """Generate Gumroad-compatible product description."""
    uses = ", ".join(lic.allowed_uses or ["personal"])
    restrictions = ", ".join(lic.restrictions or ["none"])
    product_desc = product.description if product else ""
    return f"""{product_desc}

## License Type: {lic.license_type.upper()}

### What you CAN do:
- {uses}

### Restrictions:
- {restrictions}

### Included files:
- High-resolution source files
- Commercial usage rights (as specified above)

Price includes lifetime access to all files."""


# ============================================================================
# 9.15 工厂比价工具 — P2.5.7
# ============================================================================

@router.post("/supply/factory-price-compare", response_model=ApiResponse)
def factory_price_compare(data: dict, db: Session = Depends(get_db)):
    """工厂报价对比工具 — P2.5.7.

    Body:
        product_category: str — 产品品类 (t_shirt, pin, mug, etc.)
        quantity: int — 计划生产数量
        specifications: dict (optional) — 规格要求 (颜色数、尺寸等)
        partner_ids: list[str] (optional) — 指定对比的工厂 ID，默认全部匹配
    """
    from app.services.seed_data import get_category_by_id

    product_category = data.get("product_category", "")
    quantity = data.get("quantity", 1)
    specifications = data.get("specifications", {})
    partner_ids = data.get("partner_ids", [])

    # Find matching partners by category
    query = db.query(Partner).filter(
        Partner.status == "active",
        Partner.type.in_(["manufacturer", "supplier"]),
    )

    if partner_ids:
        query = query.filter(Partner.id.in_(partner_ids))

    partners = query.all()

    # For each partner, estimate pricing based on their capabilities
    comparisons = []
    for p in partners:
        # Check if partner can handle this category
        product_categories = p.product_categories or []
        if product_category and product_categories and product_category not in product_categories:
            continue

        # Estimate from price_range if available
        price_range = p.price_range or []
        estimated_unit_price = None
        for pr in price_range:
            if pr.get("category") == product_category:
                if isinstance(pr.get("unit_price_range"), list) and len(pr["unit_price_range"]) >= 2:
                    # Adjust for quantity (rough estimate: higher qty = lower price)
                    moq = pr.get("moq", 1)
                    min_price, max_price = pr["unit_price_range"]
                    if quantity >= moq:
                        # Scale: higher quantity gets closer to lower bound
                        factor = min(1.0, moq / max(quantity, 1))
                        estimated_unit_price = round(min_price + (max_price - min_price) * factor, 2)
                    else:
                        estimated_unit_price = max_price

        comparisons.append({
            "partner_id": p.id,
            "partner_name": p.name,
            "company_name": p.company_name or "",
            "product_categories": product_categories,
            "material_capabilities": p.material_capabilities or [],
            "rating": p.rating,
            "typical_lead_time_days": p.typical_lead_time_days,
            "moq": p.moq,
            "estimated_unit_price": estimated_unit_price,
            "estimated_total": round(estimated_unit_price * quantity, 2) if estimated_unit_price else None,
            "quantity_requested": quantity,
        })

    # Sort by estimated total if available
    comparisons.sort(key=lambda x: (x["estimated_total"] or float("inf"), -x["rating"]))

    # Also include category info
    category_info = get_category_by_id(product_category) if product_category else None

    # Find matching seed data category for reference pricing
    from app.services.seed_data import PRODUCT_CATEGORIES
    seed_ref = None
    for sc in PRODUCT_CATEGORIES:
        if sc.get("id") == product_category:
            seed_ref = {
                "category_id": sc["id"],
                "name_zh": sc["name_zh"],
                "suggested_price_cny": sc["suggested_price_cny"],
                "moq": sc.get("moq"),
                "margin_pct": sc.get("margin_pct"),
            }
            break

    return ApiResponse(data={
        "product_category": product_category,
        "category_reference": seed_ref,
        "quantity": quantity,
        "specifications": specifications,
        "comparisons": comparisons,
        "total_matching_partners": len(comparisons),
    })


@router.post("/supply/mockup/printful", response_model=ApiResponse)
async def generate_printful_mockup(data: dict):
    """Printful Mockup API 照片级效果图 — P1 增强.

    通过 Printful Mockup Generator API 生成照片级产品效果图。
    API 不可用时返回 503 + 降级提示。

    Body:
        product_id: str — 产品 ID
        design_file_id: str — 设计稿文件 ID
        colors: list[str] — 颜色列表 (e.g., ["white", "black"])
    """
    from app.gateway.printful import PrintfulGateway

    product_id = data.get("product_id")
    design_file_id = data.get("design_file_id")
    colors = data.get("colors", ["white"])

    if not product_id:
        raise HTTPException(status_code=400, detail="缺少 product_id")

    try:
        import os
        api_key = os.environ.get("PRINTFUL_API_KEY", "")
        if not api_key:
            return ApiResponse(
                code=503,
                data={
                    "fallback": "canvas",
                    "message": "Printful API Key 未配置，已降级到 Canvas 平面预览",
                    "provider": "canvas",
                },
                message="照片级预览暂不可用，已切换至平面预览"
            )

        gateway = PrintfulGateway()
        mockup_results = []
        for color in colors:
            result = gateway.generate_mockup(
                product_id=product_id,
                design_file=design_file_id,
                options={"color": color},
            )
            mockup_results.append(result)

        return ApiResponse(data={
            "provider": "printful",
            "mockups": mockup_results,
            "colors": colors,
        }, message="Printful 照片级效果图生成完成")
    except Exception as e:
        return ApiResponse(
            code=503,
            data={
                "fallback": "canvas",
                "message": f"Printful API 调用失败: {str(e)}，已降级到 Canvas 平面预览",
                "provider": "canvas",
            },
            message="照片级预览暂不可用，已切换至平面预览"
        )


# ============================================================================
# 9.16 AI 产品效果图生成 — P2.5.8
# ============================================================================

@router.post("/supply/generate-mockup", response_model=ApiResponse)
async def generate_product_mockup(data: dict):
    """AI 产品效果图生成 — P2.5.8.

    通过 Ollama + PIL 生成产品效果预览图。

    Body:
        work_id: str (optional) — 源作品 ID
        category_id: str — 产品品类 ID
        prompt: str (optional) — AI 生成提示词
        style: str (optional) — 'realistic' / 'cartoon' / 'minimal'
    """
    from app.gateway.ollama import OllamaGateway
    from app.services.seed_data import get_category_by_id

    category_id = data.get("category_id", "")
    prompt_override = data.get("prompt", "")
    style = data.get("style", "realistic")

    template = get_category_by_id(category_id)
    if not template:
        raise HTTPException(status_code=400, detail=f"未知品类: {category_id}")

    # Generate mockup description via Ollama
    category_name = template["name_zh"]

    if not prompt_override:
        prompt = f"""为一个 {category_name} 生成产品展示效果图的画面描述（仅文字，不要图片）。要求：
- 风格: {style}
- 展示角度: 45度俯角，白色背景
- 光线: 柔和自然光
- 描述要详细到可以用于 PIL/Pillow 生成参考"""
    else:
        prompt = prompt_override

    try:
        ollama = OllamaGateway()
        description = await ollama.generate_description(
            work_title=category_name,
            work_type="product_mockup",
            category=style,
        )
    except Exception:
        description = f"[Mockup] {category_name} - {style} style product visualization (Ollama not available)"

    # Generate a simple placeholder mockup description
    return ApiResponse(data={
        "category": {
            "id": template["id"],
            "name_zh": template["name_zh"],
            "name_en": template["name_en"],
        },
        "style": style,
        "prompt": prompt,
        "ai_description": description,
        "status": "generated",
        "note": "P2.5.8 — 通过 Ollama 生成产品描述 + PIL 效果图占位符。完整效果图需要 ComfyUI/StableDiffusion 集成。",
        "size_spec": template.get("size_spec", {}),
    })


# ============================================================================
# 9.17 数字产品格式化元数据 — P2.5.15
# ============================================================================

@router.get("/supply/digital-product-formats", response_model=ApiResponse[list])
def list_digital_product_formats():
    """获取数字产品格式元数据 — P2.5.15.

    为不同数字产品类型提供平台格式要求。
    """
    formats = [
        {
            "product_type": "brushes",
            "name_zh": "笔刷/素材包",
            "platforms": {
                "gumroad": {"required_formats": ["ZIP"], "max_file_size_mb": 250, "preview_required": True},
                "creative_market": {"required_formats": ["ZIP"], "max_file_size_mb": 500, "preview_required": True, "min_preview_count": 4},
                "envato": {"required_formats": ["ZIP"], "max_file_size_mb": 500, "preview_required": True, "help_file_required": True},
            },
            "metadata_schema": {
                "software_compatibility": ["Procreate", "Photoshop"],
                "brush_count": 0,
                "resolution": "300 DPI",
                "file_format_note": "ABR / BRUSHSET inside ZIP",
            },
        },
        {
            "product_type": "templates",
            "name_zh": "设计模板",
            "platforms": {
                "gumroad": {"required_formats": ["ZIP", "PDF"], "max_file_size_mb": 500, "preview_required": True},
                "creative_market": {"required_formats": ["ZIP"], "max_file_size_mb": 500, "min_preview_count": 6, "documentation_required": True},
                "etsy": {"required_formats": ["PDF", "ZIP"], "max_file_size_mb": 100, "preview_required": True},
            },
            "metadata_schema": {
                "software_compatibility": ["Canva", "Adobe Illustrator", "Figma"],
                "template_count": 0,
                "editable": True,
                "dimensions": "Customizable",
            },
        },
        {
            "product_type": "fonts",
            "name_zh": "字体",
            "platforms": {
                "creative_market": {"required_formats": ["OTF", "TTF", "ZIP"], "max_file_size_mb": 100, "min_preview_count": 8},
                "envato": {"required_formats": ["OTF", "TTF", "ZIP"], "max_file_size_mb": 100, "help_file_required": True},
                "gumroad": {"required_formats": ["OTF", "TTF", "ZIP"], "max_file_size_mb": 100, "preview_required": True},
            },
            "metadata_schema": {
                "font_type": "OTF/TTF",
                "characters": "Basic Latin + Extended",
                "styles": ["Regular"],
                "web_font": False,
            },
        },
        {
            "product_type": "textures",
            "name_zh": "纹理/图案",
            "platforms": {
                "gumroad": {"required_formats": ["ZIP", "PNG"], "max_file_size_mb": 500, "preview_required": True},
                "creative_market": {"required_formats": ["ZIP"], "max_file_size_mb": 500, "min_preview_count": 5},
            },
            "metadata_schema": {
                "resolution": "4096x4096 px",
                "seamless": True,
                "color_space": "sRGB",
                "file_count": 0,
            },
        },
        {
            "product_type": "stickers_digital",
            "name_zh": "数字贴纸/表情",
            "platforms": {
                "etsy": {"required_formats": ["PNG", "ZIP"], "max_file_size_mb": 50, "preview_required": True},
                "gumroad": {"required_formats": ["PNG", "ZIP"], "max_file_size_mb": 100, "preview_required": True},
            },
            "metadata_schema": {
                "resolution": "1024x1024 px per sticker",
                "transparent": True,
                "file_format": "PNG",
                "sticker_count": 0,
            },
        },
    ]
    return ApiResponse(data=formats)


@router.post("/supply/digital-product/validate", response_model=ApiResponse)
def validate_digital_product(data: dict):
    """校验数字产品是否符合目标平台要求 — P2.5.15.

    Body:
        product_type: str — brushes / templates / fonts / textures / stickers_digital
        target_platform: str — gumroad / creative_market / envato / etsy
        file_formats: list[str]
        file_count: int
        file_size_mb: float
        has_preview: bool
    """
    product_type = data.get("product_type", "")
    target_platform = data.get("target_platform", "")
    file_formats = data.get("file_formats", [])
    file_count = data.get("file_count", 0)
    file_size_mb = data.get("file_size_mb", 0)
    has_preview = data.get("has_preview", False)

    # Get format requirements
    formats = None
    try:
        result = list_digital_product_formats()
        for f_info in result.data:
            if f_info["product_type"] == product_type:
                if target_platform in f_info.get("platforms", {}):
                    formats = f_info["platforms"][target_platform]
                    break
    except Exception:
        pass

    if not formats:
        raise HTTPException(status_code=400, detail=f"未知产品类型或目标平台: {product_type}/{target_platform}")

    checks = []
    errors = 0
    warnings = 0

    # Format check
    required = formats.get("required_formats", [])
    format_match = any(rf in file_formats for rf in required)
    checks.append({
        "check": "file_format",
        "status": "pass" if format_match else "error",
        "message": f"文件格式: {file_formats}",
        "requirement": f"需要包含 {required} 之一",
    })
    if not format_match:
        errors += 1

    # Size check
    max_size = formats.get("max_file_size_mb", 100)
    if file_size_mb <= max_size:
        checks.append({"check": "file_size", "status": "pass", "message": f"{file_size_mb}MB <= {max_size}MB"})
    else:
        checks.append({"check": "file_size", "status": "error", "message": f"{file_size_mb}MB > {max_size}MB"})
        errors += 1

    # Preview check
    preview_required = formats.get("preview_required", False)
    if preview_required:
        if has_preview:
            checks.append({"check": "preview", "status": "pass", "message": "已提供预览"})
        else:
            checks.append({"check": "preview", "status": "error", "message": "缺少预览图"})
            errors += 1

    # Min preview count
    min_previews = formats.get("min_preview_count", 0)
    if min_previews > 0:
        if file_count >= min_previews:
            checks.append({"check": "preview_count", "status": "pass", "message": f"预览数量 {file_count} >= {min_previews}"})
        else:
            checks.append({"check": "preview_count", "status": "warning", "message": f"预览数量 {file_count} < {min_previews}"})
            warnings += 1

    # Help file check
    if formats.get("help_file_required"):
        checks.append({"check": "help_file", "status": "warning", "message": "建议包含说明文件"})
        warnings += 1

    return ApiResponse(data={
        "product_type": product_type,
        "target_platform": target_platform,
        "requirements": formats,
        "checks": checks,
        "passed": errors == 0,
        "error_count": errors,
        "warning_count": warnings,
    })


# ============================================================================
# 9.18 聚合收入 + AI 变现顾问 — P2.5.11-P2.5.12
# ============================================================================

@router.get("/supply/revenue/aggregated", response_model=ApiResponse[dict])
def aggregated_revenue(db: Session = Depends(get_db)):
    """聚合收入分析 — P2.5.11.

    跨平台、跨路径收入聚合，按月份/平台/路径切分。
    """
    from sqlalchemy import func
    from datetime import date as date_type, timedelta

    # Total
    total_rev = db.query(func.sum(RevenueRecord.amount)).scalar() or 0
    total_orders = db.query(func.sum(RevenueRecord.order_count)).scalar() or 0

    # By platform
    by_platform = db.query(
        RevenueRecord.platform, func.sum(RevenueRecord.amount), func.count(RevenueRecord.id)
    ).group_by(RevenueRecord.platform).all()

    # By monetization path (join products)
    by_path_rows = db.query(
        Product.monetization_path, func.sum(RevenueRecord.amount), func.count(RevenueRecord.id.distinct())
    ).join(RevenueRecord, RevenueRecord.product_id == Product.id, isouter=True
    ).filter(Product.monetization_path.isnot(None)
    ).group_by(Product.monetization_path).all()

    # This month
    today = date_type.today()
    start_of_month = today.replace(day=1)
    month_rev = db.query(func.sum(RevenueRecord.amount)).filter(
        RevenueRecord.date >= start_of_month
    ).scalar() or 0

    # Monthly trends (last 12 months)
    monthly_trends = []
    for i in range(12):
        m_start = (today.replace(day=1) - timedelta(days=i * 31)).replace(day=1)
        if i < 11:
            m_end = (m_start.replace(day=28) + timedelta(days=4)).replace(day=1)
        else:
            m_end = today
        m_rev = db.query(func.sum(RevenueRecord.amount)).filter(
            RevenueRecord.date >= m_start,
            RevenueRecord.date < m_end,
        ).scalar() or 0
        monthly_trends.append({
            "month": m_start.strftime("%Y-%m"),
            "revenue": round(m_rev, 2),
        })

    # Product performance
    top_products = db.query(
        Product.id, Product.title, func.sum(RevenueRecord.amount)
    ).join(RevenueRecord, RevenueRecord.product_id == Product.id
    ).group_by(Product.id
    ).order_by(func.sum(RevenueRecord.amount).desc()
    ).limit(10).all()

    return ApiResponse(data={
        "summary": {
            "total_revenue": round(total_rev, 2),
            "total_orders": total_orders,
            "this_month": round(month_rev, 2),
        },
        "by_platform": [{"platform": r[0], "amount": round(r[1] or 0, 2), "count": r[2]} for r in by_platform],
        "by_monetization_path": [{"path": r[0], "amount": round(r[1] or 0, 2), "product_count": r[2]} for r in by_path_rows],
        "monthly_trends": monthly_trends,
        "top_products": [{"id": r[0], "title": r[1], "revenue": round(r[2] or 0, 2)} for r in top_products],
    })


@router.post("/supply/monetization-advisor", response_model=ApiResponse)
async def monetization_advisor(data: dict):
    """AI 变现策略顾问 — P2.5.12.

    分析创作者作品并提供变现路径建议。

    Body:
        work_id: str (optional) — 作品 ID
        work_type: str — 作品类型
        creator_type: str — 创作者类型 (illustrator/photographer/video_creator/crafter/musician/writer)
        work_title: str — 作品标题
        current_paths: list[str] — 当前使用的变现路径
    """
    from app.gateway.ollama import OllamaGateway

    work_title = data.get("work_title", "")
    work_type = data.get("work_type", "")
    creator_type = data.get("creator_type", "")
    current_paths = data.get("current_paths", [])

    # 根据创作者类型调整默认推荐路径
    creator_path_weights: dict[str, list[str]] = {
        "illustrator": ["pod", "digital", "licensing"],
        "photographer": ["pod", "digital", "licensing"],
        "video_creator": ["pod", "crowdfunding", "digital"],
        "crafter": ["pod", "custom_mfg", "crowdfunding"],
        "musician": ["digital", "licensing", "crowdfunding"],
        "writer": ["digital", "licensing", "custom_mfg"],
    }
    preferred_paths = creator_path_weights.get(creator_type, [])

    prompt = f"""你是一位创意产业变现顾问。请为以下创作者分析最佳变现策略：

创作者类型: {creator_type or '未指定'}
作品: {work_title}
类型: {work_type}
当前变现路径: {', '.join(current_paths) if current_paths else '无'}

请分析并提供：
1. 推荐变现路径（POD/众筹/授权/定制制造/数字产品）及理由
2. 推荐的销售平台（至少3个，含国内+国际）
3. 定价建议（最低/建议/高端）
4. 潜在风险提示
5. 下一步行动计划"""
    try:
        ollama = OllamaGateway()
        advice = await ollama.generate_description(
            work_title=work_title,
            work_type=work_type,
            category="monetization_advisor",
        )
    except Exception:
        advice = "[AI 顾问暂不可用 - 请确保 Ollama 已启动]"

    # Default recommendations based on work type
    from app.services.seed_data import MONETIZATION_PATHS

    return ApiResponse(data={
        "work_info": {"title": work_title, "type": work_type, "creator_type": creator_type},
        "current_paths": current_paths,
        "preferred_paths": preferred_paths,
        "ai_advice": advice,
        "recommended_paths": [
            {
                "id": p["id"],
                "name_zh": p["name_zh"],
                "reason": f"适合{creator_type or work_type}作品变现" if preferred_paths and p["id"] in preferred_paths else ("已在使用" if current_paths and p["id"] in current_paths else "可考虑"),
                "priority": preferred_paths.index(p["id"]) + 1 if preferred_paths and p["id"] in preferred_paths else 99,
            }
            for p in MONETIZATION_PATHS
        ],
    })


# ============================================================================
# P2: Design Listing CRUD (replaces flat products)
# ============================================================================

from app.models.listings import DesignListing, DesignTemplateCompatibility
from app.services.spec_checker import get_compatible_templates, compute_remediation_suggestions


@router.get("/supply/listings", response_model=ApiResponse[list])
def list_listings(
    monetization_path: Optional[str] = None,
    platform: Optional[str] = None,
    material_category: Optional[str] = None,
    status: Optional[str] = None,
    work_id: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """商品列表 — P2: 取代旧的 /supply/products."""
    query = db.query(DesignListing)
    if monetization_path:
        query = query.filter(DesignListing.monetization_path == monetization_path)
    if material_category:
        query = query.filter(DesignListing.status == status if material_category is None else True)  # material stored in template relation
    if status:
        query = query.filter(DesignListing.status == status)
    if work_id:
        query = query.filter(DesignListing.work_id == work_id)

    listings = query.order_by(DesignListing.created_at.desc()).all()

    return ApiResponse(data=[
        {
            "id": l.id, "work_id": l.work_id, "product_template_id": l.product_template_id,
            "title": l.title, "description": l.description,
            "price": l.price, "cost": l.cost, "currency": l.currency,
            "monetization_path": l.monetization_path,
            "variant_sku": l.variant_sku, "variant_name": l.variant_name,
            "spec_validation": l.spec_validation,
            "mockup_image_path": l.mockup_image_path,
            "status": l.status,
            "created_at": l.created_at.isoformat() if l.created_at else None,
            "updated_at": l.updated_at.isoformat() if l.updated_at else None,
        }
        for l in listings
    ])


@router.post("/supply/listings", response_model=ApiResponse)
def create_listing(data: dict, db: Session = Depends(get_db)):
    """创建商品 — P2: 设计稿 × 产品模板 × 定价."""
    listing = DesignListing(
        work_id=data.get("work_id"),
        product_template_id=data.get("product_template_id"),
        title=data.get("title", "未命名商品"),
        description=data.get("description"),
        price=data.get("price", 0),
        cost=data.get("cost", 0),
        currency=data.get("currency", "CNY"),
        monetization_path=data.get("monetization_path"),
        variant_sku=data.get("variant_sku"),
        variant_name=data.get("variant_name"),
        spec_validation=data.get("spec_validation"),
        spec_validated_at=datetime.utcnow() if data.get("spec_validation") else None,
        mockup_image_path=data.get("mockup_image_path"),
        design_file_path=data.get("design_file_path"),
        status=data.get("status", "draft"),
    )
    db.add(listing)
    db.commit()
    db.refresh(listing)

    return ApiResponse(message="商品已创建", data={"id": listing.id})


@router.get("/supply/listings/{listing_id}", response_model=ApiResponse)
def get_listing_detail(listing_id: str, db: Session = Depends(get_db)):
    """商品详情 — 含关联的发布/众筹/授权/收入/订单."""
    listing = db.query(DesignListing).filter(DesignListing.id == listing_id).first()
    if not listing:
        raise HTTPException(status_code=404, detail="商品不存在")

    # Publications
    pubs = db.query(ProductPublishing).filter(
        ProductPublishing.listing_id == listing_id
    ).all()

    # Revenue
    revs = db.query(RevenueRecord).filter(
        RevenueRecord.listing_id == listing_id
    ).all()

    # Orders
    ords = db.query(Order).filter(Order.listing_id == listing_id).all()

    # Campaigns linked to this listing
    camps = db.query(Campaign).filter(Campaign.listing_id == listing_id).all()

    # Licenses linked to this listing
    lies = db.query(License).filter(License.listing_id == listing_id).all()

    return ApiResponse(data={
        "id": listing.id, "work_id": listing.work_id,
        "product_template_id": listing.product_template_id,
        "title": listing.title, "description": listing.description,
        "price": listing.price, "cost": listing.cost, "currency": listing.currency,
        "monetization_path": listing.monetization_path,
        "variant_sku": listing.variant_sku, "variant_name": listing.variant_name,
        "spec_validation": listing.spec_validation,
        "mockup_image_path": listing.mockup_image_path,
        "status": listing.status,
        "publications": [
            {"id": p.id, "platform": p.platform, "status": p.status,
             "listing_url": p.listing_url, "published_at": p.published_at.isoformat() if p.published_at else None}
            for p in pubs
        ],
        "campaigns": [
            {"id": c.id, "title": c.title, "platform": c.platform, "status": c.status,
             "goal_amount": c.goal_amount, "raised_amount": c.raised_amount,
             "reward_tiers": c.reward_tiers}
            for c in camps
        ],
        "licenses": [
            {"id": l.id, "license_type": l.license_type, "price": l.price,
             "status": l.status, "contract_signed": getattr(l, 'contract_signed', False)}
            for l in lies
        ],
        "revenues": [
            {"id": r.id, "amount": r.amount, "date": r.date.isoformat() if r.date else None,
             "platform": r.platform, "net_revenue": getattr(r, 'net_revenue', 0)}
            for r in revs
        ],
        "orders": [
            {"id": o.id, "order_number": o.order_number, "status": o.status,
             "total_amount": o.total_amount}
            for o in ords
        ],
        "total_revenue": sum(r.amount for r in revs),
        "created_at": listing.created_at.isoformat() if listing.created_at else None,
    })


@router.patch("/supply/listings/{listing_id}", response_model=ApiResponse)
def update_listing(listing_id: str, data: dict, db: Session = Depends(get_db)):
    """更新商品信息."""
    listing = db.query(DesignListing).filter(DesignListing.id == listing_id).first()
    if not listing:
        raise HTTPException(status_code=404, detail="商品不存在")

    updatable = ["title", "description", "price", "cost", "currency",
                 "monetization_path", "variant_sku", "variant_name",
                 "mockup_image_path", "status", "spec_validation"]
    for key in updatable:
        if key in data:
            setattr(listing, key, data[key])

    db.commit()
    return ApiResponse(message="商品已更新")


@router.delete("/supply/listings/{listing_id}", response_model=ApiResponse)
def delete_listing(listing_id: str, db: Session = Depends(get_db)):
    """软删除商品."""
    listing = db.query(DesignListing).filter(DesignListing.id == listing_id).first()
    if not listing:
        raise HTTPException(status_code=404, detail="商品不存在")
    listing.status = "discontinued"
    db.commit()
    return ApiResponse(message="商品已下架")


# ============================================================================
# P2: Spec Validation Compatibility & Remediation
# ============================================================================

@router.post("/supply/spec-validate-compat", response_model=ApiResponse)
def validate_design_compatibility(data: dict):
    """兼容产品推荐 — P2.

    Given a design spec, return ALL product templates ranked by compatibility.
    Used when spec check fails on one template: "which OTHER products would work?"

    Body:
        dpi, width_px, height_px, color_mode, file_format, has_transparency (optional)
        exclude_category_id: optional category to exclude from results
        limit: max results (default 20)
    """
    design_spec = {
        "dpi": data.get("dpi"),
        "width_px": data.get("width_px"),
        "height_px": data.get("height_px"),
        "color_mode": data.get("color_mode"),
        "file_format": data.get("file_format"),
        "has_transparency": data.get("has_transparency"),
    }
    clean_spec = {k: v for k, v in design_spec.items() if v is not None}

    exclude_id = data.get("exclude_category_id")
    limit = data.get("limit", 20)

    compatible = get_compatible_templates(
        clean_spec, PRODUCT_CATEGORIES,
        exclude_category_id=exclude_id,
        limit=limit,
    )

    # Build recommendation text
    pass_count = sum(1 for c in compatible if c.spec_result == "pass")
    warn_count = sum(1 for c in compatible if c.spec_result == "warning")
    error_count = sum(1 for c in compatible if c.spec_result == "error")

    if pass_count > 0:
        recommendation = f"您的设计稿可以通过 {pass_count} 个产品品类的规格校验，推荐优先选择这些品类。"
    elif warn_count > 0:
        recommendation = f"您的设计稿在 {warn_count} 个品类中仅有警告，可以尝试但建议优化。"
    else:
        recommendation = "您的设计稿目前无法满足任何品类的规格要求，建议优化设计稿尺寸或选择小尺寸产品。"

    return ApiResponse(data={
        "compatible_templates": [
            {
                "template_id": c.template_id,
                "name_zh": c.name_zh,
                "name_en": c.name_en,
                "material_category": c.material_category,
                "compatibility_score": c.compatibility_score,
                "spec_result": c.spec_result,
                "error_count": c.error_count,
                "warning_count": c.warning_count,
                "min_required_px": c.min_required_px,
                "current_meets": c.current_meets,
            }
            for c in compatible
        ],
        "summary": {
            "pass_count": pass_count,
            "warning_count": warn_count,
            "error_count": error_count,
            "total_checked": len(compatible),
        },
        "recommendation": recommendation,
    })


@router.post("/supply/spec-validate-remediation", response_model=ApiResponse)
def get_remediation_suggestions(data: dict):
    """修复建议 — P2.

    Given a design spec and a failed category, return actionable remediation steps.

    Body:
        dpi, width_px, height_px, color_mode, file_format, has_transparency
        category_id: the category that failed validation
    """
    category_id = data.get("category_id")
    if not category_id:
        raise HTTPException(status_code=400, detail="缺少 category_id")

    template = get_category_by_id(category_id)
    if not template:
        raise HTTPException(status_code=400, detail=f"未知品类: {category_id}")

    design_spec = {
        "dpi": data.get("dpi"),
        "width_px": data.get("width_px"),
        "height_px": data.get("height_px"),
        "color_mode": data.get("color_mode"),
        "file_format": data.get("file_format"),
        "has_transparency": data.get("has_transparency"),
    }
    clean_spec = {k: v for k, v in design_spec.items() if v is not None}

    suggestions = compute_remediation_suggestions(clean_spec, template)

    # Also find what size would pass
    size_spec = template.get("size_spec", {})
    dpi_req = template.get("dpi_requirement", 300)
    w_mm = size_spec.get("width_mm", 0)
    h_mm = size_spec.get("height_mm", 0)
    if w_mm > 0 and h_mm > 0:
        min_px = f"{int(w_mm / 25.4 * dpi_req)}x{int(h_mm / 25.4 * dpi_req)}px"
    else:
        min_px = "N/A"

    return ApiResponse(data={
        "suggestions": suggestions,
        "required_size": min_px,
        "required_dpi": dpi_req,
        "category_name": template["name_zh"],
    })
