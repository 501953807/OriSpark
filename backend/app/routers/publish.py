"""内容分发中心 API 路由 — 对应: docs/modules-v3/05-content-distribution.md
Phase 1: AI文案、排期、Verified Badge、Feed导出
端点: 26 (publish)"""

import csv
import io
import json
import asyncio
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.publish import Product, ProductPublishing, RevenueRecord, PublishSchedule, PublishContent, PublishAnalytics
from app.schemas.common import ApiResponse
from app.gateway.ollama import OllamaGateway

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
    products = db.query(Product).order_by(Product.created_at.desc()).all()

    return ApiResponse(data=[
        {
            "id": p.id, "work_id": p.work_id, "title": p.title,
            "description": p.description, "ai_description": p.ai_description,
            "price": p.price, "category": p.category,
            "csv_export_path": p.csv_export_path,
            "created_at": p.created_at.isoformat() if p.created_at else None,
        }
        for p in products
    ])


@router.post("/publish/products", response_model=ApiResponse)
def create_product(data: dict, db: Session = Depends(get_db)):
    """创建商品."""
    product = Product(
        work_id=data.get("work_id"),
        title=data.get("title"),
        description=data.get("description"),
        price=data.get("price", 0),
        category=data.get("category"),
        specifications=data.get("specifications"),
        images=data.get("images", []),
    )
    db.add(product)
    db.commit()
    db.refresh(product)

    return ApiResponse(message="商品已创建", data={"id": product.id})


@router.put("/publish/products/{product_id}", response_model=ApiResponse)
def update_product(product_id: str, data: dict, db: Session = Depends(get_db)):
    """更新商品."""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="商品不存在")

    for key, value in data.items():
        if hasattr(product, key) and key != "id":
            setattr(product, key, value)

    db.commit()
    db.refresh(product)

    return ApiResponse(message="商品已更新", data={"id": product.id})


@router.delete("/publish/products/{product_id}", response_model=ApiResponse)
def delete_product(product_id: str, db: Session = Depends(get_db)):
    """删除商品."""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="商品不存在")

    db.delete(product)
    db.commit()

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
    data: dict = {},
    db: Session = Depends(get_db),
):
    """AI 生成商品描述 — 支持6种平台风格，Ollama 优先 + 模板回退.

    请求体:
        style: xiaohongshu/taobao/douyin/shopify/etsy/kickstarter (默认 xiaohongshu)
        language: zh/en (可选，部分风格有固定语言)
    """
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="商品不存在")

    style = data.get("style", "xiaohongshu")
    if style not in DESCRIBE_STYLES:
        raise HTTPException(
            status_code=400,
            detail=f"不支持的风格: {style}。支持: {', '.join(DESCRIBE_STYLES.keys())}",
        )

    style_config = DESCRIBE_STYLES[style]
    lang = data.get("language", style_config["lang"])

    # 构建用户提示词
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
    except Exception:
        pass

    # Ollama 不可用时使用模板回退
    if ollama_description is None or source == "template":
        ollama_description = _fallback_style_description(
            product, style, style_config, lang
        )
        source = "template"

    # 保存到数据库
    product.ai_description = ollama_description
    product.ai_desc_platform = style  # type: ignore[attr-defined]
    product.ai_desc_generated_at = datetime.now(timezone.utc)  # type: ignore[attr-defined]
    db.commit()

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
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="商品不存在")

    if platform not in PLATFORM_TEMPLATES:
        raise HTTPException(status_code=400, detail=f"不支持的平台: {platform}")

    template = PLATFORM_TEMPLATES[platform]
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=template["fields"], extrasaction='ignore')
    writer.writeheader()

    row = {
        "title": product.title,
        "description": product.ai_description or product.description or "",
        "price": product.price,
        "quantity": 1,
        "stock": 1,
        "sku": product.id[:12],
        "images": ",".join(product.images) if product.images else "",
        "category": product.category or "",
        "tags": "原创,创意",
        "specs": str(product.specifications or ""),
        "vendor": "OriStudio",
    }
    writer.writerow(row)

    csv_dir = Path("data/certificates")
    csv_dir.mkdir(parents=True, exist_ok=True)
    csv_path = csv_dir / f"product_{product_id}_{platform}.csv"

    with open(csv_path, "w", encoding="utf-8-sig") as f:
        f.write(output.getvalue())

    product.csv_export_path = str(csv_path)
    db.commit()

    return ApiResponse(
        data={
            "csv_content": output.getvalue(),
            "file_path": str(csv_path),
            "platform": platform,
        }
    )


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
def publish_product(product_id: str, platform: str = Query(...), db: Session = Depends(get_db)):
    """记录发布到指定平台 (不执行实际发布，由 ERP/MCP 自行拉取)."""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="商品不存在")

    if platform not in PLATFORM_TEMPLATES:
        raise HTTPException(status_code=400, detail=f"不支持的平台: {platform}")

    publish = ProductPublishing(
        product_id=product.id,
        platform=platform,
        status="published",
        listing_url=f"https://www.{platform}.com/item/{product.id[:12]}",
        published_at=datetime.now(timezone.utc),
    )
    db.add(publish)
    db.commit()
    db.refresh(publish)

    return ApiResponse(
        message=f"已标记发布到{PLATFORM_TEMPLATES[platform]['name']}",
        data={"publish_id": publish.id, "listing_url": publish.listing_url},
    )


