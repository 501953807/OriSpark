"""外部 API 网关适配器基类."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional


@dataclass
class NotaryResult:
    """存证结果."""
    success: bool
    record_id: Optional[str] = None
    transaction_hash: Optional[str] = None
    block_height: Optional[str] = None
    platform_url: Optional[str] = None
    error_message: Optional[str] = None


@dataclass
class SearchResult:
    """搜索结果."""
    url: str
    title: Optional[str] = None
    similarity: float = 0.0
    thumbnail_url: Optional[str] = None


class NotaryGateway(ABC):
    """存证平台网关基类."""

    @abstractmethod
    async def submit_evidence(self, file_hash: str, metadata: dict) -> NotaryResult:
        """提交证据到存证平台."""
        ...

    @abstractmethod
    async def check_status(self, record_id: str) -> str:
        """查询存证状态."""
        ...

    @abstractmethod
    def get_fee(self) -> float:
        """获取每次存证费用 (CNY)."""
        ...

    @abstractmethod
    def get_platform_name(self) -> str:
        """获取平台名称."""
        ...

    @abstractmethod
    def get_legal_level(self) -> str:
        """获取法律效力级别: national/judicial/commercial."""
        ...


class SearchGateway(ABC):
    """搜索引擎网关基类."""

    @abstractmethod
    async def search_image(self, image_path: str) -> list[SearchResult]:
        """以图搜图."""
        ...

    @abstractmethod
    def get_daily_quota(self) -> int:
        """获取每日免费配额."""
        ...

    @abstractmethod
    def get_platform_name(self) -> str:
        """获取平台名称."""
        ...


class PublishingGateway(ABC):
    """发布平台网关基类."""

    @abstractmethod
    async def connect_oauth(self, auth_code: str) -> dict:
        """OAuth 连接."""
        ...

    @abstractmethod
    async def publish_product(self, product_data: dict, images: list[str]) -> dict:
        """发布商品."""
        ...

    @abstractmethod
    async def check_publish_status(self, publish_id: str) -> str:
        """查询发布状态."""
        ...

    @abstractmethod
    def get_platform_name(self) -> str:
        """获取平台名称."""
        ...
