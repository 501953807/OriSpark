"""WebSocket 路由."""

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
