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


class TestStripeGateway:
    """Stripe Gateway 测试."""

    def test_create_transaction(self):
        gateway = StripeGateway()
        result = gateway.create_transaction(100.0, "USD")
        assert result["provider"] == "stripe"
        assert result["status"] == "created"

    def test_verify_transaction(self):
        gateway = StripeGateway()
        result = gateway.verify_transaction("txn_123")
        assert result["confirmed"] is True

    def test_release_funds(self):
        gateway = StripeGateway()
        result = gateway.release_funds("txn_123", 100.0, "USD")
        assert result["status"] == "released"

    def test_refund_funds(self):
        gateway = StripeGateway()
        result = gateway.refund_funds("txn_123", 100.0, "USD", "Customer request")
        assert result["status"] == "refunded"


class TestPayPalGateway:
    """PayPal Gateway 测试."""

    def test_create_transaction(self):
        gateway = PayPalGateway()
        result = gateway.create_transaction(100.0, "USD")
        assert result["provider"] == "paypal"
        assert result["status"] == "created"

    def test_verify_transaction(self):
        gateway = PayPalGateway()
        result = gateway.verify_transaction("txn_123")
        assert result["confirmed"] is True

    def test_release_funds(self):
        gateway = PayPalGateway()
        result = gateway.release_funds("txn_123", 100.0, "USD")
        assert result["status"] == "released"

    def test_refund_funds(self):
        gateway = PayPalGateway()
        result = gateway.refund_funds("txn_123", 100.0, "USD", "Refund")
        assert result["status"] == "refunded"


class TestWorldFirstGateway:
    """WorldFirst Gateway 测试."""

    def test_create_transaction(self):
        gateway = WorldFirstGateway()
        result = gateway.create_transaction(100.0, "USD")
        assert result["provider"] == "worldfirst"
        assert result["status"] == "created"

    def test_verify_transaction(self):
        gateway = WorldFirstGateway()
        result = gateway.verify_transaction("txn_123")
        assert result["confirmed"] is True

    def test_release_funds(self):
        gateway = WorldFirstGateway()
        result = gateway.release_funds("txn_123", 100.0, "USD")
        assert result["status"] == "released"

    def test_refund_funds(self):
        gateway = WorldFirstGateway()
        result = gateway.refund_funds("txn_123", 100.0, "USD", "Refund")
        assert result["status"] == "refunded"
