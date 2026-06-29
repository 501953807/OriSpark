"""Spring (Teespring) POD 平台网关适配器 — P2.5.14.

Spring (formerly Teespring) is a creator commerce platform for
designing and selling custom merchandise. Uses Creator API.

Mock only implementation.
"""

from typing import Optional


class SpringGateway:
    """Spring (Teespring) 平台网关 — 创建商品、管理店铺。

    Spring Creator API: https://developers.spri.ng
    未配置 API key 时返回 mock 数据。
    """

    BASE_URL = "https://api.spri.ng/v1"

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key

    @property
    def _is_configured(self) -> bool:
        return bool(self.api_key)

    # ------------------------------------------------------------------
    # 产品管理
    # ------------------------------------------------------------------
    async def create_product(self, product_data: dict) -> dict:
        """在 Spring 创建产品 (mock)."""
        title = product_data.get("title", "")
        return self._mock("create_product", product_data, {
            "id": f"sp-mock-{hash(title) & 0xFFFF:04x}",
            "title": title,
            "status": "draft",
            "url": f"https://spring.com/products/{hash(title) & 0xFFFF:04x}",
            "design_front_url": product_data.get("design_file_url", ""),
        })

    async def create_campaign(self, campaign_data: dict) -> dict:
        """创建销售活动 (campaign/listing) (mock).

        Spring 的核心理念是 campaign-based selling:
        每个产品至少有一个 campaign，设置价格、目标和截止日期。
        """
        title = campaign_data.get("title", "")
        return self._mock("create_campaign", campaign_data, {
            "id": f"sp-camp-{hash(title) & 0xFFFF:04x}",
            "title": title,
            "status": "draft",
            "goal": campaign_data.get("goal", 10),
            "end_date": campaign_data.get("end_date", "mock"),
            "url": f"https://spring.com/campaigns/{hash(title) & 0xFFFF:04x}",
        })

    async def get_product(self, product_id: str) -> dict:
        """获取产品详情 (mock)."""
        return self._mock("get_product", {"product_id": product_id}, {
            "id": product_id,
            "status": "active",
            "variants": [
                {"type": "t-shirt", "colors": ["black", "white", "navy"], "sizes": ["S", "M", "L", "XL", "2XL"]},
                {"type": "hoodie", "colors": ["black", "gray"], "sizes": ["S", "M", "L", "XL"]},
                {"type": "mug", "colors": ["white", "black"], "sizes": ["11oz"]},
            ],
            "campaigns": [
                {"id": "sp-camp-mock", "title": "Mock Campaign", "sales": 42},
            ],
        })

    async def get_analytics(self, product_id: Optional[str] = None, days: int = 30) -> dict:
        """获取销售分析 (mock)."""
        return self._mock("get_analytics", {"product_id": product_id, "days": days}, {
            "total_views": 5420,
            "total_conversions": 126,
            "conversion_rate": 2.32,
            "total_revenue": {"amount": 845.20, "currency": "USD"},
            "profit": {"amount": 372.50, "currency": "USD"},
            "profit_margin": "44%",
            "daily_stats": [
                {"date": "2025-01-01", "views": 180, "sales": 4, "revenue": 26.00},
                {"date": "2025-01-02", "views": 210, "sales": 6, "revenue": 39.00},
            ],
        })

    async def list_products(self, status: Optional[str] = "active") -> dict:
        """列出产品 (mock)."""
        return self._mock("list_products", {"status": status}, {
            "total": 15,
            "items": [
                {"id": f"sp-prod-{i:04d}", "title": f"Spring Product {i}", "status": "active", "sales": i * 7}
                for i in range(1, 6)
            ],
        })

    async def list_campaigns(self, status: Optional[str] = "active") -> dict:
        """列出活动 (mock)."""
        return self._mock("list_campaigns", {"status": status}, {
            "total": 8,
            "items": [
                {"id": f"sp-camp-{i:04d}", "title": f"Campaign {i}", "status": "active", "sales": i * 12}
                for i in range(1, 4)
            ],
        })

    # ------------------------------------------------------------------
    # 定价建议
    # ------------------------------------------------------------------
    async def get_pricing_suggestions(self, product_type: str = "t-shirt") -> dict:
        """获取定价建议 (mock)."""
        pricing = {
            "t-shirt": {"base_cost": 10.00, "suggested_price_min": 24.99, "suggested_price_optimal": 29.99, "profit_at_optimal": 12.49},
            "hoodie": {"base_cost": 20.00, "suggested_price_min": 39.99, "suggested_price_optimal": 44.99, "profit_at_optimal": 15.74},
            "mug": {"base_cost": 5.50, "suggested_price_min": 14.99, "suggested_price_optimal": 17.99, "profit_at_optimal": 8.84},
            "sticker": {"base_cost": 2.00, "suggested_price_min": 5.99, "suggested_price_optimal": 7.99, "profit_at_optimal": 4.59},
            "poster": {"base_cost": 5.00, "suggested_price_min": 14.99, "suggested_price_optimal": 19.99, "profit_at_optimal": 10.99},
            "phone_case": {"base_cost": 12.00, "suggested_price_min": 24.99, "suggested_price_optimal": 29.99, "profit_at_optimal": 11.24},
        }
        return self._mock("get_pricing_suggestions", {"product_type": product_type},
                          pricing.get(product_type, pricing["t-shirt"]))

    # ------------------------------------------------------------------
    # Mock
    # ------------------------------------------------------------------
    def _mock(self, method: str, params: dict, default: dict) -> dict:
        print(f"[Spring] MOCK {method} (no API key configured)")
        return default

    def get_platform_name(self) -> str:
        return "Spring (Teespring)"
