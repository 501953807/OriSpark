"""内容分发中心 API 路由 — 对应: docs/modules-v5/05-content-distribution.md
Phase 1: AI文案、排期、Verified Badge、Feed导出
端点: 26 (publish)

所有 DB 操作已提取至 publish_manager_service.py.
"""

import csv
import io
import json
import asyncio
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import require_auth
from app.schemas.common import ApiResponse
from app.gateway.ollama import OllamaGateway
from app.services.publish_manager_service import PublishManagerService

# ──────────────────────────────────────────────
# Request Body Models (replaces bare dict params)
# ──────────────────────────────────────────────

class CreateProductRequest(BaseModel):
    work_id: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    price: float = 0
    category: Optional[str] = None
    specifications: Optional[dict] = None
    images: list = []


class UpdateProductRequest(BaseModel):
    model_config = ConfigDict(extra="allow")


class AIDescribeRequest(BaseModel):
    style: str = "xiaohongshu"
    language: Optional[str] = None


class AddRevenueRequest(BaseModel):
    product_id: Optional[str] = None
    platform: Optional[str] = None
    amount: float = 0
    date: Optional[str] = None
    order_count: int = 1
    notes: Optional[str] = None


class CreateScheduleRequest(BaseModel):
    product_id: Optional[str] = None
    listing_id: Optional[str] = None
    work_id: Optional[str] = None
    platform: str
    scheduled_time: Optional[str] = None
    content_preview: Optional[str] = None


class CreatePublishContentRequest(BaseModel):
    work_id: Optional[str] = None
    product_id: Optional[str] = None
    title: str
    content_type: str = "work"
    text_content: Optional[str] = None
    image_paths: Optional[list] = None


class AddPublishAnalyticsRequest(BaseModel):
    platform: str
    work_id: Optional[str] = None
    product_id: Optional[str] = None
    views: int = 0
    likes: int = 0
    comments: int = 0
    shares: int = 0
    saves: int = 0
    date: Optional[str] = None
    notes: Optional[str] = None

router = APIRouter()

# ──────────────────────────────────────────────
# CSV 平台模板字段映射 (保留兼容)
# ──────────────────────────────────────────────
PLATFORM_TEMPLATES = {
    "taobao": {
        "name": "淘宝",
        "fields": ["title", "description", "price", "quantity", "images", "category"],
    },
    "xiaohongshu": {
        "name": "小红书",
        "fields": ["title", "description", "price", "tags", "images"],
    },
    "douyin": {
        "name": "抖音",
        "fields": ["title", "description", "price", "stock", "images", "specs"],
    },
    "shopify": {
        "name": "Shopify",
        "fields": ["title", "description", "price", "sku", "images", "tags", "vendor"],
    },
}

