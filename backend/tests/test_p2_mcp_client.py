"""MCP Client 集成测试 — 外部创作工具连接、事件流、会话关联."""

import pytest
import uuid
from datetime import datetime
from unittest.mock import patch, MagicMock

from app.models.mcp_client import MCPClientConfig, ToolEvent, ExternalToolConnection
from app.models.ai_session import AiCreationSession
from app.models.work import Work
from app.services.mcp_client_service import MCPClientService


def _uid(prefix="mcp_"):
    return f"{prefix}{uuid.uuid4().hex[:12]}"


def _create_config(db, name="Figma Plugin", **kwargs):
    defaults = dict(
        endpoint_url="http://localhost:3000/mcp",
        protocol="http",
        auth_type="none",
        timeout_seconds=30,
        retry_count=3,
    )
    defaults.update(kwargs)
    config = MCPClientService.create_config(db=db, name=name, **defaults)
    db.commit()
    return config


class MockSyncResponse:
    def __init__(self, json_data=None):
        self._json_data = json_data or {}

    def raise_for_status(self):
        pass

    def json(self):
        return self._json_data


class MockSyncClient:
    def __init__(self, responses=None):
        self.responses = responses or [MockSyncResponse({"result": {"protocolVersion": "2024-11-05"}})]
        self.calls = []

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass

    def post(self, url, json=None, headers=None):
        self.calls.append((url, json))
        if self.responses:
            return self.responses.pop(0)
        return MockSyncResponse({})


class TestMCPClientConfigCRUD:
    def test_create_config(self, db_session):
        config = _create_config(db_session, name="DaVinci Resolve")
        assert config.name == "DaVinci Resolve"
        assert config.endpoint_url == "http://localhost:3000/mcp"
        assert config.auth_type == "none"
        assert config.is_active is True

    def test_get_config(self, db_session):
        config = _create_config(db_session)
        found = MCPClientService.get_config(db_session, config.id)
        assert found is not None
        assert found.name == "Figma Plugin"

    def test_get_configs_list(self, db_session):
        _create_config(db_session, name="Figma Plugin")
        _create_config(db_session, name="Adobe XD")
        configs = MCPClientService.get_configs(db_session, active_only=True)
        assert len(configs) >= 2
        names = [c.name for c in configs]
        assert "Figma Plugin" in names
        assert "Adobe XD" in names

    def test_update_config(self, db_session):
        config = _create_config(db_session)
        updated = MCPClientService.update_config(db_session, config.id, name="Figma Pro")
        assert updated.name == "Figma Pro"

    def test_update_nonexistent_raises(self, db_session):
        with pytest.raises(ValueError, match="配置不存在"):
            MCPClientService.update_config(db_session, "nonexistent", name="x")


class TestExternalToolConnection:
    def test_connect_tool_success(self, db_session):
        config = _create_config(db_session)
        client = MockSyncClient()

        with patch("app.services.mcp_client_service.httpx.Client", return_value=client):
            connection = MCPClientService.connect_tool(db_session, config.id)

        assert connection.status == "connected"
        assert connection.connected_at is not None
        assert config.last_connected_at is not None
        assert config.last_error is None

    def test_disconnect_tool(self, db_session):
        config = _create_config(db_session)
        client = MockSyncClient()

        with patch("app.services.mcp_client_service.httpx.Client", return_value=client):
            conn = MCPClientService.connect_tool(db_session, config.id)

        disconnected = MCPClientService.disconnect_tool(db_session, config.id, conn.id)
        assert disconnected.status == "disconnected"
        assert disconnected.disconnected_at is not None

    def test_disconnect_nonexistent_raises(self, db_session):
        config = _create_config(db_session)
        with pytest.raises(ValueError, match="连接不存在"):
            MCPClientService.disconnect_tool(db_session, config.id, "fake-id")

    def test_get_connections(self, db_session):
        connections = MCPClientService.get_connections(db_session)
        assert isinstance(connections, list)

    def test_get_connections_filter_by_status(self, db_session):
        config = _create_config(db_session)
        client = MockSyncClient()

        with patch("app.services.mcp_client_service.httpx.Client", return_value=client):
            MCPClientService.connect_tool(db_session, config.id)

        connected = MCPClientService.get_connections(db_session, status="connected")
        assert len(connected) >= 1
        assert all(c.status == "connected" for c in connected)


