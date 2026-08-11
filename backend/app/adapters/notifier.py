"""通知推送适配器 — 符合 ADR-0001 Gateway ABC 模式."""

from abc import ABC, abstractmethod
from typing import Any, Optional
import logging

logger = logging.getLogger(__name__)


class NotifierAdapter(ABC):
    """通知推送接口.

    所有通知推送实现必须实现此接口.
    """

    @abstractmethod
    async def notify(
        self,
        user_id: str,
        type: str,
        title: str,
        content: str,
        related_module: Optional[str] = None,
        related_id: Optional[str] = None,
    ) -> None:
        """发送通知给用户."""
        ...

    @abstractmethod
    async def broadcast(
        self,
        message: dict[str, Any],
    ) -> None:
        """广播消息给所有连接客户端."""
        ...


class RealNotifierAdapter(NotifierAdapter):
    """真实 WebSocket 通知实现."""

    def __init__(self, manager=None):
        """初始化.

        Args:
            manager: ConnectionManager 实例，默认为全局单例.
        """
        from app.services.websocket_manager import manager as default_manager
        self._manager = manager or default_manager

    async def notify(
        self,
        user_id: str,
        type: str,
        title: str,
        content: str,
        related_module: Optional[str] = None,
        related_id: Optional[str] = None,
    ) -> None:
        """发送通知给用户."""
        await self._manager.broadcast({
            "type": "notification",
            "user_id": user_id,
            "notification_type": type,
            "title": title,
            "content": content,
            "related_module": related_module,
            "related_id": related_id,
        })

    async def broadcast(self, message: dict[str, Any]) -> None:
        """广播消息给所有客户端."""
        await self._manager.broadcast(message)


class MockNotifierAdapter(NotifierAdapter):
    """测试用 Mock 通知实现."""

    def __init__(self):
        self.notified_messages: list[dict] = []
        self.broadcasted_messages: list[dict] = []

    async def notify(
        self,
        user_id: str,
        type: str,
        title: str,
        content: str,
        related_module: Optional[str] = None,
        related_id: Optional[str] = None,
    ) -> None:
        """Mock 通知."""
        self.notified_messages.append({
            "user_id": user_id,
            "type": type,
            "title": title,
            "content": content,
            "related_module": related_module,
            "related_id": related_id,
        })
        logger.debug("Mock notified: %s to %s", title, user_id)

    async def broadcast(self, message: dict[str, Any]) -> None:
        """Mock 广播."""
        self.broadcasted_messages.append(message)
        logger.debug("Mock broadcasted: %s", message.get("type"))

    def get_last_notification(self) -> Optional[dict]:
        """获取最后一次通知."""
        return self.notified_messages[-1] if self.notified_messages else None

    def get_last_broadcast(self) -> Optional[dict]:
        """获取最后一次广播."""
        return self.broadcasted_messages[-1] if self.broadcasted_messages else None

    def clear(self) -> None:
        """清空记录."""
        self.notified_messages.clear()
        self.broadcasted_messages.clear()
