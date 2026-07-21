"""分润规则管理服务."""

import json
from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.models.contract import SplitRule, ContractInstance


class SplitRuleService:
    """分润规则全生命周期管理 — 报价竞争、锁定、变更."""

    PLATFORM_FEE_RATE = 0.003  # 平台固定 3‰

    @classmethod
    def get_contract_split_rules(
        cls, db: Session, contract_id: str
    ) -> list[dict]:
        """获取合约当前分润规则."""
        contract = cls._get_contract(db, contract_id)
        rules = (
            db.query(SplitRule)
            .filter(SplitRule.contract_id == contract_id)
            .order_by(SplitRule.created_at.desc())
            .all()
        )
        return [cls._rule_to_dict(r) for r in rules]

    @classmethod
    def submit_quote(
        cls,
        db: Session,
        contract_id: str,
        participant_id: str,
        role: str,
        percentage: float,
        quote_amount: float,
    ) -> SplitRule:
        """参与方提交分润报价."""
        cls._validate_role(role)
        if not 0 < percentage <= 1.0:
            raise HTTPException(status_code=400, detail="分润比例必须在 0-100% 之间")

        contract = cls._get_contract(db, contract_id)
        if contract.status != "listed":
            raise HTTPException(status_code=400, detail="仅挂牌合约可接受报价")

        existing = (
            db.query(SplitRule)
            .filter(
                SplitRule.contract_id == contract_id,
                SplitRule.participant_id == participant_id,
                SplitRule.role == role,
            )
            .first()
        )

        if existing and existing.locked_at is None:
            existing.percentage = percentage
            existing.quote_amount = quote_amount
            existing.quoted_at = datetime.utcnow()
            existing.changed_at = datetime.utcnow()
            existing.change_reason = "重新报价"
            db.commit()
            db.refresh(existing)
            return existing

        rule = SplitRule(
            id=cls._generate_id(),
            contract_id=contract_id,
            participant_id=participant_id,
            role=role,
            percentage=percentage,
            quote_amount=quote_amount,
            quoted_at=datetime.utcnow(),
        )
        db.add(rule)
        db.commit()
        db.refresh(rule)
        return rule

    @classmethod
    def lock_best_quotes(
        cls, db: Session, contract_id: str
    ) -> list[dict]:
        """锁定各角色最优报价."""
        contract = cls._get_contract(db, contract_id)
        if contract.status != "listed":
            raise HTTPException(status_code=400, detail="仅挂牌合约可锁定报价")

        roles = ["operator", "legal_rep", "tax_agent", "logistics", "insurer"]
        locked: list[dict] = []

        for role in roles:
            candidates = (
                db.query(SplitRule)
                .filter(
                    SplitRule.contract_id == contract_id,
                    SplitRule.role == role,
                    SplitRule.locked_at.is_(None),
                )
                .order_by(SplitRule.percentage.asc())
                .limit(1)
                .all()
            )
            for candidate in candidates:
                candidate.locked_at = datetime.utcnow()
                candidate.change_reason = "最优报价锁定"
                locked.append(cls._rule_to_dict(candidate))

        db.commit()
        return locked

    @classmethod
    def update_split_rules_json(
        cls, db: Session, contract_id: str, rules: list[dict]
    ) -> ContractInstance:
        """将锁定的分润规则写入合约 split_rules_json."""
        contract = cls._get_contract(db, contract_id)
        if contract.status not in ("subscribed", "escrowed"):
            raise HTTPException(
                status_code=400, detail="仅认购/托管合约可写入分润规则"
            )

        total = sum(r.get("percentage", 0) for r in rules)
        platform_fee = round(total * cls.PLATFORM_FEE_RATE, 2)
        if platform_fee > contract.total_amount:
            raise HTTPException(
                status_code=400,
                detail=f"分润总额超出合约金额（平台费 {platform_fee}）",
            )

        contract.split_rules_json = json.dumps(rules, ensure_ascii=False)
        db.commit()
        db.refresh(contract)
        return contract

    @classmethod
    def calculate_platform_fee(cls, total_amount: float) -> float:
        """计算平台 3‰ 固定费用."""
        return round(total_amount * cls.PLATFORM_FEE_RATE, 2)

    @staticmethod
    def _validate_role(role: str) -> bool:
        valid_roles = {
            "creator", "operator", "legal_rep", "tax_agent",
            "logistics", "insurer", "trader", "payment_provider", "platform",
        }
        if role not in valid_roles:
            raise HTTPException(
                status_code=400,
                detail=f"无效角色类型: {role}",
            )
        return True

    @staticmethod
    def _generate_id() -> str:
        import uuid
        return uuid.uuid4().hex

    @staticmethod
    def _get_contract(db: Session, contract_id: str) -> ContractInstance:
        contract = (
            db.query(ContractInstance)
            .filter(ContractInstance.id == contract_id)
            .first()
        )
        if not contract:
            raise HTTPException(status_code=404, detail="合约不存在")
        return contract

    @staticmethod
    def _rule_to_dict(rule: SplitRule) -> dict:
        return {
            "id": rule.id,
            "contract_id": rule.contract_id,
            "participant_id": rule.participant_id,
            "role": rule.role,
            "percentage": rule.percentage,
            "quote_amount": float(rule.quote_amount) if rule.quote_amount else None,
            "quoted_at": rule.quoted_at.isoformat() if rule.quoted_at else None,
            "locked_at": rule.locked_at.isoformat() if rule.locked_at else None,
            "changed_at": rule.changed_at.isoformat() if rule.changed_at else None,
            "change_reason": rule.change_reason,
        }
