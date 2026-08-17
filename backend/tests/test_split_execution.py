"""Split Execution Service 测试 — calculate_split, execute_split, refund_split."""

import asyncio
import json
from datetime import datetime, timezone
from pathlib import Path

import pytest
import sys
import uuid as _uuid

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from app.utils.errors import BusinessException


def _uid(prefix: str = "") -> str:
    return f"{prefix}{_uuid.uuid4().hex[:12]}"


def _run(coro):
    """Helper to run async service methods in sync test context."""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


# ── Fixtures ───────────────────────────────────────────────────────

@pytest.fixture
def escrowed_contract(db_session):
    """创建一个已托管且有分润规则的合约."""
    from app.models.contract import ContractInstance
    from app.models.system import User

    user = User(
        id=_uid("u_"),
        username=f"creator_{_uuid.uuid4().hex[:6]}",
        email=f"creator_{_uuid.uuid4().hex[:6]}@test.com",
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
        id=_uid("c_"),
        title="测试分润合约",
        description="用于分润执行测试",
        contract_type="non_exclusive_license",
        total_amount=10000.0,
        currency="CNY",
        billing_cycle="one_time",
        scope_usage="commercial",
        scope_geography="china",
        status="escrowed",
        split_rules_json=json.dumps(rules, ensure_ascii=False),
        escrow_provider="stripe",
        escrow_transaction_id="stripe_test123",
        creator_id=user.id,
    )
    db_session.add(contract)
    db_session.commit()
    return contract


