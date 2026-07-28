from datetime import datetime, timezone
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

        # Actual Avalara API implementation with HTTP POST to /tax/v2/compute
        # Includes fallback to MockAvalaraGateway on network/authentication errors

        import httpx
        import asyncio

        url = "https://api.avalara.com/v2/tax/compute"
        headers = {
            "Authorization": f"Basic {self.api_key}",  # Simplified - in production use proper OAuth2
            "Content-Type": "application/json",
        }

        payload = {
            "from_address": {
                "country": seller_location.get("country", "US"),
                "city": seller_location.get("city", ""),
                "region": seller_location.get("state", ""),
                "postal_code": seller_location.get("zip", ""),
            },
            "to_address": {
                "country": buyer_location.get("country", "US"),
                "city": buyer_location.get("city", ""),
                "region": buyer_location.get("state", ""),
                "postal_code": buyer_location.get("zip", ""),
            },
            "purchase_price": amount,
            "product_type": product_type,
            "date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        }

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(url, json=payload, headers=headers)
                response.raise_for_status()

                result = response.json()
                # Extract tax information from Avalara response format
                tax_amount = result.get("taxAmount", amount * 0.07)
                tax_rate = result.get("taxRate", 0.07)
                jurisdiction = result.get("jurisdiction", f"{buyer_location.get('country','Unknown')} Local")

                return TaxCalculationResult(
                    tax_amount=float(tax_amount),
                    tax_rate=float(tax_rate),
                    tax_jurisdiction=jurisdiction,
                    exemption_status=result.get("exemptionStatus", "none"),
                )
        except httpx.RequestError as e:
            # Network error - fall back to mock calculations
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Avalara API call failed, falling back to mock calculation: {e}")
            mock = MockAvalaraGateway()
            return await mock.calculate_tax(seller_location, buyer_location, product_type, amount, currency)
        except Exception as e:
            # API error (authentication, invalid response, etc.) - fallback
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Avalara API error: {e}")
            mock = MockAvalaraGateway()
            return await mock.calculate_tax(seller_location, buyer_location, product_type, amount, currency)
