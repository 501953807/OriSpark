"""WebSocket 路由."""

import asyncio
from datetime import datetime
from typing import Dict, Set

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.services.websocket_manager import manager

router = APIRouter()


@router.websocket("/ws/notify")
async def websocket_notify(websocket: WebSocket):
    """WebSocket 实时通知端点."""
    client_id = "default"
    await manager.connect(websocket, client_id)

    try:
        # 发送连接确认
        await websocket.send_json({
            "type": "connected",
            "message": "WebSocket 已连接",
            "active_connections": manager.active_connections,
        })

        # 保持连接，接收客户端消息
        while True:
            data = await websocket.receive_json()
            msg_type = data.get("type", "")

            if msg_type == "ping":
                await websocket.send_json({"type": "pong"})
            elif msg_type == "subscribe":
                client_id = data.get("client_id", "default")
                await manager.connect(websocket, client_id)

    except WebSocketDisconnect:
        manager.disconnect(websocket, client_id)
    except Exception:
        manager.disconnect(websocket, client_id)


# ── Chat WebSocket ────────────────────────────────────────────────

# 会话级 WebSocket 连接管理
_chat_connections: Dict[str, Dict[str, Set[WebSocket]]] = {}
_chat_lock = asyncio.Lock()


async def _get_session_connections(session_id: str) -> Dict[str, Set[WebSocket]]:
    """获取或创建会话的连接字典."""
    async with _chat_lock:
        if session_id not in _chat_connections:
            _chat_connections[session_id] = {"A": set(), "B": set()}
        return _chat_connections[session_id]


async def _cleanup_session(session_id: str):
    """清理空会话的连接记录."""
    async with _chat_lock:
        if session_id in _chat_connections:
            clients = _chat_connections[session_id]
            total = sum(len(ws_set) for ws_set in clients.values())
            if total == 0:
                del _chat_connections[session_id]


@router.websocket("/ws/chat/{session_id}")
async def websocket_chat(websocket: WebSocket, session_id: str):
    """WebSocket 聊天端点 — 支持实时双向消息收发.

    协议:
    - 客户端连接后发送 {"type": "join", "user_id": "..."} 加入会话
    - 服务端回复 {"type": "joined", "session_id": "..."}
    - 客户端发送 {"type": "message", "content": "..."} 发送消息
    - 服务端广播 {"type": "message", "sender_id": "...", "content": "...", "created_at": "..."}
    - 心跳: 客户端发送 {"type": "ping"}, 服务端回复 {"type": "pong"}
    """
    await websocket.accept()

    user_id = None
    joined = False

    try:
        # 等待客户端发送 join 消息
        while not joined:
            data = await websocket.receive_json()
            if data.get("type") == "join":
                user_id = data.get("user_id", "unknown")
                joined = True
                break
            elif data.get("type") == "ping":
                await websocket.send_json({"type": "pong"})

        # 获取会话连接池
        connections = await _get_session_connections(session_id)

        # 分配客户端角色 (A 或 B)
        role = None
        for r in ["A", "B"]:
            if len(connections[r]) < 1:
                role = r
                break

        if role is None:
            # 会话已满（双方都已连接），拒绝第三个
            await websocket.send_json({
                "type": "error",
                "message": "会话已达到最大连接数",
            })
            await websocket.close()
            return

        connections[role].add(websocket)

        # 发送加入确认
        await websocket.send_json({
            "type": "joined",
            "session_id": session_id,
            "role": role,
        })

        # 通知对方有人加入了
        other_role = "B" if role == "A" else "A"
        for ws in connections[other_role]:
            try:
                await ws.send_json({
                    "type": "peer_joined",
                    "user_id": user_id,
                })
            except Exception:
                pass

        # 主循环：接收和转发消息
        while True:
            data = await websocket.receive_json()
            msg_type = data.get("type", "")

            if msg_type == "ping":
                await websocket.send_json({"type": "pong"})

            elif msg_type == "message":
                content = data.get("content", "").strip()[:5000]
                if not content:
                    continue

                created_at = datetime.utcnow().isoformat()

                # 构建消息包
                msg_packet = {
                    "type": "message",
                    "sender_id": user_id,
                    "content": content,
                    "created_at": created_at,
                }

                # 广播给同一会话的所有其他客户端
                for r, ws_set in connections.items():
                    for ws in ws_set:
                        if ws != websocket:
                            try:
                                await ws.send_json(msg_packet)
                            except Exception:
                                pass

                # 同时发送给自己（用于乐观 UI 更新）
                await websocket.send_json(msg_packet)

    except WebSocketDisconnect:
        pass
    except Exception:
        pass
    finally:
        # 清理连接
        if role and session_id in _chat_connections:
            _chat_connections[session_id][role].discard(websocket)
            await _cleanup_session(session_id)
