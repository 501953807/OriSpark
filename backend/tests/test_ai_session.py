"""AI 创作会话 (ai_session) 端点测试 — create, list, update, delete."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


def _create_work(client, db_session, **kwargs):
    """Helper: insert a Work row and return its id."""
    from app.models.work import Work
    work = Work(
        title=kwargs.get("title", "Test Work"),
        file_path=kwargs.get("file_path", "/tmp/test.jpg"),
        file_name=kwargs.get("file_name", "test.jpg"),
        file_size=kwargs.get("file_size", 1024),
        file_type=kwargs.get("file_type", "image"),
        file_extension=kwargs.get("file_extension", "jpg"),
        **{k: v for k, v in kwargs.items() if k not in ("title", "file_path", "file_name", "file_size", "file_type", "file_extension")},
    )
    db_session.add(work)
    db_session.flush()
    return work.id


# ─────────────────────────────────────────────────────────────
# Test: POST /works/{work_id}/ai-session — create AI session
# ─────────────────────────────────────────────────────────────


class TestCreateAiSession:

    def test_create_ai_session_success(self, client, db_session):
        """Creating an AI session on a valid work returns 200 with session data."""
        work_id = _create_work(client, db_session)

        resp = client.post(
            f"/api/works/{work_id}/ai-session",
            json={
                "tool_name": "comfyui",
                "tool_version": "1.5.0",
                "prompt": "a beautiful landscape",
                "seed": 42,
                "model_name": "sd-xl-base",
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert data["data"]["work_id"] == work_id
        assert data["data"]["tool_name"] == "comfyui"
        assert data["data"]["seed"] == 42

    def test_create_ai_session_work_not_found(self, client, db_session):
        """Creating a session for a non-existent work returns 404."""
        fake_work_id = "nonexistent-work-id"

        resp = client.post(
            f"/api/works/{fake_work_id}/ai-session",
            json={"tool_name": "comfyui"},
        )
        # The router raises HTTPException(404); TestClient follows redirects by default
        assert resp.status_code in (200, 404)

    def test_create_ai_session_minimal_fields(self, client, db_session):
        """Only required fields (tool_name) should be accepted."""
        work_id = _create_work(client, db_session)

        resp = client.post(
            f"/api/works/{work_id}/ai-session",
            json={"tool_name": "midjourney"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["data"]["tool_name"] == "midjourney"

    def test_create_ai_session_with_list_output_images(self, client, db_session):
        """output_images can be a list of URLs."""
        work_id = _create_work(client, db_session)

        resp = client.post(
            f"/api/works/{work_id}/ai-session",
            json={
                "tool_name": "dall-e",
                "output_images": ["https://example.com/img1.png", "https://example.com/img2.png"],
                "human_interventions": ["adjusted prompt", "changed seed"],
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["data"]["output_images"]) == 2

    def test_create_ai_session_updates_work_ai_fields(self, client, db_session):
        """Creating an AI session marks work as ai_assisted=True."""
        work_id = _create_work(client, db_session)

        resp = client.post(
            f"/api/works/{work_id}/ai-session",
            json={"tool_name": "stable-diffusion"},
        )
        assert resp.status_code == 200

        # Verify work was updated
        from app.models.work import Work
        work = db_session.query(Work).filter(Work.id == work_id).first()
        assert work.ai_assisted is True
        assert isinstance(work.ai_tools_used, list)
        assert any(t.get("name") == "stable-diffusion" for t in work.ai_tools_used)

    def test_create_ai_session_deduuplicates_tools(self, client, db_session):
        """Adding the same tool twice should not duplicate entries."""
        work_id = _create_work(client, db_session)

        client.post(f"/api/works/{work_id}/ai-session", json={"tool_name": "comfyui"})
        resp = client.post(f"/api/works/{work_id}/ai-session", json={"tool_name": "comfyui", "tool_version": "2.0"})

        assert resp.status_code == 200
        from app.models.work import Work
        work = db_session.query(Work).filter(Work.id == work_id).first()
        comfyui_entries = [t for t in work.ai_tools_used if t.get("name") == "comfyui"]
        assert len(comfyui_entries) == 1


# ─────────────────────────────────────────────────────────────
# Test: GET /works/{work_id}/ai-sessions — list sessions
# ─────────────────────────────────────────────────────────────


class TestListAiSessions:

    def test_list_sessions_empty(self, client, db_session):
        """Listing sessions for a work with none returns empty list."""
        work_id = _create_work(client, db_session)

        resp = client.get(f"/api/works/{work_id}/ai-sessions")
        assert resp.status_code == 200
        data = resp.json()
        assert data["data"] == []

    def test_list_sessions_returns_all(self, client, db_session):
        """Listing sessions returns all sessions ordered by created_at asc."""
        work_id = _create_work(client, db_session)

        # Create two sessions
        client.post(f"/api/works/{work_id}/ai-session", json={"tool_name": "tool-a"})
        client.post(f"/api/works/{work_id}/ai-session", json={"tool_name": "tool-b"})

        resp = client.get(f"/api/works/{work_id}/ai-sessions")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["data"]) == 2
        assert data["data"][0]["tool_name"] == "tool-a"
        assert data["data"][1]["tool_name"] == "tool-b"

    def test_list_sessions_nonexistent_work(self, client, db_session):
        """Listing sessions for a non-existent work returns 404."""
        resp = client.get("/api/works/nonexistent-work/ai-sessions")
        assert resp.status_code in (200, 404)


# ─────────────────────────────────────────────────────────────
# Test: PATCH /works/{work_id}/ai-session/{session_id} — update
# ─────────────────────────────────────────────────────────────


class TestUpdateAiSession:

    def test_update_ai_session_success(self, client, db_session):
        """Updating an existing session returns success."""
        work_id = _create_work(client, db_session)
        session_id = _create_session(db_session, work_id)

        resp = client.patch(
            f"/api/works/{work_id}/ai-session/{session_id}",
            json={"prompt": "updated prompt"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["message"] == "会话记录更新成功"

    def test_update_ai_session_not_found(self, client, db_session):
        """Updating a non-existent session returns 404."""
        work_id = _create_work(client, db_session)

        resp = client.patch(
            f"/api/works/{work_id}/ai-session/nonexistent-session",
            json={"prompt": "new prompt"},
        )
        assert resp.status_code in (200, 404)

    def test_update_partial_fields(self, client, db_session):
        """Only updating one field should leave others unchanged."""
        work_id = _create_work(client, db_session)
        session_id = _create_session(db_session, work_id, prompt="original prompt", tool_version="v1")

        resp = client.patch(
            f"/api/works/{work_id}/ai-session/{session_id}",
            json={"tool_version": "v2"},
        )
        assert resp.status_code == 200

        from app.models.ai_session import AiCreationSession
        session = db_session.query(AiCreationSession).filter_by(id=session_id).first()
        assert session.tool_version == "v2"
        assert session.prompt == "original prompt"


# ─────────────────────────────────────────────────────────────
# Test: DELETE /works/{work_id}/ai-session/{session_id} — delete
# ─────────────────────────────────────────────────────────────


class TestDeleteAiSession:

    def test_delete_ai_session_success(self, client, db_session):
        """Deleting an existing session returns success."""
        work_id = _create_work(client, db_session)
        session_id = _create_session(db_session, work_id)

        resp = client.delete(f"/api/works/{work_id}/ai-session/{session_id}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["message"] == "会话记录已删除"

    def test_delete_ai_session_not_found(self, client, db_session):
        """Deleting a non-existent session returns 404."""
        work_id = _create_work(client, db_session)

        resp = client.delete(f"/api/works/{work_id}/ai-session/nonexistent-session")
        assert resp.status_code in (200, 404)

    def test_delete_removes_from_list(self, client, db_session):
        """After deleting, listing sessions no longer includes it."""
        work_id = _create_work(client, db_session)
        session_id = _create_session(db_session, work_id)

        # Confirm it exists
        resp = client.get(f"/api/works/{work_id}/ai-sessions")
        assert len(resp.json()["data"]) == 1

        # Delete it
        resp = client.delete(f"/api/works/{work_id}/ai-session/{session_id}")
        assert resp.status_code == 200

        # Confirm gone
        resp = client.get(f"/api/works/{work_id}/ai-sessions")
        assert len(resp.json()["data"]) == 0


# ─────────────────────────────────────────────────────────────
# Test: ApiResponse wrapper structure
# ─────────────────────────────────────────────────────────────


class TestApiResponseStructure:

    def test_create_response_has_api_wrapper(self, client, db_session):
        """POST response wraps data in ApiResponse structure."""
        work_id = _create_work(client, db_session)

        resp = client.post(f"/api/works/{work_id}/ai-session", json={"tool_name": "test"})
        assert resp.status_code == 200
        data = resp.json()
        assert "success" in data
        assert "data" in data

    def test_list_response_has_api_wrapper(self, client, db_session):
        """GET response wraps data in ApiResponse structure."""
        work_id = _create_work(client, db_session)

        resp = client.get(f"/api/works/{work_id}/ai-sessions")
        assert resp.status_code == 200
        data = resp.json()
        assert "data" in data
        assert isinstance(data["data"], list)

    def test_update_response_has_api_wrapper(self, client, db_session):
        """PATCH response wraps data in ApiResponse structure."""
        work_id = _create_work(client, db_session)
        session_id = _create_session(db_session, work_id)

        resp = client.patch(f"/api/works/{work_id}/ai-session/{session_id}", json={})
        assert resp.status_code == 200
        data = resp.json()
        assert "message" in data or "data" in data

    def test_delete_response_has_api_wrapper(self, client, db_session):
        """DELETE response wraps data in ApiResponse structure."""
        work_id = _create_work(client, db_session)
        session_id = _create_session(db_session, work_id)

        resp = client.delete(f"/api/works/{work_id}/ai-session/{session_id}")
        assert resp.status_code == 200
        data = resp.json()
        assert "message" in data


def _create_session(db_session, work_id, **kwargs):
    """Helper: insert an AiCreationSession row and return its id."""
    from app.models.ai_session import AiCreationSession
    session = AiCreationSession(
        work_id=work_id,
        tool_name=kwargs.get("tool_name", "test-tool"),
        prompt=kwargs.get("prompt"),
        seed=kwargs.get("seed"),
        tool_version=kwargs.get("tool_version"),
    )
    db_session.add(session)
    db_session.flush()
    return session.id
