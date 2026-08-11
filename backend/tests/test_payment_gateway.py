"""支付托管网关测试 — Stripe/WorldFirst/PayPal 三种提供方."""

import pytest
from unittest.mock import patch, MagicMock

from app.services.payment_gateway import (
    PaymentGatewayService,
    StripeGateway,
    PayPalGateway,
    WorldFirstGateway,
    PaymentGateway,
)
    PaymentGatewayService,
    StripeGateway,
    PayPalGateway,
    WorldFirstGateway,
    PaymentGateway,
)


class TestProviderRegistry:
    """测试提供方注册表."""

    def test_supported_providers(self):
        assert PaymentGatewayService.SUPPORTED_PROVIDERS == {"stripe", "paypal", "worldfirst"}

    def test_get_provider_stripe(self):
        provider = PaymentGatewayService._get_provider("stripe")
        assert isinstance(provider, StripeGateway)

    def test_get_provider_paypal(self):
        provider = PaymentGatewayService._get_provider("paypal")
        assert isinstance(provider, PayPalGateway)

    def test_get_provider_worldfirst(self):
        provider = PaymentGatewayService._get_provider("worldfirst")
        assert isinstance(provider, WorldFirstGateway)

    def test_get_provider_unknown_raises(self):
        with pytest.raises(ValueError, match="不支持的托管方"):
            PaymentGatewayService._get_provider("unknown")


class TestStripeGateway:
    """Stripe 托管实现测试."""

    def test_create_transaction(self):
        adapter = StripeGateway()
        result = adapter.create_transaction(1000.0, "CNY")
        assert result["provider"] == "stripe"
        assert result["transaction_id"].startswith("stripe_")
        assert result["amount"] == 1000.0
        assert result["currency"] == "CNY"
        assert result["status"] == "created"

    def test_verify_transaction(self):
        adapter = StripeGateway()
        result = adapter.verify_transaction("stripe_abc123")
        assert result["confirmed"] is True
        assert result["transaction_id"] == "stripe_abc123"

    def test_release_funds(self):
        adapter = StripeGateway()
        result = adapter.release_funds("stripe_abc123", 1000.0, "CNY")
        assert result["status"] == "released"
        assert result["provider"] == "stripe"

    def test_refund_funds(self):
        adapter = StripeGateway()
        result = adapter.refund_funds("stripe_abc123", 500.0, "CNY", "用户取消")
        assert result["status"] == "refunded"
        assert result["reason"] == "用户取消"


class TestPayPalGateway:
    """PayPal 托管实现测试."""

    def test_create_transaction(self):
        adapter = PayPalGateway()
        result = adapter.create_transaction(200.0, "USD")
        assert result["provider"] == "paypal"
        assert result["transaction_id"].startswith("pp_")

    def test_release_funds(self):
        adapter = PayPalGateway()
        result = adapter.release_funds("pp_xyz", 200.0, "USD")
        assert result["status"] == "released"


class TestWorldFirstGateway:
    """WorldFirst 托管实现测试."""

    def test_create_transaction(self):
        adapter = WorldFirstGateway()
        result = adapter.create_transaction(5000.0, "HKD")
        assert result["provider"] == "worldfirst"
        assert result["transaction_id"].startswith("wf_")

    def test_refund_funds(self):
        adapter = WorldFirstGateway()
        result = adapter.refund_funds("wf_abc", 5000.0, "HKD", "争议退款")
        assert result["status"] == "refunded"
        assert result["provider"] == "worldfirst"


class TestPaymentGatewayInitiate:
    """PaymentGatewayService.initiate_escrow 集成测试."""

    @pytest.fixture
    def mock_contract(self):
        contract = MagicMock()
        contract.id = "test_contract_1"
        contract.total_amount = 999.99
        contract.currency = "CNY"
        return contract

    @pytest.fixture
    def mock_db(self, mock_contract):
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = mock_contract
        return db

    def test_initiate_stripe(self, mock_db, mock_contract):
        result = PaymentGatewayService.initiate_escrow(
            db=mock_db, contract_id="test_contract_1", provider="stripe"
        )
        assert result["contract_id"] == "test_contract_1"
        assert result["provider"] == "stripe"
        assert result["amount"] == 999.99
        assert result["currency"] == "CNY"
        assert result["status"] == "escrowed"
        assert mock_contract.escrow_provider == "stripe"
        assert mock_contract.status == "escrowed"

    def test_initiate_paypal(self, mock_db, mock_contract):
        result = PaymentGatewayService.initiate_escrow(
            db=mock_db, contract_id="test_contract_1", provider="paypal"
        )
        assert result["provider"] == "paypal"

    def test_initiate_worldfirst(self, mock_db, mock_contract):
        result = PaymentGatewayService.initiate_escrow(
            db=mock_db, contract_id="test_contract_1", provider="worldfirst"
        )
        assert result["provider"] == "worldfirst"

    def test_initiate_invalid_provider(self, mock_db):
        with pytest.raises(ValueError, match="不支持的托管方"):
            PaymentGatewayService.initiate_escrow(
                db=mock_db, contract_id="test_contract_1", provider="alipay"
            )

    def test_initiate_nonexistent_contract(self):
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = None
        with pytest.raises(ValueError, match="合约不存在"):
            PaymentGatewayService.initiate_escrow(
                db=db, contract_id="nonexistent", provider="stripe"
            )


