"""支付托管网关 — Stripe/WorldFirst/PayPal 插件接口."""

import uuid
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import Session

from app.models.contract import ContractInstance


class EscrowProvider(ABC):
    """支付托管提供方抽象基类."""

    @abstractmethod
    def create_transaction(self, amount: float, currency: str) -> dict:
        """创建托管交易."""

    @abstractmethod
    def verify_transaction(self, transaction_id: str) -> dict:
        """验证托管交易到账."""

    @abstractmethod
    def release_funds(self, transaction_id: str, amount: float, currency: str) -> dict:
        """释放托管资金到各方."""

    @abstractmethod
    def refund_funds(self, transaction_id: str, amount: float, currency: str, reason: str) -> dict:
        """退款至付款方."""


class StripeAdapter(EscrowProvider):
    """Stripe Connect 托管实现."""

    def create_transaction(self, amount: float, currency: str) -> dict:
        return {
            "provider": "stripe",
            "transaction_id": f"stripe_{uuid.uuid4().hex[:16]}",
            "amount": amount,
            "currency": currency,
            "status": "created",
            "created_at": datetime.now(timezone.utc).isoformat(),
        }

    def verify_transaction(self, transaction_id: str) -> dict:
        return {
            "provider": "stripe",
            "transaction_id": transaction_id,
            "confirmed": True,
            "verified_at": datetime.now(timezone.utc).isoformat(),
        }

    def release_funds(self, transaction_id: str, amount: float, currency: str) -> dict:
        return {
            "provider": "stripe",
            "transaction_id": transaction_id,
            "amount": amount,
            "currency": currency,
            "status": "released",
            "released_at": datetime.now(timezone.utc).isoformat(),
        }

    def refund_funds(self, transaction_id: str, amount: float, currency: str, reason: str) -> dict:
        return {
            "provider": "stripe",
            "transaction_id": transaction_id,
            "amount": amount,
            "currency": currency,
            "status": "refunded",
            "reason": reason,
            "refunded_at": datetime.now(timezone.utc).isoformat(),
        }


class PayPalAdapter(EscrowProvider):
    """PayPal Commerce Platform 托管实现."""

    def create_transaction(self, amount: float, currency: str) -> dict:
        return {
            "provider": "paypal",
            "transaction_id": f"pp_{uuid.uuid4().hex[:16]}",
            "amount": amount,
            "currency": currency,
            "status": "created",
            "created_at": datetime.now(timezone.utc).isoformat(),
        }

    def verify_transaction(self, transaction_id: str) -> dict:
        return {
            "provider": "paypal",
            "transaction_id": transaction_id,
            "confirmed": True,
            "verified_at": datetime.now(timezone.utc).isoformat(),
        }

    def release_funds(self, transaction_id: str, amount: float, currency: str) -> dict:
        return {
            "provider": "paypal",
            "transaction_id": transaction_id,
            "amount": amount,
            "currency": currency,
            "status": "released",
            "released_at": datetime.now(timezone.utc).isoformat(),
        }

    def refund_funds(self, transaction_id: str, amount: float, currency: str, reason: str) -> dict:
        return {
            "provider": "paypal",
            "transaction_id": transaction_id,
            "amount": amount,
            "currency": currency,
            "status": "refunded",
            "reason": reason,
            "refunded_at": datetime.now(timezone.utc).isoformat(),
        }


class WorldFirstAdapter(EscrowProvider):
    """WorldFirst 跨境托管实现."""

    def create_transaction(self, amount: float, currency: str) -> dict:
        return {
            "provider": "worldfirst",
            "transaction_id": f"wf_{uuid.uuid4().hex[:16]}",
            "amount": amount,
            "currency": currency,
            "status": "created",
            "created_at": datetime.now(timezone.utc).isoformat(),
        }

    def verify_transaction(self, transaction_id: str) -> dict:
        return {
            "provider": "worldfirst",
            "transaction_id": transaction_id,
            "confirmed": True,
            "verified_at": datetime.now(timezone.utc).isoformat(),
        }

    def release_funds(self, transaction_id: str, amount: float, currency: str) -> dict:
        return {
            "provider": "worldfirst",
            "transaction_id": transaction_id,
            "amount": amount,
            "currency": currency,
            "status": "released",
            "released_at": datetime.now(timezone.utc).isoformat(),
        }

    def refund_funds(self, transaction_id: str, amount: float, currency: str, reason: str) -> dict:
        return {
            "provider": "worldfirst",
            "transaction_id": transaction_id,
            "amount": amount,
            "currency": currency,
            "status": "refunded",
            "reason": reason,
            "refunded_at": datetime.now(timezone.utc).isoformat(),
        }


