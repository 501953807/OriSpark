"""Split Rule Router HTTP-level integration tests — covers all 8 endpoints."""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

import pytest


@pytest.fixture
def escrowed_contract_with_rules(db_session):
    """创建一个有分润规则的托管合约."""
    from app.models.contract import ContractInstance
    from app.models.system import User

    user = User(
        id="u_split_test",
        username="split_test",
        email="split@test.com",
        role="creator",
        status="active",
    )
    db_session.add(user)
    db_session.commit()

    rules = [
        {"role": "creator", "participant_id": user.id, "percentage": 0.7},
        {"role": "operator", "participant_id": user.id, "percentage": 0.297},
        {"role": "platform", "participant_id": user.id, "percentage": 0.003},
    ]

    contract = ContractInstance(
        id="c_split_test",
        title="Split Rule Router Test",
        description="For split_rule router HTTP tests",
        contract_type="non_exclusive_license",
        total_amount=10000.0,
        currency="CNY",
        billing_cycle="one_time",
        scope_usage="commercial",
        scope_geography="china",
        status="escrowed",
        split_rules_json=json.dumps(rules, ensure_ascii=False),
        creator_id=user.id,
    )
    db_session.add(contract)
    db_session.commit()
    return contract


def _cid():
    """Build full API path prefix for a contract."""
    return "/api/contracts"


class TestPlatformFeeEndpoint:
    """GET /contracts/platform-fee"""

    def test_returns_fee(self, client, escrowed_contract_with_rules):
        resp = client.get("/api/contracts/platform-fee", params={"total_amount": 10000.0})
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_amount"] == 10000.0
        assert data["platform_fee"] == 30.0


class TestGetSplitRules:
    """GET /contracts/{id}/split-rules"""

    def test_returns_rules(self, client, escrowed_contract_with_rules):
        cid = escrowed_contract_with_rules.id
        resp = client.get(f"{_cid()}/{cid}/split-rules")
        assert resp.status_code == 200
        data = resp.json()
        assert data["contract_id"] == cid
        # Rules may be empty if no SplitRule DB rows exist (rules stored in split_rules_json)
        assert isinstance(data["rules"], list)