# ──────────────────────────────────────────────
# P1.6.1 — AI 描述多平台风格提示词模板
# ──────────────────────────────────────────────
DESCRIBE_STYLES = {
    "xiaohongshu": {
        "name": "小红书",
        "icon": "📕",
        "description": "种草文案，口语化，emoji丰富，100-200字",
        "lang": "zh",
        "system_prompt": """你是专业的小红书种草文案写手。为一个产品写一段小红书风格的种草文案。

风格要求：
- 亲切活泼的口语化表达，像朋友分享好物一样
- 适当使用 emoji 表情点缀
- 100-200字之间
- 开头用吸引人的句子引发好奇
- 突出产品的独特性和使用感受
- 结尾加上相关标签""",
    },
    "taobao": {
        "name": "淘宝",
        "icon": "🛒",
        "description": "促销导向，卖点突出，功能罗列，50-100字",
        "lang": "zh",
        "system_prompt": """你是专业的淘宝电商文案写手。为一个产品写一段淘宝风格的商品描述。

风格要求：
- 专业热情，突出卖点和促销感
- 50-100字，简洁有力
- 清晰罗列核心卖点(材质/工艺/设计)
- 突出性价比
- 适合放在淘宝商品详情页""",
    },
    "douyin": {
        "name": "抖音",
        "icon": "🎵",
        "description": "短平快，口语，钩子开头，30-60字",
        "lang": "zh",
        "system_prompt": """你是专业的抖音短视频描述写手。为一个产品写一段抖音风格的视频描述文案。

风格要求：
- 直接有力，短平快
- 30-60字，口语化
- 开头用钩子吸引注意力（"你敢信？""绝了！"等）
- 制造紧迫感或好奇心
- 适合作为短视频标题/描述""",
    },
    "shopify": {
        "name": "Shopify",
        "icon": "🛍️",
        "description": "专业产品描述，英文，100-300字",
        "lang": "en",
        "system_prompt": """You are a professional Shopify product copywriter. Write a product description for a Shopify store.

Style requirements:
- Professional and concise English
- 100-300 words
- Highlight key features and benefits
- Include material, craftsmanship, and design details
- Optimize for SEO with relevant keywords
- End with a subtle call-to-action""",
    },
    "etsy": {
        "name": "Etsy",
        "icon": "🧶",
        "description": "手工感，故事化，温暖personal，150-300字",
        "lang": "en",
        "system_prompt": """You are a warm, personal Etsy product copywriter. Write a charming Etsy-style product description.

Style requirements:
- Warm and personal tone, like an artisan describing their handcrafted piece
- Tell the story behind the design
- 150-300 words
- Highlight the handmade/unique quality
- Mention the creator's passion and process
- Include care instructions if applicable""",
    },
    "kickstarter": {
        "name": "Kickstarter",
        "icon": "🚀",
        "description": "故事驱动，愿景感，为什么支持，300-500字",
        "lang": "en",
        "system_prompt": """You are a passionate Kickstarter campaign writer. Write compelling crowdfunding copy for a creative project.

Style requirements:
- Story-driven and vision-oriented
- 300-500 words
- Start with the big vision — why this project matters
- Explain what makes it unique and innovative
- Describe the rewards and what backers will receive
- Build excitement and urgency ("Join us in bringing this to life!")
- End with a strong call-to-action for backers""",
    },
}


# ──────────────────────────────────────────────
# 产品 CRUD (保留)
# ──────────────────────────────────────────────

@router.get("/publish/products", response_model=ApiResponse[list])
def list_products(db: Session = Depends(get_db)):
    """获取商品列表."""
    svc = PublishManagerService(db)
    return ApiResponse(data=svc.list_products())


@router.post("/publish/products", response_model=ApiResponse)
async def create_product(data: CreateProductRequest, db: Session = Depends(get_db), _=Depends(require_auth)):
    """创建商品."""
    svc = PublishManagerService(db)
    result = svc.create_product(
        data.work_id, data.title, data.description, data.price,
        data.category, data.specifications, data.images,
    )
    return ApiResponse(message="商品已创建", data=result)


@router.put("/publish/products/{product_id}", response_model=ApiResponse)
async def update_product(product_id: str, data: UpdateProductRequest, db: Session = Depends(get_db), _=Depends(require_auth)):
    """更新商品."""
    svc = PublishManagerService(db)
    svc.update_product(product_id, data.model_dump(exclude_unset=True))
    return ApiResponse(message="商品已更新", data={"id": product_id})


@router.delete("/publish/products/{product_id}", response_model=ApiResponse)
async def delete_product(product_id: str, db: Session = Depends(get_db), _=Depends(require_auth)):
    """删除商品."""
    svc = PublishManagerService(db)
    svc.delete_product(product_id)
    return ApiResponse(message="商品已删除")


# ──────────────────────────────────────────────
# P1.6.1 — AI 描述多平台风格引擎
# ──────────────────────────────────────────────

@router.get("/publish/describe/styles", response_model=ApiResponse)
def get_describe_styles():
    """获取支持的 AI 描述风格列表."""
    return ApiResponse(data=[
        {
            "key": k,
            "name": v["name"],
            "icon": v["icon"],
            "description": v["description"],
            "lang": v["lang"],
        }
        for k, v in DESCRIBE_STYLES.items()
    ])


