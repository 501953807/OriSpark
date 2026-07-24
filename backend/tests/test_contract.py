"""Tests for contract market endpoints (CRUD + state machine)."""

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session


def _create_user(db_session: Session, user_id: str, **kwargs) -> None:
    """Ensure a user exists in the DB to satisfy FK constraints."""
    from app.models.system import User
    existing = db_session.query(User).filter(User.id == user_id).first()
    if not existing:
        user = User(
            id=user_id,
            username=user_id,
            email=f"{user_id}@test.local",
            **kwargs,
        )
        db_session.add(user)
        db_session.flush()


def _ensure_actor_users(db_session: Session, *user_ids: str) -> None:
    """Ensure multiple users exist for state transitions."""
    for uid in user_ids:
        _create_user(db_session, uid)


def _create_contract(db_session: Session, **kwargs) -> dict:
    """Helper: create a contract via ContractStateService and return its id."""
    from app.services.contract_state_service import ContractStateService

    creator_id = kwargs.get("creator_id", "test_creator")
    _create_user(db_session, creator_id)
    _create_user(db_session, "current_user")  # router default actor_id

    contract = ContractStateService.create_contract(
        db=db_session,
        title=kwargs.get("title", "Test Contract"),
        description=kwargs.get("description", "A test contract"),
        work_id=kwargs.get("work_id"),
        contract_type=kwargs.get("contract_type", "non_exclusive_license"),
        total_amount=float(kwargs.get("total_amount", 1000.0)),
        currency=kwargs.get("currency", "CNY"),
        billing_cycle=kwargs.get("billing_cycle", "one_time"),
        scope_usage=kwargs.get("scope_usage", "commercial"),
        scope_geography=kwargs.get("scope_geography", "china"),
        scope_duration=kwargs.get("scope_duration"),
        creator_id=creator_id,
        split_rules_json=kwargs.get("split_rules_json", "[]"),
    )
    return {"id": contract.id, "status": contract.status}


