"""商标数据库网关适配器 — 对接 CNIPA/WIPO/USPTO/EUIPO."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class TrademarkResult:
    """商标搜索结果."""
    mark_name: str
    registration_number: Optional[str] = None
    classes: list = field(default_factory=list)
    jurisdiction: str = "cn"
    similarity: float = 0.0
    status: str = "unknown"
    owner: str = ""
    url: str = ""


class TrademarkGateway(ABC):
    """商标查询网关基类."""

    @abstractmethod
    async def search(self, mark_name: str, classes: Optional[list] = None,
                     jurisdiction: str = "cn") -> list[TrademarkResult]:
        """搜索商标."""
        ...

    @abstractmethod
    async def check_similarity(self, mark_name: str, jurisdiction: str = "cn") -> float:
        """检查商标相似度 (0-100)."""
        ...


class CNIPATrademarkGateway(TrademarkGateway):
    """CNIPA 中国商标查询适配器 (v1: 本地模拟).

    实际实现需要对接 CNIPA 开放 API 或结构化爬虫.
    v1 使用内置热门品牌库做模糊匹配.
    """

    _HOT_BRANDS = [
        {"name": "Hello Kitty", "classes": ["16", "21", "25"], "jurisdiction": "cn"},
        {"name": "迪士尼", "classes": ["16", "25", "28"], "jurisdiction": "cn"},
        {"name": "原神", "classes": ["9", "16", "25"], "jurisdiction": "cn"},
        {"name": "故宫文创", "classes": ["16", "21", "35"], "jurisdiction": "cn"},
        {"name": "泡泡玛特", "classes": ["16", "28", "30"], "jurisdiction": "cn"},
    ]

    async def search(self, mark_name: str, classes: Optional[list] = None,
                     jurisdiction: str = "cn") -> list[TrademarkResult]:
        results = []
        for brand in self._HOT_BRANDS:
            if mark_name.lower() in brand["name"].lower() or brand["name"].lower() in mark_name.lower():
                results.append(TrademarkResult(
                    mark_name=brand["name"],
                    classes=brand["classes"],
                    jurisdiction=brand["jurisdiction"],
                    similarity=min(95.0, 60.0 + len(mark_name) * 3),
                    status="registered",
                ))
        return results

    async def check_similarity(self, mark_name: str, jurisdiction: str = "cn") -> float:
        results = await self.search(mark_name, jurisdiction=jurisdiction)
        return max((r.similarity for r in results), default=0.0)


class MockTrademarkGateway(TrademarkGateway):
    """模拟网关 — 用于开发和测试."""

    async def search(self, mark_name: str, classes: Optional[list] = None,
                     jurisdiction: str = "cn") -> list[TrademarkResult]:
        if "kitty" in mark_name.lower():
            return [TrademarkResult(
                mark_name="Hello Kitty", similarity=85.0,
                classes=["16", "25"], jurisdiction="us", status="registered",
                owner="Sanrio Co., Ltd.")]
        return []

    async def check_similarity(self, mark_name: str, jurisdiction: str = "cn") -> float:
        results = await self.search(mark_name)
        return max((r.similarity for r in results), default=0.0)
