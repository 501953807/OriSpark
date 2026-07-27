"""Risk Control Router HTTP-level integration tests."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

import pytest


_BASE = "/api/risk"


class TestEvaluateRisk:
    """POST /risk/evaluate"""

    def test_evaluate_risk(self, client):
        resp = client.post(f"{_BASE}/evaluate", params={
            "user_id": "test_user",
            "target_type": "user",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "id" in data
        assert "risk_score" in data
        assert "risk_level" in data

    def test_evaluate_risk_with_context(self, client):
        resp = client.post(f"{_BASE}/evaluate", params={
            "user_id": "test_user",
            "target_type": "transaction",
            "target_id": "tx_123",
        }, json={"ip": "192.168.1.1"})
        assert resp.status_code == 200


class TestBlacklist:
    """Blacklist CRUD"""

    def test_add_blacklist(self, client):
        resp = client.post(f"{_BASE}/blacklist", json={
            "user_id": "bad_user",
            "reason": "Spam detected",
            "category": "spam",
            "added_by": "admin",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "id" in data
        assert "user_id" in data

    def test_get_blacklist_status(self, client):
        resp = client.get(f"{_BASE}/blacklist/test_user/status")
        assert resp.status_code == 200
        data = resp.json()
        assert "user_id" in data
        assert "is_blacklisted" in data

    def test_remove_blacklist(self, client):
        resp = client.delete(f"{_BASE}/blacklist/test_user")
        assert resp.status_code == 200
        data = resp.json()
        assert "removed" in data


class TestRules:
    """Risk rule management"""

    def test_list_rules(self, client):
        resp = client.get(f"{_BASE}/rules")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)

    def test_list_rules_filtered(self, client):
        resp = client.get(f"{_BASE}/rules", params={
            "rule_type": "spam",
            "enabled_only": "true",
        })
        assert resp.status_code == 200

    def test_create_rule(self, client):
        resp = client.post(f"{_BASE}/rules", json={
            "name": "Test Rule",
            "description": "A test rule",
            "rule_type": "spam",
            "condition": {"field": "count", "op": "gt", "value": 100},
            "severity": "high",
            "action": "block",
            "weight": 10,
            "enabled": True,
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "id" in data
        assert data["name"] == "Test Rule"

    def test_update_rule(self, client):
        # First create a rule to update
        create_resp = client.post(f"{_BASE}/rules", json={
            "name": "Update Me",
            "description": "Will be updated",
            "rule_type": "fraud",
            "condition": {},
            "severity": "medium",
            "action": "warn",
            "weight": 5,
            "enabled": True,
        })
        assert create_resp.status_code == 200
        rule_id = create_resp.json()["id"]

        update_resp = client.put(f"{_BASE}/rules/{rule_id}", json={
            "name": "Updated Rule",
            "enabled": False,
        })
        assert update_resp.status_code == 200
        data = update_resp.json()
        assert data["name"] == "Updated Rule"

    def test_update_nonexistent_rule(self, client):
        resp = client.put(f"{_BASE}/rules/nonexistent", json={
            "name": "Nope",
        })
        assert resp.status_code == 404