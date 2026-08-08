"""小红书监测网关."""
import httpx

from app.gateway.base import SearchGateway, SearchResult
from app.config import settings


class XiaohongshuSearchGateway(SearchGateway):
    """小红书内容监测."""

    BASE_URL = "https://edith.xiaohongshu.com"

    def get_platform_name(self) -> str:
        return "小红书"

    def get_daily_quota(self) -> int:
        return 5000

    async def search_image(self, image_path: str) -> list[SearchResult]:
        """以图搜图 — 小红书监测."""
        if not settings.XIAOHONGSHU_API_KEY:
            return []
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post(
                    f"{self.BASE_URL}/api/sns/v1/search/image",
                    headers={"Authorization": f"Bearer {settings.XIAOHONGSHU_ACCESS_TOKEN}"},
                    json={"image_path": image_path},
                )
                resp.raise_for_status()
                data = resp.json()
                return [
                    SearchResult(
                        url=item.get("url", ""),
                        title=item.get("title", ""),
                        similarity=item.get("similarity", 0.0),
                    )
                    for item in data.get("items", [])
                ]
        except Exception as e:
            import logging
            logging.getLogger(__name__).warning(f"Xiaohongshu search failed: {e}")
            return []
