"""WebSocket 实时通知管理."""

import asyncio
from datetime import datetime, timezone
from typing import Dict, Set
from fastapi import WebSocket


class ConnectionManager:
    """WebSocket 连接管理器."""

    def __init__(self):
        self._connections: Dict[str, Set[WebSocket]] = {}
        self._client_ids: Dict[WebSocket, str] = {}  # 记录 websocket → client_id 映射

    async def connect(self, websocket: WebSocket, client_id: str = "default"):
        """接受 WebSocket 连接."""
        await websocket.accept()
        self._client_ids[websocket] = client_id
        if client_id not in self._connections:
            self._connections[client_id] = set()
        self._connections[client_id].add(websocket)

    def disconnect(self, websocket: WebSocket, client_id: str = "default"):
        """断开 WebSocket 连接."""
        self._client_ids.pop(websocket, None)
        if client_id in self._connections:
            self._connections[client_id].discard(websocket)
            if not self._connections[client_id]:
                del self._connections[client_id]

    def get_client_id(self, websocket: WebSocket) -> str:
        """获取 WebSocket 对应的 client_id."""
        return self._client_ids.get(websocket, "unknown")

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

    async def notify_to_client(self, client_id: str, message: dict):
        """发送消息给指定客户端（不广播）."""
        await self.send_personal(message, client_id)

    async def notify_task_progress(self, task_id: str, progress: float, detail: str = ""):
        """通知任务进度."""
        await self.broadcast({
            "type": "task_progress",
            "task_id": task_id,
            "progress": progress,
            "detail": detail,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })

    async def notify_scan_result(self, work_id: str, results_count: int):
        """通知扫描结果."""
        await self.broadcast({
            "type": "scan_result",
            "work_id": work_id,
            "results_count": results_count,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })

    async def notify_reminder(self, reminder_id: str, title: str):
        """通知提醒."""
        await self.broadcast({
            "type": "reminder",
            "reminder_id": reminder_id,
            "title": title,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })

    async def notify_certificate_ready(self, cert_id: str):
        """通知证书生成完成."""
        await self.broadcast({
            "type": "certificate_ready",
            "cert_id": cert_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })

    async def notify_contract_status_change(self, contract_id: str, old_status: str, new_status: str):
        """通知合约状态变更."""
        await self.broadcast({
            "type": "contract_status_change",
            "contract_id": contract_id,
            "old_status": old_status,
            "new_status": new_status,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })

    async def notify_infringement_detected(self, work_id: str, severity: str):
        """通知侵权监测发现."""
        await self.broadcast({
            "type": "infringement_detected",
            "work_id": work_id,
            "severity": severity,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })

    async def notify_new_message(self, session_id: str, sender_id: str, content: str):
        """通知新消息."""
        await self.broadcast({
            "type": "new_message",
            "session_id": session_id,
            "sender_id": sender_id,
            "content": content[:200],  # 截断长内容
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })

    async def notify_monitor_alert(self, work_id: str, alert_type: str, severity: str):
        """通知监测告警."""
        await self.broadcast({
            "type": "monitor_alert",
            "work_id": work_id,
            "alert_type": alert_type,
            "severity": severity,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })

    async def notify_contract_change(self, contract_id: str, status: str):
        """通知合约状态变更."""
        await self.broadcast({
            "type": "contract_change",
            "contract_id": contract_id,
            "status": status,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })

    async def notify_notification(self, title: str, body: str, category: str):
        """通知系统通知."""
        await self.broadcast({
            "type": "notification",
            "title": title,
            "body": body,
            "category": category,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })

    @property
    def active_connections(self) -> int:
        return sum(len(v) for v in self._connections.values())

    @property
    def connected_clients(self) -> list:
        """返回已连接的 client_id 列表."""
        return list(self._connections.keys())


# 全局 WebSocket 连接管理器
manager = ConnectionManager()
