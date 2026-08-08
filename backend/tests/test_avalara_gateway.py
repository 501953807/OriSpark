"""Avalara Gateway 测试."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import pytest
from app.services.avalara_gateway import (
    TaxCalculationResult,
    GatewayABC,
    MockAvalaraGateway,
    AvalaraGateway,
    get_avalara_gateway,
)


class TestMockAvalaraGateway:
    """Mock Gateway 测试."""

    @pytest.mark.asyncio
    async def test_calculate_tax_digital(self):
        """数字产品税率为 0."""
        g = MockAvalaraGateway()
        result = await g.calculate_tax(
            {"country": "US", "state": "CA"},
            {"country": "US", "state": "NY"},
            "digital",
            100.0,
        )
        assert result.tax_amount == 0.0
        assert result.tax_rate == 0.0
        assert result.tax_jurisdiction == "US Local"
        assert result.exemption_status == "none"

    @pytest.mark.asyncio
    async def test_calculate_tax_physical(self):
        """实体产品税率为 7%."""
        g = MockAvalaraGateway()
        result = await g.calculate_tax(
            {"country": "US"},
            {"country": "CN"},
            "physical",
            200.0,
        )
        assert result.tax_amount == 14.0
        assert result.tax_rate == 0.07
        assert result.tax_jurisdiction == "CN Local"

    @pytest.mark.asyncio
    async def test_calculate_tax_license(self):
        """授权产品税率为 10%."""
        g = MockAvalaraGateway()
        result = await g.calculate_tax(
            {"country": "US"},
            {"country": "JP"},
            "license",
            500.0,
        )
        assert result.tax_amount == 50.0
        assert result.tax_rate == 0.10

    @pytest.mark.asyncio
    async def test_calculate_tax_unknown_type(self):
        """未知产品类型税率为 0."""
        g = MockAvalaraGateway()
        result = await g.calculate_tax(
            {"country": "US"},
            {"country": "DE"},
            "unknown",
            100.0,
        )
        assert result.tax_amount == 0.0
        assert result.tax_rate == 0.0

    @pytest.mark.asyncio
    async def test_is_configured(self):
        """Mock Gateway 始终配置."""
        g = MockAvalaraGateway()
        assert g._is_configured is True


class TestAvalaraGateway:
    """真实 Avalara Gateway 测试."""

    @pytest.mark.asyncio
    async def test_unconfigured_uses_mock(self):
        """未配置时使用 Mock 返回值."""
        g = AvalaraGateway(api_key="")
        assert g._is_configured is False
        result = await g.calculate_tax(
            {"country": "US"},
            {"country": "CN"},
            "physical",
            100.0,
        )
        assert result.tax_amount == 7.0
        assert result.tax_rate == 0.07

    @pytest.mark.asyncio
    async def test_configured_with_key(self):
        """配置 API key 后可用."""
        g = AvalaraGateway(api_key="test-key")
        assert g._is_configured is True
        assert g.api_key == "test-key"


class TestGetAvalaraGateway:
    """工厂函数测试."""

    @pytest.mark.asyncio
    async def test_returns_mock_when_no_key(self, monkeypatch):
        """未配置环境变量时返回 Mock."""
        monkeypatch.delenv("AVALARA_LICENSE_KEY", raising=False)
        g = get_avalara_gateway()
        assert isinstance(g, MockAvalaraGateway)

    @pytest.mark.asyncio
    async def test_returns_real_when_key_set(self, monkeypatch):
        """配置环境变量时返回真实 Gateway."""
        monkeypatch.setenv("AVALARA_LICENSE_KEY", "test-key")
        g = get_avalara_gateway()
        assert isinstance(g, AvalaraGateway)
        monkeypatch.delenv("AVALARA_LICENSE_KEY", raising=False)