@router.post("/publish/products/{product_id}/describe", response_model=ApiResponse)
async def generate_ai_description(
    product_id: str,
    data: AIDescribeRequest = AIDescribeRequest(),
    db: Session = Depends(get_db),
    _=Depends(require_auth),
):
    """AI 生成商品描述 — 支持6种平台风格，Ollama 优先 + 模板回退."""
    import logging
    svc = PublishManagerService(db)
    product = svc.get_product(product_id)

    style = data.style
    if style not in DESCRIBE_STYLES:
        raise HTTPException(
            status_code=400,
            detail=f"不支持的风格: {style}。支持: {', '.join(DESCRIBE_STYLES.keys())}",
        )

    style_config = DESCRIBE_STYLES[style]
    lang = data.language or style_config["lang"]

    user_prompt = f"""产品名称：{product.title}
产品品类：{product.category or '创意作品'}
产品价格：¥{product.price}
现有描述：{product.description or '暂无'}
规格参数：{json.dumps(product.specifications or {}, ensure_ascii=False)}

请按上述风格要求生成产品描述。"""

    # 尝试 Ollama
    ollama_description = None
    source = "template"
    try:
        gateway = OllamaGateway()
        ollama_description = await gateway.generate_platform_description(
            system_prompt=style_config["system_prompt"],
            user_prompt=user_prompt,
            style=style,
        )
        if ollama_description and not ollama_description.startswith("[AI 生成失败"):
            source = "ollama"
    except Exception as e:
        logging.getLogger(__name__).exception("Error in generate_ai_description: %s", str(e))

    # Ollama 不可用时使用模板回退
    if ollama_description is None or source == "template":
        ollama_description = _fallback_style_description(product, style, style_config, lang)
        source = "template"

    # 保存到数据库
    svc.save_ai_description(product_id, ollama_description, style)

    return ApiResponse(
        data={
            "description": ollama_description,
            "style": style,
            "style_name": style_config["name"],
            "source": source,
        },
    )


def _fallback_style_description(product, style: str, style_config: dict, lang: str) -> str:
    """Ollama 不可用时的模板描述，按风格生成."""
    category = product.category or "创意作品"
    title = product.title
    price = product.price

    if style == "xiaohongshu":
        return f"""[本地模板 - 小红书风格]

姐妹们！！！今天必须分享这款{category}界的宝藏～✨

《{title}》真的绝美！

一眼就被它的设计吸引了，每一处细节都好用心💕
{category}做的太精致了，不管是自用还是送人都超级合适！
性价比也很赞，才¥{price}～

已经用了一段时间了，真香警告⚠️

#原创设计 #{category} #好物分享 #种草 #礼物推荐"""

    elif style == "taobao":
        return f"""[本地模板 - 淘宝风格]

【{title}】原创{category} | 精选材质 | 品质保障

✨ 核心卖点：
• 原创设计 — 独一无二的艺术创作
• 精工制作 — 高品质{category}工艺
• 多场景适用 — 自用/送礼/收藏皆宜

💡 规格：详见商品详情
💰 价格：¥{price}

#原创 #设计 #{category} #品质好物"""

    elif style == "douyin":
        return f"""[本地模板 - 抖音风格]

你敢信？！这款《{title}》也太绝了吧！！

原创{category}设计，细节质感拉满
品质真的可，自用送人都绝了

🔥 ¥{price} 赶紧冲

#原创设计 #{category} #好物推荐"""

    elif style == "shopify":
        return f"""[Template - Shopify Style]

**{title}** — Original {category} Design

Crafted with passion and precision, this original {category} piece brings unique artistic vision to life. Every detail has been carefully considered to deliver exceptional quality.

**Key Features:**
- Original artwork design, one of a kind
- Premium {category} craftsmanship
- Perfect for personal collection or gifting
- High-quality materials for lasting durability

**Price:** ¥{price}

Elevate your space with this distinctive creation. Order now while supplies last.

#original #design #{category.replace(' ', '')} #art #creative"""

    elif style == "etsy":
        return f"""[Template - Etsy Style]

**{title}** — A Handcrafted Original

Hello and welcome! I'm so excited to share this piece with you.

Every {category} in my shop begins as a spark of inspiration — and "{title}" was born from that creative journey. I pour my heart into every design, carefully crafting each detail to bring you something truly special.

This piece reflects my passion for original art that speaks to the soul. Whether you're treating yourself or finding the perfect gift, I hope it brings as much joy to your space as it brought me to create.

**Details:**
• Type: Original {category} design
• Price: ¥{price}
• Made with love and creativity

Thank you for supporting independent artists!

#handmade #originalart #{category} #independentartist #uniquegift"""

    elif style == "kickstarter":
        return f"""[Template - Kickstarter Style]

**{title}** — Bringing Original Creativity to Life

**The Vision**

We believe that original art deserves to be shared with the world. "{title}" represents our commitment to bold, authentic design that stands out in a world of mass-produced sameness.

**Why This Project Matters**

Every {category} in our collection is an original work — not a template, not a copy. By backing this project, you're not just getting a product; you're supporting independent creativity and helping bring unique designs to life.

**What You'll Get**

As a backer, you'll receive:
• "{title}" — an original {category} piece
• Exclusive behind-the-scenes content about the creation process
• Early access to future designs

**Specifications:**
• Category: {category}
• Reward Price: ¥{price}

**Join Us**

Help us bring original art to more people. Back this project today and be part of something truly creative!

#crowdfunding #originalart #{category} #supportcreators #independentartist"""

    return f"[本地模板] {title} — {category}"


