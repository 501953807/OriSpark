"""P1.6.5-P1.6.7 — JSON Product Feed 服务.

提供:
- 标准 JSON Product Feed (Schema 1.0)
- Google Merchant Center 转换器
- Shopify 转换器
"""

from datetime import datetime, timezone


class JsonFeedService:
    """JSON Product Feed 生成器和平台转换器."""

    @staticmethod
    def schema_definition() -> dict:
        """返回 JSON Feed Schema 1.0 定义."""
        return {
            "schema": "https://json-schema.org/draft/2020-12/schema",
            "title": "OriStudio Product Feed",
            "version": "1.0",
            "description": "标准产品数据导出格式，兼容 Google Merchant Center / Shopify / 主流ERP",
            "fields": {
                "id": "产品唯一ID",
                "sku": "SKU (自动生成: ORI-{category}-{sequence})",
                "title": "产品标题 (max 150 chars)",
                "subtitle": "副标题/卖点",
                "description": "产品描述 (max 5000 chars)",
                "ai_description": "AI 生成的营销描述",
                "product_type": "physical / digital",
                "category": "产品品类",
                "tags": "标签数组",
                "media": {
                    "main_image": "主图 {url, width, height, alt_text}",
                    "additional_images": "附加图片数组",
                    "videos": "视频数组 {url, thumbnail_url, duration_seconds, type}",
                    "design_file": "原始设计稿 {url, format, dpi}",
                },
                "pricing": {
                    "price": "价格",
                    "currency": "币种 (默认 CNY)",
                    "sale_price": "促销价",
                    "cost": "成本",
                    "margin_percent": "利润率",
                },
                "variants": "规格变体数组 [{sku, title, price_adjustment, attributes}]",
                "inventory": "库存 {quantity, availability}",
                "shipping": "物流 {weight_grams, dimensions_mm}",
                "licensing": "许可 {license_type, attribution_text, restrictions}",
                "certification": "存证信息 {sha256, notary_platform, certificate_url, verified_mark_url, ...}",
                "trademark": "商标 {registration_no, jurisdiction, classes}",
                "copyright": "版权 {registration_no, jurisdiction, author, year}",
                "publish_info": "发布信息 {platforms: [{platform, listing_url, status, published_at}]}",
            },
        }

    @staticmethod
    def supported_platforms() -> list:
        """返回支持的导出平台列表."""
        return [
            {
                "key": "universal",
                "name": "通用格式",
                "description": "标准 OriStudio JSON Product Feed (Schema 1.0)",
                "formats": ["json"],
            },
            {
                "key": "google",
                "name": "Google Merchant Center",
                "description": "Google Merchant Center Product Input schema",
                "formats": ["json"],
            },
            {
                "key": "shopify",
                "name": "Shopify",
                "description": "Shopify REST Admin API product object",
                "formats": ["json"],
            },
            {
                "key": "wangdiantong",
                "name": "旺店通",
                "description": "旺店通货品导入 JSON 格式 (计划中)",
                "formats": ["json"],
                "status": "planned",
            },
            {
                "key": "jushuitan",
                "name": "聚水潭",
                "description": "聚水潭商品导入 JSON 格式 (计划中)",
                "formats": ["json"],
                "status": "planned",
            },
        ]

    def generate_feed(self, products: list) -> dict:
        """从产品列表生成标准 JSON Product Feed.

        Args:
            products: SQLAlchemy Product 对象列表

        Returns:
            dict: {feed: {...}, products: [...]}
        """
        now = datetime.now(timezone.utc).isoformat()

        product_items = []
        for p in products:
            item = self._product_to_item(p)
            product_items.append(item)

        return {
            "feed": {
                "version": "1.0",
                "generated_at": now,
                "generated_by": "OriStudio PDH",
                "total_products": len(product_items),
            },
            "products": product_items,
        }

    def _product_to_item(self, product) -> dict:
        """将单个 Product 转换为 Feed Item."""
        # 构建 SKU
        sku = getattr(product, 'sku', None) or f"ORI-{(product.category or 'ITEM').upper()}-{product.id[:8]}"

        # 构建媒体对象
        images = getattr(product, 'images', None) or []
        media = {
            "main_image": None,
            "additional_images": [],
            "videos": [],
            "design_file": None,
        }

        if isinstance(images, list) and len(images) > 0:
            media["main_image"] = {
                "url": images[0] if isinstance(images[0], str) else str(images[0]),
                "width": 2000,
                "height": 2000,
                "alt_text": product.title,
            }
            for img_path in images[1:]:
                media["additional_images"].append({
                    "url": img_path if isinstance(img_path, str) else str(img_path),
                    "width": 2000,
                    "height": 2000,
                    "type": "detail",
                })
        elif isinstance(images, str) and images:
            media["main_image"] = {
                "url": images,
                "width": 2000,
                "height": 2000,
                "alt_text": product.title,
            }

        # 构建定价
        sale_price = getattr(product, 'sale_price', None)
        cost = getattr(product, 'cost', None)
        margin = None
        if cost and product.price:
            margin = round((product.price - cost) / product.price * 100, 1)

        pricing = {
            "price": product.price,
            "currency": getattr(product, 'currency', 'CNY') or "CNY",
        }
        if sale_price:
            pricing["sale_price"] = sale_price
        if cost:
            pricing["cost"] = cost
        if margin is not None:
            pricing["margin_percent"] = margin

        # 构建规格变体
        specifications = getattr(product, 'specifications', None)
        variants = getattr(product, 'variants', None)
        if variants is None and specifications:
            # 将旧版 specifications JSON 转换为变体格式
            variants = _convert_specs_to_variants(specifications, sku)

        # 构建认证信息
        certification = {
            "verified_mark_url": f"https://oristudio.local/api/publish/verified-mark/{product.id}/embed",
            "verification_page_url": f"https://oristudio.local/verify?cert_id=cert_{product.id[:12]}",
        }

        item = {
            "id": product.id,
            "sku": sku,
            "title": product.title,
            "subtitle": getattr(product, 'subtitle', None),
            "description": product.description or "",
            "ai_description": getattr(product, 'ai_description', None),
            "product_type": getattr(product, 'product_type', 'physical') or "physical",
            "category": product.category or "",
            "tags": ["原创", product.category] if product.category else ["原创"],
            "media": media,
            "pricing": pricing,
            "variants": variants or [],
            "inventory": {
                "quantity": getattr(product, 'quantity', 0) or 0,
                "availability": "in_stock",
            },
            "shipping": _get_shipping_info(product),
            "licensing": {
                "license_type": "all_rights_reserved",
                "attribution_text": f"© {product.title}",
                "restrictions": ["no_reproduction"],
            },
            "certification": certification,
            "publish_info": _get_publish_info(product),
            "created_at": product.created_at.isoformat() if product.created_at else None,
            "updated_at": product.updated_at.isoformat() if product.updated_at else None,
        }

        return item

    def convert_to_google(self, feed_data: dict) -> dict:
        """将标准 Feed 转换为 Google Merchant Center 格式.

        映射到 Merchant Center ProductInput schema.
        """
        google_products = []
        for p in feed_data.get("products", []):
            pricing = p.get("pricing", {})
            media = p.get("media", {})

            google_item = {
                "offerId": p.get("sku", p.get("id", "")),
                "title": p.get("title", "")[:150],
                "description": (p.get("ai_description") or p.get("description", ""))[:5000],
                "link": p.get("publish_info", {}).get("platforms", [{}])[0].get("listing_url", "") if p.get("publish_info", {}).get("platforms") else "",
                "imageLink": media.get("main_image", {}).get("url", "") if media.get("main_image") else "",
                "additionalImageLinks": [
                    img.get("url", "") for img in media.get("additional_images", [])
                ],
                "price": {
                    "value": str(pricing.get("price", 0)),
                    "currency": pricing.get("currency", "CNY"),
                },
                "availability": p.get("inventory", {}).get("availability", "in_stock"),
                "brand": "OriStudio",
                "condition": "new",
                "gtin": "",  # 如有关联
                "productTypes": [p.get("category", "")],
                "customLabels": [
                    {"name": "oristudio_product_id", "value": p.get("id", "")},
                    {"name": "oristudio_verified", "value": "true" if p.get("certification") else "false"},
                ],
            }

            # 促销价
            if pricing.get("sale_price"):
                google_item["salePrice"] = {
                    "value": str(pricing["sale_price"]),
                    "currency": pricing.get("currency", "CNY"),
                }

            # 物流
            shipping = p.get("shipping", {})
            if shipping.get("weight_grams"):
                google_item["shippingWeight"] = {
                    "value": shipping["weight_grams"],
                    "unit": "g",
                }

            google_products.append(google_item)

        return {
            "feed": {
                **feed_data.get("feed", {}),
                "target": "google_merchant_center",
                "schema": "Merchant Center ProductInput",
            },
            "products": google_products,
        }

    def convert_to_shopify(self, feed_data: dict) -> dict:
        """将标准 Feed 转换为 Shopify REST Admin API 格式."""
        shopify_products = []
        for p in feed_data.get("products", []):
            pricing = p.get("pricing", {})
            media = p.get("media", {})
            variants = p.get("variants", [])

            # 转换变体为 Shopify format
            shopify_variants = []
            if variants:
                for v in variants:
                    shopify_variants.append({
                        "sku": v.get("sku", ""),
                        "title": v.get("title", "Default Title"),
                        "price": str(pricing.get("price", 0) + v.get("price_adjustment", 0)),
                        "inventory_quantity": p.get("inventory", {}).get("quantity", 0),
                        "requires_shipping": p.get("product_type", "physical") == "physical",
                    })
            else:
                shopify_variants.append({
                    "sku": p.get("sku", ""),
                    "title": "Default Title",
                    "price": str(pricing.get("price", 0)),
                    "inventory_quantity": p.get("inventory", {}).get("quantity", 0),
                    "requires_shipping": True,
                })

            # 转换 images
            shopify_images = []
            if media.get("main_image"):
                shopify_images.append({"src": media["main_image"].get("url", "")})
            for img in media.get("additional_images", []):
                shopify_images.append({"src": img.get("url", "")})

            shopify_item = {
                "title": p.get("title", "")[:255],
                "body_html": f"<p>{p.get('ai_description') or p.get('description', '')}</p>",
                "vendor": "OriStudio",
                "product_type": p.get("category", ""),
                "tags": ", ".join(p.get("tags", [])),
                "variants": shopify_variants,
                "images": shopify_images,
                "status": "draft",
                "metafields_global_title_tag": p.get("title", ""),
                "metafields_global_description_tag": (p.get("description") or "")[:320],
            }

            # OriStudio 自定义 metafields
            if p.get("certification"):
                shopify_item["metafields"] = [
                    {
                        "namespace": "oristudio",
                        "key": "verified",
                        "value": "true",
                        "type": "boolean",
                    },
                    {
                        "namespace": "oristudio",
                        "key": "product_id",
                        "value": p.get("id", ""),
                        "type": "single_line_text_field",
                    },
                ]

            shopify_products.append(shopify_item)

        return {
            "feed": {
                **feed_data.get("feed", {}),
                "target": "shopify",
                "schema": "Shopify REST Admin API Product",
            },
            "products": shopify_products,
        }


