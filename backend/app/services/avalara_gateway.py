"""Avalara 税务计算 Gateway ABC 模式."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from decimal import Decimal
from typing import Optional


@dataclass
class TaxCalculationResult:
    tax_amount: float
    tax_rate: float
    tax_jurisdiction: str
    exemption_status: str


class GatewayABC(ABC):
    """外部 API 抽象基类."""

    @property
    @abstractmethod
    def _is_configured(self) -> bool:
        ...

    @abstractmethod
    async def calculate_tax(
        self,
        seller_location: dict[str, str],
        buyer_location: dict[str, str],
        product_type: str,
        amount: float,
        currency: str = "CNY",
    ) -> TaxCalculationResult:
        ...


class MockAvalaraGateway(GatewayABC):
    """Mock 实现 — 开发/测试环境使用."""

    @property
    def _is_configured(self) -> bool:
        return True

    async def calculate_tax(
        self,
        seller_location: dict[str, str],
        buyer_location: dict[str, str],
        product_type: str,
        amount: float,
        currency: str = "CNY",
    ) -> TaxCalculationResult:
        rates: dict[str, float] = {"digital": 0.0, "physical": 0.07, "license": 0.10}
        rate = rates.get(product_type, 0.0)
        tax = round(amount * rate, 2)
        country = buyer_location.get("country", "CN")
        return TaxCalculationResult(
            tax_amount=tax,
            tax_rate=rate,
            tax_jurisdiction=f"{country} Local",
            exemption_status="none",
        )


class AvalaraGateway(GatewayABC):
    """真实 Avalara API 实现 — 需要 API key."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or ""

    @property
    def _is_configured(self) -> bool:
        return bool(self.api_key)

    async def calculate_tax(
        self,
        seller_location: dict[str, str],
        buyer_location: dict[str, str],
        product_type: str,
        amount: float,
        currency: str = "CNY",
    ) -> TaxCalculationResult:
        if not self._is_configured:
            mock = MockAvalaraGateway()
            return await mock.calculate_tax(seller_location, buyer_location, product_type, amount, currency)
        # TODO: 实际调用 Avalara API
        ...
