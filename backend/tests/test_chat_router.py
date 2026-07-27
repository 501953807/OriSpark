"""Chat Router HTTP-level integration tests."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

import pytest


_BASE = "/api/chat"


class TestListSessions:
    """GET /chat/sessions"""

    def test_list_empty(self, client):
        resp = client.get(f"{_BASE}/sessions")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)


class TestStartSession:
    """POST /chat/sessions"""

    def test_start_session(self, client):
        resp = client.post(f"{_BASE}/sessions", params={
            "partner_id": "test_partner",
        })
        assert resp.status_code in (200, 404)  # 200 if partner exists, 404 if not

    def test_start_self_chat(self, client):
        resp = client.post(f"{_BASE}/sessions", params={
            "partner_id": "local",  # fallback auth user
        })
        assert resp.status_code == 400


class TestListMessages:
    """GET /chat/sessions/{session_id}/messages"""

    def test_messages_nonexistent_session(self, client):
        resp = client.get(f"{_BASE}/sessions/nonexistent_session/messages")
        assert resp.status_code in (404, 500)


class TestSendMessage:
    """POST /chat/sessions/{session_id}/messages"""

    def test_send_empty_message(self, client):
        resp = client.post(f"{_BASE}/sessions/test_session/messages", params={
            "content": "   ",
        })
        assert resp.status_code in (400, 422)

    def test_send_message_nonexistent_session(self, client):
        resp = client.post(f"{_BASE}/sessions/nonexistent/messages", params={
            "content": "Hello world",
        })
        assert resp.status_code in (404, 500)