def _convert_specs_to_variants(specifications, base_sku: str) -> list:
    """将旧版 specifications JSON 转换为变体列表."""
    if not specifications:
        return []

    variants = []
    if isinstance(specifications, dict):
        # 查找可能是变体的键 (size, color, style等)
        variant_keys = {"size", "sizes", "color", "colors", "style", "styles", "规格", "型号", "尺码", "颜色"}
        for key, value in specifications.items():
            if key.lower() in variant_keys:
                values = value if isinstance(value, list) else [value]
                for i, v in enumerate(values):
                    variants.append({
                        "sku": f"{base_sku}-{str(v).upper()[:8]}",
                        "title": str(v),
                        "price_adjustment": 0,
                        "attributes": {key: str(v)},
                    })
                break

    if not variants:
        variants.append({
            "sku": base_sku,
            "title": "默认",
            "price_adjustment": 0,
            "attributes": specifications if isinstance(specifications, dict) else {"spec": str(specifications)},
        })

    return variants


def _get_shipping_info(product) -> dict:
    """获取物流信息."""
    weight = getattr(product, 'weight_grams', None)
    dimensions = getattr(product, 'dimensions_mm', None)

    shipping = {}
    if weight:
        shipping["weight_grams"] = weight
    if dimensions:
        shipping["dimensions_mm"] = dimensions

    return shipping


def _get_publish_info(product) -> dict:
    """获取发布状态信息."""
    publishings = getattr(product, 'publishings', None) or []
    platforms = []
    for pub in publishings:
        platforms.append({
            "platform": pub.platform if hasattr(pub, 'platform') else "unknown",
            "listing_url": pub.listing_url if hasattr(pub, 'listing_url') else "",
            "status": pub.status if hasattr(pub, 'status') else "draft",
            "published_at": pub.published_at.isoformat() if hasattr(pub, 'published_at') and pub.published_at else None,
        })

    return {"platforms": platforms} if platforms else {"platforms": []}