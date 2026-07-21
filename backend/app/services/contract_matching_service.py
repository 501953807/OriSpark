"""合约撮合引擎服务."""

from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.models.contract import ContractMatching, ContractInstance


class ContractMatchingService:
    """合约撮合推荐服务 — 基于标签/地域/评分的匹配推送."""

    async def get_listed_contracts(
        self,
        db: Session,
        participant_type: str = "operator",
        limit: int = 20,
        offset: int = 0,
    ) -> list[dict]:
        """获取可撮合的挂牌合约列表."""
        contracts = (
            db.query(ContractInstance)
            .filter(ContractInstance.status == "listed")
            .order_by(ContractInstance.published_at.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )
        return [self._contract_to_dict(c) for c in contracts]

    async def push_match(
        self,
        db: Session,
        contract_id: str,
        participant_type: str,
        participant_id: str,
        match_score: float,
        match_reason: str = "",
    ) -> ContractMatching:
        """推送撮合推荐."""
        contract = self._get_contract(db, contract_id)
        if contract.status != "listed":
            raise HTTPException(status_code=400, detail="仅挂牌合约可被撮合")

        matching = ContractMatching(
            id=self._generate_id(),
            contract_id=contract_id,
            participant_type=participant_type,
            participant_id=participant_id,
            match_score=match_score,
            match_reason=match_reason,
            pushed_at=datetime.utcnow(),
        )
        db.add(matching)
        db.commit()
        db.refresh(matching)
        return matching

    async def record_view(
        self, db: Session, matching_id: str
    ) -> ContractMatching:
        """记录查看行为."""
        matching = self._get_matching(db, matching_id)
        matching.viewed_at = datetime.utcnow()
        db.commit()
        db.refresh(matching)
        return matching

    async def record_response(
        self, db: Session, matching_id: str, response: str, counter_offer_json: Optional[str] = None
    ) -> ContractMatching:
        """记录参与方响应."""
        matching = self._get_matching(db, matching_id)
        valid_responses = {"accepted", "declined", "counter_offer"}
        if response not in valid_responses:
            raise HTTPException(status_code=400, detail=f"无效响应类型: {response}")
        matching.responded_at = datetime.utcnow()
        matching.response = response
        if counter_offer_json:
            matching.counter_offer_json = counter_offer_json
        db.commit()
        db.refresh(matching)
        return matching

    async def get_participant_matches(
        self,
        db: Session,
        participant_id: str,
        participant_type: str,
        limit: int = 20,
        offset: int = 0,
    ) -> list[dict]:
        """获取某参与方的撮合记录."""
        records = (
            db.query(ContractMatching)
            .filter(
                ContractMatching.participant_id == participant_id,
                ContractMatching.participant_type == participant_type,
            )
            .order_by(ContractMatching.pushed_at.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )
        return [self._matching_to_dict(r) for r in records]

    @staticmethod
    def _generate_id() -> str:
        import uuid
        return uuid.uuid4().hex

    def _get_contract(self, db: Session, contract_id: str) -> ContractInstance:
        contract = (
            db.query(ContractInstance)
            .filter(ContractInstance.id == contract_id)
            .first()
        )
        if not contract:
            raise HTTPException(status_code=404, detail="合约不存在")
        return contract

    def _get_matching(self, db: Session, matching_id: str) -> ContractMatching:
        matching = (
            db.query(ContractMatching)
            .filter(ContractMatching.id == matching_id)
            .first()
        )
        if not matching:
            raise HTTPException(status_code=404, detail="撮合记录不存在")
        return matching

    @staticmethod
    def _contract_to_dict(contract: ContractInstance) -> dict:
        return {
            "id": contract.id,
            "title": contract.title,
            "description": contract.description,
            "work_id": contract.work_id,
            "contract_type": contract.contract_type,
            "total_amount": float(contract.total_amount),
            "currency": contract.currency,
            "billing_cycle": contract.billing_cycle,
            "scope_usage": contract.scope_usage,
            "scope_geography": contract.scope_geography,
            "scope_duration": contract.scope_duration,
            "status": contract.status,
            "verified": contract.verified,
            "published_at": contract.published_at.isoformat() if contract.published_at else None,
        }

    @staticmethod
    def _matching_to_dict(matching: ContractMatching) -> dict:
        return {
            "id": matching.id,
            "contract_id": matching.contract_id,
            "participant_type": matching.participant_type,
            "participant_id": matching.participant_id,
            "match_score": matching.match_score,
            "match_reason": matching.match_reason,
            "pushed_at": matching.pushed_at.isoformat() if matching.pushed_at else None,
            "viewed_at": matching.viewed_at.isoformat() if matching.viewed_at else None,
            "responded_at": matching.responded_at.isoformat() if matching.responded_at else None,
            "response": matching.response,
        }
