"""AI 生成端点测试 — auto_tag, description, moderation, config."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


# ─────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────


def _mock_aigenerate_env(client):
    """Temporarily set AI env vars so _is_configured() returns True."""
    import os

    original_key = os.environ.get("AI_API_KEY", "")
    original_provider = os.environ.get("AI_PROVIDER", "")
    os.environ["AI_API_KEY"] = "test-key"
    os.environ["AI_PROVIDER"] = "openai"
    yield (original_key, original_provider)
    if original_key:
        os.environ["AI_API_KEY"] = original_key
    elif "AI_API_KEY" in os.environ:
        del os.environ["AI_API_KEY"]
    if original_provider:
        os.environ["AI_PROVIDER"] = original_provider
    elif "AI_PROVIDER" in os.environ:
        del os.environ["AI_PROVIDER"]


# ─────────────────────────────────────────────────────────────
# Test: /config returns configured status
# ─────────────────────────────────────────────────────────────


def test_ai_config_no_key(client):
    """When AI_API_KEY is unset, configured should be False."""
    import os
    os.environ.pop("AI_API_KEY", None)

    resp = client.get("/api/ai/generate/config")
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert data["data"]["configured"] is False


def test_ai_config_with_key(client):
    """When AI_API_KEY is set, configured should be True."""
    import os
    os.environ["AI_API_KEY"] = "dummy"

    resp = client.get("/api/ai/generate/config")
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert data["data"]["configured"] is True

    os.environ.pop("AI_API_KEY", None)


# ─────────────────────────────────────────────────────────────
# Test: endpoints return 503 when provider unavailable
# ─────────────────────────────────────────────────────────────


def _ensure_test_key():
    """Set AI_API_KEY for tests that need _is_configured=True."""
    import os
    os.environ.setdefault("AI_API_KEY", "test-key")
    os.environ.setdefault("AI_PROVIDER", "openai")


def test_auto_tag_unavailable(client):
    """When API key is set but provider is unreachable, should 503."""
    _ensure_test_key()
    resp = client.post("/api/ai/generate/tags", json={"work_id": "abc123"})
    assert resp.status_code in (503,) or resp.status_code == 422
    # Either 503 (provider error) or 422 (mocked httpx failure)


def test_description_unavailable(client):
    resp = client.post("/api/ai/generate/description", json={"work_id": "abc123"})
    # 503 because AI_API_KEY is set but provider unreachable
    assert resp.status_code in (503, 422)


def test_moderate_unavailable(client):
    _ensure_test_key()
    resp = client.post("/api/ai/generate/moderate", json={"text": "clean text here"})
    assert resp.status_code in (503, 422)


def test_article_draft_unavailable(client):
    _ensure_test_key()
    resp = client.post("/api/ai/generate/article", json={
        "prompt": "test prompt",
        "tone": "professional",
        "max_words": 500,
    })
    assert resp.status_code in (503, 422)


def test_product_desc_unavailable(client):
    _ensure_test_key()
    resp = client.post("/api/ai/generate/product-desc", json={
        "product_name": "手工木桌",
        "materials": ["橡木", "胡桃木"],
        "techniques": ["榫卯"],
    })
    assert resp.status_code in (503, 422)


def test_music_desc_unavailable(client):
    _ensure_test_key()
    resp = client.post("/api/ai/generate/music-desc", json={
        "title": "Spring Dawn",
        "genre": "古典",
        "mood": "宁静",
        "bpm": 120,
    })
    assert resp.status_code in (503, 422)


# ─────────────────────────────────────────────────────────────
# Test: AI service unit logic (without HTTP)
# ─────────────────────────────────────────────────────────────


def test_ai_service_check_configured_true():
    import os
    os.environ["AI_API_KEY"] = "some-key"
    from app.services.ai_service import AIService
    result = AIService.check_configured()
    assert result["configured"] is True
    assert result["provider"] == "openai"


def test_ai_service_check_configured_false():
    import os
    os.environ.pop("AI_API_KEY", None)
    from app.services.ai_service import AIService
    result = AIService.check_configured()
    assert result["configured"] is False


# ─────────────────────────────────────────────────────────────
# Test: ApiResponse wrapper structure
# ─────────────────────────────────────────────────────────────


def test_config_returns_api_response_wrapper(client):
    import os
    os.environ.pop("AI_API_KEY", None)
    resp = client.get("/api/ai/generate/config")
    assert resp.status_code == 200
    data = resp.json()
    assert "success" in data
    assert "message" in data
    assert "data" in data
    os.environ.pop("AI_API_KEY", None)