class TestToolEvents:
    def test_receive_event(self, db_session):
        config = _create_config(db_session)
        event = MCPClientService.receive_event(
            db=db_session,
            config_id=config.id,
            event_type="file_saved",
            event_data={"file_path": "/tmp/test.figma"},
            work_id=_uid("w_"),
            user_id=_uid("u_"),
        )
        assert event.event_type == "file_saved"
        assert event.processed is False
        assert event.work_id is not None

    def test_receive_event_updates_connection_count(self, db_session):
        config = _create_config(db_session)
        client = MockSyncClient()

        with patch("app.services.mcp_client_service.httpx.Client", return_value=client):
            conn = MCPClientService.connect_tool(db_session, config.id)

        event = MCPClientService.receive_event(
            db=db_session,
            config_id=config.id,
            event_type="selection_changed",
            event_data={"selected": ["layer-1"]},
            session_id=conn.id,
        )
        db_session.refresh(conn)
        assert conn.event_count == 1
        assert conn.last_heartbeat_at is not None

    def test_get_events_filter_by_work_id(self, db_session):
        config = _create_config(db_session)
        work_id = _uid("w_")
        MCPClientService.receive_event(
            db=db_session, config_id=config.id, event_type="render_started", event_data={}, work_id=work_id
        )
        events = MCPClientService.get_events(db_session, work_id=work_id)
        assert len(events) >= 1
        assert all(e.work_id == work_id for e in events)

    def test_get_events_filter_by_processed(self, db_session):
        config = _create_config(db_session)
        MCPClientService.receive_event(
            db=db_session, config_id=config.id, event_type="test", event_data={}
        )
        unprocessed = MCPClientService.get_events(db_session, processed=False)
        assert all(not e.processed for e in unprocessed)


class TestAutoLinkSession:
    def test_auto_link_event_to_session(self, db_session):
        config = _create_config(db_session)
        work = Work(
            id=_uid("w_"),
            title="test work",
            file_path="/tmp/test_work",
            file_name="test_work",
            file_size=0,
            file_type="image",
            file_extension="png",
            status="active",
            created_at=datetime.utcnow(),
        )
        db_session.add(work)
        db_session.flush()

        session = AiCreationSession(
            id=_uid("s_"),
            work_id=work.id,
            tool_name="DALL-E",
            prompt="a sunset over mountains",
            created_at=datetime.utcnow(),
        )
        db_session.add(session)
        db_session.flush()

        event = MCPClientService.receive_event(
            db=db_session,
            config_id=config.id,
            event_type="export_started",
            event_data={"format": "png"},
            work_id=work.id,
        )

        linked = MCPClientService.auto_link_session(
            db=db_session,
            event_id=event.id,
            work_id=work.id,
            session_id=session.id,
        )
        assert linked.session_id == session.id
        assert linked.processed is True
        assert linked.processed_at is not None
        assert linked.error_message is None

    def test_auto_link_nonexistent_event_raises(self, db_session):
        with pytest.raises(ValueError, match="事件不存在"):
            MCPClientService.auto_link_session(db_session, "fake-event-id", work_id="w1")


class TestCallTool:
    def test_call_tool_success(self, db_session):
        config = _create_config(db_session)
        mock_result = {
            "jsonrpc": "2.0",
            "result": {"content": [{"type": "text", "text": "ok"}]},
        }

        client = MockSyncClient(responses=[MockSyncResponse(mock_result)])

        with patch("app.services.mcp_client_service.httpx.Client", return_value=client):
            result = MCPClientService.call_tool(db_session, config.id, "export_image", {"path": "/tmp/out.png"})

        assert result["result"]["content"][0]["text"] == "ok"

    def test_call_tool_nonexistent_config_raises(self, db_session):
        with pytest.raises(ValueError, match="配置不存在"):
            MCPClientService.call_tool(db_session, "fake-config", "any", {})
