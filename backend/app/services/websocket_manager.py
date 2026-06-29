"""WebSocket 实时通知管理."""

import json
import asyncio
from typing import Dict, Set
from fastapi import WebSocket


class ConnectionManager:
    """WebSocket 连接管理器."""

    def __init__(self):
        self._connections: Dict[str, Set[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, client_id: str = "default"):
        """接受 WebSocket 连接."""
        await websocket.accept()
        if client_id not in self._connections:
            self._connections[client_id] = set()
        self._connections[client_id].add(websocket)

    def disconnect(self, websocket: WebSocket, client_id: str = "default"):
        """断开 WebSocket 连接."""
        if client_id in self._connections:
            self._connections[client_id].discard(websocket)
            if not self._connections[client_id]:
                del self._connections[client_id]

    async def send_personal(self, message: dict, client_id: str):
        """发送消息给指定客户端."""
        if client_id in self._connections:
            dead = set()
            for ws in self._connections[client_id]:
                try:
                    await ws.send_json(message)
                except Exception:
                    dead.add(ws)
            self._connections[client_id] -= dead

    async def broadcast(self, message: dict):
        """广播消息给所有客户端."""
        for client_id in list(self._connections.keys()):
            await self.send_personal(message, client_id)

    async def notify_task_progress(self, task_id: str, progress: float, detail: str = ""):
        """通知任务进度."""
        await self.broadcast({
            "type": "task_progress",
            "task_id": task_id,
            "progress": progress,
            "detail": detail,
        })

    async def notify_scan_result(self, work_id: str, results_count: int):
        """通知扫描结果."""
        await self.broadcast({
            "type": "scan_result",
            "work_id": work_id,
            "results_count": results_count,
        })

    async def notify_reminder(self, reminder_id: str, title: str):
        """通知提醒."""
        await self.broadcast({
            "type": "reminder",
            "reminder_id": reminder_id,
            "title": title,
        })

    async def notify_certificate_ready(self, cert_id: str):
        """通知证书生成完成."""
        await self.broadcast({
            "type": "certificate_ready",
            "cert_id": cert_id,
        })

    @property
    def active_connections(self) -> int:
        return sum(len(v) for v in self._connections.values())


# 全局 WebSocket 连接管理器
manager = ConnectionManager()