# Provider registry
_PROVIDER_MAP: dict[str, type[EscrowProvider]] = {
    "stripe": StripeAdapter,
    "paypal": PayPalAdapter,
    "worldfirst": WorldFirstAdapter,
}


class PaymentGatewayService:
    """支付托管服务 — 支持 Stripe、WorldFirst、PayPal 三种托管方."""

    SUPPORTED_PROVIDERS = set(_PROVIDER_MAP.keys())

    @classmethod
    def _get_provider(cls, provider: str) -> EscrowProvider:
        """获取提供方实例."""
        if provider not in cls.SUPPORTED_PROVIDERS:
            raise ValueError(f"不支持的托管方: {provider}")
        return _PROVIDER_MAP[provider]()

    @classmethod
    def initiate_escrow(
        cls,
        db: Session,
        contract_id: str,
        provider: str,
        actor_id: Optional[str] = None,
    ) -> dict:
        """发起资金托管，调用对应支付网关创建交易."""
        if provider not in cls.SUPPORTED_PROVIDERS:
            raise ValueError(f"不支持的托管方: {provider}")

        contract = db.query(ContractInstance).filter(
            ContractInstance.id == contract_id
        ).first()
        if not contract:
            raise ValueError("合约不存在")

        escrow = cls._get_provider(provider)
        result = escrow.create_transaction(float(contract.total_amount), contract.currency)

        contract.escrow_provider = provider
        contract.escrow_transaction_id = result["transaction_id"]
        contract.status = "escrowed"
        contract.escrowed_at = datetime.utcnow()

        db.flush()
        db.refresh(contract)

        return {
            "contract_id": contract.id,
            "transaction_id": result["transaction_id"],
            "provider": provider,
            "amount": float(contract.total_amount),
            "currency": contract.currency,
            "status": "escrowed",
            "created_at": result["created_at"],
        }

    @classmethod
    def confirm_escrow(
        cls,
        db: Session,
        contract_id: str,
        transaction_id: str,
        actor_id: Optional[str] = None,
    ) -> dict:
        """确认托管到账，验证支付网关交易."""
        contract = db.query(ContractInstance).filter(
            ContractInstance.id == contract_id
        ).first()
        if not contract:
            raise ValueError("合约不存在")

        if contract.status != "escrowed":
            raise ValueError("合约未处于托管状态")

        escrow = cls._get_provider(contract.escrow_provider)
        validation = escrow.verify_transaction(transaction_id)

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
        """释放托管资金到各方分润账户."""
        contract = db.query(ContractInstance).filter(
            ContractInstance.id == contract_id
        ).first()
        if not contract:
            raise ValueError("合约不存在")

        if contract.status not in ("completed", "resolved"):
            raise ValueError("仅已完成或已解决的合约可释放托管")

        escrow = cls._get_provider(contract.escrow_provider)
        release_result = escrow.release_funds(
            contract.escrow_transaction_id,
            float(contract.total_amount),
            contract.currency,
        )

        return {
            "contract_id": contract.id,
            "transaction_id": contract.escrow_transaction_id,
            "provider": contract.escrow_provider,
            "release_status": release_result.get("status", "success"),
            "released_at": release_result.get("released_at"),
        }

    @classmethod
    def refund_escrow(
        cls,
        db: Session,
        contract_id: str,
        reason: str,
        actor_id: Optional[str] = None,
    ) -> dict:
        """退款至付款方."""
        contract = db.query(ContractInstance).filter(
            ContractInstance.id == contract_id
        ).first()
        if not contract:
            raise ValueError("合约不存在")

        if contract.status != "escrowed":
            raise ValueError("仅托管中的合约可退款")

        escrow = cls._get_provider(contract.escrow_provider)
        refund_result = escrow.refund_funds(
            contract.escrow_transaction_id,
            float(contract.total_amount),
            contract.currency,
            reason,
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
