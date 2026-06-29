"""MCP (Model Context Protocol) Server — OriStudio PDH.

P2.6.1-P2.6.4: Implements MCP with HTTP transport at /mcp endpoint.
Provides 7 Tools for product data access:
- list_products
- get_product
- search_products
- get_product_certificate
- get_verified_mark
- get_revenue_summary
- get_product_feed
"""

import csv
import io
import json
import hashlib
import time
import threading
from datetime import date, datetime
from typing import Optional, Any
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.publish import Product, ProductPublishing, RevenueRecord, VerifiedMark
from app.schemas.common import ApiResponse

router = APIRouter()

# ─────────────────────────────────────────────────────────────
# P2.6.6: MCP API Key Auth + Rate Limiting
# ─────────────────────────────────────────────────────────────

MCP_API_KEYS = {
    "mcp-dev-key-001": {"name": "Development", "rate_limit": 100},
    "mcp-local-default": {"name": "Local Default", "rate_limit": 60},
}

_rate_limit_store: dict[str, list[float]] = {}
_rate_limit_lock = threading.Lock()


def verify_mcp_api_key(request: Request) -> dict:
    """Verify MCP API key from Authorization header."""
    auth = request.headers.get("Authorization", "")
    if not auth:
        raise HTTPException(status_code=401, detail="Missing MCP API key")

    if auth.startswith("Bearer "):
        api_key = auth[7:].strip()
    else:
        api_key = auth.strip()

    if api_key not in MCP_API_KEYS:
        raise HTTPException(status_code=403, detail="Invalid MCP API key")

    return MCP_API_KEYS[api_key]


def check_rate_limit(key_name: str, max_requests: int) -> bool:
    """Window-based rate limiting (60s sliding window)."""
    now = time.time()
    window = 60.0

    with _rate_limit_lock:
        bucket = _rate_limit_store.get(key_name, [])
        # Remove expired entries
        bucket = [t for t in bucket if now - t < window]
        if len(bucket) >= max_requests:
            return False
        bucket.append(now)
        _rate_limit_store[key_name] = bucket
        return True


# ─────────────────────────────────────────────────────────────
# MCP Protocol Handlers (JSON-RPC 2.0 over HTTP)
# ─────────────────────────────────────────────────────────────

MCP_VERSION = "2024-11-05"
SERVER_NAME = "oristudio-pdh-mcp"
SERVER_VERSION = "1.0.0"

# Tool definitions for MCP tools/list
TOOL_DEFINITIONS = [
    {
        "name": "list_products",
        "description": "List all products in the OriStudio Product Data Hub (PDH). Returns product id, title, price, category, and status.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "category": {"type": "string", "description": "Filter by product category"},
                "status": {"type": "string", "description": "Filter by product status (active/inactive)"},
                "limit": {"type": "integer", "description": "Maximum number of products to return (default 50)"},
            },
        },
    },
    {
        "name": "get_product",
        "description": "Get detailed information about a specific product by ID, including AI-generated description, specifications, media, pricing, and publish status.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "product_id": {"type": "string", "description": "The unique product ID"},
            },
            "required": ["product_id"],
        },
    },
    {
        "name": "search_products",
        "description": "Search products by keyword across title, description, and category fields.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search keyword"},
                "category": {"type": "string", "description": "Optional category filter"},
            },
            "required": ["query"],
        },
    },
    {
        "name": "get_product_certificate",
        "description": "Get the blockchain/notary certificate information for a product, including SHA-256 hash, notary platform, and certificate URL.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "product_id": {"type": "string", "description": "The unique product ID"},
            },
            "required": ["product_id"],
        },
    },
    {
        "name": "get_verified_mark",
        "description": "Get the OriStudio Verified badge for a product, including QR code URL, verification page URL, and embed codes (HTML/JS).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "product_id": {"type": "string", "description": "The unique product ID"},
            },
            "required": ["product_id"],
        },
    },
    {
        "name": "get_revenue_summary",
        "description": "Get revenue summary data including total revenue, order count, platform breakdown, and monthly trends.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "period": {"type": "string", "description": "Aggregation period: month, year, or all"},
            },
        },
    },
    {
        "name": "get_product_feed",
        "description": "Export the product feed in a specified format. Supports universal (standard JSON), google (Google Merchant Center), shopify, wangdiantong, wanliuniu, jushuitan.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "format": {"type": "string", "description": "Feed format: universal, google, shopify, wangdiantong, wanliuniu, jushuitan (default universal)"},
                "category": {"type": "string", "description": "Optional category filter"},
            },
        },
    },
]


