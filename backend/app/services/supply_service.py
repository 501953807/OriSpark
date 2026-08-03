"""商业转化引擎服务层 — 对应: docs/modules-v5/04-monetization-engine.md

包含: 产品品类、变现路径、平台列表、设计规格校验、Products CRUD、
变现渠道、众筹项目、IP授权、合作伙伴、订单管理、收入统计、
POD发布、中国POD平台、奖励档位模板、定价计算、授权导出、
工厂比价、Mockup生成、数字产品格式化、聚合收入、变现顾问、
Design Listing CRUD、规格兼容性、修复建议。
"""
import logging
import uuid
from datetime import date, datetime, timedelta, timezone
from typing import Optional

from fastapi import HTTPException
from sqlalchemy import func, cast, String
from sqlalchemy.orm import Session

from app.models.supply import Partner, Order, OrderPayment, OrderCommunication, Reminder
from app.models.publish import Product, RevenueRecord, ProductPublishing
from app.models.monetization import ProductTemplate, MonetizationChannel, Campaign, License
from app.models.listings import DesignListing, DesignTemplateCompatibility
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
)

from app.utils.crypto import encrypt, decrypt
from app.services.seed_data import (
    PRODUCT_CATEGORIES, MATERIAL_CATEGORIES, MONETIZATION_PATHS, PLATFORMS,
    get_categories_by_material, get_category_by_id, get_monetization_path,
)
from app.services.spec_checker import (
    validate_design_spec, validate_for_multiple_categories,
    get_compatible_templates, compute_remediation_suggestions,
)


# ================================================================
# -- Helper functions --
# ================================================================

