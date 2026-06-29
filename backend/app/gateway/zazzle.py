"""Zazzle POD 平台网关适配器 — P2.5.14.

Zazzle is a POD marketplace for custom products. No public REST API;
uses bulk upload CSV or Partner API (invite-only).

Mock only implementation.
"""

from typing import Optional


class ZazzleGateway:
    """Zazzle 平台网关 — 批量上传产品，管理商店。

    Zazzle 主要通过 CSV 批量上传工具和 Partner API (邀请制)。
    未配置时返回 mock 数据。
    """

    UPLOAD_URL = "https://www.zazzle.com/sell/designs"
    DASHBOARD_URL = "https://www.zazzle.com/sell/stats"

    def __init__(self, partner_api_key: Optional[str] = None):
        self.partner_api_key = partner_api_key

    # ------------------------------------------------------------------
    # 产品上传
    # ------------------------------------------------------------------
    async def upload_design(
        self,
        design_file_path: str,
        title: str,
        description: str = "",
        tags: list[str] | None = None,
        product_types: list[str] | None = None,
    ) -> dict:
        """上传设计到 Zazzle (mock)."""
        return self._mock(
            "upload_design",
            {"title": title, "product_types": product_types or []},
            {
                "id": f"zz-mock-{hash(title) & 0xFFFF:04x}",
                "status": "mock_draft",
                "title": title,
                "url": f"https://www.zazzle.com/store/mock/product/{hash(title) & 0xFFFF:04x}",
                "enabled_products": product_types or [
                    "invitation", "greeting-card", "postcard",
                    "t-shirt", "hoodie", "mug", "poster",
                    "sticker", "phone-case", "pillow",
                    "canvas-print", "notebook", "bag",
                    "ornament", "keychain", "water-bottle",
                ],
            },
        )

    async def get_store_stats(self, store_id: Optional[str] = None) -> dict:
        """获取商店销售统计 (mock)."""
        return self._mock("get_store_stats", {"store_id": store_id}, {
            "store_id": store_id or "mock-store",
            "total_products": 87,
            "total_sales": 432,
            "total_revenue": {"amount": 1245.60, "currency": "USD"},
            "this_month": {"sales": 28, "revenue": 89.30},
            "royalty_rate": "15%",
            "top_products": [
                {"title": "Mock Wedding Invitation", "sales": 120},
                {"title": "Mock Birthday Card", "sales": 95},
            ],
        })

    async def list_products(self, status: Optional[str] = "active") -> dict:
        """列出产品 (mock)."""
        return self._mock("list_products", {"status": status}, {
            "total": 87,
            "items": [
                {"id": f"zz-prod-{i:04d}", "title": f"Zazzle Product {i}", "status": "active"}
                for i in range(1, 6)
            ],
        })

    # ------------------------------------------------------------------
    # CSV 批量导入模板
    # ------------------------------------------------------------------
    def generate_csv_template(self, designs: list[dict]) -> str:
        """生成 Zazzle 兼容的 CSV 导入文件。

        Args:
            designs: [{title, description, tags, image_url, product_type}]
        """
        import io
        import csv

        buf = io.StringIO()
        writer = csv.writer(buf)
        writer.writerow([
            "Title", "Description", "Tags", "Image URL",
            "Product Type", "Design Placement", "Colors", "Default View",
        ])
        for d in designs:
            writer.writerow([
                d.get("title", ""),
                d.get("description", ""),
                ";".join(d.get("tags", [])) if isinstance(d.get("tags"), list) else d.get("tags", ""),
                d.get("image_url", ""),
                d.get("product_type", "t_shirt"),
                d.get("placement", "center"),
                d.get("colors", "white"),
                d.get("default_view", "front"),
            ])
        return buf.getvalue()

    # ------------------------------------------------------------------
    # Mock
    # ------------------------------------------------------------------
    def _mock(self, method: str, params: dict, default: dict) -> dict:
        print(f"[Zazzle] MOCK {method} (no API configured)")
        return default

    def get_platform_name(self) -> str:
        return "Zazzle"