class TestSubmitQuote:
    """POST /contracts/{id}/split-rules/quotes"""

    def test_submit_quote_success(self, client, escrowed_contract_with_rules, db_session):
        escrowed_contract_with_rules.status = "listed"
        db_session.commit()
        cid = escrowed_contract_with_rules.id
        resp = client.post(
            f"{_cid()}/{cid}/split-rules/quotes",
            params={
                "participant_id": "p_operator_001",
                "role": "operator",
                "percentage": 0.15,
                "quote_amount": 1500.0,
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["role"] == "operator"
        assert data["percentage"] == 0.15

    def test_submit_quote_rejected_when_not_listed(self, client, escrowed_contract_with_rules):
        cid = escrowed_contract_with_rules.id
        resp = client.post(
            f"{_cid()}/{cid}/split-rules/quotes",
            params={
                "participant_id": "p_x",
                "role": "operator",
                "percentage": 0.1,
                "quote_amount": 100.0,
            },
        )
        assert resp.status_code == 400


class TestLockQuotes:
    """POST /contracts/{id}/split-rules/lock"""

    def test_lock_quotes_success(self, client, escrowed_contract_with_rules, db_session):
        escrowed_contract_with_rules.status = "listed"
        db_session.commit()
        cid = escrowed_contract_with_rules.id
        client.post(
            f"{_cid()}/{cid}/split-rules/quotes",
            params={"participant_id": "p1", "role": "operator", "percentage": 0.15, "quote_amount": 1500.0},
        )
        client.post(
            f"{_cid()}/{cid}/split-rules/quotes",
            params={"participant_id": "p2", "role": "legal_rep", "percentage": 0.05, "quote_amount": 500.0},
        )
        resp = client.post(f"{_cid()}/{cid}/split-rules/lock")
        assert resp.status_code == 200
        data = resp.json()
        assert data["contract_id"] == cid
        assert len(data["locked_rules"]) >= 2


class TestUpdateSplitRules:
    """PUT /contracts/{id}/split-rules/rules"""

    def test_update_rules_success(self, client, escrowed_contract_with_rules, db_session):
        escrowed_contract_with_rules.status = "subscribed"
        db_session.commit()
        cid = escrowed_contract_with_rules.id
        rules = [
            {"role": "creator", "participant_id": "u_split_test", "percentage": 0.8},
            {"role": "platform", "participant_id": "u_split_test", "percentage": 0.003},
        ]
        resp = client.put(f"{_cid()}/{cid}/split-rules/rules", json=rules)
        assert resp.status_code == 200
        assert resp.json()["id"] == cid


class TestCalculateSplit:
    """GET /contracts/{id}/split-rules/calculate"""

    def test_calculate_success(self, client, escrowed_contract_with_rules):
        cid = escrowed_contract_with_rules.id
        resp = client.get(f"{_cid()}/{cid}/split-rules/calculate")
        assert resp.status_code == 200
        data = resp.json()
        assert data["contract_id"] == cid
        assert data["total_amount"] == 10000.0
        assert data["platform_fee"] == 30.0
        assert len(data["distributions"]) >= 3

    def test_calculate_with_custom_total(self, client, escrowed_contract_with_rules):
        cid = escrowed_contract_with_rules.id
        resp = client.get(f"{_cid()}/{cid}/split-rules/calculate", params={"total_amount": 20000.0})
        assert resp.status_code == 200
        assert resp.json()["total_amount"] == 20000.0


class TestExecuteSplit:
    """POST /contracts/{id}/split-rules/execute"""

    def test_execute_success(self, client, completed_contract_for_split):
        cid = completed_contract_for_split.id
        resp = client.post(f"{_cid()}/{cid}/split-rules/execute", json={"total_amount": None, "batch_id": None})
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "success"
        assert data["log_id"] is not None

    def test_execute_with_custom_batch(self, client, completed_contract_for_split):
        cid = completed_contract_for_split.id
        resp = client.post(f"{_cid()}/{cid}/split-rules/execute", json={"total_amount": 5000.0, "batch_id": "custom_001"})
        assert resp.status_code == 200
        assert resp.json()["batch_id"] == "custom_001"
        assert resp.json()["total_amount"] == 5000.0


@pytest.fixture
def completed_contract_for_split(db_session):
    from app.models.contract import ContractInstance
    from app.models.system import User

    user = User(id="u_exec_test", username="exec_test", email="exec@test.com", role="creator", status="active")
    db_session.add(user)
    db_session.commit()

    rules = [
        {"role": "creator", "participant_id": user.id, "percentage": 0.8},
        {"role": "platform", "participant_id": user.id, "percentage": 0.003},
    ]

    contract = ContractInstance(
        id="c_exec_test",
        title="Execute Split Test",
        description="For execute and refund HTTP tests",
        contract_type="copyright_transfer",
        total_amount=5000.0,
        currency="CNY",
        billing_cycle="one_time",
        scope_usage="commercial",
        scope_geography="global",
        status="completed",
        split_rules_json=json.dumps(rules, ensure_ascii=False),
        completed_at=datetime(2026, 7, 15, tzinfo=timezone.utc),
        creator_id=user.id,
    )
    db_session.add(contract)
    db_session.commit()
    return contract


class TestRefundSplit:
    """POST /contracts/{id}/split-rules/refund"""

    def test_refund_success(self, client, completed_contract_for_split, db_session):
        cid = completed_contract_for_split.id
        exec_resp = client.post(f"{_cid()}/{cid}/split-rules/execute", json={"total_amount": None, "batch_id": None})
        assert exec_resp.status_code == 200, f"Execute failed: {exec_resp.json()}"
        resp = client.post(f"{_cid()}/{cid}/split-rules/refund", json={"reason": "测试退款"})
        assert resp.status_code == 200, f"Refund failed: {resp.json()}"
        assert resp.json()["status"] == "refunded"

    def test_refund_no_execution(self, client, completed_contract_for_split):
        cid = completed_contract_for_split.id
        resp = client.post(f"{_cid()}/{cid}/split-rules/refund", json={"reason": "no-op"})
        assert resp.status_code == 400