@pytest.fixture
def completed_contract(db_session):
    """创建一个已完成的合约（有分润规则）."""
    from app.models.contract import ContractInstance
    from app.models.system import User

    user = User(
        id=_uid("u_"),
        username=f"creator_{_uuid.uuid4().hex[:6]}",
        email=f"creator_{_uuid.uuid4().hex[:6]}@test.com",
        role="creator",
        status="active",
    )
    db_session.add(user)
    db_session.commit()

    rules = [
        {"role": "creator", "participant_id": user.id, "percentage": 0.8},
        {"role": "platform", "participant_id": user.id, "percentage": 0.003},
    ]

    contract = ContractInstance(
        id=_uid("c_"),
        title="已完成合约",
        description="用于退款测试",
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


@pytest.fixture
def no_split_rules_contract(db_session):
    """创建一个没有分润规则的合约."""
    from app.models.contract import ContractInstance
    from app.models.system import User

    user = User(
        id=_uid("u_"),
        username=f"creator_{_uuid.uuid4().hex[:6]}",
        email=f"creator_{_uuid.uuid4().hex[:6]}@test.com",
        role="creator",
        status="active",
    )
    db_session.add(user)
    db_session.commit()

    contract = ContractInstance(
        id=_uid("c_"),
        title="无分润规则合约",
        description="split_rules_json 为空",
        contract_type="product_license",
        total_amount=3000.0,
        currency="CNY",
        billing_cycle="monthly",
        scope_usage="personal",
        scope_geography="china",
        status="escrowed",
        split_rules_json="[]",
        creator_id=user.id,
    )
    db_session.add(contract)
    db_session.commit()
    return contract


@pytest.fixture
def executing_contract(db_session):
    """创建一个履约中的合约（可用于 execute_split 测试）."""
    from app.models.contract import ContractInstance
    from app.models.system import User

    user = User(
        id=_uid("u_"),
        username=f"creator_{_uuid.uuid4().hex[:6]}",
        email=f"creator_{_uuid.uuid4().hex[:6]}@test.com",
        role="creator",
        status="active",
    )
    db_session.add(user)
    db_session.commit()

    rules = [
        {"role": "creator", "participant_id": user.id, "percentage": 0.9},
        {"role": "platform", "participant_id": user.id, "percentage": 0.003},
    ]

    contract = ContractInstance(
        id=_uid("c_"),
        title="履约中合约",
        description="用于execute_split在executing状态测试",
        contract_type="exclusive_license",
        total_amount=8000.0,
        currency="CNY",
        billing_cycle="monthly",
        scope_usage="commercial",
        scope_geography="eu",
        status="executing",
        split_rules_json=json.dumps(rules, ensure_ascii=False),
        creator_id=user.id,
    )
    db_session.add(contract)
    db_session.commit()
    return contract


# ── Test: calculate_split ──────────────────────────────────────────

class TestCalculateSplit:
    """calculate_split."""

    def test_returns_correct_distributions(self, db_session, escrowed_contract):
        from app.services.split_rule_service import SplitRuleService
        result = SplitRuleService.calculate_split(db_session, escrowed_contract.id)

        assert result["contract_id"] == escrowed_contract.id
        assert result["total_amount"] == 10000.0
        assert result["platform_fee"] == 30.0  # 10000 * 0.003

        roles = {d["role"]: d for d in result["distributions"]}
        assert roles["creator"]["percentage"] == 0.7
        assert roles["creator"]["amount"] == 7000.0
        assert roles["platform"]["percentage"] == 0.003
        assert roles["platform"]["amount"] == 30.0

    def test_custom_total_amount(self, db_session, escrowed_contract):
        from app.services.split_rule_service import SplitRuleService
        result = SplitRuleService.calculate_split(db_session, escrowed_contract.id, total_amount=20000.0)
        assert result["total_amount"] == 20000.0
        assert result["distributions"][0]["amount"] == 14000.0  # 20000 * 0.7

    def test_raises_when_no_rules(self, db_session, no_split_rules_contract):
        from app.services.split_rule_service import SplitRuleService
        with pytest.raises(BusinessException) as exc_info:
            SplitRuleService.calculate_split(db_session, no_split_rules_contract.id)
        assert "暂无分润规则" in str(exc_info.value) or "分润规则为空" in str(exc_info.value)

    def test_decimal_rounding(self, db_session, escrowed_contract):
        """测试金额小数四舍五入精度."""
        from app.services.split_rule_service import SplitRuleService
        # 修改合约金额为有复杂小数的值
        escrowed_contract.total_amount = 9999.99
        db_session.commit()
        result = SplitRuleService.calculate_split(db_session, escrowed_contract.id)
        # 每个 distribution amount 应保留两位小数
        for d in result["distributions"]:
            assert d["amount"] == round(d["amount"], 2)


# ── Test: execute_split ────────────────────────────────────────────

class TestExecuteSplit:
    """execute_split."""

    def test_execute_success_no_escrow(self, db_session, completed_contract):
        from app.services.split_rule_service import SplitRuleService
        result = SplitRuleService.execute_split(db_session, completed_contract.id)

        assert result["status"] == "success"
        assert result["log_id"] is not None
        assert "batch_id" in result
        assert len(result["distributions"]) > 0

        # Verify SplitExecutionLog was created
        from app.models.contract import SplitExecutionLog
        log = db_session.get(SplitExecutionLog, result["log_id"])
        assert log is not None
        assert log.status == "success"
        assert log.detail_json is not None

    def test_execute_in_executing_state(self, db_session, executing_contract):
        """履约中状态也应允许执行分润."""
        from app.services.split_rule_service import SplitRuleService
        result = SplitRuleService.execute_split(db_session, executing_contract.id)
        assert result["status"] == "success"

    def test_execute_fails_draft_status(self, db_session, no_split_rules_contract):
        """草稿状态不允许执行分润."""
        from app.services.split_rule_service import SplitRuleService
        no_split_rules_contract.status = "draft"
        db_session.commit()
        with pytest.raises(BusinessException) as exc_info:
            SplitRuleService.execute_split(db_session, no_split_rules_contract.id)
        assert "不允许执行分润" in str(exc_info.value)

    def test_execute_with_custom_batch_id(self, db_session, completed_contract):
        from app.services.split_rule_service import SplitRuleService
        result = SplitRuleService.execute_split(
            db_session, completed_contract.id, batch_id="custom_batch_001"
        )
        assert result["batch_id"] == "custom_batch_001"

    def test_execute_with_custom_total(self, db_session, completed_contract):
        from app.services.split_rule_service import SplitRuleService
        result = SplitRuleService.execute_split(
            db_session, completed_contract.id, total_amount=7500.0
        )
        assert result["total_amount"] == 7500.0
        # creator gets 80% of 7500 = 6000
        creator_dist = [d for d in result["distributions"] if d["role"] == "creator"][0]
        assert creator_dist["amount"] == 6000.0

    def test_execution_log_has_detail_json(self, db_session, completed_contract):
        from app.services.split_rule_service import SplitRuleService
        SplitRuleService.execute_split(db_session, completed_contract.id)

        from app.models.contract import SplitExecutionLog
        log = (
            db_session.query(SplitExecutionLog)
            .filter(SplitExecutionLog.contract_id == completed_contract.id)
            .first()
        )
        assert log is not None
        assert log.detail_json is not None
        details = json.loads(log.detail_json)
        assert isinstance(details, list)
        assert len(details) > 0


# ── Test: refund_split ─────────────────────────────────────────────

class TestRefundSplit:
    """refund_split."""

    def test_refund_success(self, db_session, completed_contract):
        from app.services.split_rule_service import SplitRuleService
        # First execute, then refund
        SplitRuleService.execute_split(db_session, completed_contract.id)
        result = SplitRuleService.refund_split(db_session, completed_contract.id, reason="客户取消")
        assert result["status"] == "refunded"

    def test_refund_no_execution_record(self, db_session, completed_contract):
        """没有执行记录时应抛出异常."""
        from app.services.split_rule_service import SplitRuleService
        with pytest.raises(BusinessException) as exc_info:
            SplitRuleService.refund_split(db_session, completed_contract.id, reason="no-op")
        assert "可退款的有效分润执行记录" in str(exc_info.value)

    def test_refund_marks_as_refunded(self, db_session, completed_contract):
        from app.services.split_rule_service import SplitRuleService
        SplitRuleService.execute_split(db_session, completed_contract.id)
        SplitRuleService.refund_split(db_session, completed_contract.id, reason="测试退款")

        from app.models.contract import SplitExecutionLog
        log = (
            db_session.query(SplitExecutionLog)
            .filter(SplitExecutionLog.contract_id == completed_contract.id)
            .first()
        )
        assert log.status == "refunded"

    def test_refund_fails_for_failed_execution(self, db_session, escrowed_contract):
        """仅对 success 状态的执行记录退款，failed 的不行."""
        from app.services.split_rule_service import SplitRuleService
        # Create a failed execution manually
        from app.models.contract import SplitExecutionLog
        failed_log = SplitExecutionLog(
            id=_uid("log_"),
            contract_id=escrowed_contract.id,
            execution_batch="2026-07_monthly",
            total_amount=10000.0,
            platform_fee=30.0,
            executor="manual",
            status="failed",
            error_message="test failure",
            detail_json="[]",
        )
        db_session.add(failed_log)
        db_session.commit()

        with pytest.raises(BusinessException) as exc_info:
            SplitRuleService.refund_split(db_session, escrowed_contract.id, reason="should fail")
        assert "可退款的有效分润执行记录" in str(exc_info.value)


# ── Integration Tests ──────────────────────────────────────────────

class TestIntegration:
    """端到端集成测试 — 从报价到执行到退款."""

    def test_full_flow_quote_lock_execute(self, db_session):
        """完整流程：提交报价 → 锁定 → 写入合约 → 计算 → 执行."""
        from app.models.contract import ContractInstance
        from app.models.system import User
        from app.services.split_rule_service import SplitRuleService

        # Create a creator user for this test
        creator = User(
            id=_uid("u_"),
            username=f"creator_{_uuid.uuid4().hex[:6]}",
            email=f"creator_{_uuid.uuid4().hex[:6]}@test.com",
            role="creator",
            status="active",
        )
        db_session.add(creator)
        db_session.commit()

        # 1. 创建挂牌合约
        contract = ContractInstance(
            id=_uid("c_"),
            title="全流程测试合约",
            description="从报价到退款",
            contract_type="non_exclusive_license",
            total_amount=10000.0,
            currency="CNY",
            billing_cycle="one_time",
            scope_usage="commercial",
            scope_geography="china",
            status="listed",
            split_rules_json="[]",
            creator_id=creator.id,
        )
        db_session.add(contract)
        db_session.commit()

        # 2. 提交报价（使用 lock_best_quotes 会锁定的角色）
        SplitRuleService.submit_quote(
            db_session, contract.id, creator.id, "operator", 0.15, 1500.0,
        )
        SplitRuleService.submit_quote(
            db_session, contract.id, creator.id, "legal_rep", 0.05, 500.0,
        )

        # 3. 锁定报价
        locked = SplitRuleService.lock_best_quotes(db_session, contract.id)
        assert len(locked) >= 2

        # 4. 推进状态到 subscribed，然后写入分润规则
        from app.services.contract_state_service import ContractStateService
        # State path: listed -> active -> subscribed
        ContractStateService.validate_transition(db_session, contract.id, "active")
        ContractStateService.validate_transition(db_session, contract.id, "subscribed")

        # Expire session objects to avoid stale state after validate_transition commits
        db_session.expire_all()

        # Lock returns the locked rules from SplitRule table
        rules = [
            {"role": r["role"], "participant_id": r["participant_id"], "percentage": r["percentage"]}
            for r in locked
        ]
        rules.append({"role": "creator", "participant_id": creator.id, "percentage": 0.8})
        assert len(rules) == 3, f"Expected 3 rules, got {len(rules)}"

        SplitRuleService.update_split_rules_json(db_session, contract.id, rules)

        # 5. 继续推进到 completed
        ContractStateService.validate_transition(db_session, contract.id, "escrowed")
        ContractStateService.validate_transition(db_session, contract.id, "insured")
        ContractStateService.validate_transition(db_session, contract.id, "executing")
        ContractStateService.validate_transition(db_session, contract.id, "completed")

        # 6. 计算分润
        calc = SplitRuleService.calculate_split(db_session, contract.id)
        assert calc["total_amount"] == 10000.0
        assert len(calc["distributions"]) > 0

        # 7. 执行分润
        exec_result = SplitRuleService.execute_split(db_session, contract.id)
        assert exec_result["status"] == "success"
        assert exec_result["log_id"] is not None

    def test_calculate_then_execute_consistency(self, db_session, completed_contract):
        """calculate_split 和 execute_split 返回的分润明细应一致."""
        from app.services.split_rule_service import SplitRuleService
        calc = SplitRuleService.calculate_split(db_session, completed_contract.id)
        exec_result = SplitRuleService.execute_split(db_session, completed_contract.id)

        assert exec_result["total_amount"] == calc["total_amount"]
        assert exec_result["platform_fee"] == calc["platform_fee"]
        assert len(exec_result["distributions"]) == len(calc["distributions"])

        for calc_d, exec_d in zip(calc["distributions"], exec_result["distributions"]):
            assert calc_d["role"] == exec_d["role"]
            assert abs(calc_d["amount"] - exec_d["amount"]) < 0.01
