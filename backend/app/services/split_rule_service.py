"""分润规则管理服务."""

import json
import uuid
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP
from typing import Optional

from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.models.contract import SplitRule, ContractInstance, SplitExecutionLog


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

        total_pct = sum(r.get("percentage", 0) for r in rules)
        platform_fee = round(total_pct * cls.PLATFORM_FEE_RATE, 2)
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
    def calculate_split(
        cls, db: Session, contract_id: str, total_amount: Optional[float] = None
    ) -> dict:
        """计算分润方案 — 读取合约 split_rules_json，按百分比分配金额.

        Returns:
            {
                "contract_id": str,
                "total_amount": float,
                "platform_fee": float,
                "distributions": [
                    {"role": str, "participant_id": str, "percentage": float, "amount": float},
                    ...
                ],
            }
        """
        contract = cls._get_contract(db, contract_id)
        if not contract.split_rules_json or contract.split_rules_json == "[]":
            raise HTTPException(
                status_code=400,
                detail="合约暂无分润规则，请先锁定报价",
            )

        rules = json.loads(contract.split_rules_json)
        if not rules:
            raise HTTPException(status_code=400, detail="分润规则为空")

        amount = Decimal(str(total_amount or contract.total_amount))
        platform_fee = float((amount * Decimal(str(cls.PLATFORM_FEE_RATE))).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))
        distributions = []

        for rule in rules:
            pct = Decimal(str(rule.get("percentage", 0)))
            dist_amount = float((amount * pct).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))
            distributions.append({
                "role": rule["role"],
                "participant_id": rule["participant_id"],
                "percentage": rule["percentage"],
                "amount": dist_amount,
            })

        return {
            "contract_id": contract.id,
            "total_amount": float(amount),
            "platform_fee": platform_fee,
            "distributions": distributions,
        }

    @classmethod
    def execute_split(
        cls,
        db: Session,
        contract_id: str,
        actor_id: Optional[str] = None,
        total_amount: Optional[float] = None,
        batch_id: Optional[str] = None,
    ) -> dict:
        """执行分润 — 计算分润方案，创建 SplitExecutionLog，调用支付网关释放资金.

        状态流转: 合约需处于 completed/resolved/executing 状态.
        如果合约配置了 escrow_provider，则通过该 provider 执行资金分发.
        """
        contract = cls._get_contract(db, contract_id)
        if contract.status not in ("completed", "resolved", "executing"):
            raise HTTPException(
                status_code=400,
                detail=f"当前状态 {contract.status} 不允许执行分润",
            )

        # 1. 计算分润
        calc = cls.calculate_split(db, contract_id, total_amount)

        # 2. 生成 batch_id
        if not batch_id:
            cycle = contract.completed_at or datetime.utcnow()
            batch_id = f"{cycle.strftime('%Y-%m')}_monthly"

        # 3. 尝试调用支付网关释放资金
        executor = "manual"
        error_message = None
        if contract.escrow_provider and contract.escrow_transaction_id:
            try:
                from app.services.payment_gateway import PaymentGatewayService
                pgw_result = PaymentGatewayService.release_escrow(
                    db, contract_id, actor_id=actor_id,
                )
                executor = pgw_result.get("provider", "stripe")
            except Exception as e:
                error_message = str(e)
        else:
            # 无支付托管配置是正常情况（模拟执行），不算错误
            executor = "manual"

        # 4. 创建执行日志
        exec_log = SplitExecutionLog(
            id=uuid.uuid4().hex,
            contract_id=contract_id,
            execution_batch=batch_id,
            total_amount=calc["total_amount"],
            platform_fee=calc["platform_fee"],
            executor=executor,
            status="success" if not error_message else "failed",
            error_message=error_message,
            detail_json=json.dumps(calc["distributions"], ensure_ascii=False),
            executed_at=datetime.utcnow(),
        )
        db.add(exec_log)
        db.commit()
        db.refresh(exec_log)

        return {
            "log_id": exec_log.id,
            "batch_id": batch_id,
            "status": exec_log.status,
            "total_amount": calc["total_amount"],
            "platform_fee": calc["platform_fee"],
            "distributions": calc["distributions"],
            "error": error_message,
        }

    @classmethod
    def refund_split(
        cls,
        db: Session,
        contract_id: str,
        reason: str,
        actor_id: Optional[str] = None,
    ) -> dict:
        """退款分润 — 将最近的成功执行记录标记为 refunded，调用支付网关退款.

        仅允许对 status=success 的执行记录进行退款.
        """
        contract = cls._get_contract(db, contract_id)

        # 查找最近的成功执行记录
        latest_exec = (
            db.query(SplitExecutionLog)
            .filter(
                SplitExecutionLog.contract_id == contract_id,
                SplitExecutionLog.status == "success",
            )
            .order_by(SplitExecutionLog.executed_at.desc())
            .first()
        )

        if not latest_exec:
            raise HTTPException(
                status_code=400,
                detail="没有找到可退款的有效分润执行记录",
            )

        # 调用支付网关退款
        refund_executor = "manual"
        if contract.escrow_provider and contract.escrow_transaction_id:
            try:
                from app.services.payment_gateway import PaymentGatewayService
                PaymentGatewayService.refund_escrow(
                    db, contract_id, reason=reason, actor_id=actor_id,
                )
                refund_executor = contract.escrow_provider
            except Exception as e:
                reason = f"{reason} | 网关退款失败: {str(e)}"

        # 更新执行日志状态
        latest_exec.status = "refunded"
        latest_exec.executor = refund_executor
        db.commit()
        db.refresh(latest_exec)

        return {
            "log_id": latest_exec.id,
            "contract_id": contract_id,
            "status": "refunded",
            "reason": reason,
            "refunded_at": latest_exec.executed_at.isoformat() if latest_exec.executed_at else None,
        }

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
