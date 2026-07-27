"""Contract Matching Router HTTP-level integration tests — covers all 5 endpoints."""

import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

import pytest


@pytest.fixture
def listed_contract(db_session):
    from app.models.contract import ContractInstance
    from app.models.system import User

    user = User(
        id="u_match_test",
        username="match_test",
        email="match@test.com",
        role="creator",
        status="active",
    )
    db_session.add(user)
    db_session.commit()

    contract = ContractInstance(
        id="c_match_test",
        title="Match Test Contract",
        description="For contract matching router HTTP tests",
        contract_type="non_exclusive_license",
        total_amount=5000.0,
        currency="CNY",
        billing_cycle="one_time",
        scope_usage="commercial",
        scope_geography="china",
        status="listed",
        published_at=datetime(2026, 7, 20, tzinfo=timezone.utc),
        creator_id=user.id,
    )
    db_session.add(contract)
    db_session.commit()
    return contract


_BASE = "/api/contracts"


class TestGetListedContracts:
    """GET /contracts/matches/listed"""

    def test_returns_empty_list(self, client, db_session):
        resp = client.get(f"{_BASE}/matches/listed")
        assert resp.status_code == 200
        # Service returns a list directly
        data = resp.json()
        assert isinstance(data, list)

    def test_returns_listed_contracts(self, client, listed_contract):
        resp = client.get(f"{_BASE}/matches/listed", params={"participant_type": "operator"})
        assert resp.status_code == 200
        data = resp.json()
        # Service returns a list of dicts
        items = data if isinstance(data, list) else data.get("items", [])
        assert any(item.get("id") == "c_match_test" for item in items)


class TestPushMatch:
    """POST /contracts/{id}/matches/push"""

    def test_push_match_success(self, client, listed_contract):
        resp = client.post(
            f"{_BASE}/{listed_contract.id}/matches/push",
            json={
                "participant_type": "operator",
                "participant_id": "u_match_test",
                "match_score": 0.85,
                "match_reason": "商业使用范围匹配",
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "pushed"
        assert "id" in data

    def test_push_match_rejects_non_listed(self, client, listed_contract, db_session):
        listed_contract.status = "active"
        db_session.commit()
        resp = client.post(
            f"{_BASE}/{listed_contract.id}/matches/push",
            json={
                "participant_type": "operator",
                "participant_id": "anyone",
                "match_score": 0.5,
            },
        )
        assert resp.status_code == 400


class TestRecordView:
    """POST /contracts/matches/{id}/view"""

    def test_record_view_sets_timestamp(self, client, listed_contract, db_session):
        push_resp = client.post(
            f"{_BASE}/{listed_contract.id}/matches/push",
            json={
                "participant_type": "operator",
                "participant_id": "u_match_test",
                "match_score": 0.9,
            },
        )
        assert push_resp.status_code == 200
        matching_id = push_resp.json()["id"]

        resp = client.post(f"{_BASE}/matches/{matching_id}/view")
        assert resp.status_code == 200
        data = resp.json()
        assert "viewed_at" in data


class TestRecordResponse:
    """POST /contracts/matches/{id}/respond"""

    def test_accept_response(self, client, listed_contract, db_session):
        push_resp = client.post(
            f"{_BASE}/{listed_contract.id}/matches/push",
            json={
                "participant_type": "operator",
                "participant_id": "u_match_test",
                "match_score": 0.9,
            },
        )
        matching_id = push_resp.json()["id"]
        resp = client.post(
            f"{_BASE}/matches/{matching_id}/respond",
            json={"response": "accepted"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["response"] == "accepted"

    def test_counter_offer_with_json(self, client, listed_contract, db_session):
        push_resp = client.post(
            f"{_BASE}/{listed_contract.id}/matches/push",
            json={
                "participant_type": "creator",
                "participant_id": "u_match_test",
                "match_score": 0.7,
            },
        )
        matching_id = push_resp.json()["id"]
        resp = client.post(
            f"{_BASE}/matches/{matching_id}/respond",
            json={
                "response": "counter_offer",
                "counter_offer_json": '{"total_amount": 6000}',
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["response"] == "counter_offer"


class TestGetParticipantMatches:
    """GET /contracts/participants/{id}/matches"""

    def test_get_participant_matches(self, client, listed_contract, db_session):
        for score in [0.8, 0.6]:
            client.post(
                f"{_BASE}/{listed_contract.id}/matches/push",
                json={
                    "participant_type": "operator",
                    "participant_id": "u_match_test",
                    "match_score": score,
                },
            )

        resp = client.get(
            f"{_BASE}/participants/u_match_test/matches",
            params={"participant_type": "operator"},
        )
        assert resp.status_code == 200
        data = resp.json()
        items = data if isinstance(data, list) else data.get("items", [])
        assert len(items) >= 2