# ──────────────────────────────────────────────
# 旧版导出 (保留兼容)
# ──────────────────────────────────────────────

@router.get("/publish/export/{product_id}", response_model=ApiResponse)
def export_product_csv(product_id: str, platform: str = Query(default="taobao"), db: Session = Depends(get_db)):
    """导出商品 CSV (按平台模板)."""
    if platform not in PLATFORM_TEMPLATES:
        raise HTTPException(status_code=400, detail=f"不支持的平台: {platform}")

    svc = PublishManagerService(db)
    template = PLATFORM_TEMPLATES[platform]
    result = svc.export_product_csv(product_id, platform, template)
    return ApiResponse(data=result)


@router.get("/publish/platforms", response_model=ApiResponse)
def get_publish_platforms():
    """获取支持的发布平台."""
    return ApiResponse(data=[
        {
            "key": k, "name": v["name"], "fields": v["fields"],
            "auth_type": "oauth" if k != "shopify" else "api_key",
        }
        for k, v in PLATFORM_TEMPLATES.items()
    ])


@router.post("/publish/publish/{product_id}", response_model=ApiResponse)
async def publish_product(product_id: str, platform: str = Query(...), db: Session = Depends(get_db), _=Depends(require_auth)):
    """记录发布到指定平台 (不执行实际发布，由 ERP/MCP 自行拉取)."""
    if platform not in PLATFORM_TEMPLATES:
        raise HTTPException(status_code=400, detail=f"不支持的平台: {platform}")

    svc = PublishManagerService(db)
    result = svc.publish_product(product_id, platform)
    return ApiResponse(
        message=f"已标记发布到{PLATFORM_TEMPLATES[platform]['name']}",
        data=result,
    )


# ──────────────────────────────────────────────
# P1.6.3 — OriStudio Verified 徽章
# ──────────────────────────────────────────────

@router.post("/publish/products/{product_id}/verified-badge", response_model=ApiResponse)
async def generate_verified_badge(product_id: str, db: Session = Depends(get_db), _=Depends(require_auth)):
    """为产品生成 OriStudio Verified 徽章 (QR码 + SVG + PNG + Embed代码)."""
    svc = PublishManagerService(db)
    product = svc.get_product(product_id)
    from app.services.verified_badge import VerifiedBadgeService
    service = VerifiedBadgeService()
    result = service.generate(product_id=product_id, product_title=product.title)

    svc.save_verified_mark(product_id, result["qr_url"], result["verify_url"])

    return ApiResponse(
        message="Verified 徽章已生成",
        data=result,
    )


@router.get("/publish/verified-mark/{product_id}/embed", response_model=ApiResponse)
def get_verified_embed(product_id: str, db: Session = Depends(get_db)):
    """获取 OriStudio Verified 徽章嵌入代码 (HTML/JS snippet)."""
    svc = PublishManagerService(db)
    product = svc.get_product(product_id)
    from app.services.verified_badge import VerifiedBadgeService
    service = VerifiedBadgeService()
    embed = service.generate_embed_snippet(product_id=product_id, product_title=product.title)

    return ApiResponse(data=embed)


# ──────────────────────────────────────────────
# P1.6.5-P1.6.7 — JSON Product Feed
# ──────────────────────────────────────────────

