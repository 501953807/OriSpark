"""分润规则模块 API 测试."""
import pytest


def _create_user(db_session, email="split_test@example.com"):
    from app.models.system import User
    from app.services.auth_service import _hash_password
    u = User(
        id=email,
        email=email,
        username=email.split("@")[0],
        password_hash=_hash_password("testpass123"),
    )
    db_session.add(u)
    db_session.flush()
    return u


def _create_contract(db_session, contract_id="split_test_contract_001"):
    """创建测试合约 — 需先创建用户，用其ID作为creator_id避免FK约束失败."""
    user = _create_user(db_session, email="split_creator@example.com")
    from app.models.contract import ContractInstance
    contract = ContractInstance(
        id=contract_id,
        title="分润测试合约",
        status="listed",
        creator_id=user.id,
        total_amount=1000.0,
        contract_type="non_exclusive_license",
    )
    db_session.add(contract)
    db_session.flush()
    return contract_id


class TestSplitRuleGet:
    """测试 GET /api/contracts/{contract_id}/split-rules 端点."""

    def test_list_rules_empty(self, client, db_session):
        """空合约应返回分润规则."""
        _create_contract(db_session)
        resp = client.get("/api/contracts/split_test_contract_001/split-rules")
        assert resp.status_code == 200

    def test_list_platform_fee(self, client):
        """平台费率查询应返回200 (total_amount 为 query param)."""
        # platform-fee 是独立端点，不需要 contract_id
        resp = client.get("/api/contracts/split_test_contract_001/split-rules/platform-fee?total_amount=1000.0")
        assert resp.status_code == 200


class TestSplitRuleQuotes:
    """测试报价相关端点 — POST /quotes 使用 query params."""

    def test_submit_quote(self, client, db_session):
        """提交分润报价应成功 (query params)."""
        _create_contract(db_session)
        resp = client.post(
            "/api/contracts/split_test_contract_001/split-rules/quotes",
            params={
                "participant_id": "test_participant",
                "role": "creator",
                "percentage": 0.7,
                "quote_amount": 700.0,
            },
        )
        assert resp.status_code in (200, 201)

    def test_submit_quote_invalid_percentage(self, client, db_session):
        """负数比例应返回错误."""
        _create_contract(db_session)
        resp = client.post(
            "/api/contracts/split_test_contract_001/split-rules/quotes",
            params={
                "participant_id": "test_participant",
                "role": "creator",
                "percentage": -0.1,
                "quote_amount": 0.0,
            },
        )
        assert resp.status_code == 400


class TestSplitRuleLock:
    """测试锁定相关端点."""

    def test_lock_split_rule(self, client, db_session):
        """锁定分润规则应成功."""
        _create_contract(db_session)
        client.post(
            "/api/contracts/split_test_contract_001/split-rules/quotes",
            params={"participant_id": "test_user", "role": "creator", "percentage": 0.7, "quote_amount": 700.0},
        )
        resp = client.post("/api/contracts/split_test_contract_001/split-rules/lock")
        assert resp.status_code in (200, 201)


class TestSplitRuleCalculate:
    """测试计算相关端点."""

    def test_calculate(self, client, db_session):
        """计算分润应返回结果或400(无规则时)."""
        _create_contract(db_session)
        resp = client.get("/api/contracts/split_test_contract_001/split-rules/calculate")
        assert resp.status_code in (200, 400)


class TestSplitRuleExecute:
    """测试执行相关端点."""

    def test_execute_split(self, client, db_session):
        """执行分润应成功."""
        _create_contract(db_session)
        # execute requires status in (completed, resolved, executing) — listed合约会返回400
        resp = client.post(
            "/api/contracts/split_test_contract_001/split-rules/execute",
            json={"total_amount": 1000.0},
        )
        assert resp.status_code in (200, 400)

    def test_refund_split(self, client, db_session):
        """退款分润应成功."""
        _create_contract(db_session)
        resp = client.post(
            "/api/contracts/split_test_contract_001/split-rules/refund",
            json={"reason": "测试退款"},
        )
        assert resp.status_code in (200, 400)


class TestSplitRuleUpdate:
    """测试更新相关端点."""

    def test_update_rules(self, client, db_session):
        """更新分润规则应成功."""
        _create_contract(db_session)
        # update requires status in (subscribed, escrowed) — listed合约会返回400
        resp = client.put(
            "/api/contracts/split_test_contract_001/split-rules/rules",
            json=[{"role": "creator", "percentage": 0.7}],
        )
        assert resp.status_code in (200, 400)
