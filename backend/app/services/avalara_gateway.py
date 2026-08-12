"""Avalara 税务计算 Gateway ABC 模式."""

import logging
import os
from abc import ABC, abstractmethod
from dataclasses import dataclass
from decimal import Decimal
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class TaxCalculationResult:
    tax_amount: float
    tax_rate: float
    tax_jurisdiction: str
    exemption_status: str


class AvalaraTaxGateway(ABC):
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


class MockAvalaraGateway(AvalaraTaxGateway):
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


class RealAvalaraGateway(AvalaraTaxGateway):
    """真实 Avalara API 实现 — 需要 API key."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.environ.get("AVALARA_LICENSE_KEY", "")

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
            return await mock.calculate_tax(
                seller_location, buyer_location, product_type, amount, currency
            )

        try:
            import httpx
            from datetime import datetime, timezone

            url = "https://api.avalara.com/v2/tax/compute"
            headers = {
                "Authorization": f"Basic {self.api_key}",
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

            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(url, json=payload, headers=headers)
                response.raise_for_status()

                result = response.json()
                return TaxCalculationResult(
                    tax_amount=float(result.get("taxAmount", amount * 0.07)),
                    tax_rate=float(result.get("taxRate", 0.07)),
                    tax_jurisdiction=result.get(
                        "jurisdiction",
                        f"{buyer_location.get('country', 'Unknown')} Local",
                    ),
                    exemption_status=result.get("exemptionStatus", "none"),
                )
        except httpx.RequestError as e:
            logger.warning(f"Avalara API request failed, using mock: {e}")
            mock = RealAvalaraGateway()
            return await mock.calculate_tax(
                seller_location, buyer_location, product_type, amount, currency
            )
        except Exception as e:
            logger.error(f"Avalara API error: {e}")
            mock = RealAvalaraGateway()
            return await mock.calculate_tax(
                seller_location, buyer_location, product_type, amount, currency
            )


def get_avalara_gateway() -> AvalaraTaxGateway:
    """根据环境变量选择 Avalara 网关实现.

    生产环境: 配置 AVALARA_LICENSE_KEY 使用真实 API
    开发/测试: 未配置时使用 Mock 实现
    """
    if os.environ.get("AVALARA_LICENSE_KEY"):
        return RealAvalaraGateway()
    return MockAvalaraGateway()