def _handle_tools_list() -> dict:
    """Handle tools/list MCP request."""
    return {"tools": TOOL_DEFINITIONS}


def _handle_tools_call(name: str, arguments: dict, db: Session) -> dict:
    """Handle tools/call MCP request."""
    handlers = {
        "list_products": _tool_list_products,
        "get_product": _tool_get_product,
        "search_products": _tool_search_products,
        "get_product_certificate": _tool_get_product_certificate,
        "get_verified_mark": _tool_get_verified_mark,
        "get_revenue_summary": _tool_get_revenue_summary,
        "get_product_feed": _tool_get_product_feed,
    }
    handler = handlers.get(name)
    if not handler:
        return {"content": [{"type": "text", "text": f"Unknown tool: {name}"}], "isError": True}
    try:
        result = handler(arguments, db)
        return {"content": [{"type": "text", "text": json.dumps(result, ensure_ascii=False, default=str)}]}
    except Exception as e:
        return {"content": [{"type": "text", "text": f"Tool error: {str(e)}"}], "isError": True}


# ─────────────────────────────────────────────────────────────
# Tool Implementations
# ─────────────────────────────────────────────────────────────

def _tool_list_products(args: dict, db: Session) -> dict:
    category = args.get("category")
    status = args.get("status", "active")
    limit = min(args.get("limit", 50), 200)

    query = db.query(Product)
    if category:
        query = query.filter(Product.category == category)
    if status:
        query = query.filter(Product.status == status)

    products = query.order_by(Product.created_at.desc()).limit(limit).all()
    return {
        "total": len(products),
        "products": [
            {
                "id": p.id,
                "title": p.title,
                "price": p.price,
                "category": p.category,
                "status": p.status,
                "created_at": p.created_at.isoformat() if p.created_at else None,
            }
            for p in products
        ],
    }


def _tool_get_product(args: dict, db: Session) -> dict:
    product_id = args.get("product_id", "")
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        return {"error": f"Product not found: {product_id}"}

    publishings = db.query(ProductPublishing).filter(
        ProductPublishing.product_id == product_id
    ).all()

    return {
        "id": product.id,
        "work_id": product.work_id,
        "title": product.title,
        "description": product.description,
        "ai_description": product.ai_description,
        "price": product.price,
        "cost": product.cost,
        "currency": product.currency,
        "category": product.category,
        "monetization_path": product.monetization_path,
        "material_category": product.material_category,
        "platform": product.platform,
        "platform_product_id": product.platform_product_id,
        "platform_status": product.platform_status,
        "specifications": product.specifications,
        "images": product.images,
        "status": product.status,
        "created_at": product.created_at.isoformat() if product.created_at else None,
        "updated_at": product.updated_at.isoformat() if product.updated_at else None,
        "publishings": [
            {
                "platform": pub.platform,
                "listing_url": pub.listing_url,
                "status": pub.status,
                "published_at": pub.published_at.isoformat() if pub.published_at else None,
            }
            for pub in publishings
        ],
    }


def _tool_search_products(args: dict, db: Session) -> dict:
    query_text = args.get("query", "")
    category = args.get("category")
    limit = min(args.get("limit", 50), 200)

    search = f"%{query_text}%"
    q = db.query(Product).filter(
        (Product.title.ilike(search))
        | (Product.description.ilike(search))
        | (Product.category.ilike(search))
    )
    if category:
        q = q.filter(Product.category == category)

    products = q.order_by(Product.created_at.desc()).limit(limit).all()
    return {
        "query": query_text,
        "total": len(products),
        "products": [
            {
                "id": p.id,
                "title": p.title,
                "price": p.price,
                "category": p.category,
                "description": (p.description or "")[:200],
                "status": p.status,
            }
            for p in products
        ],
    }


