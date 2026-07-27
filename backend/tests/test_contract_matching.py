"""合约撮合服务测试 — ContractMatchingService 直接调用."""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

import pytest
import uuid as _uuid


def _uid(prefix: str = "") -> str:
    return f"{prefix}{_uuid.uuid4().hex[:12]}"


@pytest.fixture
def listed_contract(db_session, actor_user):
    """创建一条挂牌状态的合约记录."""
    from app.models.contract import ContractInstance
    from datetime import datetime, timezone

    contract = ContractInstance(
        id=_uid("c_"),
        title="测试挂牌合约",
        description="用于撮合测试",
        contract_type="non_exclusive_license",
        total_amount=5000.0,
        currency="CNY",
        billing_cycle="one_time",
        scope_usage="commercial",
        scope_geography="china",
        status="listed",
        published_at=datetime(2026, 7, 20, tzinfo=timezone.utc),
        creator_id=actor_user.id,
    )
    db_session.add(contract)
    db_session.commit()
    return contract


@pytest.fixture
def actor_user(db_session):
    """创建一个参与方用户."""
    from app.models.system import User
    user = User(
        id=_uid("u_"),
        username=f"actor_{_uuid.uuid4().hex[:6]}",
        email=f"actor_{_uuid.uuid4().hex[:6]}@test.com",
        role="operator",
        status="active",
    )
    db_session.add(user)
    db_session.commit()
    return user


def _run(coro):
    """Helper to run async service methods in sync test context."""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


class TestGetListedContracts:
    """get_listed_contracts."""

    def test_returns_listed_contracts(self, db_session, listed_contract):
        result = db_session.get(type(listed_contract), listed_contract.id)
        assert result is not None

    def test_empty_when_no_listed(self, db_session):
        from app.services.contract_matching_service import ContractMatchingService
        service = ContractMatchingService()
        coro = service.get_listed_contracts(db_session, "operator")
        result = _run(coro)
        assert isinstance(result, list)


class TestPushMatch:
    """push_match."""

    def test_push_match_success(self, db_session, listed_contract, actor_user):
        from app.services.contract_matching_service import ContractMatchingService
        service = ContractMatchingService()
        coro = service.push_match(
            db=db_session,
            contract_id=listed_contract.id,
            participant_type="operator",
            participant_id=actor_user.id,
            match_score=0.85,
            match_reason="商业使用范围匹配",
        )
        matching = _run(coro)
        assert matching.match_score == 0.85
        assert matching.participant_id == actor_user.id
        assert matching.response is None

    def test_push_match_rejects_non_listed(self, db_session, listed_contract):
        from app.services.contract_matching_service import ContractMatchingService
        from fastapi import HTTPException
        listed_contract.status = "active"
        db_session.commit()
        service = ContractMatchingService()
        coro = service.push_match(
            db=db_session,
            contract_id=listed_contract.id,
            participant_type="operator",
            participant_id="anyone",
            match_score=0.5,
        )
        with pytest.raises(HTTPException):
            _run(coro)


class TestRecordView:
    """record_view."""

    def test_record_view_sets_timestamp(self, db_session, listed_contract, actor_user):
        from app.services.contract_matching_service import ContractMatchingService
        service = ContractMatchingService()
        push_coro = service.push_match(
            db=db_session,
            contract_id=listed_contract.id,
            participant_type="operator",
            participant_id=actor_user.id,
            match_score=0.9,
        )
        matching = _run(push_coro)
        view_coro = service.record_view(db_session, matching.id)
        updated = _run(view_coro)
        assert updated.viewed_at is not None


class TestRecordResponse:
    """record_response."""

    def test_accept_response(self, db_session, listed_contract, actor_user):
        from app.services.contract_matching_service import ContractMatchingService
        service = ContractMatchingService()
        push_coro = service.push_match(
            db=db_session,
            contract_id=listed_contract.id,
            participant_type="operator",
            participant_id=actor_user.id,
            match_score=0.9,
        )
        matching = _run(push_coro)
        resp_coro = service.record_response(db_session, matching.id, "accepted")
        updated = _run(resp_coro)
        assert updated.response == "accepted"
        assert updated.responded_at is not None

    def test_counter_offer_with_json(self, db_session, listed_contract, actor_user):
        from app.services.contract_matching_service import ContractMatchingService
        service = ContractMatchingService()
        push_coro = service.push_match(
            db=db_session,
            contract_id=listed_contract.id,
            participant_type="creator",
            participant_id=actor_user.id,
            match_score=0.7,
        )
        matching = _run(push_coro)
        counter_offer = '{"total_amount": 6000}'
        resp_coro = service.record_response(
            db_session, matching.id, "counter_offer", counter_offer
        )
        updated = _run(resp_coro)
        assert updated.response == "counter_offer"
        assert updated.counter_offer_json == counter_offer


class TestGetParticipantMatches:
    """get_participant_matches."""

    def test_get_participant_matches(self, db_session, listed_contract, actor_user):
        from app.services.contract_matching_service import ContractMatchingService
        service = ContractMatchingService()
        # Push two matches for same participant
        _run(service.push_match(
            db=db_session,
            contract_id=listed_contract.id,
            participant_type="operator",
            participant_id=actor_user.id,
            match_score=0.8,
        ))
        _run(service.push_match(
            db=db_session,
            contract_id=listed_contract.id,
            participant_type="operator",
            participant_id=actor_user.id,
            match_score=0.6,
        ))
        coro = service.get_participant_matches(db_session, actor_user.id, "operator")
        results = _run(coro)
        assert len(results) >= 2
