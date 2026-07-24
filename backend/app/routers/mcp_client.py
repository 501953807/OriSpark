"""MCP Client 路由 — 外部创作工具连接管理."""

import json
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.mcp_client import MCPClientConfig, ToolEvent, ExternalToolConnection
from app.schemas.common import ApiResponse
from app.services.mcp_client_service import MCPClientService


router = APIRouter()


@router.post("/mcp-client/configs", response_model=ApiResponse)
async def create_config(
    body: dict,
    db: Session = Depends(get_db),
):
    """创建 MCP Client 配置."""
    try:
        config = MCPClientService.create_config(
            db=db,
            name=body["name"],
            endpoint_url=body["endpoint_url"],
            protocol=body.get("protocol", "http"),
            auth_type=body.get("auth_type", "none"),
            auth_token=body.get("auth_token"),
            description=body.get("description"),
            timeout_seconds=body.get("timeout_seconds", 30),
            retry_count=body.get("retry_count", 3),
        )
        return ApiResponse(
            success=True,
            data={
                "id": config.id,
                "name": config.name,
                "endpoint_url": config.endpoint_url,
                "protocol": config.protocol,
                "is_active": config.is_active,
            },
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/mcp-client/configs", response_model=ApiResponse)
async def list_configs(
    active_only: bool = True,
    limit: int = Query(default=20, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    """获取 MCP Client 配置列表."""
    configs = MCPClientService.get_configs(
        db=db, active_only=active_only, limit=limit, offset=offset
    )
    return ApiResponse(
        success=True,
        data=[
            {
                "id": c.id,
                "name": c.name,
                "endpoint_url": c.endpoint_url,
                "protocol": c.protocol,
                "auth_type": c.auth_type,
                "is_active": c.is_active,
                "last_connected_at": c.last_connected_at.isoformat() if c.last_connected_at else None,
                "created_at": c.created_at.isoformat() if c.created_at else None,
            }
            for c in configs
        ],
    )


@router.get("/mcp-client/configs/{config_id}", response_model=ApiResponse)
async def get_config(config_id: str, db: Session = Depends(get_db)):
    """获取单个配置."""
    config = MCPClientService.get_config(db, config_id)
    if not config:
        raise HTTPException(status_code=404, detail="配置不存在")
    return ApiResponse(
        success=True,
        data={
            "id": config.id,
            "name": config.name,
            "endpoint_url": config.endpoint_url,
            "protocol": config.protocol,
            "auth_type": config.auth_type,
            "is_active": config.is_active,
            "last_connected_at": config.last_connected_at.isoformat() if config.last_connected_at else None,
            "last_error": config.last_error,
            "created_at": config.created_at.isoformat() if config.created_at else None,
        },
    )


@router.patch("/mcp-client/configs/{config_id}", response_model=ApiResponse)
async def update_config(
    config_id: str,
    body: dict,
    db: Session = Depends(get_db),
):
    """更新配置."""
    try:
        config = MCPClientService.update_config(db, config_id, **body)
        return ApiResponse(
            success=True,
            data={"id": config.id, "name": config.name},
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/mcp-client/configs/{config_id}/connect", response_model=ApiResponse)
async def connect_tool(config_id: str, db: Session = Depends(get_db)):
    """连接到外部创作工具."""
    try:
        connection = await MCPClientService.connect_tool(db, config_id)
        return ApiResponse(
            success=True,
            data={
                "connection_id": connection.connection_id,
                "status": connection.status,
                "connected_at": connection.connected_at.isoformat() if connection.connected_at else None,
            },
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/mcp-client/connections/{connection_id}/disconnect", response_model=ApiResponse)
async def disconnect_tool(connection_id: str, db: Session = Depends(get_db)):
    """断开外部工具连接."""
    try:
        # 需要从连接中获取 config_id
        conn = db.query(ExternalToolConnection).filter(
            ExternalToolConnection.id == connection_id
        ).first()
        if not conn:
            raise HTTPException(status_code=404, detail="连接不存在")

        result = await MCPClientService.disconnect_tool(
            db, conn.config_id, connection_id
        )
        return ApiResponse(
            success=True,
            data={"status": result.status},
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/mcp-client/configs/{config_id}/call-tool", response_model=ApiResponse)
async def call_tool(
    config_id: str,
    body: dict,
    db: Session = Depends(get_db),
):
    """调用外部工具的 MCP 工具."""
    try:
        tool_name = body["tool_name"]
        arguments = body.get("arguments", {})
        result = await MCPClientService.call_tool(
            db, config_id, tool_name, arguments
        )
        return ApiResponse(success=True, data=result)
    except KeyError:
        raise HTTPException(status_code=400, detail="缺少 tool_name 参数")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/mcp-client/configs/{config_id}/events", response_model=ApiResponse)
async def receive_event(
    config_id: str,
    body: dict,
    db: Session = Depends(get_db),
):
    """接收并存储外部工具事件."""
    try:
        event = await MCPClientService.receive_event(
            db=db,
            config_id=config_id,
            event_type=body["event_type"],
            event_data=body.get("event_data", {}),
            work_id=body.get("work_id"),
            user_id=body.get("user_id"),
            session_id=body.get("session_id"),
        )
        return ApiResponse(
            success=True,
            data={
                "id": event.id,
                "event_type": event.event_type,
                "received_at": event.received_at.isoformat() if event.received_at else None,
            },
        )
    except KeyError:
        raise HTTPException(status_code=400, detail="缺少 event_type 参数")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/mcp-client/events", response_model=ApiResponse)
async def list_events(
    config_id: Optional[str] = None,
    work_id: Optional[str] = None,
    processed: Optional[bool] = None,
    limit: int = Query(default=50, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    """获取事件列表."""
    events = MCPClientService.get_events(
        db=db,
        config_id=config_id,
        work_id=work_id,
        processed=processed,
        limit=limit,
        offset=offset,
    )
    return ApiResponse(
        success=True,
        data=[
            {
                "id": e.id,
                "config_id": e.config_id,
                "event_type": e.event_type,
                "event_data": e.event_data,
                "work_id": e.work_id,
                "user_id": e.user_id,
                "session_id": e.session_id,
                "received_at": e.received_at.isoformat() if e.received_at else None,
                "processed": e.processed,
            }
            for e in events
        ],
    )


@router.post("/mcp-client/events/{event_id}/link", response_model=ApiResponse)
async def link_event_to_session(
    event_id: str,
    body: dict,
    db: Session = Depends(get_db),
):
    """将事件关联到 AI 会话."""
    try:
        event = MCPClientService.auto_link_session(
            db=db,
            event_id=event_id,
            work_id=body["work_id"],
            session_id=body.get("session_id"),
        )
        return ApiResponse(
            success=True,
            data={
                "id": event.id,
                "work_id": event.work_id,
                "session_id": event.session_id,
                "processed": event.processed,
            },
        )
    except KeyError:
        raise HTTPException(status_code=400, detail="缺少 work_id 参数")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/mcp-client/connections", response_model=ApiResponse)
async def list_connections(
    config_id: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = Query(default=20, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    """获取连接列表."""
    connections = MCPClientService.get_connections(
        db=db, config_id=config_id, status=status, limit=limit, offset=offset
    )
    return ApiResponse(
        success=True,
        data=[
            {
                "id": c.id,
                "config_id": c.config_id,
                "connection_id": c.connection_id,
                "status": c.status,
                "connected_at": c.connected_at.isoformat() if c.connected_at else None,
                "event_count": c.event_count,
                "conn_metadata": c.conn_metadata,
            }
            for c in connections
        ],
    )