def _tool_get_product_certificate(args: dict, db: Session) -> dict:
    product_id = args.get("product_id", "")
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        return {"error": f"Product not found: {product_id}"}

    # Gather certificate info from related tables
    from app.models.notary import NotaryRecord

    notary_records = db.query(NotaryRecord).filter(
        NotaryRecord.work_id == product.work_id
    ).all() if product.work_id else []

    return {
        "product_id": product.id,
        "product_title": product.title,
        "notary_records": [
            {
                "id": n.id,
                "platform": n.platform,
                "tx_hash": n.tx_hash,
                "blockchain": getattr(n, 'blockchain', None),
                "certificate_url": getattr(n, 'certificate_url', None),
                "status": getattr(n, 'status', 'unknown'),
                "created_at": n.created_at.isoformat() if n.created_at else None,
            }
            for n in notary_records
        ],
        "total_notary_records": len(notary_records),
    }


def _tool_get_verified_mark(args: dict, db: Session) -> dict:
    product_id = args.get("product_id", "")
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        return {"error": f"Product not found: {product_id}"}

    mark = db.query(VerifiedMark).filter(VerifiedMark.product_id == product_id).first()

    if not mark:
        # Generate one on the fly
        from app.services.verified_badge import VerifiedBadgeService
        service = VerifiedBadgeService()
        result = service.generate(product_id=product.id, product_title=product.title)
        embed = service.generate_embed_snippet(product_id=product.id, product_title=product.title)
        return {
            "product_id": product.id,
            "product_title": product.title,
            "qr_url": result.get("qr_url"),
            "verify_url": result.get("verify_url"),
            "embed_html": embed.get("html"),
        }

    return {
        "product_id": product.id,
        "product_title": product.title,
        "qr_url": mark.qr_code,
        "verify_url": mark.cert_url,
    }


def _tool_get_revenue_summary(args: dict, db: Session) -> dict:
    period = args.get("period", "month")
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

    by_platform: dict[str, float] = {}
    for r in filtered:
        p = r.platform or "unknown"
        by_platform[p] = by_platform.get(p, 0) + (r.amount or 0)

    monthly_trend: dict[str, float] = {}
    for r in records:
        if r.date:
            key = r.date.strftime("%Y-%m")
            monthly_trend[key] = monthly_trend.get(key, 0) + (r.amount or 0)

    return {
        "period": period,
        "label": label,
        "total_amount": round(total_amount, 2),
        "total_orders": total_orders,
        "by_platform": by_platform,
        "monthly_trend": dict(sorted(monthly_trend.items())),
    }


def _tool_get_product_feed(args: dict, db: Session) -> dict:
    fmt = args.get("format", "universal")
    category = args.get("category")
    supported = {"universal", "google", "shopify", "wangdiantong", "wanliuniu", "jushuitan"}

    if fmt not in supported:
        return {"error": f"Unsupported format: {fmt}. Supported: {', '.join(supported)}"}

    query = db.query(Product)
    if category:
        query = query.filter(Product.category == category)
    products = query.order_by(Product.created_at.desc()).all()

    from app.services.json_feed import JsonFeedService
    feed_service = JsonFeedService()
    feed_data = feed_service.generate_feed(products)

    if fmt == "google":
        feed_data = feed_service.convert_to_google(feed_data)
    elif fmt == "shopify":
        feed_data = feed_service.convert_to_shopify(feed_data)
    elif fmt == "wangdiantong":
        feed_data = _convert_to_wangdiantong(feed_data, products)
        feed_data["feed"]["target"] = "wangdiantong"
    elif fmt == "wanliuniu":
        feed_data = _convert_to_wanliuniu(feed_data, products)
        feed_data["feed"]["target"] = "wanliuniu"
    elif fmt == "jushuitan":
        feed_data = _convert_to_jushuitan(feed_data, products)
        feed_data["feed"]["target"] = "jushuitan"

    feed_data["feed"]["target"] = feed_data.get("feed", {}).get("target", fmt)
    return feed_data


