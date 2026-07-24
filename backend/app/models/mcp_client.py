"""MCP Client 外部创作工具连接配置模型."""

from datetime import datetime

from sqlalchemy import (
    Column, String, Integer, Text, Boolean, DateTime, JSON, Index, ForeignKey,
)

from app.database import Base
from app.models.work import generate_uuid


class MCPClientConfig(Base):
    """MCP Client 外部工具连接配置表."""
    __tablename__ = "mcp_client_configs"

    id = Column(String(32), primary_key=True, default=generate_uuid)
    name = Column(String(100), nullable=False, unique=True)
    description = Column(Text, nullable=True)
    endpoint_url = Column(String(500), nullable=False)
    protocol = Column(String(20), default="http", comment="http/sse/stdio")
    auth_type = Column(String(50), default="none", comment="bearer_token/api_key/oauth2/custom")
    auth_token = Column(Text, nullable=True, comment="加密存储的认证令牌")
    timeout_seconds = Column(Integer, default=30)
    retry_count = Column(Integer, default=3)
    is_active = Column(Boolean, default=True)
    last_connected_at = Column(DateTime, nullable=True)
    last_error = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index("idx_mcp_config_name", "name"),
        Index("idx_mcp_config_active", "is_active"),
    )


class ToolEvent(Base):
    """外部创作工具事件记录表."""
    __tablename__ = "tool_events"

    id = Column(String(32), primary_key=True, default=generate_uuid)
    config_id = Column(String(32), ForeignKey("mcp_client_configs.id", ondelete="CASCADE"), nullable=False)
    event_type = Column(String(100), nullable=False, comment="如 file_saved, selection_changed, render_started")
    event_data = Column(JSON, nullable=True, comment="事件数据载荷")
    work_id = Column(String(32), nullable=True, comment="关联的作品 ID")
    user_id = Column(String(32), nullable=True, comment="触发事件的用户 ID")
    session_id = Column(String(32), nullable=True, comment="关联的 AI 会话 ID")
    received_at = Column(DateTime, default=datetime.utcnow, index=True)
    processed = Column(Boolean, default=False)
    processed_at = Column(DateTime, nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("idx_tool_event_config", "config_id"),
        Index("idx_tool_event_work", "work_id"),
        Index("idx_tool_event_session", "session_id"),
    )


class ExternalToolConnection(Base):
    """外部创作工具实时连接状态表."""
    __tablename__ = "external_tool_connections"

    id = Column(String(32), primary_key=True, default=generate_uuid)
    config_id = Column(String(32), ForeignKey("mcp_client_configs.id", ondelete="CASCADE"), nullable=False)
    connection_id = Column(String(100), nullable=False, comment="外部工具的会话标识")
    status = Column(String(20), default="disconnected", comment="connected/disconnected/error")
    connected_at = Column(DateTime, nullable=True)
    disconnected_at = Column(DateTime, nullable=True)
    last_heartbeat_at = Column(DateTime, nullable=True)
    event_count = Column(Integer, default=0)
    conn_metadata = Column(JSON, nullable=True, comment="连接元数据（如工具版本、插件名）")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index("idx_ext_conn_config", "config_id"),
        Index("idx_ext_conn_status", "status"),
    )
