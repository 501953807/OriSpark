"""Gelato POD 平台网关适配器 — P2.5.14.

Gelato is a global print-on-demand platform with a REST API
for order management and product creation.

Mock only implementation (no API key configured).
"""

from typing import Optional


class GelatoGateway:
    """Gelato 平台网关 — 创建产品、管理订单。

    Gelato API docs: https://gelato.com/api
    未配置 API key 时返回 mock 数据。
    """

    BASE_URL = "https://api.gelato.com/v1"

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key

    @property
    def _is_configured(self) -> bool:
        return bool(self.api_key)

    # ------------------------------------------------------------------
    # 产品管理
    # ------------------------------------------------------------------
    async def create_product(self, product_data: dict) -> dict:
        """在 Gelato 创建产品 (mock)."""
        if not self._is_configured:
            return self._mock("create_product", product_data, {
                "id": f"gel-mock-{hash(product_data.get('title', '')) & 0xFFFF:04x}",
                "status": "draft",
                "title": product_data.get("title", ""),
            })
        return self._mock("create_product", product_data, {
            "id": f"gel-api-{hash(product_data.get('title', '')) & 0xFFFF:04x}",
            "status": "draft",
        })

    async def get_product(self, product_id: str) -> dict:
        """获取产品详情 (mock)."""
        return self._mock("get_product", {"product_id": product_id}, {
            "id": product_id,
            "status": "synced",
            "print_areas": ["front", "back"],
            "variants": [{"size": "M", "color": "white", "price": 24.99}],
        })

    async def list_products(self, offset: int = 0, limit: int = 20) -> dict:
        """列出产品 (mock)."""
        return self._mock("list_products", {}, {
            "total": 10,
            "items": [{"id": f"gel-prod-{i:04d}", "title": f"Gelato Product {i}"} for i in range(1, 6)],
        })

    # ------------------------------------------------------------------
    # 订单
    # ------------------------------------------------------------------
    async def create_order(self, order_data: dict) -> dict:
        """创建订单 (mock)."""
        return self._mock("create_order", order_data, {
            "order_id": f"gel-ord-{hash(str(order_data)) & 0xFFFF:04x}",
            "status": "pending",
            "estimated_ship_date": "mock-2025-01-15",
        })

    async def get_order(self, order_id: str) -> dict:
        """获取订单状态 (mock)."""
        return self._mock("get_order", {"order_id": order_id}, {
            "order_id": order_id,
            "status": "in_production",
            "tracking": None,
        })

    # ------------------------------------------------------------------
    # 目录与定价
    # ------------------------------------------------------------------
    async def get_catalog(self, category: Optional[str] = None) -> dict:
        """获取产品目录与定价 (mock)."""
        catalog = {
            "products": [
                {"id": "t-shirt-unisex", "name": "Classic T-Shirt", "base_price_usd": 9.50, "brands": ["Gildan", "Bella+Canvas"]},
                {"id": "hoodie", "name": "Pullover Hoodie", "base_price_usd": 20.00, "brands": ["Gildan"]},
                {"id": "mug-11oz", "name": "11oz Ceramic Mug", "base_price_usd": 5.50, "brands": ["Generic"]},
                {"id": "poster-a3", "name": "A3 Poster", "base_price_usd": 4.00, "brands": ["Generic"]},
                {"id": "phone-case", "name": "Phone Case", "base_price_usd": 11.00, "brands": ["Generic"]},
                {"id": "tote-bag", "name": "Cotton Tote Bag", "base_price_usd": 8.00, "brands": ["Generic"]},
                {"id": "notebook-a5", "name": "A5 Notebook", "base_price_usd": 7.00, "brands": ["Generic"]},
            ],
        }
        return self._mock("get_catalog", {"category": category}, catalog)

    async def get_shipping_zones(self) -> dict:
        """获取配送区域与费率 (mock)."""
        return self._mock("get_shipping_zones", {}, {
            "zones": [
                {"zone": "EU", "countries": ["DE", "FR", "IT", "ES", "NL"], "production_days": 2},
                {"zone": "US", "countries": ["US"], "production_days": 2},
                {"zone": "Asia", "countries": ["CN", "JP", "KR"], "production_days": 3},
                {"zone": "Global", "countries": ["AU", "CA", "BR"], "production_days": 4},
            ],
        })

    # ------------------------------------------------------------------
    # Mock
    # ------------------------------------------------------------------
    def _mock(self, method: str, params: dict, default: dict) -> dict:
        print(f"[Gelato] MOCK {method} (no API key configured)")
        return default

    def get_platform_name(self) -> str:
        return "Gelato"
