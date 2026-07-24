"""MCP Client 出站服务 — 连接外部创作工具并接收事件流."""

import json
import uuid
from datetime import datetime, timedelta
from typing import Optional

import httpx
from sqlalchemy.orm import Session

from app.models.mcp_client import MCPClientConfig, ToolEvent, ExternalToolConnection


class MCPClientService:
    """MCP Client 服务 — 出站连接外部创作工具."""

    @classmethod
    def create_config(
        cls,
        db: Session,
        name: str,
        endpoint_url: str,
        protocol: str = "http",
        auth_type: str = "none",
        auth_token: Optional[str] = None,
        description: Optional[str] = None,
        timeout_seconds: int = 30,
        retry_count: int = 3,
    ) -> MCPClientConfig:
        """创建 MCP Client 配置."""
        config = MCPClientConfig(
            id=str(uuid.uuid4().hex),
            name=name,
            endpoint_url=endpoint_url,
            protocol=protocol,
            auth_type=auth_type,
            auth_token=auth_token,
            description=description,
            timeout_seconds=timeout_seconds,
            retry_count=retry_count,
        )
        db.add(config)
        db.commit()
        db.refresh(config)
        return config

    @classmethod
    def get_config(cls, db: Session, config_id: str) -> Optional[MCPClientConfig]:
        """获取配置."""
        return db.query(MCPClientConfig).filter(
            MCPClientConfig.id == config_id
        ).first()

    @classmethod
    def get_configs(
        cls,
        db: Session,
        active_only: bool = True,
        limit: int = 20,
        offset: int = 0,
    ) -> list[MCPClientConfig]:
        """获取配置列表."""
        query = db.query(MCPClientConfig)
        if active_only:
            query = query.filter(MCPClientConfig.is_active == True)
        return query.order_by(
            MCPClientConfig.created_at.desc()
        ).offset(offset).limit(limit).all()

    @classmethod
    def update_config(
        cls,
        db: Session,
        config_id: str,
        **kwargs,
    ) -> MCPClientConfig:
        """更新配置."""
        config = cls.get_config(db, config_id)
        if not config:
            raise ValueError("配置不存在")

        for key, value in kwargs.items():
            if hasattr(config, key):
                setattr(config, key, value)

        config.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(config)
        return config

    @classmethod
    def connect_tool(
        cls,
        db: Session,
        config_id: str,
        connection_id: Optional[str] = None,
    ) -> ExternalToolConnection:
        """连接到外部创作工具."""
        config = cls.get_config(db, config_id)
        if not config:
            raise ValueError("配置不存在")

        conn_id = connection_id or str(uuid.uuid4().hex)

        # 初始化 MCP 会话
        init_payload = {
            "jsonrpc": "2.0",
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {
                    "name": "oristudio-mcp-client",
                    "version": "1.0.0",
                },
            },
            "id": str(uuid.uuid4().hex[:12]),
        }

        headers = {"Content-Type": "application/json"}
        if config.auth_type == "bearer_token" and config.auth_token:
            headers["Authorization"] = f"Bearer {config.auth_token}"
        elif config.auth_type == "api_key" and config.auth_token:
            headers["X-API-Key"] = config.auth_token

        try:
            with httpx.Client(timeout=config.timeout_seconds) as client:
                response = client.post(
                    config.endpoint_url,
                    json=init_payload,
                    headers=headers,
                )
                response.raise_for_status()
                result = response.json()

                # 发送 initialized notification
                notify_payload = {
                    "jsonrpc": "2.0",
                    "method": "notifications/initialized",
                    "params": {},
                }
                client.post(
                    config.endpoint_url,
                    json=notify_payload,
                    headers=headers,
                )

                connection = ExternalToolConnection(
                    id=str(uuid.uuid4().hex),
                    config_id=config_id,
                    connection_id=conn_id,
                    status="connected",
                    connected_at=datetime.utcnow(),
                    last_heartbeat_at=datetime.utcnow(),
                    conn_metadata=result.get("result", {}),
                )
                db.add(connection)

                # 更新配置最后连接时间
                config.last_connected_at = datetime.utcnow()
                config.last_error = None
                db.commit()

                return connection

        except Exception as e:
            config.last_error = str(e)
            db.commit()
            raise ValueError(f"连接失败: {str(e)}")

    @classmethod
    def disconnect_tool(
        cls,
        db: Session,
        config_id: str,
        connection_id: str,
    ) -> ExternalToolConnection:
        """断开外部工具连接."""
        connection = db.query(ExternalToolConnection).filter(
            ExternalToolConnection.id == connection_id,
            ExternalToolConnection.config_id == config_id,
        ).first()

        if not connection:
            raise ValueError("连接不存在")

        connection.status = "disconnected"
        connection.disconnected_at = datetime.utcnow()
        db.commit()
        db.refresh(connection)
        return connection

    @classmethod
    def call_tool(
        cls,
        db: Session,
        config_id: str,
        tool_name: str,
        arguments: dict,
        connection_id: Optional[str] = None,
    ) -> dict:
        """调用外部工具的 MCP 工具."""
        config = cls.get_config(db, config_id)
        if not config:
            raise ValueError("配置不存在")

        headers = {"Content-Type": "application/json"}
        if config.auth_type == "bearer_token" and config.auth_token:
            headers["Authorization"] = f"Bearer {config.auth_token}"
        elif config.auth_type == "api_key" and config.auth_token:
            headers["X-API-Key"] = config.auth_token

        payload = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": arguments,
            },
            "id": str(uuid.uuid4().hex[:12]),
        }

        try:
            with httpx.Client(timeout=config.timeout_seconds) as client:
                response = client.post(
                    config.endpoint_url,
                    json=payload,
                    headers=headers,
                )
                response.raise_for_status()
                return response.json()

        except Exception as e:
            raise ValueError(f"工具调用失败: {str(e)}")

    @classmethod
    def receive_event(
        cls,
        db: Session,
        config_id: str,
        event_type: str,
        event_data: dict,
        work_id: Optional[str] = None,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
    ) -> ToolEvent:
        """接收并存储外部工具事件."""
        config = cls.get_config(db, config_id)
        if not config:
            raise ValueError("配置不存在")

        event = ToolEvent(
            id=str(uuid.uuid4().hex),
            config_id=config_id,
            event_type=event_type,
            event_data=event_data,
            work_id=work_id,
            user_id=user_id,
            session_id=session_id,
            received_at=datetime.utcnow(),
        )
        db.add(event)

        # 更新连接计数
        if session_id:
            connection = db.query(ExternalToolConnection).filter(
                ExternalToolConnection.id == session_id,
                ExternalToolConnection.config_id == config_id,
            ).first()
            if connection:
                connection.event_count += 1
                connection.last_heartbeat_at = datetime.utcnow()

        db.commit()
        db.refresh(event)
        return event

    @classmethod
    def auto_link_session(
        cls,
        db: Session,
        event_id: str,
        work_id: str,
        session_id: Optional[str] = None,
    ) -> ToolEvent:
        """自动关联事件到 AI 会话."""
        event = db.query(ToolEvent).filter(
            ToolEvent.id == event_id
        ).first()

        if not event:
            raise ValueError("事件不存在")

        event.work_id = work_id
        if session_id:
            event.session_id = session_id
        event.processed = True
        event.processed_at = datetime.utcnow()
        event.error_message = None

        db.commit()
        db.refresh(event)
        return event

    @classmethod
    def get_events(
        cls,
        db: Session,
        config_id: Optional[str] = None,
        work_id: Optional[str] = None,
        processed: Optional[bool] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[ToolEvent]:
        """获取事件列表."""
        query = db.query(ToolEvent)

        if config_id:
            query = query.filter(ToolEvent.config_id == config_id)
        if work_id:
            query = query.filter(ToolEvent.work_id == work_id)
        if processed is not None:
            query = query.filter(ToolEvent.processed == processed)

        return query.order_by(
            ToolEvent.received_at.desc()
        ).offset(offset).limit(limit).all()

    @classmethod
    def get_connections(
        cls,
        db: Session,
        config_id: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> list[ExternalToolConnection]:
        """获取连接列表."""
        query = db.query(ExternalToolConnection)

        if config_id:
            query = query.filter(ExternalToolConnection.config_id == config_id)
        if status:
            query = query.filter(ExternalToolConnection.status == status)

        return query.order_by(
            ExternalToolConnection.created_at.desc()
        ).offset(offset).limit(limit).all()
