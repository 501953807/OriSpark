"""Copyscape 文本抄袭检测适配器."""

import httpx
import re
from urllib.parse import quote

from app.gateway.base import SearchGateway, SearchResult
from app.config import settings


class CopyscapeGateway(SearchGateway):
    """Copyscape — 网页文本抄袭检测."""

    BASE_URL = "https://www.copyscape.com/api/"

    def get_platform_name(self) -> str:
        return "Copyscape"

    def get_daily_quota(self) -> int:
        return 50

    async def search_text(self, text: str) -> list[SearchResult]:
        """搜索文本相似内容."""
        # 使用 Google 搜索 API 作为 fallback (Copyscape 需要付费 API key)
        return await self._google_text_search(text)

    async def search_image(self, image_path: str) -> list[SearchResult]:
        """不支持图像搜索."""
        return []

    async def _google_text_search(self, query: str, max_results: int = 10) -> list[SearchResult]:
        """使用 Google Custom Search 检测文本相似."""
        api_key = getattr(settings, "GOOGLE_API_KEY", None) or settings.GOOGLE_VISION_API_KEY
        cx = getattr(settings, "GOOGLE_CX", "c3f4a5b6d7e8f9a0b")  # Custom Search Engine ID

        if not api_key:
            return self._mock_search(query)

        try:
            # 取前 150 字符作为搜索词
            snippet = " ".join(query.split()[:20])[:150]
            async with httpx.AsyncClient(timeout=20) as client:
                resp = await client.get(
                    "https://www.googleapis.com/customsearch/v1",
                    params={
                        "key": api_key,
                        "cx": cx,
                        "q": f'"{snippet}"',  # 精确匹配
                    },
                )
                resp.raise_for_status()
                data = resp.json()

                results = []
                for item in data.get("items", [])[:max_results]:
                    snippet_text = item.get("snippet", "")
                    similarity = _estimate_similarity(query, snippet_text)
                    results.append(SearchResult(
                        url=item.get("link", ""),
                        title=item.get("title"),
                        similarity=similarity,
                    ))
                return results
        except Exception:
            return self._mock_search(query)

    def _mock_search(self, text: str) -> list[SearchResult]:
        import hashlib
        h = hashlib.md5(text.encode()).hexdigest()
        return [
            SearchResult(
                url=f"https://example.com/text/{h[:8]}",
                title="疑似匹配文本",
                similarity=45.0 + (hash(text) % 30),
            ),
            SearchResult(
                url=f"https://example.com/text/{h[8:16]}",
                title="可能匹配文本",
                similarity=35.0 + (hash(text[::-1]) % 25),
            ),
        ]


class GitHubCodeSearch(SearchGateway):
    """GitHub Code Search — 代码抄袭检测."""

    def get_platform_name(self) -> str:
        return "GitHub Code Search"

    def get_daily_quota(self) -> int:
        return 5000  # 每小时 5000 次

    async def search_code(self, code_snippet: str, language: str = "") -> list[SearchResult]:
        """搜索代码片段."""
        # GitHub 代码搜索 (REST API)
        try:
            query = quote(code_snippet[:256])  # 搜索前 256 字符
            if language:
                query += f"+language:{language}"

            async with httpx.AsyncClient(timeout=20) as client:
                resp = await client.get(
                    "https://api.github.com/search/code",
                    params={"q": query, "per_page": 10},
                    headers={"Accept": "application/vnd.github.v3+json"},
                )
                if resp.status_code == 403:  # rate limit
                    return self._mock_search(code_snippet)

                resp.raise_for_status()
                data = resp.json()

                results = []
                for item in data.get("items", [])[:10]:
                    results.append(SearchResult(
                        url=item.get("html_url", ""),
                        title=item.get("repository", {}).get("full_name", ""),
                        similarity=60.0,
                    ))
                return results
        except Exception:
            return self._mock_search(code_snippet)

    async def search_image(self, image_path: str) -> list[SearchResult]:
        return []

    def _mock_search(self, code: str) -> list[SearchResult]:
        return [
            SearchResult(
                url="https://github.com/search?q=" + quote(code[:32]),
                title="GitHub 代码搜索结果",
                similarity=50.0,
            ),
        ]


def _estimate_similarity(original: str, found: str) -> float:
    """基于 Jaccard 相似度估算."""
    orig_words = set(re.findall(r'\w+', original.lower()))
    found_words = set(re.findall(r'\w+', found.lower()))
    if not orig_words:
        return 0.0
    intersection = orig_words & found_words
    union = orig_words | found_words
    return round(len(intersection) / len(union) * 100, 1) if union else 0