@router.get("/publish/feed", response_model=ApiResponse)
def get_product_feed(
    category: Optional[str] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """生成标准 JSON Product Feed (Schema 1.0)."""
    svc = PublishManagerService(db)
    products = svc.get_product_feed(category)

    from app.services.json_feed import JsonFeedService
    feed_service = JsonFeedService()
    feed_data = feed_service.generate_feed(products)

    return ApiResponse(data=feed_data)


@router.get("/publish/feed/schema", response_model=ApiResponse)
def get_feed_schema():
    """获取 JSON Product Feed Schema 定义."""
    from app.services.json_feed import JsonFeedService
    return ApiResponse(data=JsonFeedService.schema_definition())


@router.get("/publish/feed/platforms", response_model=ApiResponse)
def get_feed_platforms():
    """获取支持的 Feed 导出平台列表."""
    from app.services.json_feed import JsonFeedService
    return ApiResponse(data=JsonFeedService.supported_platforms())


@router.get("/publish/feed/export", response_model=ApiResponse)
def export_feed(
    platform: str = Query(default="universal"),
    category: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """按目标平台格式导出 Product Feed."""
    supported = {"universal", "google", "shopify"}
    if platform not in supported:
        raise HTTPException(
            status_code=400,
            detail=f"不支持的平台: {platform}。支持: {', '.join(supported)}",
        )

    svc = PublishManagerService(db)
    products = svc.get_product_feed(category)

    from app.services.json_feed import JsonFeedService
    feed_service = JsonFeedService()
    feed_data = feed_service.generate_feed(products)

    if platform == "google":
        feed_data = feed_service.convert_to_google(feed_data)
    elif platform == "shopify":
        feed_data = feed_service.convert_to_shopify(feed_data)

    feed_data["feed"]["target_platform"] = platform
    return ApiResponse(data=feed_data)


# ──────────────────────────────────────────────
# P1.6.9-P1.6.11 — 收入追踪增强
# ──────────────────────────────────────────────

@router.get("/publish/revenue/summary", response_model=ApiResponse)
def get_revenue_summary(
    period: str = Query(default="month"),
    db: Session = Depends(get_db),
):
    """收入汇总 — 支持 month/year 聚合维度."""
    from app.models.publish import RevenueRecord
    svc = PublishManagerService(db)
    all_records = svc.list_revenue_records()
    return ApiResponse(data=svc.get_revenue_summary(all_records, period))


MAX_CSV_SIZE = 5 * 1024 * 1024  # 5MB

@router.post("/publish/revenue/import", response_model=ApiResponse)
async def import_revenue_csv(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    _=Depends(require_auth),
):
    """导入平台对账单 CSV."""
    if not file.filename or not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="请上传 CSV 文件")

    content = await file.read()
    if len(content) > MAX_CSV_SIZE:
        raise HTTPException(status_code=400, detail=f"文件大小不能超过 {MAX_CSV_SIZE / (1024*1024):.0f}MB")

    text = content.decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(text))

    if not reader.fieldnames:
        raise HTTPException(status_code=400, detail="CSV 文件为空或格式不正确")

    fieldnames = [f.strip().lower() for f in reader.fieldnames]
    rows = []
    is_taobao = "商品名称" in fieldnames or "订单金额" in fieldnames or "商品id" in fieldnames
    is_douyin = "douyin" in " ".join(fieldnames) or "支付金额" in fieldnames

    for row in reader:
        normalized = {k.strip().lower(): v.strip() for k, v in row.items()}
        if is_taobao:
            platform = "taobao"
            amount = float(normalized.get("订单金额", normalized.get("amount", 0)))
            record_date_str = normalized.get("订单创建时间", normalized.get("date", ""))
            order_count = int(normalized.get("订单数", normalized.get("order_count", 1)))
            notes = normalized.get("商品名称", normalized.get("notes", ""))
        elif is_douyin:
            platform = "douyin"
            amount = float(normalized.get("支付金额", normalized.get("amount", 0)))
            record_date_str = normalized.get("下单时间", normalized.get("date", ""))
            order_count = int(normalized.get("订单数", normalized.get("order_count", 1)))
            notes = normalized.get("商品名称", normalized.get("notes", ""))
        else:
            platform = normalized.get("platform", "imported")
            amount = float(normalized.get("amount", 0))
            record_date_str = normalized.get("date", "")
            order_count = int(normalized.get("order_count", 1))
            notes = normalized.get("notes", "")

        try:
            record_date = datetime.strptime(record_date_str[:10], "%Y-%m-%d").date()
        except (ValueError, IndexError):
            record_date = date.today()

        rows.append({
            "platform": platform,
            "amount": amount,
            "date": record_date,
            "order_count": order_count,
            "notes": f"[CSV导入] {notes}" if notes else "[CSV导入]",
        })

    svc = PublishManagerService(db)
    result = svc.import_revenue_records(rows)
    return ApiResponse(
        message=f"已导入 {result['imported']} 条收入记录",
        data={
            "imported": result["imported"],
            "total_amount": result["total_amount"],
            "errors": result["errors"],
            "detected_format": "taobao" if is_taobao else ("douyin" if is_douyin else "generic"),
        },
    )


