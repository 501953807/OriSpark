import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

import pytest
from app.services.ai_training_service import generate_exclude_clause, upsert_ai_license
from app.models.ai_training_license import CCProtocol


# ─────────────────────────────────────────────────────────────
# Unit tests: service layer
# ─────────────────────────────────────────────────────────────


def test_generate_exclude_clause_cc0():
    clause = generate_exclude_clause(CCProtocol.CC0)
    assert "AI Training Exclusion" in clause
    assert "Machine Learning" in clause


def test_generate_exclude_clause_cc_by_nc():
    clause = generate_exclude_clause(CCProtocol.CC_BY_NC)
    assert "AI Training Exclusion" in clause
    assert "CC-BY-NC already restricts commercial use" in clause


def test_generate_exclude_clause_other():
    # CC-BY has no special exclusion needed (non-commercial already implied)
    clause = generate_exclude_clause(CCProtocol.CC_BY)
    assert clause == ""


# ─────────────────────────────────────────────────────────────
# HTTP-level integration tests for ai_training router
# ─────────────────────────────────────────────────────────────


@pytest.fixture
def work(db_session):
    """Create a work to associate AI training license with."""
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


_BASE = "/api/ai-training"


class TestGetAiLicense:
    """GET /ai-training/{work_id}"""

    def test_get_license_not_found(self, client, work):
        """When no license exists for the work, should return 404."""
        resp = client.get(f"{_BASE}/{work.id}")
        assert resp.status_code == 404
        data = resp.json()
        assert data["detail"] == "未找到AI授权配置"

    def test_get_license_after_upsert(self, client, work):
        """After creating a license via PUT, GET should return it."""
        # First create via PUT
        client.put(
            f"{_BASE}/{work.id}",
            json={
                "work_id": work.id,
                "enabled": True,
                "cc_protocol": "CC-BY",
                "price_per_use_cents": 10,
            },
        )
        # Then retrieve via GET — GET returns the model directly (no ApiResponse wrapper)
        resp = client.get(f"{_BASE}/{work.id}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["work_id"] == work.id
        assert data["enabled"] is True
        assert data["cc_protocol"] == "CC-BY"
        assert data["price_per_use_cents"] == 10

    def test_get_license_unknown_work(self, client):
        """GET for a non-existent work should return 404."""
        resp = client.get(f"{_BASE}/nonexistent_work_id")
        assert resp.status_code == 404


class TestUpdateAiLicense:
    """PUT /ai-training/{work_id}"""

    def test_upsert_license_enabled(self, client, work):
        """Creating an enabled license should set exclude_ai_training_clause."""
        resp = client.put(
            f"{_BASE}/{work.id}",
            json={
                "work_id": work.id,
                "enabled": True,
                "cc_protocol": "CC0",
                "price_per_use_cents": 5,
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["work_id"] == work.id
        assert data["enabled"] is True
        assert data["cc_protocol"] == "CC0"
        assert data["price_per_use_cents"] == 5
        assert data["exclude_ai_training_clause"] is not None
        assert "AI Training Exclusion" in data["exclude_ai_training_clause"]

    def test_upsert_license_disabled(self, client, work):
        """Creating a disabled license should have no exclude clause."""
        resp = client.put(
            f"{_BASE}/{work.id}",
            json={
                "work_id": work.id,
                "enabled": False,
                "cc_protocol": "CC-BY-NC",
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["enabled"] is False
        assert data["exclude_ai_training_clause"] is None

    def test_upsert_license_default_values(self, client, work):
        """Omitting optional fields should use defaults (CC0, price=5)."""
        resp = client.put(
            f"{_BASE}/{work.id}",
            json={"work_id": work.id, "enabled": True},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["cc_protocol"] == "CC0"
        assert data["price_per_use_cents"] == 5

    def test_upsert_license_overwrite_existing(self, client, work):
        """Updating an existing license should overwrite previous values."""
        # First create with CC0
        resp1 = client.put(
            f"{_BASE}/{work.id}",
            json={"work_id": work.id, "enabled": True, "cc_protocol": "CC0"},
        )
        assert resp1.status_code == 200
        assert resp1.json()["cc_protocol"] == "CC0"

        # Update to CC_BY_NC
        resp2 = client.put(
            f"{_BASE}/{work.id}",
            json={
                "work_id": work.id,
                "enabled": True,
                "cc_protocol": "CC-BY-NC",
                "price_per_use_cents": 20,
            },
        )
        assert resp2.status_code == 200
        data = resp2.json()
        assert data["cc_protocol"] == "CC-BY-NC"
        assert data["price_per_use_cents"] == 20
        assert "CC-BY-NC already restricts commercial use" in data["exclude_ai_training_clause"]

    def test_upsert_license_toggle_enabled_off(self, client, work):
        """Toggling enabled=False should clear the exclude clause."""
        # Create enabled
        client.put(
            f"{_BASE}/{work.id}",
            json={"work_id": work.id, "enabled": True, "cc_protocol": "CC-BY-SA"},
        )
        resp1 = client.get(f"{_BASE}/{work.id}")
        assert resp1.json()["exclude_ai_training_clause"] is not None

        # Disable
        resp2 = client.put(
            f"{_BASE}/{work.id}",
            json={"work_id": work.id, "enabled": False},
        )
        assert resp2.status_code == 200
        assert resp2.json()["exclude_ai_training_clause"] is None

    def test_upsert_all_cc_protocols(self, client, work):
        """Test all CC protocol values are accepted (hyphenated format)."""
        for protocol in ["CC0", "CC-BY", "CC-BY-NC", "CC-BY-SA", "CC-BY-NC-SA", "CC-BY-NC-ND"]:
            resp = client.put(
                f"{_BASE}/{work.id}",
                json={"work_id": work.id, "enabled": True, "cc_protocol": protocol},
            )
            assert resp.status_code == 200, f"Failed for protocol {protocol}"
            data = resp.json()
            assert data["cc_protocol"] == protocol
