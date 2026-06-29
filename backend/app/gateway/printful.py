"""Printful POD 平台网关适配器 — P2.5.1.

在 API key 未配置时提供 mock 响应。
"""

import httpx
from typing import Optional

from app.config import settings


class PrintfulGateway:
    """Printful POD 平台网关 — 创建/同步产品、推送设计稿、获取订单状态。"""

    BASE_URL = "https://api.printful.com"

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or getattr(settings, "PRINTFUL_API_KEY", None)

    @property
    def _is_configured(self) -> bool:
        return bool(self.api_key)

    # ------------------------------------------------------------------
    # 产品管理
    # ------------------------------------------------------------------
    async def create_product(self, product_data: dict) -> dict:
        """在 Printful 创建 sync product。

        Args:
            product_data: {title, description, design_file_url, category, price, currency}
        """
        if not self._is_configured:
            return self._mock("create_product", product_data, {"id": "pf-mock-001", "status": "draft"})

        try:
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.post(
                    f"{self.BASE_URL}/store/products",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    json={
                        "sync_product": {
                            "name": product_data.get("title", ""),
                            "thumbnail": product_data.get("design_file_url", ""),
                        },
                        "sync_variants": [
                            {
                                "retail_price": str(product_data.get("price", "29.99")),
                                "currency": product_data.get("currency", "USD"),
                                "files": [{"url": product_data.get("design_file_url", "")}],
                            }
                        ],
                    },
                )
                resp.raise_for_status()
                data = resp.json()
                return {
                    "id": str(data["result"].get("id", "")),
                    "status": "draft",
                    "external_id": str(data["result"].get("sync_product", {}).get("external_id", data["result"].get("id", ""))),
                }
        except Exception as e:
            print(f"[Printful] create_product error: {e}")
            return self._mock("create_product", product_data, {"id": f"pf-err-{hash(product_data.get('title','')) & 0xFFFF:04x}", "status": "error", "error": str(e)})

    async def get_product(self, product_id: str) -> dict:
        """获取 Printful 产品详情。"""
        if not self._is_configured:
            return self._mock("get_product", {"id": product_id}, {"id": product_id, "status": "synced"})

        try:
            async with httpx.AsyncClient(timeout=15) as client:
                resp = await client.get(
                    f"{self.BASE_URL}/store/products/{product_id}",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                )
                resp.raise_for_status()
                return resp.json().get("result", {})
        except Exception as e:
            return {"id": product_id, "status": "error", "error": str(e)}

    async def list_products(self, offset: int = 0, limit: int = 20) -> dict:
        """列出 Printful 商店产品。"""
        if not self._is_configured:
            return self._mock("list_products", {}, {"items": [], "total": 0})

        try:
            async with httpx.AsyncClient(timeout=15) as client:
                resp = await client.get(
                    f"{self.BASE_URL}/store/products",
                    params={"offset": offset, "limit": limit},
                    headers={"Authorization": f"Bearer {self.api_key}"},
                )
                resp.raise_for_status()
                return resp.json().get("result", {})
        except Exception as e:
            return {"items": [], "total": 0, "error": str(e)}

    # ------------------------------------------------------------------
    # 订单状态
    # ------------------------------------------------------------------
    async def get_orders(self, status: Optional[str] = None, offset: int = 0, limit: int = 20) -> dict:
        """获取 Printful 订单列表。"""
        if not self._is_configured:
            return self._mock("get_orders", {}, {"items": [], "total": 0})

        try:
            async with httpx.AsyncClient(timeout=15) as client:
                params = {"offset": offset, "limit": limit}
                if status:
                    params["status"] = status
                resp = await client.get(
                    f"{self.BASE_URL}/orders",
                    params=params,
                    headers={"Authorization": f"Bearer {self.api_key}"},
                )
                resp.raise_for_status()
                return resp.json().get("result", {})
        except Exception as e:
            return {"items": [], "total": 0, "error": str(e)}

    # ------------------------------------------------------------------
    # Mock 工厂
    # ------------------------------------------------------------------
    def _mock(self, method: str, params: dict, default: dict) -> dict:
        """当 API key 未配置时返回 mock 数据。"""
        print(f"[Printful] MOCK {method} (no API key configured)")
        # 尝试回填请求标题
        if "id" not in default and "title" in params:
            default["id"] = f"pf-mock-{hash(params['title']) & 0xFFFF:04x}"
        return default

    # ------------------------------------------------------------------
    # 成本与报价
    # ------------------------------------------------------------------
    async def get_shipping_rates(self, product_id: str, country_code: str = "CN") -> dict:
        """获取运费报价。"""
        if not self._is_configured:
            return self._mock("get_shipping_rates", {"product_id": product_id}, {"rates": []})

        try:
            async with httpx.AsyncClient(timeout=15) as client:
                resp = await client.post(
                    f"{self.BASE_URL}/shipping/rates",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    json={
                        "recipient": {"country_code": country_code},
                        "items": [{"sync_variant_id": product_id, "quantity": 1}],
                    },
                )
                resp.raise_for_status()
                return resp.json().get("result", {"rates": []})
        except Exception:
            return {"rates": []}

    def get_platform_name(self) -> str:
        return "Printful"