# ──────────────────────────────────────────────
# P1.6.3 — OriStudio Verified 徽章
# ──────────────────────────────────────────────

@router.post("/publish/products/{product_id}/verified-badge", response_model=ApiResponse)
def generate_verified_badge(product_id: str, db: Session = Depends(get_db)):
    """为产品生成 OriStudio Verified 徽章 (QR码 + SVG + PNG + Embed代码)."""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="商品不存在")

    from app.services.verified_badge import VerifiedBadgeService

    service = VerifiedBadgeService()
    result = service.generate(product_id=product.id, product_title=product.title)

    # 保存徽章记录 (更新或插入)
    from app.models.publish import VerifiedMark
    existing = db.query(VerifiedMark).filter(VerifiedMark.product_id == product_id).first()
    if existing:
        existing.qr_code = result["qr_url"]
        existing.cert_url = result["verify_url"]
    else:
        mark = VerifiedMark(
            product_id=product.id,
            qr_code=result["qr_url"],
            cert_url=result["verify_url"],
        )
        db.add(mark)

    db.commit()

    return ApiResponse(
        message="Verified 徽章已生成",
        data=result,
    )


@router.get("/publish/verified-mark/{product_id}/embed", response_model=ApiResponse)
def get_verified_embed(product_id: str, db: Session = Depends(get_db)):
    """获取 OriStudio Verified 徽章嵌入代码 (HTML/JS snippet)."""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="商品不存在")

    from app.services.verified_badge import VerifiedBadgeService

    service = VerifiedBadgeService()
    embed = service.generate_embed_snippet(product_id=product.id, product_title=product.title)

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
    query = db.query(Product)
    if category:
        query = query.filter(Product.category == category)
    products = query.order_by(Product.created_at.desc()).all()

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
    """按目标平台格式导出 Product Feed.

    支持: universal (标准), google (Google Merchant Center), shopify
    """
    supported = {"universal", "google", "shopify"}
    if platform not in supported:
        raise HTTPException(
            status_code=400,
            detail=f"不支持的平台: {platform}。支持: {', '.join(supported)}",
        )

    query = db.query(Product)
    if category:
        query = query.filter(Product.category == category)
    products = query.order_by(Product.created_at.desc()).all()

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
    """收入汇总 — 支持 month/year 聚合维度.

    返回: 总收入、订单数、按平台分组、按产品分组、月度趋势
    """
    records = db.query(RevenueRecord).all()

    now = date.today()
    if period == "month":
        filtered = [r for r in records if r.date and r.date.year == now.year and r.date.month == now.month]
        label = f"{now.year}年{now.month}月"
    elif period == "year":
        filtered = [r for r in records if r.date and r.date.year == now.year]
        label = f"{now.year}年"
    else:
        filtered = records
        label = "全部"

    total_amount = sum(r.amount or 0 for r in filtered)
    total_orders = sum(r.order_count or 0 for r in filtered)
    total_refunds = sum(getattr(r, 'refund_amount', 0) or 0 for r in filtered)

    # 按平台分组
    by_platform: dict[str, float] = {}
    for r in filtered:
        p = r.platform or "unknown"
        by_platform[p] = by_platform.get(p, 0) + (r.amount or 0)

    # 按产品分组
    by_product: dict[str, dict] = {}
    for r in filtered:
        pid = r.product_id or "unknown"
        if pid not in by_product:
            by_product[pid] = {"product_id": pid, "amount": 0, "order_count": 0}
        by_product[pid]["amount"] += r.amount or 0
        by_product[pid]["order_count"] += r.order_count or 0

    # 月度趋势
    monthly_trend: dict[str, float] = {}
    for r in records:
        if r.date:
            key = r.date.strftime("%Y-%m")
            monthly_trend[key] = monthly_trend.get(key, 0) + (r.amount or 0)

    return ApiResponse(
        data={
            "period": period,
            "label": label,
            "total_amount": round(total_amount, 2),
            "total_orders": total_orders,
            "total_refunds": round(total_refunds, 2),
            "platform_count": len(by_platform),
            "by_platform": by_platform,
            "by_product": sorted(by_product.values(), key=lambda x: x["amount"], reverse=True),
            "monthly_trend": dict(sorted(monthly_trend.items())),
        }
    )