# ─────────────────────────────────────────────────────────────
# P2.6.5: ERP Feed Converters
# ─────────────────────────────────────────────────────────────

def _convert_to_wangdiantong(feed_data: dict, products: list) -> dict:
    """Convert standard feed to 旺店通 ERP goods import format.

    旺店通商品导入 JSON 格式:
    - spec_no: 商家编码
    - goods_no: 货号
    - goods_name: 货品名称
    - retail_price: 零售价
    - market_price: 市场价
    - brand_name: 品牌
    - class_name: 分类
    - remark: 备注
    """
    wdt_items = []
    for p in products:
        wdt_items.append({
            "spec_no": f"ORI-{(p.category or 'ITEM').upper()}-{p.id[:8]}",
            "goods_no": f"ORI-{p.id[:12]}",
            "goods_name": p.title[:200],
            "goods_type": 1,  # 1=成品
            "retail_price": p.price,
            "market_price": p.price,
            "brand_name": "OriStudio",
            "class_name": p.category or "未分类",
            "remark": (p.description or "")[:500],
            "barcode": "",
            "weight": getattr(p, 'weight_grams', None) or 0,
            "is_valid": 1,
            "modified": datetime.utcnow().isoformat(),
        })

    return {
        "feed": feed_data.get("feed", {}),
        "products": wdt_items,
        "erp_config": {
            "format": "wangdiantong",
            "fields_mapping": {
                "spec_no": "商家编码",
                "goods_no": "货号",
                "goods_name": "货品名称",
                "retail_price": "零售价",
                "brand_name": "品牌",
                "class_name": "分类",
            },
        },
    }


def _convert_to_jushuitan(feed_data: dict, products: list) -> dict:
    """Convert standard feed to 聚水潭 ERP product import format.

    聚水潭商品导入 JSON 格式:
    - sku_id: 商品编码
    - name: 商品名称
    - sale_price: 单价
    - short_name: 简称
    - category: 分类
    - brand: 品牌
    - remark: 备注
    """
    jst_items = []
    for p in products:
        jst_items.append({
            "sku_id": f"ORI-{(p.category or 'ITEM').upper()}-{p.id[:8]}",
            "i_id": f"ORI-{p.id[:12]}",
            "name": p.title[:200],
            "sale_price": p.price,
            "cost_price": getattr(p, 'cost', 0) or 0,
            "short_name": (p.title[:50] if p.title else ""),
            "category": p.category or "未分类",
            "brand": "OriStudio",
            "remark": (p.description or "")[:500],
            "pic": (p.images[0] if isinstance(p.images, list) and p.images else ""),
            "pic_big": "",
            "weight": getattr(p, 'weight_grams', None) or 0,
            "enabled": True,
            "modified": datetime.utcnow().isoformat(),
        })

    return {
        "feed": feed_data.get("feed", {}),
        "products": jst_items,
        "erp_config": {
            "format": "jushuitan",
            "fields_mapping": {
                "sku_id": "商品编码",
                "i_id": "款式编码",
                "name": "商品名称",
                "sale_price": "单价",
                "category": "分类",
                "brand": "品牌",
            },
        },
    }


