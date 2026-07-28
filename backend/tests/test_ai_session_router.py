"""AI Session Router HTTP-level integration tests — covers all 4 endpoints."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

import pytest
import time
import json
import base64


def _create_token(user_id: str) -> str:
    """Create a valid JWT token using the deps._sign function signature."""
    from app.deps import _sign
    header = {"alg": "HS256", "typ": "JWT"}
    exp = int(time.time()) + 3600  # 1 hour expiry
    payload = {"sub": user_id, "iat": int(time.time()), "exp": exp}

    def b64encode(data: str) -> str:
        return base64.urlsafe_b64encode(data.encode()).rstrip(b"=").decode()

    h = b64encode(json.dumps(header))
    p = b64encode(json.dumps(payload))
    sig = _sign(f"{h}.{p}")
    return f"{h}.{p}.{sig}"


def _auth_headers(user_id: str = "test_user") -> dict:
    """Return headers with a valid JWT token for the given user_id."""
    token = _create_token(user_id)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def work(db_session):
    """创建一个作品用于关联 AI session."""
    from app.models.work import Work
    w = Work(
        title="Test Artwork",
        file_path="/tmp/test_art.png",
        file_name="test_art.png",
        file_size=10240,
        file_type="image",
        file_extension="png",
        sha256="abc123def456" * 4,
        status="active",
    )
    db_session.add(w)
    db_session.commit()
    return w


_BASE = "/api/works"

# Use valid JWT tokens instead of "local" fallback
_AUTH = _auth_headers("test_user")


class TestCreateAiSession:
    """POST /works/{work_id}/ai-session"""

    def test_create_session_success(self, client, work):
        resp = client.post(
            f"{_BASE}/{work.id}/ai-session",
            json={
                "tool_name": "stable_diffusion",
                "prompt": "a beautiful landscape",
                "model_name": "sd-xl-v1.0",
                "seed": 42,
                "parameters": {"steps": 30, "cfg_scale": 7.5},
            },
            headers=_AUTH,
        )
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["tool_name"] == "stable_diffusion"
        assert data["work_id"] == work.id
        assert data["prompt"] == "a beautiful landscape"
        assert data["seed"] == 42
        assert data["model_name"] == "sd-xl-v1.0"

    def test_create_session_fails_for_unknown_work(self, client):
        resp = client.post(
            f"{_BASE}/nonexistent_work/ai-session",
            json={"tool_name": "dall_e"},
            headers=_AUTH,
        )
        assert resp.status_code == 404


class TestListAiSessions:
    """GET /works/{work_id}/ai-sessions"""

    def test_list_sessions_empty(self, client, work):
        resp = client.get(f"{_BASE}/{work.id}/ai-sessions")
        assert resp.status_code == 200
        assert resp.json()["data"] == []

    def test_list_sessions_with_data(self, client, work):
        # Create two sessions
        for tool in ["stable_diffusion", "midjourney"]:
            client.post(
                f"{_BASE}/{work.id}/ai-session",
                json={"tool_name": tool, "prompt": f"test {tool}"},
                headers=_AUTH,
            )
        resp = client.get(f"{_BASE}/{work.id}/ai-sessions")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert len(data) >= 2
        tools = [item["tool_name"] for item in data]
        assert "stable_diffusion" in tools
        assert "midjourney" in tools

    def test_list_for_unknown_work(self, client):
        resp = client.get(f"{_BASE}/nonexistent_work/ai-sessions")
        assert resp.status_code == 404


class TestUpdateAiSession:
    """PATCH /works/{work_id}/ai-session/{session_id}"""

    def test_update_session_success(self, client, work):
        create_resp = client.post(
            f"{_BASE}/{work.id}/ai-session",
            json={"tool_name": "stable_diffusion", "prompt": "original prompt"},
            headers=_AUTH,
        )
        session_id = create_resp.json()["data"]["id"]
        resp = client.patch(
            f"{_BASE}/{work.id}/ai-session/{session_id}",
            json={"prompt": "updated prompt", "negative_prompt": "blurry"},
            headers=_AUTH,
        )
        assert resp.status_code == 200
        assert resp.json()["message"] == "会话记录更新成功"

    def test_update_nonexistent_session(self, client, work):
        resp = client.patch(
            f"{_BASE}/{work.id}/ai-session/nonexist",
            json={"prompt": "new prompt"},
            headers=_AUTH,
        )
        assert resp.status_code == 404


class TestDeleteAiSession:
    """DELETE /works/{work_id}/ai-session/{session_id}"""

    def test_delete_session_success(self, client, work):
        create_resp = client.post(
            f"{_BASE}/{work.id}/ai-session",
            json={"tool_name": "dall_e"},
            headers=_AUTH,
        )
        session_id = create_resp.json()["data"]["id"]
        resp = client.delete(
            f"{_BASE}/{work.id}/ai-session/{session_id}",
            headers=_AUTH,
        )
        assert resp.status_code == 200
        # Verify it's gone
        list_resp = client.get(f"{_BASE}/{work.id}/ai-sessions")
        data = list_resp.json()["data"]
        ids = [item["id"] for item in data]
        assert session_id not in ids

    def test_delete_nonexistent_session(self, client, work):
        resp = client.delete(
            f"{_BASE}/{work.id}/ai-session/nonexist",
            headers=_AUTH,
        )
        assert resp.status_code == 404