@router.post("/publish/revenue/import", response_model=ApiResponse)
async def import_revenue_csv(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """导入平台对账单 CSV.

    支持的 CSV 格式:
    - 通用格式: platform,amount,date,order_count,product_sku,notes
    - 淘宝格式: 自动解析
    - 抖音格式: 自动解析

    返回: 导入记录数、总金额
    """
    if not file.filename or not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="请上传 CSV 文件")

    content = await file.read()
    text = content.decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(text))

    if not reader.fieldnames:
        raise HTTPException(status_code=400, detail="CSV 文件为空或格式不正确")

    fieldnames = [f.strip().lower() for f in reader.fieldnames]
    imported = 0
    total_amount = 0.0
    errors = []

    # 自动检测平台格式
    is_taobao = "商品名称" in fieldnames or "订单金额" in fieldnames or "商品id" in fieldnames
    is_douyin = "douyin" in " ".join(fieldnames) or "支付金额" in fieldnames

    for idx, row in enumerate(reader, start=1):
        try:
            normalized = {k.strip().lower(): v.strip() for k, v in row.items()}

            if is_taobao:
                platform = "taobao"
                amount = float(normalized.get("订单金额", normalized.get("amount", 0)))
                product_sku = normalized.get("商品id", normalized.get("product_sku", ""))
                record_date_str = normalized.get("订单创建时间", normalized.get("date", ""))
                order_count = int(normalized.get("订单数", normalized.get("order_count", 1)))
                notes = normalized.get("商品名称", normalized.get("notes", ""))
            elif is_douyin:
                platform = "douyin"
                amount = float(normalized.get("支付金额", normalized.get("amount", 0)))
                product_sku = normalized.get("商品id", normalized.get("product_sku", ""))
                record_date_str = normalized.get("下单时间", normalized.get("date", ""))
                order_count = int(normalized.get("订单数", normalized.get("order_count", 1)))
                notes = normalized.get("商品名称", normalized.get("notes", ""))
            else:
                platform = normalized.get("platform", "imported")
                amount = float(normalized.get("amount", 0))
                product_sku = normalized.get("product_sku", normalized.get("sku", ""))
                record_date_str = normalized.get("date", "")
                order_count = int(normalized.get("order_count", 1))
                notes = normalized.get("notes", "")

            # 解析日期
            try:
                record_date = datetime.strptime(record_date_str[:10], "%Y-%m-%d").date()
            except (ValueError, IndexError):
                record_date = date.today()

            record = RevenueRecord(
                platform=platform,
                amount=amount,
                date=record_date,
                order_count=order_count,
                notes=f"[CSV导入] {notes}" if notes else "[CSV导入]",
            )
            db.add(record)
            imported += 1
            total_amount += amount

        except (ValueError, KeyError) as e:
            errors.append({"row": idx, "error": str(e)})
            continue

    db.commit()

    return ApiResponse(
        message=f"已导入 {imported} 条收入记录",
        data={
            "imported": imported,
            "total_amount": round(total_amount, 2),
            "errors": errors,
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
    query = db.query(RevenueRecord)
    if platform:
        query = query.filter(RevenueRecord.platform == platform)

    records = query.order_by(RevenueRecord.date.desc()).all()

    return ApiResponse(data=[
        {
            "id": r.id, "product_id": r.product_id,
            "platform": r.platform, "amount": r.amount,
            "currency": r.currency, "date": r.date.isoformat() if r.date else None,
            "order_count": r.order_count, "notes": r.notes,
        }
        for r in records
    ])


@router.post("/publish/revenue", response_model=ApiResponse)
def add_revenue(data: dict, db: Session = Depends(get_db)):
    """添加收入记录."""
    # 处理日期: 支持 date 对象和字符串
    raw_date = data.get("date", date.today())
    if isinstance(raw_date, str):
        try:
            raw_date = datetime.strptime(raw_date[:10], "%Y-%m-%d").date()
        except (ValueError, IndexError):
            raw_date = date.today()
    elif not isinstance(raw_date, (date, datetime)):
        raw_date = date.today()

    record = RevenueRecord(
        product_id=data.get("product_id"),
        platform=data.get("platform"),
        amount=data.get("amount", 0),
        date=raw_date,
        order_count=data.get("order_count", 1),
        notes=data.get("notes"),
    )
    db.add(record)
    db.commit()

    return ApiResponse(message="收入记录已添加")


# ─── Content Distribution Center endpoints (P2) ───


@router.post("/publish/schedule", response_model=ApiResponse)
def create_schedule(data: dict, db: Session = Depends(get_db)):
    """创建排期发布."""
    from datetime import datetime as dt
    sched_time = data.get("scheduled_time")
    if isinstance(sched_time, str):
        sched_time = dt.fromisoformat(sched_time.replace("Z", "+00:00"))
    schedule = PublishSchedule(
        product_id=data.get("product_id"),
        listing_id=data.get("listing_id"),
        work_id=data.get("work_id"),
        platform=data["platform"],
        scheduled_time=sched_time or datetime.utcnow(),
        content_preview=data.get("content_preview"),
    )
    db.add(schedule)
    db.commit()
    return ApiResponse(message="排期已创建")


@router.get("/publish/schedules", response_model=ApiResponse[list])
def list_schedules(db: Session = Depends(get_db)):
    """获取排期列表."""
    schedules = db.query(PublishSchedule).order_by(
        PublishSchedule.scheduled_time.desc()
    ).all()
    return ApiResponse(data=[
        {
            "id": s.id,
            "platform": s.platform,
            "scheduled_time": s.scheduled_time.isoformat() if s.scheduled_time else None,
            "status": s.status,
            "content_preview": s.content_preview,
            "executed_at": s.executed_at.isoformat() if s.executed_at else None,
        }
        for s in schedules
    ])


@router.delete("/publish/schedules/{schedule_id}", response_model=ApiResponse)
def delete_schedule(schedule_id: str, db: Session = Depends(get_db)):
    """取消排期."""
    schedule = db.query(PublishSchedule).filter(PublishSchedule.id == schedule_id).first()
    if not schedule:
        raise HTTPException(status_code=404, detail="排期不存在")
    if schedule.status != "scheduled":
        raise HTTPException(status_code=400, detail="只能取消待发布的排期")
    schedule.status = "cancelled"
    db.commit()
    return ApiResponse(message="排期已取消")


@router.get("/publish/contents", response_model=ApiResponse[list])
def list_publish_contents(db: Session = Depends(get_db)):
    """获取发布内容列表."""
    contents = db.query(PublishContent).order_by(
        PublishContent.created_at.desc()
    ).all()
    return ApiResponse(data=[
        {
            "id": c.id,
            "title": c.title,
            "content_type": c.content_type,
            "text_content": c.text_content,
            "image_paths": c.image_paths,
            "created_at": c.created_at.isoformat() if c.created_at else None,
        }
        for c in contents
    ])


@router.post("/publish/contents", response_model=ApiResponse)
def create_publish_content(data: dict, db: Session = Depends(get_db)):
    """创建发布内容."""
    content = PublishContent(
        work_id=data.get("work_id"),
        product_id=data.get("product_id"),
        title=data["title"],
        content_type=data.get("content_type", "work"),
        text_content=data.get("text_content"),
        image_paths=data.get("image_paths"),
    )
    db.add(content)
    db.commit()
    return ApiResponse(message="发布内容已创建")


@router.get("/publish/analytics", response_model=ApiResponse[list])
def list_publish_analytics(platform: Optional[str] = None, db: Session = Depends(get_db)):
    """获取影响力分析数据."""
    query = db.query(PublishAnalytics)
    if platform:
        query = query.filter(PublishAnalytics.platform == platform)
    analytics = query.order_by(PublishAnalytics.date.desc()).all()
    return ApiResponse(data=[
        {
            "id": a.id,
            "platform": a.platform,
            "work_id": a.work_id,
            "product_id": a.product_id,
            "views": a.views,
            "likes": a.likes,
            "comments": a.comments,
            "shares": a.shares,
            "saves": a.saves,
            "date": a.date.isoformat() if a.date else None,
            "notes": a.notes,
        }
        for a in analytics
    ])


@router.post("/publish/analytics", response_model=ApiResponse)
def add_publish_analytics(data: dict, db: Session = Depends(get_db)):
    """录入平台影响力数据."""
    from datetime import date as d
    raw_date = data.get("date", str(d.today()))
    if isinstance(raw_date, str):
        try:
            raw_date = d.strptime(raw_date[:10], "%Y-%m-%d")
        except (ValueError, IndexError):
            raw_date = d.today()
    analytics = PublishAnalytics(
        platform=data["platform"],
        work_id=data.get("work_id"),
        product_id=data.get("product_id"),
        views=data.get("views", 0),
        likes=data.get("likes", 0),
        comments=data.get("comments", 0),
        shares=data.get("shares", 0),
        saves=data.get("saves", 0),
        date=raw_date,
        notes=data.get("notes"),
    )
    db.add(analytics)
    db.commit()
    return ApiResponse(message="影响力数据已录入")
