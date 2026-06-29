"""P1.6 产品数据中心 (PDH) API 测试."""

import io
import json


# ──────────────────────────────────────────────
# AI 描述风格引擎 (P1.6.1)
# ──────────────────────────────────────────────

def test_describe_styles(client):
    """测试获取支持的 AI 描述风格列表."""
    resp = client.get("/api/publish/describe/styles")
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert isinstance(data["data"], list)
    assert len(data["data"]) >= 6  # 6种风格
    styles = {s["key"] for s in data["data"]}
    assert "xiaohongshu" in styles
    assert "taobao" in styles
    assert "douyin" in styles
    assert "shopify" in styles
    assert "etsy" in styles
    assert "kickstarter" in styles


def test_describe_with_style(client):
    """测试使用指定风格生成 AI 描述 (模板回退)."""
    # 先创建商品
    resp = client.post("/api/publish/products", json={
        "title": "AI描述测试商品",
        "description": "这是一个测试商品",
        "price": 99.0,
        "category": "t_shirt",
    })
    assert resp.status_code == 200
    product_id = resp.json()["data"]["id"]

    # 测试小红书风格
    resp = client.post(
        f"/api/publish/products/{product_id}/describe",
        json={"style": "xiaohongshu"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert data["data"]["style"] == "xiaohongshu"
    assert data["data"]["style_name"] == "小红书"
    assert "description" in data["data"]
    # 模板回退包含标记
    assert "本地模板" in data["data"]["description"]
    assert data["data"]["source"] == "template"


def test_describe_with_shopify_style(client):
    """测试 Shopify 英文风格."""
    resp = client.post("/api/publish/products", json={
        "title": "Shopify Test Product",
        "price": 49.0,
        "category": "poster",
    })
    assert resp.status_code == 200
    product_id = resp.json()["data"]["id"]

    resp = client.post(
        f"/api/publish/products/{product_id}/describe",
        json={"style": "shopify"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["data"]["style"] == "shopify"
    assert "Template" in data["data"]["description"]  # English template


def test_describe_invalid_style(client):
    """测试无效风格返回400."""
    resp = client.post("/api/publish/products", json={
        "title": "无效风格测试",
        "price": 10.0,
        "category": "mug",
    })
    product_id = resp.json()["data"]["id"]

    resp = client.post(
        f"/api/publish/products/{product_id}/describe",
        json={"style": "invalid_style"},
    )
    assert resp.status_code == 400
    assert "不支持的风格" in resp.json()["detail"]


# ──────────────────────────────────────────────
# Verified 徽章 (P1.6.3)
# ──────────────────────────────────────────────

def test_generate_verified_badge(client):
    """测试生成 Verified 徽章."""
    resp = client.post("/api/publish/products", json={
        "title": "徽章测试商品",
        "price": 88.0,
        "category": "sticker",
    })
    assert resp.status_code == 200
    product_id = resp.json()["data"]["id"]

    resp = client.post(f"/api/publish/products/{product_id}/verified-badge")
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    result = data["data"]
    assert "verify_url" in result
    assert "badge_svg" in result
    assert "badge_png_b64" in result
    assert "embed_code" in result
    assert "cert_id" in result["verify_url"]
    # SVG badge should contain product title
    assert "徽章测试商品" in result["badge_svg"]


def test_verified_badge_embed(client):
    """测试获取嵌入代码."""
    resp = client.post("/api/publish/products", json={
        "title": "嵌入代码测试",
        "price": 66.0,
        "category": "poster",
    })
    assert resp.status_code == 200
    product_id = resp.json()["data"]["id"]

    # 先生成徽章
    client.post(f"/api/publish/products/{product_id}/verified-badge")

    # 获取嵌入代码
    resp = client.get(f"/api/publish/verified-mark/{product_id}/embed")
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    embed = data["data"]
    assert "html" in embed
    assert "js" in embed
    assert "verify_url" in embed
    assert "OriStudio Verified" in embed["html"]


def test_verified_badge_nonexistent_product(client):
    """测试不存在的产品返回404."""
    resp = client.post("/api/publish/products/nonexistent_id/verified-badge")
    assert resp.status_code == 404


# ──────────────────────────────────────────────
# JSON Product Feed (P1.6.5-P1.6.7)
# ──────────────────────────────────────────────

def test_feed_schema(client):
    """测试获取 Feed Schema 定义."""
    resp = client.get("/api/publish/feed/schema")
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert data["data"]["version"] == "1.0"
    assert "fields" in data["data"]


def test_feed_platforms(client):
    """测试获取支持的 Feed 平台列表."""
    resp = client.get("/api/publish/feed/platforms")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data["data"], list)
    platforms = {p["key"] for p in data["data"]}
    assert "universal" in platforms
    assert "google" in platforms
    assert "shopify" in platforms


def test_feed_empty(client):
    """测试 Feed 基本结构."""
    resp = client.get("/api/publish/feed")
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert data["data"]["feed"]["version"] == "1.0"
    assert data["data"]["feed"]["total_products"] >= 0
    assert isinstance(data["data"]["products"], list)


def test_feed_with_products(client):
    """测试有产品时生成 Feed."""
    # 创建2个产品
    for i in range(2):
        resp = client.post("/api/publish/products", json={
            "title": f"Feed测试商品{i}",
            "description": f"这是测试商品{i}",
            "price": 99.0 + i * 10,
            "category": "mug",
            "images": [f"/api/files/test_img_{i}.jpg"],
        })
        assert resp.status_code == 200

    resp = client.get("/api/publish/feed")
    assert resp.status_code == 200
    data = resp.json()
    assert data["data"]["feed"]["total_products"] >= 2
    products = data["data"]["products"]
    assert len(products) >= 2

    # 验证 Feed Item 结构
    item = products[0]
    assert "id" in item
    assert "sku" in item
    assert "title" in item
    assert "pricing" in item
    assert "media" in item
    assert "certification" in item


def test_feed_filter_by_category(client):
    """测试按品类过滤 Feed."""
    # 创建不同品类的产品
    client.post("/api/publish/products", json={
        "title": "T恤产品", "price": 129.0, "category": "t_shirt",
    })
    client.post("/api/publish/products", json={
        "title": "杯子产品", "price": 49.0, "category": "mug",
    })

    resp = client.get("/api/publish/feed", params={"category": "t_shirt"})
    assert resp.status_code == 200
    data = resp.json()
    for p in data["data"]["products"]:
        assert p["category"] == "t_shirt"


def test_feed_export_google(client):
    """测试 Google Merchant Center 格式导出."""
    resp = client.post("/api/publish/products", json={
        "title": "Google导出测试",
        "price": 199.0,
        "category": "poster",
    })
    assert resp.status_code == 200

    resp = client.get("/api/publish/feed/export", params={"platform": "google"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["data"]["feed"]["target"] == "google_merchant_center"
    products = data["data"]["products"]
    if products:
        p = products[0]
        assert "offerId" in p
        assert "price" in p
        assert "brand" in p
        assert p["brand"] == "OriStudio"


def test_feed_export_shopify(client):
    """测试 Shopify 格式导出."""
    resp = client.post("/api/publish/products", json={
        "title": "Shopify导出测试",
        "price": 149.0,
        "category": "sticker",
    })
    assert resp.status_code == 200

    resp = client.get("/api/publish/feed/export", params={"platform": "shopify"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["data"]["feed"]["target"] == "shopify"
    products = data["data"]["products"]
    if products:
        p = products[0]
        assert "variants" in p
        assert "body_html" in p


def test_feed_export_invalid_platform(client):
    """测试无效平台返回400."""
    resp = client.get("/api/publish/feed/export", params={"platform": "invalid"})
    assert resp.status_code == 400


# ──────────────────────────────────────────────
# 收入追踪增强 (P1.6.9-P1.6.11)
# ──────────────────────────────────────────────

def test_revenue_summary(client):
    """测试收入汇总."""
    from datetime import date

    # 添加当月测试数据
    test_platforms = ["taobao", "douyin", "etsy"]
    for platform, amount in zip(test_platforms, [1000, 500, 300]):
        client.post("/api/publish/revenue", json={
            "platform": platform,
            "amount": amount,
            "date": date.today().isoformat(),
            "order_count": 2,
        })

    resp = client.get("/api/publish/revenue/summary", params={"period": "month"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    summary = data["data"]
    assert "total_amount" in summary
    assert "total_orders" in summary
    assert "by_platform" in summary
    assert "by_product" in summary
    assert "monthly_trend" in summary
    # Check at least our 3 platforms plus anything from other tests
    assert len(summary["by_platform"]) >= 1


def test_revenue_summary_year(client):
    """测试年度收入汇总."""
    resp = client.get("/api/publish/revenue/summary", params={"period": "year"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["data"]["period"] == "year"


def test_revenue_import_csv(client):
    """测试 CSV 导入收入记录."""
    csv_content = "platform,amount,date,order_count,notes\ntaobao,500,2026-06-01,3,测试订单1\ndouyin,300,2026-06-02,2,测试订单2\n"
    csv_file = io.BytesIO(csv_content.encode("utf-8-sig"))
    csv_file.name = "test_import.csv"  # io.BytesIO has no name attr, but UploadFile will handle it

    # FastAPI TestClient with files
    resp = client.post(
        "/api/publish/revenue/import",
        files={"file": ("test_revenue_import.csv", csv_content.encode("utf-8-sig"), "text/csv")},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert data["data"]["imported"] == 2
    assert data["data"]["total_amount"] == 800.0


def test_revenue_import_taobao_csv(client):
    """测试淘宝格式 CSV 导入."""
    csv_content = "商品名称,订单金额,订单创建时间,商品id,订单数\n测试商品,299.00,2026-06-01,item123,1\n"
    resp = client.post(
        "/api/publish/revenue/import",
        files={"file": ("taobao_import.csv", csv_content.encode("utf-8-sig"), "text/csv")},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["data"]["detected_format"] == "taobao"
    assert data["data"]["imported"] >= 1


def test_revenue_import_invalid_file(client):
    """测试非CSV文件导入返回400."""
    resp = client.post(
        "/api/publish/revenue/import",
        files={"file": ("test.txt", b"not csv", "text/plain")},
    )
    assert resp.status_code == 400


# ──────────────────────────────────────────────
# 现有端点回归测试
# ──────────────────────────────────────────────

def test_list_products(client):
    """测试获取商品列表."""
    resp = client.get("/api/publish/products")
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert isinstance(data["data"], list)


def test_create_product(client):
    """测试创建商品."""
    resp = client.post("/api/publish/products", json={
        "title": "回归测试商品",
        "price": 128.0,
        "category": "mug",
    })
    assert resp.status_code == 200
    assert resp.json()["data"]["id"]


def test_export_csv(client):
    """测试 CSV 导出."""
    resp = client.post("/api/publish/products", json={
        "title": "导出测试商品",
        "price": 79.0,
        "category": "sticker",
    })
    product_id = resp.json()["data"]["id"]

    resp = client.get(f"/api/publish/export/{product_id}", params={"platform": "taobao"})
    assert resp.status_code == 200
    data = resp.json()
    assert "csv_content" in data["data"]


def test_publish_product(client):
    """测试发布产品."""
    resp = client.post("/api/publish/products", json={
        "title": "发布测试商品",
        "price": 199.0,
    })
    product_id = resp.json()["data"]["id"]

    resp = client.post(f"/api/publish/publish/{product_id}", params={"platform": "shopify"})
    assert resp.status_code == 200
    data = resp.json()
    assert "已标记发布" in data["message"]


def test_add_and_list_revenue(client):
    """测试添加和列出收入记录."""
    resp = client.post("/api/publish/revenue", json={
        "platform": "taobao",
        "amount": 500.0,
        "date": "2026-06-01",
        "order_count": 3,
        "notes": "测试收入",
    })
    assert resp.status_code == 200

    resp = client.get("/api/publish/revenue")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data["data"], list)


def test_get_platforms(client):
    """测试获取平台列表."""
    resp = client.get("/api/publish/platforms")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data["data"], list)
    assert len(data["data"]) >= 4