class TestPaymentGatewayConfirm:
    """PaymentGatewayService.confirm_escrow 测试."""

    @pytest.fixture
    def escrowed_contract(self):
        contract = MagicMock()
        contract.id = "test_contract_1"
        contract.escrow_provider = "stripe"
        contract.escrow_transaction_id = "stripe_abc123"
        contract.status = "escrowed"
        return contract

    @pytest.fixture
    def mock_db(self, escrowed_contract):
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = escrowed_contract
        return db

    def test_confirm_stripe(self, mock_db, escrowed_contract):
        result = PaymentGatewayService.confirm_escrow(
            db=mock_db,
            contract_id="test_contract_1",
            transaction_id="stripe_abc123",
        )
        assert result["status"] == "escrow_confirmed"
        assert result["transaction_id"] == "stripe_abc123"

    def test_confirm_wrong_status(self, escrowed_contract):
        escrowed_contract.status = "active"
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = escrowed_contract
        with pytest.raises(ValueError, match="未处于托管状态"):
            PaymentGatewayService.confirm_escrow(
                db=db,
                contract_id="test_contract_1",
                transaction_id="stripe_abc123",
            )


class TestPaymentGatewayRelease:
    """PaymentGatewayService.release_escrow 测试."""

    @pytest.fixture
    def completed_contract(self):
        contract = MagicMock()
        contract.id = "test_contract_1"
        contract.escrow_provider = "stripe"
        contract.escrow_transaction_id = "stripe_abc123"
        contract.total_amount = 999.99
        contract.currency = "CNY"
        contract.status = "completed"
        return contract

    @pytest.fixture
    def mock_db(self, completed_contract):
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = completed_contract
        return db

    def test_release_completed_contract(self, mock_db, completed_contract):
        result = PaymentGatewayService.release_escrow(
            db=mock_db, contract_id="test_contract_1"
        )
        assert result["release_status"] == "released"
        assert result["provider"] == "stripe"

    def test_release_non_completed_contract(self, completed_contract):
        completed_contract.status = "escrowed"
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = completed_contract
        with pytest.raises(ValueError, match="仅已完成或已解决的合约可释放托管"):
            PaymentGatewayService.release_escrow(
                db=db, contract_id="test_contract_1"
            )


class TestPaymentGatewayRefund:
    """PaymentGatewayService.refund_escrow 测试."""

    @pytest.fixture
    def escrowed_contract(self):
        contract = MagicMock()
        contract.id = "test_contract_1"
        contract.escrow_provider = "paypal"
        contract.escrow_transaction_id = "pp_xyz789"
        contract.total_amount = 500.0
        contract.currency = "CNY"
        contract.status = "escrowed"
        return contract

    @pytest.fixture
    def mock_db(self, escrowed_contract):
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = escrowed_contract
        return db

    def test_refund_escrowed_contract(self, mock_db, escrowed_contract):
        result = PaymentGatewayService.refund_escrow(
            db=mock_db,
            contract_id="test_contract_1",
            reason="买家申请退款",
        )
        assert result["refund_status"] == "refunded"
        assert result["reason"] == "买家申请退款"
        assert escrowed_contract.status == "refunded"

    def test_refund_non_escrowed_contract(self, escrowed_contract):
        escrowed_contract.status = "completed"
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = escrowed_contract
        with pytest.raises(ValueError, match="仅托管中的合约可退款"):
            PaymentGatewayService.refund_escrow(
                db=db,
                contract_id="test_contract_1",
                reason="测试",
            )
