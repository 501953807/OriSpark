"""支付托管网关 — Stripe/WorldFirst/PayPal 插件接口."""

import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import Session

from app.models.contract import ContractInstance


class PaymentGatewayService:
    """支付托管服务 — 支持 Stripe、WorldFirst、PayPal 三种托管方."""

    SUPPORTED_PROVIDERS = {"stripe", "worldfirst", "paypal"}

    @classmethod
    def initiate_escrow(
        cls,
        db: Session,
        contract_id: str,
        provider: str,
        amount: float,
        currency: str,
        actor_id: Optional[str] = None,
    ) -> dict:
        """发起资金托管."""
        if provider not in cls.SUPPORTED_PROVIDERS:
            raise ValueError(f"不支持的托管方: {provider}")

        contract = db.query(ContractInstance).filter(
            ContractInstance.id == contract_id
        ).first()
        if not contract:
            raise ValueError("合约不存在")

        # 生成托管交易 ID
        transaction_id = f"escrow_{uuid.uuid4().hex[:16]}"

        # 调用对应支付网关
        result = cls._create_escrow_transaction(provider, amount, currency)

        # 更新合约状态
        contract.escrow_provider = provider
        contract.escrow_transaction_id = transaction_id
        contract.status = "escrowed"
        contract.escrowed_at = datetime.utcnow()

        db.flush()
        db.refresh(contract)

        return {
            "contract_id": contract.id,
            "transaction_id": transaction_id,
            "provider": provider,
            "amount": amount,
            "currency": currency,
            "status": "escrowed",
            "created_at": datetime.now(timezone.utc).isoformat(),
        }

    @classmethod
    def confirm_escrow(
        cls,
        db: Session,
        contract_id: str,
        transaction_id: str,
        actor_id: Optional[str] = None,
    ) -> dict:
        """确认托管到账."""
        contract = db.query(ContractInstance).filter(
            ContractInstance.id == contract_id
        ).first()
        if not contract:
            raise ValueError("合约不存在")

        if contract.status != "escrowed":
            raise ValueError("合约未处于托管状态")

        # 验证托管交易
        validation = cls._verify_escrow_transaction(
            contract.escrow_provider, transaction_id
        )

        if not validation.get("confirmed"):
            raise ValueError(f"托管交易验证失败: {validation.get('error')}")

        contract.escrow_transaction_id = transaction_id
        contract.updated_at = datetime.utcnow()

        db.flush()
        db.refresh(contract)

        return {
            "contract_id": contract.id,
            "transaction_id": transaction_id,
            "status": "escrow_confirmed",
        }

    @classmethod
    def release_escrow(
        cls,
        db: Session,
        contract_id: str,
        actor_id: Optional[str] = None,
    ) -> dict:
        """释放托管资金."""
        contract = db.query(ContractInstance).filter(
            ContractInstance.id == contract_id
        ).first()
        if not contract:
            raise ValueError("合约不存在")

        if contract.status not in ("completed", "resolved"):
            raise ValueError("仅已完成或已解决的合约可释放托管")

        # 调用支付网关释放资金
        release_result = cls._release_funds(
            contract.escrow_provider,
            contract.escrow_transaction_id,
            float(contract.total_amount),
            contract.currency,
        )

        return {
            "contract_id": contract.id,
            "transaction_id": contract.escrow_transaction_id,
            "provider": contract.escrow_provider,
            "release_status": release_result.get("status", "success"),
        }

    @classmethod
    def refund_escrow(
        cls,
        db: Session,
        contract_id: str,
        reason: str,
        actor_id: Optional[str] = None,
    ) -> dict:
        """退款."""
        contract = db.query(ContractInstance).filter(
            ContractInstance.id == contract_id
        ).first()
        if not contract:
            raise ValueError("合约不存在")

        if contract.status != "escrowed":
            raise ValueError("仅托管中的合约可退款")

        # 调用支付网关退款
        refund_result = cls._refund_funds(
            contract.escrow_provider,
            contract.escrow_transaction_id,
            float(contract.total_amount),
            contract.currency,
        )

        contract.status = "refunded"
        contract.review_comment = reason
        contract.updated_at = datetime.utcnow()

        db.flush()
        db.refresh(contract)

        return {
            "contract_id": contract.id,
            "transaction_id": contract.escrow_transaction_id,
            "provider": contract.escrow_provider,
            "refund_status": refund_result.get("status", "success"),
            "reason": reason,
        }

    @classmethod
    def _create_escrow_transaction(
        cls, provider: str, amount: float, currency: str
    ) -> dict:
        """创建托管交易 (模拟实现)."""
        return {
            "provider": provider,
            "amount": amount,
            "currency": currency,
            "status": "created",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    @classmethod
    def _verify_escrow_transaction(
        cls, provider: str, transaction_id: str
    ) -> dict:
        """验证托管交易 (模拟实现)."""
        return {
            "provider": provider,
            "transaction_id": transaction_id,
            "confirmed": True,
            "verified_at": datetime.now(timezone.utc).isoformat(),
        }

    @classmethod
    def _release_funds(
        cls, provider: str, transaction_id: str, amount: float, currency: str
    ) -> dict:
        """释放托管资金 (模拟实现)."""
        return {
            "provider": provider,
            "transaction_id": transaction_id,
            "amount": amount,
            "currency": currency,
            "status": "released",
            "released_at": datetime.now(timezone.utc).isoformat(),
        }

    @classmethod
    def _refund_funds(
        cls, provider: str, transaction_id: str, amount: float, currency: str
    ) -> dict:
        """退款 (模拟实现)."""
        return {
            "provider": provider,
            "transaction_id": transaction_id,
            "amount": amount,
            "currency": currency,
            "status": "refunded",
            "refunded_at": datetime.now(timezone.utc).isoformat(),
        }