# ──────────────────────────────────────────────
# 收入记录 CRUD (保留)
# ──────────────────────────────────────────────

@router.get("/publish/revenue", response_model=ApiResponse)
def list_revenue(
    platform: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """获取收入记录."""
    svc = PublishManagerService(db)
    return ApiResponse(data=svc.list_revenue(platform))


@router.post("/publish/revenue", response_model=ApiResponse)
async def add_revenue(data: AddRevenueRequest, db: Session = Depends(get_db), _=Depends(require_auth)):
    """添加收入记录."""
    record_date = date.today()
    if data.date:
        try:
            record_date = datetime.strptime(data.date[:10], "%Y-%m-%d").date()
        except (ValueError, IndexError):
            pass

    svc = PublishManagerService(db)
    svc.add_revenue(
        product_id=data.product_id,
        platform=data.platform,
        amount=data.amount,
        date_val=record_date,
        order_count=data.order_count,
        notes=data.notes,
    )
    return ApiResponse(message="收入记录已添加")


# ─── Content Distribution Center endpoints (P2) ───


@router.post("/publish/schedule", response_model=ApiResponse)
async def create_schedule(data: CreateScheduleRequest, db: Session = Depends(get_db), _=Depends(require_auth)):
    """创建排期发布."""
    sched_time = None
    if data.scheduled_time:
        sched_time = datetime.fromisoformat(data.scheduled_time.replace("Z", "+00:00"))
    svc = PublishManagerService(db)
    svc.create_schedule(
        data.product_id, data.listing_id, data.work_id,
        data.platform, sched_time or datetime.now(timezone.utc), data.content_preview,
    )
    return ApiResponse(message="排期已创建")


@router.get("/publish/schedules", response_model=ApiResponse[list])
def list_schedules(db: Session = Depends(get_db)):
    """获取排期列表."""
    svc = PublishManagerService(db)
    return ApiResponse(data=svc.list_schedules())


@router.delete("/publish/schedules/{schedule_id}", response_model=ApiResponse)
async def delete_schedule(schedule_id: str, db: Session = Depends(get_db), _=Depends(require_auth)):
    """取消排期."""
    svc = PublishManagerService(db)
    svc.cancel_schedule(schedule_id)
    return ApiResponse(message="排期已取消")


@router.get("/publish/contents", response_model=ApiResponse[list])
def list_publish_contents(db: Session = Depends(get_db)):
    """获取发布内容列表."""
    svc = PublishManagerService(db)
    return ApiResponse(data=svc.list_contents())


@router.post("/publish/contents", response_model=ApiResponse)
async def create_publish_content(data: CreatePublishContentRequest, db: Session = Depends(get_db), _=Depends(require_auth)):
    """创建发布内容."""
    svc = PublishManagerService(db)
    svc.create_content(
        data.work_id, data.product_id, data.title,
        data.content_type, data.text_content, data.image_paths,
    )
    return ApiResponse(message="发布内容已创建")


@router.get("/publish/analytics", response_model=ApiResponse[list])
def list_publish_analytics(platform: Optional[str] = None, db: Session = Depends(get_db)):
    """获取影响力分析数据."""
    svc = PublishManagerService(db)
    return ApiResponse(data=svc.list_analytics(platform))


@router.post("/publish/analytics", response_model=ApiResponse)
async def add_publish_analytics(data: AddPublishAnalyticsRequest, db: Session = Depends(get_db), _=Depends(require_auth)):
    """录入平台影响力数据."""
    record_date = date.today()
    if data.date:
        try:
            record_date = datetime.strptime(data.date[:10], "%Y-%m-%d").date()
        except (ValueError, IndexError):
            pass
    svc = PublishManagerService(db)
    svc.add_analytics(
        platform=data.platform,
        work_id=data.work_id,
        product_id=data.product_id,
        views=data.views,
        likes=data.likes,
        comments=data.comments,
        shares=data.shares,
        saves=data.saves,
        date_val=record_date,
        notes=data.notes,
    )
    return ApiResponse(message="影响力数据已录入")
