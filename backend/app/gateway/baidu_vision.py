"""百度识图 API 适配器."""

import httpx

from app.gateway.base import SearchGateway, SearchResult
from app.config import settings


class BaiduVisionGateway(SearchGateway):
    """百度识图 — 以图搜图."""

    BASE_URL = "https://aip.baidubce.com/rest/2.0/image-classify/v2"

    def __init__(self):
        self._daily_used = 0

    def get_platform_name(self) -> str:
        return "百度识图"

    def get_daily_quota(self) -> int:
        return 100

    async def search_image(self, image_path: str) -> list[SearchResult]:
        """以图搜图."""
        api_key = settings.BAIDU_VISION_API_KEY
        if not api_key:
            # 模拟结果
            import hashlib
            h = hashlib.md5(image_path.encode()).hexdigest()
            return [
                SearchResult(
                    url=f"https://example.com/similar/{h[:8]}",
                    title="百度搜索结果",
                    similarity=78.5,
                )
            ]

        try:
            import base64
            with open(image_path, "rb") as f:
                image_b64 = base64.b64encode(f.read()).decode()

            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.post(
                    f"{self.BASE_URL}/similar-search",
                    params={"access_token": api_key},
                    json={"image": image_b64},
                )
                resp.raise_for_status()
                data = resp.json()

                results = []
                for item in data.get("results", [])[:10]:
                    results.append(SearchResult(
                        url=item.get("url", ""),
                        title=item.get("title"),
                        similarity=float(item.get("score", 0)),
                    ))
                self._daily_used += 1
                return results
        except Exception:
            return []


class BaiduTextSearch(SearchGateway):
    """百度文本搜索."""

    def get_platform_name(self) -> str:
        return "百度文本搜索"

    def get_daily_quota(self) -> int:
        return 50

    async def search_image(self, image_path: str) -> list[SearchResult]:
        # 文本搜索不支持图像
        return []
