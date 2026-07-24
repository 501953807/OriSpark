"""P1 端到端集成测试 — 合约市场 + 支付托管 + 物流商."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

import pytest
import uuid as _uuid

from app.services.contract_state_service import ContractStateService
from app.services.payment_gateway import PaymentGatewayService
from app.services.logistics_service import LogisticsService
from app.models.contract import ContractInstance
from app.models.logistics import LogisticsProvider


# ── Fixtures ──────────────────────────────────────────────────────


def _uid(prefix: str = "") -> str:
    return f"{prefix}{_uuid.uuid4().hex[:12]}"


@pytest.fixture
def creator(db_session):
    """创建测试用户."""
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
    return user


@pytest.fixture
def subscriber(db_session):
    """创建认购方用户."""
    from app.models.system import User
    user = User(
        id=_uid("u_"),
        username=f"subscriber_{_uuid.uuid4().hex[:6]}",
        email=f"subscriber_{_uuid.uuid4().hex[:6]}@test.com",
        role="trader",
        status="active",
    )
    db_session.add(user)
    db_session.commit()
    return user


def _create_contract_via_model(db_session, creator_id: str, **kwargs) -> ContractInstance:
    """直接通过 ORM 创建合约，避免 service 内部 commit 与 fixture rollback 冲突."""
    defaults = dict(
        title="插画授权合约",
        description="商业插画授权合同",
        contract_type="non_exclusive_license",
        total_amount=5000.0,
        currency="CNY",
        billing_cycle="one_time",
        scope_usage="commercial",
        scope_geography="china",
        scope_duration="1year",
        split_rules_json="[]",
        status="draft",
    )
    defaults.update(kwargs)
    contract = ContractInstance(id=_uid("c_"), creator_id=creator_id, **defaults)
    db_session.add(contract)
    db_session.commit()
    return contract


@pytest.fixture
def draft_contract(db_session, creator):
    """创建合约草稿."""
    return _create_contract_via_model(db_session, creator.id)


@pytest.fixture
def sample_provider(db_session):
    """创建测试物流商."""
    provider = LogisticsProvider(
        id=_uid("p_"),
        name="测试物流",
        contact_email="logistics@test.com",
        contact_phone="13800138000",
        description="测试物流服务商",
        status="active",
        rating=0.0,
    )
    db_session.add(provider)
    db_session.commit()
    return provider


# ── 合约状态机测试 ────────────────────────────────────────────────


def test_create_contract_returns_draft(draft_contract):
    """创建合约初始状态为 draft."""
    assert draft_contract.status == "draft"
    assert draft_contract.title == "插画授权合约"


def test_publish_contract(db_session, draft_contract):
    """draft -> listed."""
    contract = ContractStateService.publish_contract(
        db_session, draft_contract.id, actor_id="platform"
    )
    assert contract.status == "listed"


def test_activate_contract(db_session, draft_contract):
    """draft -> listed -> active."""
    ContractStateService.publish_contract(db_session, draft_contract.id)
    contract = ContractStateService.activate_contract(
        db_session, draft_contract.id, actor_id="platform"
    )
    assert contract.status == "active"
    assert contract.verified == "approved"


def test_subscribe_contract(db_session, draft_contract, subscriber):
    """active -> subscribed."""
    ContractStateService.publish_contract(db_session, draft_contract.id)
    ContractStateService.activate_contract(db_session, draft_contract.id)
    contract = ContractStateService.subscribe_contract(
        db_session, draft_contract.id, subscriber.id, actor_id=subscriber.id
    )
    assert contract.status == "subscribed"
    assert contract.operator_id == subscriber.id


def test_full_lifecycle_to_completed(db_session, draft_contract, subscriber):
    """完整生命周期：draft -> listed -> active -> subscribed -> escrowed -> insured -> executing -> completed."""
    cid = draft_contract.id

    ContractStateService.publish_contract(db_session, cid)
    ContractStateService.activate_contract(db_session, cid)
    ContractStateService.subscribe_contract(db_session, cid, subscriber.id)
    ContractStateService.initiate_escrow(db_session, cid, "stripe")
    ContractStateService.activate_insurance(db_session, cid, policy_no="POL_TEST_001")
    ContractStateService.start_execution(db_session, cid)
    contract = ContractStateService.complete_contract(db_session, cid)

    assert contract.status == "completed"
    assert contract.completed_at is not None


def test_dispute_flow(db_session, draft_contract, subscriber):
    """履约中争议流程：executing -> dispute -> resolved -> completed."""
    cid = draft_contract.id

    ContractStateService.publish_contract(db_session, cid)
    ContractStateService.activate_contract(db_session, cid)
    ContractStateService.subscribe_contract(db_session, cid, subscriber.id)
    ContractStateService.initiate_escrow(db_session, cid, "paypal")
    ContractStateService.activate_insurance(db_session, cid, policy_no="POL_TEST_002")
    ContractStateService.start_execution(db_session, cid)
    ContractStateService.reject_inspection(
        db_session, cid, reason="交付物不满足需求"
    )
    ContractStateService.resolve_dispute(db_session, cid, resolution="重新交付通过")
    contract = ContractStateService.complete_contract(db_session, cid)

    assert contract.status == "completed"


def test_invalid_transition_rejected(db_session, draft_contract):
    """非法状态流转应抛出异常."""
    with pytest.raises(Exception):
        ContractStateService.validate_transition(
            db_session, draft_contract.id, "completed"
        )


def test_cancel_from_draft(db_session, draft_contract):
    """draft 阶段可取消."""
    contract = ContractStateService.cancel_contract(
        db_session, draft_contract.id, reason="创作者主动取消"
    )
    assert contract.status == "cancelled"


def test_cancel_from_listed(db_session, draft_contract):
    """listed 阶段可取消."""
    ContractStateService.publish_contract(db_session, draft_contract.id)
    contract = ContractStateService.cancel_contract(
        db_session, draft_contract.id, reason="未通过审核"
    )
    assert contract.status == "cancelled"


def test_cancel_from_subscribed(db_session, draft_contract, subscriber):
    """subscribed 阶段可取消."""
    ContractStateService.publish_contract(db_session, draft_contract.id)
    ContractStateService.activate_contract(db_session, draft_contract.id)
    ContractStateService.subscribe_contract(db_session, draft_contract.id, subscriber.id)
    contract = ContractStateService.cancel_contract(
        db_session, draft_contract.id, reason="交易取消"
    )
    assert contract.status == "cancelled"


def test_get_status_summary(db_session, draft_contract):
    """获取合约状态摘要."""
    summary = ContractStateService.get_contract_status_summary(
        db_session, draft_contract.id
    )
    assert summary["status"] == "draft"
    assert summary["title"] == "插画授权合约"
    assert "next_possible" in summary
    assert any(s["status"] == "listed" for s in summary["next_possible"])


def test_get_timeline_after_transitions(db_session, draft_contract, subscriber):
    """状态变更后时间线包含审计记录."""
    cid = draft_contract.id
    ContractStateService.publish_contract(db_session, cid)
    ContractStateService.activate_contract(db_session, cid)
    ContractStateService.subscribe_contract(db_session, cid, subscriber.id)

    timeline = ContractStateService.get_contract_timeline(db_session, cid)
    assert len(timeline) >= 3


# ── 支付托管测试 ──────────────────────────────────────────────────


def test_initiate_escrow_success(db_session, draft_contract, subscriber):
    """发起资金托管成功."""
    cid = draft_contract.id
    ContractStateService.publish_contract(db_session, cid)
    ContractStateService.activate_contract(db_session, cid)
    ContractStateService.subscribe_contract(db_session, cid, subscriber.id)

    result = PaymentGatewayService.initiate_escrow(
        db_session, cid, "stripe", 5000.0, "CNY"
    )
    assert result["provider"] == "stripe"
    assert result["amount"] == 5000.0
    assert result["currency"] == "CNY"
    assert result["status"] == "escrowed"
    assert result["transaction_id"].startswith("escrow_")


def test_confirm_escrow_success(db_session, draft_contract, subscriber):
    """确认托管到账."""
    cid = draft_contract.id
    ContractStateService.publish_contract(db_session, cid)
    ContractStateService.activate_contract(db_session, cid)
    ContractStateService.subscribe_contract(db_session, cid, subscriber.id)

    init_result = PaymentGatewayService.initiate_escrow(
        db_session, cid, "worldfirst", 5000.0, "CNY"
    )
    confirm_result = PaymentGatewayService.confirm_escrow(
        db_session, cid, init_result["transaction_id"]
    )
    assert confirm_result["status"] == "escrow_confirmed"


def test_release_escrow_after_completion(db_session, draft_contract, subscriber):
    """已完成合约可释放托管."""
    cid = draft_contract.id
    ContractStateService.publish_contract(db_session, cid)
    ContractStateService.activate_contract(db_session, cid)
    ContractStateService.subscribe_contract(db_session, cid, subscriber.id)
    PaymentGatewayService.initiate_escrow(db_session, cid, "stripe", 5000.0, "CNY")
    ContractStateService.activate_insurance(db_session, cid, policy_no="POL_RELEASE_001")
    ContractStateService.start_execution(db_session, cid)
    ContractStateService.complete_contract(db_session, cid)

    result = PaymentGatewayService.release_escrow(db_session, cid)
    assert result["release_status"] == "released"


def test_refund_escrow(db_session, draft_contract, subscriber):
    """托管中的合约可退款."""
    cid = draft_contract.id
    ContractStateService.publish_contract(db_session, cid)
    ContractStateService.activate_contract(db_session, cid)
    ContractStateService.subscribe_contract(db_session, cid, subscriber.id)

    PaymentGatewayService.initiate_escrow(
        db_session, cid, "paypal", 5000.0, "CNY"
    )
    result = PaymentGatewayService.refund_escrow(
        db_session, cid, reason="交易取消，全额退款"
    )
    assert result["refund_status"] == "refunded"

    # 验证合约状态已变为 refunded
    contract = db_session.query(ContractInstance).filter(
        ContractInstance.id == cid
    ).first()
    assert contract.status == "refunded"


def test_refund_escrow_not_escrowed(db_session, draft_contract):
    """非托管状态合约不能退款."""
    with pytest.raises(ValueError):
        PaymentGatewayService.refund_escrow(
            db_session, draft_contract.id, reason="测试退款"
        )


def test_release_escrow_before_completion(db_session, draft_contract, subscriber):
    """未完成合约不能释放托管."""
    cid = draft_contract.id
    ContractStateService.publish_contract(db_session, cid)
    ContractStateService.activate_contract(db_session, cid)
    ContractStateService.subscribe_contract(db_session, cid, subscriber.id)
    PaymentGatewayService.initiate_escrow(
        db_session, cid, "stripe", 5000.0, "CNY"
    )

    with pytest.raises(ValueError):
        PaymentGatewayService.release_escrow(db_session, cid)


def test_unsupported_provider_raises(db_session, draft_contract):
    """不支持的托管方应抛出异常."""
    with pytest.raises(ValueError):
        PaymentGatewayService.initiate_escrow(
            db_session, draft_contract.id, "unknown_provider", 100.0, "CNY"
        )


def test_escrow_nonexistent_contract(db_session):
    """不存在合约不能发起托管."""
    with pytest.raises(ValueError):
        PaymentGatewayService.initiate_escrow(
            db_session, "nonexistent_id", "stripe", 100.0, "CNY"
        )


# ── 物流商测试 ────────────────────────────────────────────────────


def test_create_provider(sample_provider):
    """创建物流商成功."""
    assert sample_provider.name == "测试物流"
    assert sample_provider.status == "active"
    assert sample_provider.rating == 0.0


def test_get_providers(db_session, sample_provider):
    """获取物流商列表."""
    providers = LogisticsService.get_providers(db_session)
    assert len(providers) >= 1
    names = [p.name for p in providers]
    assert "测试物流" in names


def test_update_provider(db_session, sample_provider):
    """更新物流商信息."""
    updated = LogisticsService.update_provider(
        db_session, sample_provider.id, rating=4.8, status="active"
    )
    assert updated.rating == 4.8


def test_get_nonexistent_provider(db_session):
    """不存在的物流商返回 None."""
    result = LogisticsService.get_provider(db_session, "nonexistent")
    assert result is None


def test_create_shipment(db_session, draft_contract, sample_provider):
    """创建发货记录."""
    shipment = LogisticsService.create_shipment(
        db_session,
        contract_id=draft_contract.id,
        provider_id=sample_provider.id,
        tracking_number="SF1234567890",
        recipient_name="张三",
        recipient_address="北京市朝阳区",
        sender_name="李四",
        sender_address="上海市浦东新区",
        shipping_cost=15.0,
    )
    assert shipment.tracking_number == "SF1234567890"
    assert shipment.status == "pending"
    assert shipment.contract_id == draft_contract.id


def test_shipment_workflow(db_session, draft_contract, sample_provider):
    """完整物流工作流：创建 -> 发货 -> 在途 -> 送达 -> 确认收货."""
    shipment = LogisticsService.create_shipment(
        db_session,
        contract_id=draft_contract.id,
        provider_id=sample_provider.id,
        tracking_number="YTO9876543210",
    )

    shipped = LogisticsService.update_shipment_status(
        db_session, shipment.id, "shipped",
        location="上海分拨中心",
        description="已揽收",
    )
    assert shipped.status == "shipped"
    assert shipped.shipped_at is not None

    in_transit = LogisticsService.update_shipment_status(
        db_session, shipment.id, "in_transit",
        location="北京分拨中心",
        description="运输中",
    )
    assert in_transit.status == "in_transit"

    delivered = LogisticsService.update_shipment_status(
        db_session, shipment.id, "delivered",
        location="收货地址",
        description="已签收",
    )
    assert delivered.status == "delivered"
    assert delivered.delivered_at is not None

    confirmed = LogisticsService.confirm_delivery(
        db_session, shipment.id, confirmed_by="张三"
    )
    assert confirmed.status == "delivered"


def test_get_tracking_events(db_session, draft_contract, sample_provider):
    """获取发货轨迹事件."""
    shipment = LogisticsService.create_shipment(
        db_session, contract_id=draft_contract.id, provider_id=sample_provider.id
    )
    LogisticsService.update_shipment_status(
        db_session, shipment.id, "shipped",
        location="上海", description="已揽收"
    )
    events = LogisticsService.get_tracking_events(db_session, shipment.id)
    assert len(events) >= 2  # created + shipped


def test_get_shipments_by_contract(db_session, draft_contract, sample_provider):
    """按合约查询发货记录."""
    LogisticsService.create_shipment(
        db_session, contract_id=draft_contract.id, provider_id=sample_provider.id
    )
    shipments = LogisticsService.get_shipments_by_contract(
        db_session, draft_contract.id
    )
    assert len(shipments) >= 1


def test_provider_contract_count_increases(db_session, draft_contract, sample_provider):
    """创建发货后物流商合同计数增加."""
    initial_count = sample_provider.contract_count
    LogisticsService.create_shipment(
        db_session, contract_id=draft_contract.id, provider_id=sample_provider.id
    )
    updated = LogisticsService.get_provider(db_session, sample_provider.id)
    assert updated.contract_count == initial_count + 1


def test_logistics_invalid_operation(db_session):
    """无效操作应抛出异常."""
    with pytest.raises(ValueError):
        LogisticsService.update_shipment_status(
            db_session, "nonexistent_shipment", "shipped"
        )


def test_logistics_invalid_status(db_session, draft_contract, sample_provider):
    """无效状态应抛出异常."""
    shipment = LogisticsService.create_shipment(
        db_session, contract_id=draft_contract.id, provider_id=sample_provider.id
    )
    with pytest.raises(ValueError, match="无效状态"):
        LogisticsService.update_shipment_status(
            db_session, shipment.id, "invalid_status"
        )


def test_shipment_for_nonexistent_contract(db_session, sample_provider):
    """不存在的合约不能创建发货."""
    with pytest.raises(ValueError, match="合约不存在"):
        LogisticsService.create_shipment(
            db_session,
            contract_id="nonexistent_contract",
            provider_id=sample_provider.id,
        )


# ── 合约 + 物流联动测试 ──────────────────────────────────────────


def test_confirm_delivery_triggers_execution(db_session, draft_contract, subscriber, sample_provider):
    """确认收货应触发合约进入执行状态."""
    cid = draft_contract.id
    ContractStateService.publish_contract(db_session, cid)
    ContractStateService.activate_contract(db_session, cid)
    ContractStateService.subscribe_contract(db_session, cid, subscriber.id)
    PaymentGatewayService.initiate_escrow(db_session, cid, "stripe", 5000.0, "CNY")
    ContractStateService.activate_insurance(db_session, cid, policy_no="POL_LOGISTICS_001")

    shipment = LogisticsService.create_shipment(
        db_session, contract_id=cid, provider_id=sample_provider.id
    )
    LogisticsService.update_shipment_status(db_session, shipment.id, "delivered")
    LogisticsService.confirm_delivery(db_session, shipment.id, confirmed_by="张三")

    contract = db_session.query(ContractInstance).filter(
        ContractInstance.id == cid
    ).first()
    assert contract.status == "executing"


def test_payment_escrow_and_logistics_linked(db_session, draft_contract, subscriber, sample_provider):
    """支付托管与物流记录关联到同一合约."""
    cid = draft_contract.id
    ContractStateService.publish_contract(db_session, cid)
    ContractStateService.activate_contract(db_session, cid)
    ContractStateService.subscribe_contract(db_session, cid, subscriber.id)

    escrow = PaymentGatewayService.initiate_escrow(
        db_session, cid, "stripe", 5000.0, "CNY"
    )
    assert escrow["contract_id"] == cid

    shipment = LogisticsService.create_shipment(
        db_session, contract_id=cid, provider_id=sample_provider.id
    )
    assert shipment.contract_id == cid

    # 两个记录都关联同一合约
    contract = db_session.query(ContractInstance).filter(
        ContractInstance.id == cid
    ).first()
    assert contract.escrow_transaction_id == escrow["transaction_id"]
    assert contract.status == "escrowed"