def _filter_partners(partners_list: list, product_category: Optional[str] = None) -> list:
    """Post-filter partners by product_category (SQLite JSON limitation)."""
    results = []
    for p in partners_list:
        pdata = {
            "id": p.id, "name": p.name, "company_name": p.company_name,
            "type": p.type,
            "contact_person": p.contact_person,
            "phone": decrypt(p.phone) if p.phone else None,
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
    return (
        f"{product_desc}\n\n"
        f"## License Type: {lic.license_type.upper()}\n\n"
        f"### What you CAN do:\n- {uses}\n\n"
        f"### Restrictions:\n- {restrictions}\n\n"
        f"### Included files:\n"
        f"- High-resolution source files\n"
        f"- Commercial usage rights (as specified above)\n\n"
        f"Price includes lifetime access to all files."
    )


# ================================================================
# -- Service class --
# ================================================================

class SupplyService:
    def __init__(self, db=None):
        self.db = db

    # ---- 产品品类与变现路径 ----

    def list_product_categories(self, material: Optional[str] = None) -> ApiResponse:
        """获取全品类列表 (按材质分类)."""
        categories = PRODUCT_CATEGORIES
        if material:
            categories = [c for c in categories if c["material_category"] == material]

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

    def list_monetization_paths(self) -> ApiResponse:
        """获取五条变现路径."""
        return ApiResponse(data=MONETIZATION_PATHS)

    def list_platforms(self) -> ApiResponse:
        """获取支持的变现平台列表."""
        return ApiResponse(data=PLATFORMS)

    # ---- 设计规格校验 ----

    def validate_design_spec(self, data: SpecValidateRequest) -> ApiResponse:
        """校验设计稿是否满足指定产品规格."""
        template = get_category_by_id(data.category_id)
        if not template:
            raise HTTPException(status_code=400, detail=f"未知品类: {data.category_id}")

        design_spec = {
            "dpi": data.dpi,
            "width_px": data.width_px,
            "height_px": data.height_px,
            "color_mode": data.color_mode,
            "file_format": data.file_format,
            "has_transparency": data.has_transparency,
        }
        report = validate_design_spec(template, **{k: v for k, v in design_spec.items() if v is not None})

        compatible = get_compatible_templates(
            design_spec, PRODUCT_CATEGORIES,
            exclude_category_id=data.category_id,
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
                {"check": c.check, "status": c.status, "message": c.message, "suggestion": c.suggestion}
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
                    "min_required_px": c.min_required_px,
                    "current_meets": c.current_meets,
                }
                for c in compatible
            ],
        })

    def validate_design_batch(self, data: SpecValidateBatchRequest) -> ApiResponse:
        """批量校验设计稿."""
        if not data.category_ids:
            raise HTTPException(status_code=400, detail="缺少 category_ids")

        templates = [get_category_by_id(cid) for cid in data.category_ids]
        templates = [t for t in templates if t is not None]
        if not templates:
            raise HTTPException(status_code=400, detail="找不到任何有效品类")

        design_spec = {
            "dpi": data.dpi,
            "width_px": data.width_px,
            "height_px": data.height_px,
            "color_mode": data.color_mode,
            "file_format": data.file_format,
            "has_transparency": data.has_transparency,
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
                    "checks": [
                        {"check": c.check, "status": c.status, "message": c.message, "suggestion": c.suggestion}
                        for c in r.checks
                    ],
                }
                for r in reports
            ],
            "overall_passed": all(r.passed for r in reports),
            "total_errors": sum(r.error_count for r in reports),
            "total_warnings": sum(r.warning_count for r in reports),
        })

    # ---- Products CRUD ----

    def list_products(self, monetization_path=None, platform=None, material_category=None,
                      status=None, work_id=None) -> ApiResponse:
        """产品列表."""
        query = self.db.query(Product)
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

    def create_product(self, data: ProductCreate) -> ApiResponse:
        """创建商品."""
        product = Product(
            work_id=data.work_id,
            title=data.title,
            description=data.description,
            price=data.price,
            cost=data.cost,
            currency=data.currency,
            category=data.category,
            monetization_path=data.monetization_path,
            material_category=data.material_category,
            platform=data.platform,
            specifications=data.specifications,
            design_variant_path=data.design_variant_path,
            mockup_image_path=data.mockup_image_path,
            images=data.images,
            platform_status=data.platform_status,
            status=data.status,
        )
        self.db.add(product)
        try:
            self.db.commit()
            self.db.refresh(product)
        except Exception:
            self.db.rollback()
            raise
        return ApiResponse(message="商品已创建", data={"id": product.id})

    def get_product(self, product_id: str) -> ApiResponse:
        """获取商品详情."""
        p = self.db.query(Product).filter(Product.id == product_id).first()
        if not p:
            raise HTTPException(status_code=404, detail="商品不存在")

        revenues = self.db.query(RevenueRecord).filter(RevenueRecord.product_id == product_id).all()

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
                {
                    "id": r.id, "amount": r.amount, "currency": r.currency,
                    "date": r.date.isoformat() if r.date else None,
                    "platform": r.platform, "order_count": r.order_count,
                    "source": getattr(r, 'source', 'manual'),
                    "refund_amount": getattr(r, 'refund_amount', 0),
                    "platform_fee": getattr(r, 'platform_fee', 0),
                    "net_revenue": getattr(r, 'net_revenue', 0),
                    "notes": r.notes,
                }
                for r in revenues
            ],
            "total_revenue": sum(r.amount for r in revenues),
            "created_at": p.created_at.isoformat() if p.created_at else None,
            "updated_at": p.updated_at.isoformat() if p.updated_at else None,
        })

    def update_product(self, product_id: str, data: ProductUpdate) -> ApiResponse:
        """更新商品."""
        p = self.db.query(Product).filter(Product.id == product_id).first()
        if not p:
            raise HTTPException(status_code=404, detail="商品不存在")

        for key, value in data.model_dump(exclude_none=True).items():
            setattr(p, key, value)

        try:
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise
        return ApiResponse(message="商品已更新")

    # ---- 变现渠道 ----

    def list_channels(self, channel_type=None, status="active") -> ApiResponse:
        """变现渠道列表."""
        query = self.db.query(MonetizationChannel)
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

    def create_channel(self, data: ChannelCreate) -> ApiResponse:
        """添加变现渠道."""
        channel = MonetizationChannel(
            name=data.name,
            channel_type=data.channel_type,
            platform=data.platform,
            platform_store_id=data.platform_store_id,
            platform_store_url=data.platform_store_url,
            credentials_encrypted=encrypt(data.credentials) if data.credentials else None,
            status=data.status,
        )
        self.db.add(channel)
        try:
            self.db.commit()
            self.db.refresh(channel)
        except Exception:
            self.db.rollback()
            raise
        return ApiResponse(message="渠道已添加", data={"id": channel.id})

    # ---- 众筹项目 ----

    def list_campaigns(self, platform=None, status=None) -> ApiResponse:
        """众筹项目列表."""
        query = self.db.query(Campaign)
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

    def create_campaign(self, data: CampaignCreate) -> ApiResponse:
        """创建众筹项目."""
        campaign = Campaign(
            title=data.title,
            description=data.description,
            platform=data.platform,
            platform_campaign_id=data.platform_campaign_id,
            platform_url=data.platform_url,
            goal_amount=data.goal_amount,
            currency=data.currency,
            raised_amount=data.raised_amount,
            backer_count=data.backer_count,
            reward_tiers=data.reward_tiers,
            launch_date=data.launch_date,
            end_date=data.end_date,
            estimated_delivery_date=data.estimated_delivery_date,
            related_product_ids=data.related_product_ids,
            related_work_ids=data.related_work_ids,
            status=data.status,
        )
        self.db.add(campaign)
        try:
            self.db.commit()
            self.db.refresh(campaign)
        except Exception:
            self.db.rollback()
            raise
        return ApiResponse(message="众筹项目已创建", data={"id": campaign.id})

    def update_campaign(self, campaign_id: str, data: CampaignUpdate) -> ApiResponse:
        """更新众筹项目."""
        c = self.db.query(Campaign).filter(Campaign.id == campaign_id).first()
        if not c:
            raise HTTPException(status_code=404, detail="众筹项目不存在")

        for key, value in data.model_dump(exclude_none=True).items():
            setattr(c, key, value)

        try:
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise
        return ApiResponse(message="众筹项目已更新")

    def export_campaign_report(self, campaign_id: str) -> ApiResponse:
        """导出众筹项目报表."""
        c = self.db.query(Campaign).filter(Campaign.id == campaign_id).first()
        if not c:
            raise HTTPException(status_code=404, detail="众筹项目不存在")

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

        tier_revenue = sum(ts["revenue"] for ts in tier_stats)

        related_orders = self.db.query(Order).filter(Order.campaign_id == campaign_id).all()
        order_stats = {"total": len(related_orders), "by_status": {}}
        for o in related_orders:
            order_stats["by_status"][o.status] = order_stats["by_status"].get(o.status, 0) + 1

        funding_pct = round(c.raised_amount / c.goal_amount * 100, 1) if c.goal_amount > 0 else 0

        return ApiResponse(data={
            "campaign": {
                "id": c.id, "title": c.title, "platform": c.platform, "status": c.status,
                "launch_date": c.launch_date.isoformat() if c.launch_date else None,
                "end_date": c.end_date.isoformat() if c.end_date else None,
                "estimated_delivery_date": c.estimated_delivery_date.isoformat() if c.estimated_delivery_date else None,
            },
            "funding": {
                "goal_amount": c.goal_amount, "raised_amount": c.raised_amount,
                "currency": c.currency, "backer_count": c.backer_count,
                "funding_pct": funding_pct, "tier_revenue": tier_revenue,
            },
            "reward_tiers": tier_stats,
            "orders": order_stats,
            "export_time": datetime.now(timezone.utc).isoformat(),
        })

    def list_reward_tier_templates(self) -> ApiResponse:
        """获取众筹奖励档位模板."""
        templates = [
            {"id": "rt_basic_3", "name_zh": "基础三档", "description": "入门档 + 标准档 + 豪华档",
             "tiers": [
                 {"name": "早鸟支持", "price_suggestions": {"min": 1, "max": 49}, "type": "support", "digital_only": True},
                 {"name": "标准档", "price_suggestions": {"min": 49, "max": 199}, "type": "product", "includes_product": True},
                 {"name": "豪华档", "price_suggestions": {"min": 199, "max": 599}, "type": "bundle", "includes_product": True, "extras": ["签名", "限量编号"]},
             ]},
            {"id": "rt_pod", "name_zh": "POD预定模式", "description": "适合按需打印产品，T恤/海报/周边",
             "tiers": [
                 {"name": "单品档", "price_suggestions": {"min": 59, "max": 159}, "type": "single_product", "includes_product": True},
                 {"name": "组合档", "price_suggestions": {"min": 159, "max": 359}, "type": "bundle", "includes_product": True, "item_count": 2},
                 {"name": "全套档", "price_suggestions": {"min": 359, "max": 999}, "type": "full_set", "includes_product": True, "item_count": "all"},
             ]},
            {"id": "rt_digital", "name_zh": "数字产品模式", "description": "适合笔刷/素材/模板等数字产品众筹",
             "tiers": [
                 {"name": "基础包", "price_suggestions": {"min": 9, "max": 49}, "type": "digital_basic", "file_count": "5-10"},
                 {"name": "完整包", "price_suggestions": {"min": 49, "max": 149}, "type": "digital_full", "file_count": "20-50"},
                 {"name": "终身会员", "price_suggestions": {"min": 149, "max": 499}, "type": "digital_lifetime", "includes_future_updates": True},
             ]},
            {"id": "rt_fan_builder", "name_zh": "粉丝建设模式", "description": "Patreon风格，按月支持+独家内容",
             "tiers": [
                 {"name": "关注者", "price_suggestions": {"min": 5, "max": 15}, "type": "monthly", "recurring": True, "perks": ["幕后内容"]},
                 {"name": "支持者", "price_suggestions": {"min": 15, "max": 49}, "type": "monthly", "recurring": True, "perks": ["投票权", "独家内容"]},
                 {"name": "赞助者", "price_suggestions": {"min": 49, "max": 199}, "type": "monthly", "recurring": True, "perks": ["署名", "定制内容", "1v1沟通"]},
             ]},
            {"id": "rt_stretch_goals", "name_zh": "解锁目标模式", "description": "含解锁目标的众筹结构，适合创意玩具/桌游/艺术书",
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

    def calculate_funding_goal(self, data: FundingGoalRequest) -> ApiResponse:
        """计算建议众筹目标金额."""
        tiers = data.tiers
        manufacturing_cost = data.manufacturing_cost
        shipping_cost = data.shipping_cost
        platform_fee_pct = data.platform_fee_pct
        buffer_pct = data.buffer_pct
        currency = data.currency

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

        platform_fee = total_estimated_revenue * (platform_fee_pct / 100)
        net_revenue = total_estimated_revenue - platform_fee
        total_costs = manufacturing_cost + shipping_cost
        break_even = total_costs / (1 - platform_fee_pct / 100) if total_costs > 0 else 0
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
            "currency": currency,
            "parameters": {"platform_fee_pct": platform_fee_pct, "buffer_pct": buffer_pct},
        })

    # ---- IP 授权 ----

    def list_licenses(self, license_type=None, status="active") -> ApiResponse:
        """授权记录列表."""
        query = self.db.query(License)
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

    def list_license_templates(self) -> ApiResponse:
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

    def create_license(self, data: LicenseCreate) -> ApiResponse:
        """创建授权条款."""
        license_record = License(
            work_id=data.work_id,
            license_type=data.license_type,
            platform=data.platform,
            allowed_uses=data.allowed_uses,
            restrictions=data.restrictions,
            price=data.price,
            currency=data.currency,
            platform_listing_id=data.platform_listing_id,
            platform_listing_url=data.platform_listing_url,
            status=data.status,
        )
        self.db.add(license_record)
        try:
            self.db.commit()
            self.db.refresh(license_record)
        except Exception:
            self.db.rollback()
            raise
        return ApiResponse(message="授权已创建", data={"id": license_record.id})

    def export_license(self, license_id: str, format: str) -> ApiResponse:
        """导出授权为第三方平台格式."""
        lic = self.db.query(License).filter(License.id == license_id).first()
        if not lic:
            raise HTTPException(status_code=404, detail="授权记录不存在")

        product = None
        if lic.work_id:
            product = self.db.query(Product).filter(Product.work_id == lic.work_id).first()

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
                "exported_at": datetime.now(timezone.utc).isoformat(),
            }
        elif format == "creative_market":
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
                "exported_at": datetime.now(timezone.utc).isoformat(),
            }
        elif format == "gumroad":
            result = {
                "format": "gumroad",
                "listing_data": {
                    "name": product.title if product else f"Design License - {lic.id[:8]}",
                    "description": _generate_gumroad_description(lic, product),
                    "price": int(lic.price * 100),
                    "currency": lic.currency.lower(),
                    "discoverable": True,
                },
                "exported_at": datetime.now(timezone.utc).isoformat(),
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
                "exported_at": datetime.now(timezone.utc).isoformat(),
            }
        else:
            raise HTTPException(status_code=400, detail=f"不支持的导出格式: {format}")

        result["base_license"] = base_info
        return ApiResponse(data=result)

    # ---- Partners ----

    def list_partners(self, status="active", partner_type=None, product_category=None) -> ApiResponse:
        """获取合作伙伴列表."""
        query = self.db.query(Partner)
        if status:
            query = query.filter(Partner.status == status)
        if partner_type:
            query = query.filter(Partner.type == partner_type)

        partners = query.order_by(Partner.created_at.desc()).all()
        return ApiResponse(data=_filter_partners(partners, product_category))

    def create_partner(self, data: SupplyPartnerCreate) -> ApiResponse:
        """创建合作伙伴."""
        partner = Partner(
            name=data.name,
            company_name=data.company_name,
            type=data.type,
            contact_person=data.contact_person,
            phone=encrypt(data.phone) if data.phone else None,
            email=data.email,
            address=data.address,
            website=data.website,
            categories=data.categories or [],
            product_categories=data.product_categories,
            material_capabilities=data.material_capabilities,
            moq_per_category=data.moq_per_category,
            typical_lead_time_days=data.typical_lead_time_days,
            price_range=data.price_range,
            moq=data.moq,
            rating=data.rating,
            tags=data.tags or [],
            notes=data.notes,
        )
        self.db.add(partner)
        try:
            self.db.commit()
            self.db.refresh(partner)
        except Exception:
            self.db.rollback()
            raise
        return ApiResponse(message="联系人已创建", data={"id": partner.id})

    # ---- Orders ----

    def list_orders(self, status=None, partner_id=None, order_type=None, campaign_id=None) -> ApiResponse:
        """获取订单列表."""
        query = self.db.query(Order)
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

    def create_order(self, data: SupplyOrderCreate) -> ApiResponse:
        """创建订单."""
        order_number = f"ORD-{uuid.uuid4().hex[:8].upper()}"
        total = data.total_amount
        deposit_paid = data.deposit_paid

        order = Order(
            order_number=order_number,
            order_type=data.order_type,
            partner_id=data.partner_id,
            campaign_id=data.campaign_id,
            product_id=data.product_id,
            product_name=data.product_name,
            product_category=data.product_category,
            quantity=data.quantity,
            specifications=data.specifications,
            design_file_path=data.design_file_path,
            unit_price=data.unit_price,
            total_amount=total,
            deposit_percent=data.deposit_percent,
            deposit_paid=deposit_paid,
            balance_due=total - deposit_paid,
            shipping_cost=data.shipping_cost,
            status=data.status,
            expected_date=data.expected_date,
            sample_requested=data.sample_requested,
            notes=data.notes,
        )
        self.db.add(order)
        try:
            self.db.commit()
            self.db.refresh(order)
        except Exception:
            self.db.rollback()
            raise
        return ApiResponse(message="订单已创建", data={"id": order.id, "order_number": order_number})

    def update_order_status(self, order_id: str, data: OrderStatusUpdate) -> ApiResponse:
        """更新订单状态."""
        o = self.db.query(Order).filter(Order.id == order_id).first()
        if not o:
            raise HTTPException(status_code=404, detail="订单不存在")

        for key, value in data.model_dump(exclude_none=True).items():
            setattr(o, key, value)

        try:
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise
        return ApiResponse(message="订单状态已更新")

    def manage_order_sample(self, order_id: str, data: OrderSampleAction) -> ApiResponse:
        """样品管理."""
        o = self.db.query(Order).filter(Order.id == order_id).first()
        if not o:
            raise HTTPException(status_code=404, detail="订单不存在")

        action = data.action
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

        try:
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise
        return ApiResponse(message=f"样品状态已更新 (action={action})")

    # ---- Revenue ----

    def list_revenue(self, platform=None) -> ApiResponse:
        """收入列表."""
        query = self.db.query(RevenueRecord)
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

    def create_revenue(self, data: RevenueCreate) -> ApiResponse:
        """手动录入收入."""
        revenue = RevenueRecord(
            product_id=data.product_id,
            platform=data.platform,
            amount=data.amount,
            currency=data.currency,
            date=data.resolved_date,
            order_count=data.order_count,
            source=data.source,
            refund_amount=data.refund_amount,
            platform_fee=data.platform_fee,
            net_revenue=data.net_revenue,
            notes=data.notes,
        )
        self.db.add(revenue)
        try:
            self.db.commit()
            self.db.refresh(revenue)
        except Exception:
            self.db.rollback()
            raise
        return ApiResponse(message="收入已记录", data={"id": revenue.id})

    def revenue_summary(self) -> ApiResponse:
        """收入汇总."""
        total_row = self.db.query(func.sum(RevenueRecord.amount), func.count(RevenueRecord.id)).first()
        total_amount = total_row[0] or 0
        total_orders = total_row[1] or 0

        by_platform_rows = self.db.query(
            RevenueRecord.platform, func.sum(RevenueRecord.amount), func.count(RevenueRecord.id)
        ).group_by(RevenueRecord.platform).all()

        by_platform = [
            {"platform": row[0], "amount": row[1] or 0, "order_count": row[2] or 0}
            for row in by_platform_rows
        ]

        product_count = self.db.query(func.count(Product.id)).scalar()
        channel_count = self.db.query(func.count(MonetizationChannel.id)).filter(
            MonetizationChannel.status == "active"
        ).scalar()

        return ApiResponse(data={
            "total_revenue": round(total_amount, 2),
            "total_orders": total_orders,
            "active_products": product_count,
            "active_channels": channel_count,
            "by_platform": by_platform,
        })

    def supply_dashboard(self) -> ApiResponse:
        """变现仪表盘."""
        total_rev = self.db.query(func.sum(RevenueRecord.amount)).scalar() or 0
        total_order_count = self.db.query(func.sum(RevenueRecord.order_count)).scalar() or 0

        path_counts = self.db.query(
            Product.monetization_path, func.count(Product.id)
        ).filter(Product.status == "active").group_by(Product.monetization_path).all()

        by_path = [{"path": row[0] or "unknown", "product_count": row[1]} for row in path_counts]

        mat_counts = self.db.query(
            Product.material_category, func.count(Product.id)
        ).filter(Product.status == "active").group_by(Product.material_category).all()

        by_material = [{"material": row[0] or "unknown", "product_count": row[1]} for row in mat_counts]

        rev_by_platform = self.db.query(
            RevenueRecord.platform, func.sum(RevenueRecord.amount)
        ).group_by(RevenueRecord.platform).all()

        channel_count = self.db.query(func.count(MonetizationChannel.id)).filter(
            MonetizationChannel.status == "active"
        ).scalar()

        partner_count = self.db.query(func.count(Partner.id)).filter(
            Partner.status == "active"
        ).scalar()

        campaign_count = self.db.query(func.count(Campaign.id)).scalar()
        active_campaigns = self.db.query(func.count(Campaign.id)).filter(
            Campaign.status.in_(["launching", "funded", "fulfilling"])
        ).scalar()

        total_products = self.db.query(func.count(Product.id)).scalar()

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
            "monetization_path_slots": [
                {"id": path["id"], "name_zh": path["name_zh"], "icon": path["icon"]}
                for path in MONETIZATION_PATHS
            ],
        })

    def aggregated_revenue(self) -> ApiResponse:
        """聚合收入分析."""
        total_rev = self.db.query(func.sum(RevenueRecord.amount)).scalar() or 0
        total_orders = self.db.query(func.sum(RevenueRecord.order_count)).scalar() or 0

        by_platform = self.db.query(
            RevenueRecord.platform, func.sum(RevenueRecord.amount), func.count(RevenueRecord.id)
        ).group_by(RevenueRecord.platform).all()

        by_path_rows = self.db.query(
            Product.monetization_path, func.sum(RevenueRecord.amount), func.count(RevenueRecord.id.distinct())
        ).join(RevenueRecord, RevenueRecord.product_id == Product.id, isouter=True
        ).filter(Product.monetization_path.isnot(None)
        ).group_by(Product.monetization_path).all()

        today = date.today()
        start_of_month = today.replace(day=1)
        month_rev = self.db.query(func.sum(RevenueRecord.amount)).filter(
            RevenueRecord.date >= start_of_month
        ).scalar() or 0

        monthly_trends = []
        for i in range(12):
            m_start = (today.replace(day=1) - timedelta(days=i * 31)).replace(day=1)
            if i < 11:
                m_end = (m_start.replace(day=28) + timedelta(days=4)).replace(day=1)
            else:
                m_end = today
            m_rev = self.db.query(func.sum(RevenueRecord.amount)).filter(
                RevenueRecord.date >= m_start,
                RevenueRecord.date < m_end,
            ).scalar() or 0
            monthly_trends.append({"month": m_start.strftime("%Y-%m"), "revenue": round(m_rev, 2)})

        top_products = self.db.query(
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

    # ---- Reminders ----

    def list_reminders(self, status="pending") -> ApiResponse:
        """获取提醒列表."""
        query = self.db.query(Reminder)
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

    def create_reminder(self, data: ReminderCreate) -> ApiResponse:
        """创建提醒."""
        reminder = Reminder(
            type=data.type,
            related_id=data.related_id,
            title=data.title,
            remind_at=data.remind_at,
        )
        self.db.add(reminder)
        try:
            self.db.commit()
            self.db.refresh(reminder)
        except Exception:
            self.db.rollback()
            raise
        return ApiResponse(message="提醒已创建", data={"id": reminder.id})

    # ---- POD 发布 ----

    async def publish_to_pod(self, data: PublishToPodRequest) -> ApiResponse:
        """发布设计到 POD 平台."""
        from app.gateway.printful import PrintfulGateway
        from app.gateway.redbubble import RedbubbleGateway

        platform = data.platform
        product_data = data.product_data
        action = data.action

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
            return ApiResponse(data={
                "platform": platform, "platform_name": gw.get_platform_name(),
                "action": action, "result": result
            })

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
            return ApiResponse(data={
                "platform": platform, "platform_name": gw.get_platform_name(),
                "action": action, "result": result
            })

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

        raise HTTPException(status_code=400, detail=f"不支持的 POD 平台: {platform}")

    # ---- 中国 POD 平台 ----

    def list_chinese_pod_platforms(self) -> ApiResponse:
        """获取中国 POD 平台列表."""
        from app.services.chinese_pod import CHINESE_POD_PLATFORMS
        return ApiResponse(data=CHINESE_POD_PLATFORMS)

    def get_chinese_pod_platform_detail(self, platform_id: str) -> ApiResponse:
        """获取中国 POD 平台详情."""
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

    # ---- 工厂比价 ----

    def factory_price_compare(self, data: FactoryPriceCompareRequest) -> ApiResponse:
        """工厂报价对比工具."""
        product_category = data.product_category
        quantity = data.quantity
        specifications = data.specifications
        partner_ids = data.partner_ids

        query = self.db.query(Partner).filter(
            Partner.status == "active",
            Partner.type.in_(["manufacturer", "supplier"]),
        )
        if partner_ids:
            query = query.filter(Partner.id.in_(partner_ids))

        partners = query.all()

        comparisons = []
        for p in partners:
            product_categories = p.product_categories or []
            if product_category and product_categories and product_category not in product_categories:
                continue

            price_range = p.price_range or []
            estimated_unit_price = None
            for pr in price_range:
                if pr.get("category") == product_category:
                    if isinstance(pr.get("unit_price_range"), list) and len(pr["unit_price_range"]) >= 2:
                        moq = pr.get("moq", 1)
                        min_price, max_price = pr["unit_price_range"]
                        if quantity >= moq:
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

        comparisons.sort(key=lambda x: (x["estimated_total"] or float("inf"), -x["rating"]))

        category_info = get_category_by_id(product_category) if product_category else None

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

    # ---- Mockup 生成 ----

    async def generate_printful_mockup(self, product_id: str, design_file_id: str, colors: list) -> ApiResponse:
        """Printful Mockup API 照片级效果图."""
        from app.gateway.printful import PrintfulGateway
        import os

        if not product_id:
            raise HTTPException(status_code=400, detail="缺少 product_id")

        try:
            api_key = os.environ.get("PRINTFUL_API_KEY", "")
            if not api_key:
                return ApiResponse(
                    code=503,
                    data={"fallback": "canvas", "message": "Printful API Key 未配置，已降级到 Canvas 平面预览", "provider": "canvas"},
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
                "provider": "printful", "mockups": mockup_results, "colors": colors,
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

    async def generate_product_mockup(self, category_id: str, prompt_override: str = "", style: str = "") -> ApiResponse:
        """AI 产品效果图生成."""
        from app.gateway.ollama import OllamaGateway

        template = get_category_by_id(category_id)
        if not template:
            raise HTTPException(status_code=400, detail=f"未知品类: {category_id}")

        category_name = template["name_zh"]

        if not prompt_override:
            prompt = (
                f"为一个 {category_name} 生成产品展示效果图的画面描述（仅文字，不要图片）。"
                f"要求：风格: {style}，展示角度: 45度俯角，白色背景，光线: 柔和自然光，"
                f"描述要详细到可以用于 PIL/Pillow 生成参考"
            )
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

        return ApiResponse(data={
            "category": {"id": template["id"], "name_zh": template["name_zh"], "name_en": template["name_en"]},
            "style": style, "prompt": prompt, "ai_description": description,
            "status": "generated",
            "note": "P2.5.8 — 通过 Ollama 生成产品描述 + PIL 效果图占位符。完整效果图需要 ComfyUI/StableDiffusion 集成。",
            "size_spec": template.get("size_spec", {}),
        })

    # ---- 数字产品格式化 ----

    def list_digital_product_formats(self) -> ApiResponse:
        """获取数字产品格式元数据."""
        formats = [
            {"product_type": "brushes", "name_zh": "笔刷/素材包",
             "platforms": {
                 "gumroad": {"required_formats": ["ZIP"], "max_file_size_mb": 250, "preview_required": True},
                 "creative_market": {"required_formats": ["ZIP"], "max_file_size_mb": 500, "preview_required": True, "min_preview_count": 4},
                 "envato": {"required_formats": ["ZIP"], "max_file_size_mb": 500, "preview_required": True, "help_file_required": True},
             },
             "metadata_schema": {"software_compatibility": ["Procreate", "Photoshop"], "brush_count": 0, "resolution": "300 DPI", "file_format_note": "ABR / BRUSHSET inside ZIP"}},
            {"product_type": "templates", "name_zh": "设计模板",
             "platforms": {
                 "gumroad": {"required_formats": ["ZIP", "PDF"], "max_file_size_mb": 500, "preview_required": True},
                 "creative_market": {"required_formats": ["ZIP"], "max_file_size_mb": 500, "min_preview_count": 6, "documentation_required": True},
                 "etsy": {"required_formats": ["PDF", "ZIP"], "max_file_size_mb": 100, "preview_required": True},
             },
             "metadata_schema": {"software_compatibility": ["Canva", "Adobe Illustrator", "Figma"], "template_count": 0, "editable": True, "dimensions": "Customizable"}},
            {"product_type": "fonts", "name_zh": "字体",
             "platforms": {
                 "creative_market": {"required_formats": ["OTF", "TTF", "ZIP"], "max_file_size_mb": 100, "min_preview_count": 8},
                 "envato": {"required_formats": ["OTF", "TTF", "ZIP"], "max_file_size_mb": 100, "help_file_required": True},
                 "gumroad": {"required_formats": ["OTF", "TTF", "ZIP"], "max_file_size_mb": 100, "preview_required": True},
             },
             "metadata_schema": {"font_type": "OTF/TTF", "characters": "Basic Latin + Extended", "styles": ["Regular"], "web_font": False}},
            {"product_type": "textures", "name_zh": "纹理/图案",
             "platforms": {
                 "gumroad": {"required_formats": ["ZIP", "PNG"], "max_file_size_mb": 500, "preview_required": True},
                 "creative_market": {"required_formats": ["ZIP"], "max_file_size_mb": 500, "min_preview_count": 5},
             },
             "metadata_schema": {"resolution": "4096x4096 px", "seamless": True, "color_space": "sRGB", "file_count": 0}},
            {"product_type": "stickers_digital", "name_zh": "数字贴纸/表情",
             "platforms": {
                 "etsy": {"required_formats": ["PNG", "ZIP"], "max_file_size_mb": 50, "preview_required": True},
                 "gumroad": {"required_formats": ["PNG", "ZIP"], "max_file_size_mb": 100, "preview_required": True},
             },
             "metadata_schema": {"resolution": "1024x1024 px per sticker", "transparent": True, "file_format": "PNG", "sticker_count": 0}},
        ]
        return ApiResponse(data=formats)

    # ---- Monetization Advisor ----

    async def monetization_advisor(self, work_title: str, work_type: str, creator_type: str, current_paths: list) -> ApiResponse:
        """AI 变现策略顾问."""
        from app.gateway.ollama import OllamaGateway

        creator_path_weights = {
            "illustrator": ["pod", "digital", "licensing"],
            "photographer": ["pod", "digital", "licensing"],
            "video_creator": ["pod", "crowdfunding", "digital"],
            "crafter": ["pod", "custom_mfg", "crowdfunding"],
            "musician": ["digital", "licensing", "crowdfunding"],
            "writer": ["digital", "licensing", "custom_mfg"],
        }
        preferred_paths = creator_path_weights.get(creator_type, [])

        try:
            ollama = OllamaGateway()
            advice = await ollama.generate_description(
                work_title=work_title,
                work_type=work_type,
                category="monetization_advisor",
            )
        except Exception:
            advice = "[AI 顾问暂不可用 - 请确保 Ollama 已启动]"

        return ApiResponse(data={
            "work_info": {"title": work_title, "type": work_type, "creator_type": creator_type},
            "current_paths": current_paths,
            "preferred_paths": preferred_paths,
            "ai_advice": advice,
            "recommended_paths": [
                {
                    "id": p["id"],
                    "name_zh": p["name_zh"],
                    "reason": (f"适合{creator_type or work_type}作品变现"
                               if preferred_paths and p["id"] in preferred_paths
                               else ("已在使用" if current_paths and p["id"] in current_paths else "可考虑")),
                    "priority": preferred_paths.index(p["id"]) + 1 if preferred_paths and p["id"] in preferred_paths else 99,
                }
                for p in MONETIZATION_PATHS
            ],
        })

    # ---- Design Listing CRUD ----

    def list_listings(self, monetization_path=None, platform=None, material_category=None,
                      status=None, work_id=None) -> ApiResponse:
        """商品列表 — 取代旧的 /supply/products."""
        query = self.db.query(DesignListing)
        if monetization_path:
            query = query.filter(DesignListing.monetization_path == monetization_path)
        if material_category is not None:
            pass  # material stored in template relation, not directly filterable
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

    def create_listing(self, data) -> ApiResponse:
        """创建商品."""
        listing = DesignListing(
            work_id=data.work_id,
            product_template_id=data.product_template_id,
            title=data.title,
            description=data.description,
            price=data.price,
            cost=data.cost,
            currency=data.currency,
            monetization_path=data.monetization_path,
            variant_sku=data.variant_sku,
            variant_name=data.variant_name,
            spec_validation=data.spec_validation,
            spec_validated_at=datetime.now(timezone.utc) if data.spec_validation else None,
            mockup_image_path=data.mockup_image_path,
            design_file_path=data.design_file_path,
            status=data.status,
        )
        self.db.add(listing)
        try:
            self.db.commit()
            self.db.refresh(listing)
        except Exception:
            self.db.rollback()
            raise
        return ApiResponse(message="商品已创建", data={"id": listing.id})

    def get_listing_detail(self, listing_id: str) -> ApiResponse:
        """商品详情."""
        listing = self.db.query(DesignListing).filter(DesignListing.id == listing_id).first()
        if not listing:
            raise HTTPException(status_code=404, detail="商品不存在")

        pubs = self.db.query(ProductPublishing).filter(ProductPublishing.listing_id == listing_id).all()
        revs = self.db.query(RevenueRecord).filter(RevenueRecord.listing_id == listing_id).all()
        ords = self.db.query(Order).filter(Order.listing_id == listing_id).all()
        camps = self.db.query(Campaign).filter(Campaign.listing_id == listing_id).all()
        lies = self.db.query(License).filter(License.listing_id == listing_id).all()

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
                 "listing_url": p.listing_url,
                 "published_at": p.published_at.isoformat() if p.published_at else None}
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
                 "status": l.status,
                 "contract_signed": getattr(l, 'contract_signed', False)}
                for l in lies
            ],
            "revenues": [
                {"id": r.id, "amount": r.amount,
                 "date": r.date.isoformat() if r.date else None,
                 "platform": r.platform,
                 "net_revenue": getattr(r, 'net_revenue', 0)}
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

    def update_listing(self, listing_id: str, data) -> ApiResponse:
        """更新商品信息."""
        listing = self.db.query(DesignListing).filter(DesignListing.id == listing_id).first()
        if not listing:
            raise HTTPException(status_code=404, detail="商品不存在")

        for key, value in data.model_dump(exclude_none=True).items():
            setattr(listing, key, value)

        try:
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise
        return ApiResponse(message="商品已更新")

    def delete_listing(self, listing_id: str) -> ApiResponse:
        """软删除商品."""
        listing = self.db.query(DesignListing).filter(DesignListing.id == listing_id).first()
        if not listing:
            raise HTTPException(status_code=404, detail="商品不存在")
        listing.status = "discontinued"
        try:
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise
        return ApiResponse(message="商品已下架")

    # ---- Spec Validation Compatibility & Remediation ----

    def validate_design_compatibility(self, design_spec: dict, exclude_category_id=None, limit=10) -> ApiResponse:
        """兼容产品推荐."""
        clean_spec = {k: v for k, v in design_spec.items() if v is not None}

        compatible = get_compatible_templates(
            clean_spec, PRODUCT_CATEGORIES,
            exclude_category_id=exclude_category_id,
            limit=limit,
        )

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

    def get_remediation_suggestions(self, category_id: str, design_spec: dict) -> ApiResponse:
        """修复建议."""
        if not category_id:
            raise HTTPException(status_code=400, detail="缺少 category_id")

        template = get_category_by_id(category_id)
        if not template:
            raise HTTPException(status_code=400, detail=f"未知品类: {category_id}")

        clean_spec = {k: v for k, v in design_spec.items() if v is not None}
        suggestions = compute_remediation_suggestions(clean_spec, template)

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
