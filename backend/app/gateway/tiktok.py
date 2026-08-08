"""TikTok 监测网关."""
import httpx

from app.gateway.base import SearchGateway, SearchResult
from app.config import settings


class TikTokSearchGateway(SearchGateway):
    """TikTok 内容监测."""

    BASE_URL = "https://open.tiktokapis.com/v2"

    def get_platform_name(self) -> str:
        return "TikTok"

    def get_daily_quota(self) -> int:
        return 10000

    async def search_image(self, image_path: str) -> list[SearchResult]:
        """以图搜图 — TikTok 监测."""
        if not settings.TIKTOK_APP_KEY:
            return []
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post(
                    f"{self.BASE_URL}/search/content/",
                    headers={"Authorization": f"Bearer {settings.TIKTOK_ACCESS_TOKEN}"},
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
            logging.getLogger(__name__).warning(f"TikTok search failed: {e}")
            return []
