"""Society6 POD 平台网关适配器 — P2.5.14.

Society6 is an artist-driven POD marketplace. No public REST API;
returns mock data. In production, use Playwright browser automation
or manual upload.

Mock only implementation.
"""

from typing import Optional


class Society6Gateway:
    """Society6 平台网关 — 上传设计、管理店铺。

    Society6 不提供公开 API，此适配器提供 mock 响应。
    完整实现需要 Playwright 浏览器自动化。
    """

    UPLOAD_URL = "https://society6.com/upload"
    DASHBOARD_URL = "https://society6.com/dashboard"

    def __init__(self, use_browser: bool = False):
        self.use_browser = use_browser

    # ------------------------------------------------------------------
    # 产品上传
    # ------------------------------------------------------------------
    async def upload_design(
        self,
        design_file_path: str,
        title: str,
        description: str = "",
        tags: list[str] | None = None,
        category: str = "illustration",
    ) -> dict:
        """上传设计到 Society6 (mock)."""
        return self._mock(
            "upload_design",
            {"title": title, "category": category},
            {
                "id": f"s6-mock-{hash(title) & 0xFFFF:04x}",
                "status": "mock_draft",
                "title": title,
                "url": f"https://society6.com/product/mock-{hash(title) & 0xFFFF:04x}",
                "enabled_products": [
                    "art-print", "canvas", "framed-print", "tapestry",
                    "t-shirt", "hoodie", "tote-bag", "mug",
                    "throw-pillow", "duvet-cover", "shower-curtain",
                    "phone-case", "laptop-skin", "wall-clock",
                    "rug", "bath-mat", "coasters",
                ],
            },
        )

    async def get_artist_stats(self, artist_id: Optional[str] = None) -> dict:
        """获取艺术家销售统计 (mock)."""
        return self._mock("get_artist_stats", {}, {
            "artist_id": artist_id or "mock-artist",
            "total_sales": 156,
            "total_earnings": {"amount": 342.78, "currency": "USD"},
            "this_month": {"sales": 12, "earnings": 28.45},
            "top_products": [
                {"title": "Mock Art Print", "sales": 45},
                {"title": "Mock Framed Canvas", "sales": 32},
            ],
            "followers": 1280,
        })

    async def list_products(self, status: Optional[str] = None) -> dict:
        """列出店铺产品 (mock)."""
        return self._mock("list_products", {"status": status}, {
            "total": 24,
            "items": [
                {"id": f"s6-prod-{i:04d}", "title": f"Mock Design {i}", "status": "active"}
                for i in range(1, 6)
            ],
        })

    # ------------------------------------------------------------------
    # Mock
    # ------------------------------------------------------------------
    def _mock(self, method: str, params: dict, default: dict) -> dict:
        print(f"[Society6] MOCK {method} (no API configured)")
        return default

    def get_platform_name(self) -> str:
        return "Society6"
