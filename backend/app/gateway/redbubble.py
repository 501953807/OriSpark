"""Redbubble POD 平台网关适配器 — P2.5.2.

Redbubble 没有公开 REST API；通过 Playwright 浏览器自动化或 RSS/CSV
导入作为备选。在未配置时返回 mock 数据。
"""

from typing import Optional


class RedbubbleGateway:
    """Redbubble 平台网关 — 上传设计、管理作品集、查看销售数据。

    由于 Redbubble 不提供公开 API，此适配器通过以下方式交互：
    1. 如果配置了浏览器自动化 (Playwright)：模拟上传流程
    2. CSV 批量导入模板生成
    3. 未配置时返回 mock
    """

    UPLOAD_URL = "https://www.redbubble.com/portfolio/images/new"
    DASHBOARD_URL = "https://www.redbubble.com/portfolio"

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
        enable_for: list[str] | None = None,
    ) -> dict:
        """上传设计到 Redbubble。

        Args:
            design_file_path: 本地设计文件路径
            title: 作品标题
            description: 作品描述
            tags: 标签列表
            enable_for: 启用的产品类型列表，默认全部
        """
        if not self.use_browser:
            return self._mock(
                "upload_design",
                {"title": title, "tags": tags or []},
                {
                    "id": f"rb-mock-{hash(title) & 0xFFFF:04x}",
                    "status": "mock_draft",
                    "title": title,
                    "url": f"https://www.redbubble.com/people/mock/works/{hash(title) & 0xFFFF:04x}",
                    "enabled_products": enable_for or [
                        "t-shirt", "sticker", "mug", "phone-case", "poster",
                        "hoodie", "tote-bag", "notebook", "pillow", "coaster",
                    ],
                },
            )

        # 浏览器自动化路径 (需要 playwright)
        try:
            from app.gateway.playwright_pub import PlaywrightPublisher
            publisher = PlaywrightPublisher()
            result = await publisher.publish_to_redbubble(
                design_file_path=design_file_path,
                title=title,
                description=description,
                tags=tags or [],
                enable_for=enable_for,
            )
            return result
        except ImportError:
            return self._mock(
                "upload_design",
                {"title": title},
                {"id": f"rb-nobrowser-{hash(title) & 0xFFFF:04x}", "status": "error", "error": "Playwright not available"},
            )

    async def get_sales_stats(self) -> dict:
        """获取销售统计数据 (scrape 或 mock)。"""
        if not self.use_browser:
            return self._mock("get_sales_stats", {}, {
                "total_sales": 42,
                "total_earnings": {"amount": 128.34, "currency": "USD"},
                "this_month": {"sales": 8, "earnings": 24.12},
                "top_products": [
                    {"title": "Mock Design A", "sales": 15},
                    {"title": "Mock Design B", "sales": 10},
                ],
            })

        return self._mock("get_sales_stats", {}, {"total_sales": 0, "total_earnings": {"amount": 0, "currency": "USD"}})

    # ------------------------------------------------------------------
    # 批量 CSV 导入模板
    # ------------------------------------------------------------------
    def generate_csv_template(self, designs: list[dict]) -> str:
        """生成 Redbubble 兼容的 CSV 导入文件内容。

        Args:
            designs: [{title, tags, description, image_url}]
        """
        import io
        import csv

        buf = io.StringIO()
        writer = csv.writer(buf)
        writer.writerow(["title", "tags", "description", "image_url", "default_product", "enabled_products"])
        for d in designs:
            writer.writerow([
                d.get("title", ""),
                ",".join(d.get("tags", [])),
                d.get("description", ""),
                d.get("image_url", ""),
                d.get("default_product", "sticker"),
                ",".join(d.get("enabled_products", ["sticker", "t-shirt", "mug", "poster"])),
            ])
        return buf.getvalue()

    # ------------------------------------------------------------------
    # Mock
    # ------------------------------------------------------------------
    def _mock(self, method: str, params: dict, default: dict) -> dict:
        print(f"[Redbubble] MOCK {method} (no automation configured)")
        return default

    def get_platform_name(self) -> str:
        return "Redbubble"
