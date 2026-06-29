"""P2.5 变现引擎深度集成测试."""

import pytest


# ═══════════════════════════════════════════════════════════════════
# P2.5.1-P2.5.2: POD 平台发布
# ═══════════════════════════════════════════════════════════════════

class TestPublishToPod:
    """POD 平台发布端点测试."""

    def test_publish_printful_mock(self, client):
        """Printful mock 发布."""
        resp = client.post("/api/supply/publish-to-pod", json={
            "platform": "printful",
            "product_data": {"title": "Test T-Shirt", "category": "t_shirt", "price": 29.99},
            "action": "publish",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert data["data"]["platform"] == "printful"
        assert data["data"]["result"]["status"] in ("draft", "error")

    def test_publish_redbubble_mock(self, client):
        """Redbubble mock 上传."""
        resp = client.post("/api/supply/publish-to-pod", json={
            "platform": "redbubble",
            "product_data": {"title": "Test Design", "tags": ["art", "illustration"]},
            "action": "publish",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert data["data"]["platform"] == "redbubble"

    def test_publish_chinese_pod(self, client):
        """中国 POD 平台查询."""
        for plat in ["yingge", "yunda", "dingzhilian", "shanyin"]:
            resp = client.post("/api/supply/publish-to-pod", json={
                "platform": plat,
                "product_data": {"title": "Test", "category": "t_shirt"},
                "action": "publish",
            })
            assert resp.status_code == 200
            assert resp.json()["data"]["platform"] == plat
            assert "platform_info" in resp.json()["data"]

    def test_publish_invalid_platform(self, client):
        """无效平台报错."""
        resp = client.post("/api/supply/publish-to-pod", json={
            "platform": "nonexistent",
            "product_data": {"title": "Test"},
            "action": "publish",
        })
        assert resp.status_code == 400

    def test_printful_cost_estimate(self, client):
        """Printful 运费估算."""
        resp = client.post("/api/supply/publish-to-pod", json={
            "platform": "printful",
            "product_data": {"platform_product_id": "mock", "country_code": "CN"},
            "action": "cost_estimate",
        })
        assert resp.status_code == 200
        assert "rates" in resp.json()["data"]["result"]

    def test_redbubble_csv_template(self, client):
        """Redbubble CSV 模板生成."""
        resp = client.post("/api/supply/publish-to-pod", json={
            "platform": "redbubble",
            "product_data": {
                "designs": [
                    {"title": "Design 1", "tags": ["art"], "description": "A test", "image_url": "http://example.com/1.png"},
                ],
            },
            "action": "csv_template",
        })
        assert resp.status_code == 200
        assert "csv_content" in resp.json()["data"]


# ═══════════════════════════════════════════════════════════════════
# P2.5.13: 中国 POD 平台模板
# ═══════════════════════════════════════════════════════════════════

class TestChinesePodPlatforms:
    """中国 POD 平台端点测试."""

    def test_list_platforms(self, client):
        """列出所有中国 POD 平台."""
        resp = client.get("/api/supply/chinese-pod-platforms")
        assert resp.status_code == 200
        data = resp.json()
        platforms = data["data"]
        assert len(platforms) == 4
        platform_ids = [p["id"] for p in platforms]
        assert "yingge" in platform_ids
        assert "yunda" in platform_ids
        assert "dingzhilian" in platform_ids
        assert "shanyin" in platform_ids

    def test_get_platform_detail(self, client):
        """获取单个平台详情."""
        resp = client.get("/api/supply/chinese-pod-platforms/yingge")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["platform"]["name"] == "印鸽"
        assert "t_shirt" in data["categories"]
        assert "default_dpi" in data["specs"]

    def test_platform_detail_404(self, client):
        """未知平台返回 404."""
        resp = client.get("/api/supply/chinese-pod-platforms/unknown")
        assert resp.status_code == 404


# ═══════════════════════════════════════════════════════════════════
# P2.5.3-P2.5.4: 众筹管理增强
# ═══════════════════════════════════════════════════════════════════

class TestCampaignEnhancements:
    """众筹增强功能测试."""

    def _create_campaign(self, client):
        """Helper: 创建测试众筹."""
        resp = client.post("/api/supply/campaigns", json={
            "title": "Test Campaign",
            "platform": "kickstarter",
            "goal_amount": 10000,
            "currency": "CNY",
            "raised_amount": 5000,
            "backer_count": 100,
            "reward_tiers": [
                {"name": "Early Bird", "price": 49, "limit": 200, "sold": 80},
                {"name": "Standard", "price": 99, "limit": 100, "sold": 25},
                {"name": "Deluxe", "price": 199, "limit": 50, "sold": 5},
            ],
        })
        assert resp.status_code == 200
        return resp.json()["data"]["id"]

    def test_campaign_report(self, client):
        """众筹项目报表导出."""
        cid = self._create_campaign(client)
        resp = client.get(f"/api/supply/campaigns/{cid}/report")
        assert resp.status_code == 200
        report = resp.json()["data"]
        assert report["campaign"]["title"] == "Test Campaign"
        assert report["funding"]["goal_amount"] == 10000
        assert report["funding"]["raised_amount"] == 5000
        assert len(report["reward_tiers"]) == 3
        # Check tier stats
        tiers = report["reward_tiers"]
        assert tiers[0]["sold"] == 80
        assert tiers[0]["revenue"] == 80 * 49
        assert tiers[2]["sold_out"] is False  # 5 < 50

    def test_reward_templates(self, client):
        """奖励档位模板列表."""
        resp = client.get("/api/supply/campaigns/reward-templates")
        assert resp.status_code == 200
        templates = resp.json()["data"]
        assert len(templates) >= 5
        assert any(t["id"] == "rt_basic_3" for t in templates)
        assert any(t["id"] == "rt_pod" for t in templates)

    def test_calculate_funding_goal(self, client):
        """计算建议众筹目标."""
        resp = client.post("/api/supply/campaigns/calculate-goal", json={
            "tiers": [
                {"name": "Early", "price": 49, "estimated_backers": 100},
                {"name": "Standard", "price": 99, "estimated_backers": 50},
            ],
            "manufacturing_cost": 3000,
            "shipping_cost": 1000,
            "platform_fee_pct": 8.0,
            "buffer_pct": 15.0,
        })
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["total_estimated_revenue"] == 49 * 100 + 99 * 50
        assert data["suggested_goal"] > 0
        assert len(data["tier_projection"]) == 2

    def test_campaign_report_404(self, client):
        """不存在的众筹返回 404."""
        resp = client.get("/api/supply/campaigns/nonexistent/report")
        assert resp.status_code == 404


# ═══════════════════════════════════════════════════════════════════
# P2.5.5-P2.5.6: IP 授权市场格式导出
# ═══════════════════════════════════════════════════════════════════

class TestLicenseExport:
    """授权导出测试."""

    def _create_license(self, client):
        """Helper: 创建测试授权."""
        resp = client.post("/api/supply/licenses", json={
            "work_id": None,
            "license_type": "commercial_extended",
            "platform": "creative_market",
            "allowed_uses": ["commercial", "resale", "modification"],
            "restrictions": [],
            "price": 199,
        })
        assert resp.status_code == 200
        return resp.json()["data"]["id"]

    def test_export_creative_fabrica(self, client):
        """导出为 Creative Fabrica 格式."""
        lid = self._create_license(client)
        resp = client.get(f"/api/supply/licenses/{lid}/export?format=creative_fabrica")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["format"] == "creative_fabrica"
        assert data["listing_data"]["license_type"] == "Commercial"

    def test_export_creative_market(self, client):
        """导出为 Creative Market 格式."""
        lid = self._create_license(client)
        resp = client.get(f"/api/supply/licenses/{lid}/export?format=creative_market")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["format"] == "creative_market"

    def test_export_gumroad(self, client):
        """导出为 Gumroad 格式."""
        lid = self._create_license(client)
        resp = client.get(f"/api/supply/licenses/{lid}/export?format=gumroad")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["format"] == "gumroad"
        assert "price" in data["listing_data"]

    def test_export_envato(self, client):
        """导出为 Envato 格式."""
        lid = self._create_license(client)
        resp = client.get(f"/api/supply/licenses/{lid}/export?format=envato")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["format"] == "envato"
        assert data["listing_data"]["extended_price"] == 199 * 5

    def test_export_invalid_format(self, client):
        """不支持的导出格式报错."""
        lid = self._create_license(client)
        resp = client.get(f"/api/supply/licenses/{lid}/export?format=bad_format")
        assert resp.status_code == 400


# ═══════════════════════════════════════════════════════════════════
# P2.5.7: 工厂比价工具
# ═══════════════════════════════════════════════════════════════════

class TestFactoryPriceCompare:
    """工厂比价测试."""

    def _create_partner(self, client, name, categories, price_range=None):
        """Helper: 创建测试工厂."""
        resp = client.post("/api/supply/partners", json={
            "name": name,
            "company_name": f"{name} Co.",
            "type": "manufacturer",
            "contact_person": "Test",
            "product_categories": categories,
            "material_capabilities": ["textile"],
            "typical_lead_time_days": 14,
            "rating": 4,
            "price_range": price_range or [],
        })
        assert resp.status_code == 200
        return resp.json()["data"]["id"]

    def test_compare_no_partners(self, client):
        """无匹配工厂时返回空."""
        resp = client.post("/api/supply/factory-price-compare", json={
            "product_category": "t_shirt",
            "quantity": 100,
        })
        assert resp.status_code == 200
        assert resp.json()["data"]["comparisons"] == []

    def test_compare_with_partners(self, client):
        """有匹配工厂时的对比."""
        self._create_partner(client, "Factory A", ["t_shirt"], [
            {"category": "t_shirt", "unit_price_range": [30, 50], "moq": 50}
        ])
        self._create_partner(client, "Factory B", ["t_shirt", "hoodie"], [
            {"category": "t_shirt", "unit_price_range": [25, 45], "moq": 100}
        ])

        resp = client.post("/api/supply/factory-price-compare", json={
            "product_category": "t_shirt",
            "quantity": 200,
        })
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert len(data["comparisons"]) == 2
        # Both factories should appear (order depends on tie-breaking)
        partner_names = [c["partner_name"] for c in data["comparisons"]]
        assert "Factory A" in partner_names
        assert "Factory B" in partner_names

    def test_compare_specific_partners(self, client):
        """指定工厂 ID 对比."""
        pid_a = self._create_partner(client, "Factory A", ["t_shirt"])
        self._create_partner(client, "Factory B", ["t_shirt"])

        resp = client.post("/api/supply/factory-price-compare", json={
            "product_category": "t_shirt",
            "quantity": 100,
            "partner_ids": [pid_a],
        })
        assert resp.status_code == 200
        comparisons = resp.json()["data"]["comparisons"]
        assert len(comparisons) == 1
        assert comparisons[0]["partner_id"] == pid_a


# ═══════════════════════════════════════════════════════════════════
# P2.5.8: AI 产品效果图生成
# ═══════════════════════════════════════════════════════════════════

class TestGenerateMockup:
    """AI 产品效果图测试."""

    def test_generate_mockup(self, client):
        """生成效果图描述."""
        resp = client.post("/api/supply/generate-mockup", json={
            "category_id": "cat_hard_mug",
            "style": "realistic",
        })
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["category"]["id"] == "cat_hard_mug"
        assert data["category"]["name_zh"] == "陶瓷杯/马克杯"
        assert data["style"] == "realistic"
        assert "ai_description" in data

    def test_generate_mockup_invalid_category(self, client):
        """无效品类报错."""
        resp = client.post("/api/supply/generate-mockup", json={
            "category_id": "nonexistent",
        })
        assert resp.status_code == 400

    def test_generate_with_prompt(self, client):
        """自定义 prompt 生成."""
        resp = client.post("/api/supply/generate-mockup", json={
            "category_id": "cat_textile_tshirt",
            "prompt": "Generate a minimalist t-shirt mockup with pastel colors on a light wood background",
            "style": "minimal",
        })
        assert resp.status_code == 200
        assert resp.json()["data"]["style"] == "minimal"


# ═══════════════════════════════════════════════════════════════════
# P2.5.15: 数字产品格式元数据
# ═══════════════════════════════════════════════════════════════════

class TestDigitalProductFormats:
    """数字产品格式测试."""

    def test_list_formats(self, client):
        """获取格式列表."""
        resp = client.get("/api/supply/digital-product-formats")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert len(data) >= 4
        product_types = [f["product_type"] for f in data]
        assert "brushes" in product_types
        assert "templates" in product_types

    def test_validate_digital_product_pass(self, client):
        """校验通过的数字产品."""
        resp = client.post("/api/supply/digital-product/validate", json={
            "product_type": "brushes",
            "target_platform": "gumroad",
            "file_formats": ["ZIP"],
            "file_count": 5,
            "file_size_mb": 100,
            "has_preview": True,
        })
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["passed"] is True
        assert data["error_count"] == 0

    def test_validate_digital_product_fail(self, client):
        """校验失败的数字产品."""
        resp = client.post("/api/supply/digital-product/validate", json={
            "product_type": "brushes",
            "target_platform": "gumroad",
            "file_formats": ["PSD"],  # wrong format
            "file_count": 1,
            "file_size_mb": 300,  # too large
            "has_preview": False,  # no preview
        })
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["passed"] is False
        assert data["error_count"] >= 2

    def test_validate_unknown_combo(self, client):
        """未知组合报错."""
        resp = client.post("/api/supply/digital-product/validate", json={
            "product_type": "unknown",
            "target_platform": "unknown",
            "file_formats": [],
            "file_count": 0,
            "file_size_mb": 0,
            "has_preview": False,
        })
        assert resp.status_code == 400


# ═══════════════════════════════════════════════════════════════════
# P2.5.11-P2.5.12: 聚合收入 + AI 变现顾问
# ═══════════════════════════════════════════════════════════════════

class TestRevenueAggregation:
    """聚合收入分析测试."""

    def test_aggregated_revenue(self, client):
        """聚合收入端点."""
        resp = client.get("/api/supply/revenue/aggregated")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert "summary" in data
        assert "by_platform" in data
        assert "by_monetization_path" in data
        assert "monthly_trends" in data
        assert len(data["monthly_trends"]) == 12

    def test_monetization_advisor(self, client):
        """AI 变现顾问."""
        resp = client.post("/api/supply/monetization-advisor", json={
            "work_type": "illustration",
            "work_title": "星空幻想系列",
            "current_paths": ["pod", "digital"],
        })
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["work_info"]["title"] == "星空幻想系列"
        assert "ai_advice" in data
        assert len(data["recommended_paths"]) >= 4


# ═══════════════════════════════════════════════════════════════════
# P2.5 Gateway 直接测试
# ═══════════════════════════════════════════════════════════════════

class TestPrintfulGateway:
    """Printful 网关单元测试."""

    def test_mock_create_product(self):
        """Mock 模式创建产品."""
        from app.gateway.printful import PrintfulGateway
        import asyncio
        gw = PrintfulGateway(api_key=None)
        result = asyncio.run(gw.create_product({
            "title": "Test Mug", "category": "mug", "price": 19.99,
        }))
        assert result["status"] == "draft"
        assert "id" in result

    def test_mock_get_product(self):
        """Mock 模式获取产品."""
        from app.gateway.printful import PrintfulGateway
        import asyncio
        gw = PrintfulGateway(api_key=None)
        result = asyncio.run(gw.get_product("pf-mock-001"))
        assert result["status"] == "synced"

    def test_mock_list_products(self):
        """Mock 模式列出产品."""
        from app.gateway.printful import PrintfulGateway
        import asyncio
        gw = PrintfulGateway(api_key=None)
        result = asyncio.run(gw.list_products())
        assert "items" in result


class TestRedbubbleGateway:
    """Redbubble 网关单元测试."""

    def test_mock_upload_design(self):
        """Mock 上传设计."""
        from app.gateway.redbubble import RedbubbleGateway
        import asyncio
        gw = RedbubbleGateway(use_browser=False)
        result = asyncio.run(gw.upload_design(
            design_file_path="/tmp/test.png",
            title="Test Artwork",
            tags=["art", "design"],
        ))
        assert result["status"] == "mock_draft"
        assert "id" in result
        assert len(result["enabled_products"]) >= 5

    def test_mock_sales_stats(self):
        """Mock 销售统计."""
        from app.gateway.redbubble import RedbubbleGateway
        import asyncio
        gw = RedbubbleGateway(use_browser=False)
        result = asyncio.run(gw.get_sales_stats())
        assert result["total_sales"] > 0
        assert "total_earnings" in result
        assert "top_products" in result

    def test_csv_template(self):
        """CSV 导入模板."""
        from app.gateway.redbubble import RedbubbleGateway
        gw = RedbubbleGateway()
        csv_data = gw.generate_csv_template([
            {"title": "Design 1", "tags": ["art"], "description": "Nice design"},
            {"title": "Design 2", "tags": ["nature"], "description": "Another one"},
        ])
        assert "Design 1" in csv_data
        assert "Design 2" in csv_data
        assert csv_data.startswith("title,tags,description")
