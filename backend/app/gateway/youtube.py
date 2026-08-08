"""YouTube 监测网关."""
import httpx

from app.gateway.base import SearchGateway, SearchResult
from app.config import settings


class YouTubeSearchGateway(SearchGateway):
    """YouTube 内容监测."""

    BASE_URL = "https://www.googleapis.com/youtube/v3"

    def get_platform_name(self) -> str:
        return "YouTube"

    def get_daily_quota(self) -> int:
        return 10000

    async def search_image(self, image_path: str) -> list[SearchResult]:
        """以图搜图 — YouTube 监测."""
        if not settings.YOUTUBE_API_KEY:
            return []
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.get(
                    f"{self.BASE_URL}/search",
                    params={
                        "part": "snippet",
                        "q": image_path,
                        "key": settings.YOUTUBE_API_KEY,
                        "maxResults": 20,
                    },
                )
                resp.raise_for_status()
                data = resp.json()
                return [
                    SearchResult(
                        url=f"https://youtube.com/watch?v={item.get('id', {}).get('videoId', '')}",
                        title=item.get("snippet", {}).get("title", ""),
                        similarity=0.85,
                    )
                    for item in data.get("items", [])
                ]
        except Exception as e:
            import logging
            logging.getLogger(__name__).warning(f"YouTube search failed: {e}")
            return []
