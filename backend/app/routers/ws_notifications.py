"""通知 WebSocket 端点 — 按 user_id 隔离推送."""

import logging
from typing import Dict, Set

from fastapi import APIRouter, Depends, Query, WebSocket, WebSocketDisconnect

from app.deps import _verify_token
from app.services.websocket_manager import manager

logger = logging.getLogger(__name__)
router = APIRouter()

_connections: Dict[str, Set[WebSocket]] = {}


@router.websocket("/ws/notifications")
async def notification_ws(websocket: WebSocket, token: str = Query(...)):
    """WebSocket 实时推送新通知，通过查询参数 token 认证."""
    user_id = _verify_token(token)
    if not user_id:
        await websocket.close(code=4001)
        return

    await websocket.accept()

    if user_id not in _connections:
        _connections[user_id] = set()
    _connections[user_id].add(websocket)

    try:
        while True:
            data = await websocket.receive_json()
            msg_type = data.get("type", "")
            if msg_type == "ping":
                await websocket.send_json({"type": "pong"})
            elif msg_type == "subscribe":
                await websocket.send_json({"type": "subscribed", "user_id": user_id})
    except WebSocketDisconnect:
        pass
    except Exception:
        logger.warning("WebSocket notification error for user %s", user_id)
    finally:
        _connections.get(user_id, set()).discard(websocket)
        if user_id in _connections and not _connections[user_id]:
            del _connections[user_id]


async def notify_realtime(user_id: str, notification: dict) -> None:
    """向指定用户的 WebSocket 客户端推送新通知."""
    if user_id not in _connections or not _connections[user_id]:
        return
    dead = set()
    for ws in _connections[user_id]:
        try:
            await ws.send_json(notification)
        except Exception:
            dead.add(ws)
    _connections[user_id] -= dead
    if not _connections[user_id]:
        del _connections[user_id]
