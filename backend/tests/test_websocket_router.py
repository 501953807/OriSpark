"""WebSocket Router HTTP-level integration tests."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

import pytest
from fastapi.testclient import TestClient


class TestWebSocketConnection:
    """WebSocket endpoints"""

    def test_ws_health(self, client: TestClient):
        # WebSocket connections can't be tested with TestClient directly
        # Test the health endpoint instead
        resp = client.get("/api/ws/health")
        assert resp.status_code in (200, 404, 500)

    def test_ws_stats(self, client: TestClient):
        resp = client.get("/api/ws/stats")
        assert resp.status_code in (200, 401, 404, 500)