def _convert_to_wanliuniu(feed_data: dict, products: list) -> dict:
    """Convert standard feed to 万里牛 ERP product import format. — P2.6.5

    万里牛（hupun.com）商品导入 JSON 格式:
    - item_code: 商家编码
    - goods_code: 货号
    - goods_name: 货品名称
    - goods_type: 货品类型
    - sale_price: 销售价
    - purchase_price: 采购价
    - category_name: 分类名称
    - brand_name: 品牌
    - remark: 备注
    - weight: 重量(g)
    - item_size: 规格尺寸
    - unit_name: 单位
    - unit_code: 单位编码
    """
    wln_items = []
    for p in products:
        wln_items.append({
            "item_code": f"ORI-{(p.category or 'ITEM').upper()}-{p.id[:8]}",
            "goods_code": f"G-ORI-{p.id[:12]}",
            "goods_name": p.title[:200],
            "goods_type": "成品",
            "sale_price": p.price,
            "purchase_price": getattr(p, 'cost', 0) or 0,
            "market_price": p.price,
            "category_name": p.category or "未分类",
            "brand_name": "OriStudio",
            "remark": (p.description or "")[:500],
            "weight": getattr(p, 'weight_grams', None) or 0,
            "item_size": "",
            "unit_name": "件",
            "unit_code": "PCS",
            "is_enabled": True,
            "modified": datetime.utcnow().isoformat(),
        })

    return {
        "feed": feed_data.get("feed", {}),
        "products": wln_items,
        "erp_config": {
            "format": "wanliuniu",
            "vendor": "万里牛 (hupun.com)",
            "api_version": "v2",
            "fields_mapping": {
                "item_code": "商家编码",
                "goods_code": "货号",
                "goods_name": "货品名称",
                "goods_type": "货品类型",
                "sale_price": "销售价",
                "purchase_price": "采购价",
                "category_name": "分类名称",
                "brand_name": "品牌",
                "remark": "备注",
                "weight": "重量(g)",
                "unit_name": "单位",
            },
            "integration_note": "万里牛 ERP 通过 HTTP POST /open/api/goods/batch_import 进行批量导入",
        },
    }


# ─────────────────────────────────────────────────────────────
# MCP HTTP Transport Endpoints
# ─────────────────────────────────────────────────────────────

@router.post("/mcp")
async def mcp_endpoint(request: Request, db: Session = Depends(get_db)):
    """MCP JSON-RPC 2.0 over HTTP endpoint.

    Supports: initialize, tools/list, tools/call, notifications/initialized.
    """
    # Auth + rate limiting
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Bearer token required")

    api_key = auth[7:].strip()
    key_info = MCP_API_KEYS.get(api_key)
    if not key_info:
        raise HTTPException(status_code=403, detail="Invalid MCP API key")

    if not check_rate_limit(key_info["name"], key_info["rate_limit"]):
        raise HTTPException(status_code=429, detail="Rate limit exceeded")

    try:
        body = await request.json()
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON body")

    # Validate JSON-RPC structure
    jsonrpc = body.get("jsonrpc", "")
    if jsonrpc != "2.0":
        raise HTTPException(status_code=400, detail="Only JSON-RPC 2.0 is supported")

    method = body.get("method", "")
    req_id = body.get("id")
    params = body.get("params", {})

    # Route to handler
    if method == "initialize":
        result = {
            "protocolVersion": MCP_VERSION,
            "capabilities": {
                "tools": {},
            },
            "serverInfo": {
                "name": SERVER_NAME,
                "version": SERVER_VERSION,
            },
        }
    elif method == "tools/list":
        result = _handle_tools_list()
    elif method == "tools/call":
        tool_name = params.get("name", "")
        tool_args = params.get("arguments", {})
        result = _handle_tools_call(tool_name, tool_args, db)
    elif method == "notifications/initialized":
        result = {}
    else:
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "error": {"code": -32601, "message": f"Method not found: {method}"},
        }

    return {"jsonrpc": "2.0", "id": req_id, "result": result}


@router.get("/mcp")
def mcp_info():
    """MCP server information (GET for discovery)."""
    return {
        "protocol": "mcp",
        "version": MCP_VERSION,
        "server": SERVER_NAME,
        "server_version": SERVER_VERSION,
        "tools_count": len(TOOL_DEFINITIONS),
        "tools": [
            {"name": t["name"], "description": t["description"]}
            for t in TOOL_DEFINITIONS
        ],
        "transport": "HTTP JSON-RPC 2.0",
        "authentication": "Bearer API Key required",
        "documentation": "POST /mcp with JSON-RPC 2.0 requests",
    }