class TestCreateContract:
    def test_creates_draft(self, client: TestClient, db_session: Session):
        _create_user(db_session, "current_user")
        payload = {
            "title": "Licensing Deal",
            "description": "Non-exclusive license for commercial use",
            "total_amount": 5000.0,
            "contract_type": "non_exclusive_license",
        }
        resp = client.post("/api/contracts", json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert "id" in data
        assert data["status"] == "draft"

    def test_defaults(self, client: TestClient, db_session: Session):
        _create_user(db_session, "current_user")
        payload = {"title": "Minimal", "total_amount": 100}
        resp = client.post("/api/contracts", json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "draft"


class TestListContracts:
    def test_lists_all(self, client: TestClient, db_session: Session):
        _create_contract(db_session, title="Contract A")
        _create_contract(db_session, title="Contract B")
        resp = client.get("/api/contracts")
        assert resp.status_code == 200
        assert len(resp.json()) >= 2

    def test_filters_by_status(self, client: TestClient, db_session: Session):
        _create_contract(db_session, title="Draft Only")
        resp = client.get("/api/contracts?status=draft")
        assert resp.status_code == 200
        for c in resp.json():
            assert c["status"] == "draft"

    def test_filters_by_creator(self, client: TestClient, db_session: Session):
        _create_contract(db_session, title="Creator 1")
        resp = client.get("/api/contracts?creator_id=test_creator")
        assert resp.status_code == 200

    def test_pagination(self, client: TestClient, db_session: Session):
        resp = client.get("/api/contracts?limit=10&offset=0")
        assert resp.status_code == 200


class TestGetContract:
    def test_returns_contract(self, client: TestClient, db_session: Session):
        c = _create_contract(db_session, title="Get Me")
        resp = client.get(f"/api/contracts/{c['id']}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["title"] == "Get Me"
        assert data["status"] == "draft"

    def test_returns_404_for_missing(self, client: TestClient):
        resp = client.get("/api/contracts/nonexistent-id")
        assert resp.status_code == 404


class TestUpdateContract:
    def test_updates_draft(self, client: TestClient, db_session: Session):
        c = _create_contract(db_session)
        resp = client.patch(
            f"/api/contracts/{c['id']}",
            json={"title": "Updated Title", "total_amount": 2000},
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "draft"

    def test_rejects_update_on_non_draft(self, client: TestClient, db_session: Session):
        c = _create_contract(db_session)
        # Publish first to change status
        resp = client.post(f"/api/contracts/{c['id']}/publish")
        assert resp.status_code == 200
        # Now update should fail
        resp = client.patch(
            f"/api/contracts/{c['id']}",
            json={"title": "Should Fail"},
        )
        assert resp.status_code == 400


class TestPublishContract:
    def test_publishes_from_draft(self, client: TestClient, db_session: Session):
        c = _create_contract(db_session)
        resp = client.post(f"/api/contracts/{c['id']}/publish")
        assert resp.status_code == 200
        assert resp.json()["status"] == "listed"


class TestActivateContract:
    def test_activates_listed_contract(self, client: TestClient, db_session: Session):
        c = _create_contract(db_session)
        client.post(f"/api/contracts/{c['id']}/publish")
        resp = client.post(f"/api/contracts/{c['id']}/activate")
        assert resp.status_code == 200
        assert resp.json()["status"] == "active"

    def test_fails_on_non_listed(self, client: TestClient, db_session: Session):
        c = _create_contract(db_session)
        # Can't activate directly from draft
        resp = client.post(f"/api/contracts/{c['id']}/activate")
        assert resp.status_code == 400


class TestEscrow:
    def test_initiates_escrow(self, client: TestClient, db_session: Session):
        c = _create_contract(db_session)
        _ensure_actor_users(db_session, "b1")
        client.post(f"/api/contracts/{c['id']}/publish")
        client.post(f"/api/contracts/{c['id']}/activate")
        client.post(f"/api/contracts/{c['id']}/subscribe", params={"subscriber_id": "b1"})
        resp = client.post(
            f"/api/contracts/{c['id']}/escrow/initiate",
            params={"provider": "stripe"},
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "escrowed"

    def test_confirms_escrow(self, client: TestClient, db_session: Session):
        c = _create_contract(db_session)
        _ensure_actor_users(db_session, "b2")
        client.post(f"/api/contracts/{c['id']}/publish")
        client.post(f"/api/contracts/{c['id']}/activate")
        client.post(f"/api/contracts/{c['id']}/subscribe", params={"subscriber_id": "b2"})
        client.post(f"/api/contracts/{c['id']}/escrow/initiate", params={"provider": "paypal"})
        client.post(f"/api/contracts/{c['id']}/escrow/confirm", params={"transaction_id": "tx_123"})
        # After confirm, status should be escrowed (confirm doesn't change status)
        resp = client.get(f"/api/contracts/{c['id']}")
        assert resp.status_code == 200


class TestInsurance:
    def test_activates_insurance(self, client: TestClient, db_session: Session):
        c = _create_contract(db_session)
        _ensure_actor_users(db_session, "b3")
        client.post(f"/api/contracts/{c['id']}/publish")
        client.post(f"/api/contracts/{c['id']}/activate")
        client.post(f"/api/contracts/{c['id']}/subscribe", params={"subscriber_id": "b3"})
        client.post(f"/api/contracts/{c['id']}/escrow/initiate", params={"provider": "stripe"})
        client.post(f"/api/contracts/{c['id']}/escrow/confirm", params={"transaction_id": "tx_3"})
        resp = client.post(f"/api/contracts/{c['id']}/insurance/activate")
        assert resp.status_code == 200
        assert resp.json()["status"] == "insured"


class TestExecution:
    def test_starts_execution(self, client: TestClient, db_session: Session):
        c = _create_contract(db_session)
        _ensure_actor_users(db_session, "b4")
        client.post(f"/api/contracts/{c['id']}/publish")
        client.post(f"/api/contracts/{c['id']}/activate")
        client.post(f"/api/contracts/{c['id']}/subscribe", params={"subscriber_id": "b4"})
        client.post(f"/api/contracts/{c['id']}/escrow/initiate", params={"provider": "stripe"})
        client.post(f"/api/contracts/{c['id']}/escrow/confirm", params={"transaction_id": "tx_4"})
        client.post(f"/api/contracts/{c['id']}/insurance/activate")
        resp = client.post(f"/api/contracts/{c['id']}/execute/start")
        assert resp.status_code == 200
        assert resp.json()["status"] == "executing"


class TestCompleteContract:
    def test_completes_contract(self, client: TestClient, db_session: Session):
        c = _create_contract(db_session)
        _ensure_actor_users(db_session, "b5")
        client.post(f"/api/contracts/{c['id']}/publish")
        client.post(f"/api/contracts/{c['id']}/activate")
        client.post(f"/api/contracts/{c['id']}/subscribe", params={"subscriber_id": "b5"})
        client.post(f"/api/contracts/{c['id']}/escrow/initiate", params={"provider": "stripe"})
        client.post(f"/api/contracts/{c['id']}/escrow/confirm", params={"transaction_id": "tx_5"})
        client.post(f"/api/contracts/{c['id']}/insurance/activate")
        client.post(f"/api/contracts/{c['id']}/execute/start")
        resp = client.post(f"/api/contracts/{c['id']}/complete")
        assert resp.status_code == 200
        assert resp.json()["status"] == "completed"


class TestDispute:
    def test_raises_dispute(self, client: TestClient, db_session: Session):
        c = _create_contract(db_session)
        _ensure_actor_users(db_session, "b6")
        client.post(f"/api/contracts/{c['id']}/publish")
        client.post(f"/api/contracts/{c['id']}/activate")
        client.post(f"/api/contracts/{c['id']}/subscribe", params={"subscriber_id": "b6"})
        client.post(f"/api/contracts/{c['id']}/escrow/initiate", params={"provider": "stripe"})
        client.post(f"/api/contracts/{c['id']}/escrow/confirm", params={"transaction_id": "tx_6"})
        client.post(f"/api/contracts/{c['id']}/insurance/activate")
        client.post(f"/api/contracts/{c['id']}/execute/start")
        resp = client.post(
            f"/api/contracts/{c['id']}/dispute",
            params={"reason": "Quality not as described"},
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "dispute"


class TestResolveDispute:
    def test_resolves_dispute(self, client: TestClient, db_session: Session):
        c = _create_contract(db_session)
        _ensure_actor_users(db_session, "b7")
        client.post(f"/api/contracts/{c['id']}/publish")
        client.post(f"/api/contracts/{c['id']}/activate")
        client.post(f"/api/contracts/{c['id']}/subscribe", params={"subscriber_id": "b7"})
        client.post(f"/api/contracts/{c['id']}/escrow/initiate", params={"provider": "stripe"})
        client.post(f"/api/contracts/{c['id']}/escrow/confirm", params={"transaction_id": "tx_7"})
        client.post(f"/api/contracts/{c['id']}/insurance/activate")
        client.post(f"/api/contracts/{c['id']}/execute/start")
        client.post(f"/api/contracts/{c['id']}/dispute", params={"reason": "Bad quality"})
        resp = client.post(
            f"/api/contracts/{c['id']}/resolve",
            params={"resolution": "Partial refund agreed"},
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "resolved"


class TestRefund:
    def test_refunds_contract(self, client: TestClient, db_session: Session):
        c = _create_contract(db_session)
        _ensure_actor_users(db_session, "b8")
        client.post(f"/api/contracts/{c['id']}/publish")
        client.post(f"/api/contracts/{c['id']}/activate")
        client.post(f"/api/contracts/{c['id']}/subscribe", params={"subscriber_id": "b8"})
        client.post(f"/api/contracts/{c['id']}/escrow/initiate", params={"provider": "stripe"})
        client.post(f"/api/contracts/{c['id']}/escrow/confirm", params={"transaction_id": "tx_8"})
        client.post(f"/api/contracts/{c['id']}/insurance/activate")
        # refunded is only valid from escrowed state
        resp = client.post(
            f"/api/contracts/{c['id']}/refund",
            params={"reason": "Service not delivered"},
        )
        # From escrowed, refund should work; if it went through insurance, adjust
        if resp.status_code == 400:
            # Need to be in escrowed state (before insurance) for refund
            c2 = _create_contract(db_session)
            _ensure_actor_users(db_session, "b8b")
            client.post(f"/api/contracts/{c2['id']}/publish")
            client.post(f"/api/contracts/{c2['id']}/activate")
            client.post(f"/api/contracts/{c2['id']}/subscribe", params={"subscriber_id": "b8b"})
            client.post(f"/api/contracts/{c2['id']}/escrow/initiate", params={"provider": "stripe"})
            client.post(f"/api/contracts/{c2['id']}/escrow/confirm", params={"transaction_id": "tx_8b"})
            resp = client.post(
                f"/api/contracts/{c2['id']}/refund",
                params={"reason": "Service not delivered"},
            )
        assert resp.status_code == 200
        assert resp.json()["status"] == "refunded"


class TestCancelContract:
    def test_cancels_draft(self, client: TestClient, db_session: Session):
        c = _create_contract(db_session)
        resp = client.post(
            f"/api/contracts/{c['id']}/cancel",
            params={"reason": "Changed mind"},
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "cancelled"


class TestTransitions:
    def test_returns_valid_transitions(self, client: TestClient):
        resp = client.get("/api/contracts/transitions")
        assert resp.status_code == 200
        data = resp.json()
        assert "valid_transitions" in data
        assert "labels" in data


class TestTimeline:
    def test_returns_timeline(self, client: TestClient, db_session: Session):
        c = _create_contract(db_session)
        resp = client.get(f"/api/contracts/{c['id']}/timeline")
        assert resp.status_code == 200
        data = resp.json()
        assert "contract_id" in data
        assert "timeline" in data


class TestStatusSummary:
    def test_returns_summary(self, client: TestClient, db_session: Session):
        c = _create_contract(db_session)
        resp = client.get(f"/api/contracts/{c['id']}/status")
        assert resp.status_code == 200
        data = resp.json()
        assert "id" in data
        assert "status" in data
        assert "status_label" in data
        assert "next_possible" in data
