"""合约生命周期管理服务."""

import uuid
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.models.contract import ContractInstance


class ContractEscrowService:
    """合约全生命周期管理."""

    # 合法状态流转
    VALID_TRANSITIONS = {
        "draft": ["listed", "cancelled"],
        "listed": ["active", "cancelled"],
        "active": ["subscribed"],
        "subscribed": ["escrowed", "cancelled"],
        "escrowed": ["insured", "refunded"],
        "insured": ["executing"],
        "executing": ["inspect", "completed"],
        "inspect": ["completed", "dispute"],
        "dispute": ["resolved", "refunded"],
        "resolved": ["completed"],
        "refunded": ["cancelled"],
        "completed": [],
        "cancelled": [],
    }

    async def create_contract(
        self,
        db: Session,
        title: str,
        description: str,
        work_id: str,
        contract_type: str,
        total_amount: float,
        currency: str,
        billing_cycle: str,
        scope_usage: str,
        scope_geography: str,
        scope_duration: str,
        creator_id: str,
        split_rules_json: str = "[]",
    ) -> ContractInstance:
        """创建合约草稿."""
        contract = ContractInstance(
            id=uuid.uuid4().hex,
            title=title,
            description=description,
            work_id=work_id,
            contract_type=contract_type,
            total_amount=total_amount,
            currency=currency,
            billing_cycle=billing_cycle,
            scope_usage=scope_usage,
            scope_geography=scope_geography,
            scope_duration=scope_duration,
            creator_id=creator_id,
            split_rules_json=split_rules_json,
            status="draft",
        )
        db.add(contract)
        db.commit()
        db.refresh(contract)
        return contract

    async def publish_contract(self, db: Session, contract_id: str) -> ContractInstance:
        """发布合约挂牌."""
        contract = self._get_contract(db, contract_id)
        self._validate_transition(contract.status, "listed")
        contract.status = "listed"
        contract.published_at = datetime.utcnow()
        contract.verified = "pending"
        db.commit()
        db.refresh(contract)
        return contract

    async def subscribe_contract(
        self, db: Session, contract_id: str, subscriber_id: str
    ) -> ContractInstance:
        """认购合约."""
        contract = self._get_contract(db, contract_id)
        self._validate_transition(contract.status, "subscribed")
        contract.status = "subscribed"
        contract.subscribed_at = datetime.utcnow()
        contract.operator_id = subscriber_id
        db.commit()
        db.refresh(contract)
        return contract

    async def initiate_escrow(
        self, db: Session, contract_id: str, provider: str
    ) -> ContractInstance:
        """发起资金托管."""
        contract = self._get_contract(db, contract_id)
        self._validate_transition(contract.status, "escrowed")
        contract.status = "escrowed"
        contract.escrowed_at = datetime.utcnow()
        contract.escrow_provider = provider
        db.commit()
        db.refresh(contract)
        return contract

    async def confirm_escrow(
        self, db: Session, contract_id: str, transaction_id: str
    ) -> ContractInstance:
        """确认托管到账."""
        contract = self._get_contract(db, contract_id)
        if contract.status != "escrowed":
            raise HTTPException(status_code=400, detail="合约未处于托管状态")
        contract.escrow_transaction_id = transaction_id
        db.commit()
        db.refresh(contract)
        return contract

    async def activate_insurance(self, db: Session, contract_id: str) -> ContractInstance:
        """激活保险."""
        contract = self._get_contract(db, contract_id)
        self._validate_transition(contract.status, "insured")
        contract.status = "insured"
        db.commit()
        db.refresh(contract)
        return contract

    async def execute_contract(self, db: Session, contract_id: str) -> ContractInstance:
        """开始履约."""
        contract = self._get_contract(db, contract_id)
        self._validate_transition(contract.status, "executing")
        contract.status = "executing"
        contract.executed_at = datetime.utcnow()
        db.commit()
        db.refresh(contract)
        return contract

    async def complete_contract(self, db: Session, contract_id: str) -> ContractInstance:
        """完成合约."""
        contract = self._get_contract(db, contract_id)
        self._validate_transition(contract.status, "completed")
        contract.status = "completed"
        contract.completed_at = datetime.utcnow()
        db.commit()
        db.refresh(contract)
        return contract

    async def reject_inspection(
        self, db: Session, contract_id: str, reason: str
    ) -> ContractInstance:
        """拒绝验货/发起争议."""
        contract = self._get_contract(db, contract_id)
        self._validate_transition(contract.status, "dispute")
        contract.status = "dispute"
        contract.review_comment = reason
        db.commit()
        db.refresh(contract)
        return contract

    async def cancel_contract(
        self, db: Session, contract_id: str, reason: str
    ) -> ContractInstance:
        """取消合约."""
        contract = self._get_contract(db, contract_id)
        if contract.status not in ("draft", "listed", "subscribed"):
            raise HTTPException(status_code=400, detail="当前状态不可取消")
        contract.status = "cancelled"
        contract.review_comment = reason
        db.commit()
        db.refresh(contract)
        return contract

    async def get_contract_timeline(
        self, db: Session, contract_id: str
    ) -> list[dict]:
        """获取合约时间线."""
        contract = self._get_contract(db, contract_id)
        timeline = []
        for field, label in [
            ("created_at", "创建"),
            ("published_at", "挂牌"),
            ("subscribed_at", "认购"),
            ("escrowed_at", "托管"),
            ("executed_at", "履约"),
            ("completed_at", "完成"),
        ]:
            value = getattr(contract, field, None)
            if value:
                timeline.append({"timestamp": value.isoformat(), "event": label})
        return timeline

    def _get_contract(self, db: Session, contract_id: str) -> ContractInstance:
        """获取合约实例."""
        contract = db.query(ContractInstance).filter(ContractInstance.id == contract_id).first()
        if not contract:
            raise HTTPException(status_code=404, detail="合约不存在")
        return contract

    def _validate_transition(self, current: str, target: str) -> bool:
        """验证状态流转是否合法."""
        allowed = self.VALID_TRANSITIONS.get(current, [])
        if target not in allowed:
            raise HTTPException(
                status_code=400,
                detail=f"非法状态流转：{current} -> {target}",
            )
        return True
