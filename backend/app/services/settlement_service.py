"""结算业务逻辑."""

from decimal import Decimal
from typing import Optional

from sqlalchemy.orm import Session

from app.models.settlement import TaxCalculation, MultiCurrencySettlement
from app.models.tax_settlement import TaxReport
from app.services.avalara_gateway import MockAvalaraGateway, TaxCalculationResult


async def calculate_tax(
    db: Session,
    seller_location: dict[str, str],
    buyer_location: dict[str, str],
    product_type: str,
    amount: float,
    currency: str = "CNY",
    contract_id: Optional[str] = None,
    transaction_id: Optional[str] = None,
) -> TaxCalculation:
    """执行税务计算并持久化结果."""
    gateway = MockAvalaraGateway()
    result: TaxCalculationResult = await gateway.calculate_tax(
        seller_location, buyer_location, product_type, amount, currency,
    )

    calc = TaxCalculation(
        contract_id=contract_id,
        transaction_id=transaction_id,
        seller_location=seller_location,
        buyer_location=buyer_location,
        product_type=product_type,
        amount=Decimal(str(amount)),
        currency=currency,
        tax_amount=Decimal(str(result.tax_amount)),
        tax_rate=Decimal(str(result.tax_rate)),
        tax_jurisdiction=result.tax_jurisdiction,
        exemption_status=result.exemption_status,
        calculated_by="avalara",
    )
    db.add(calc)
    db.flush()
    return calc


async def convert_currency(
    db: Session,
    source_currency: str,
    target_currency: str,
    amount: float,
    exchange_source: Optional[str] = None,
) -> tuple[float, float]:
    """模拟汇率转换 (实际应接入 Stripe/ECB API)."""
    rates: dict[str, dict[str, float]] = {
        "CNY": {"USD": 0.14, "EUR": 0.13, "GBP": 0.11, "JPY": 21.0},
        "USD": {"CNY": 7.14, "EUR": 0.93, "GBP": 0.79, "JPY": 150.0},
        "EUR": {"CNY": 7.69, "USD": 1.08, "GBP": 0.85, "JPY": 161.0},
    }
    row = rates.get(source_currency)
    if not row or target_currency not in row:
        rate = 1.0  # same currency or unknown
    else:
        rate = row[target_currency]

    converted = round(amount * rate, 2)
    return amount, converted


def generate_tax_report(
    db: Session,
    participant_id: str,
    period: str,
    currency: str = "CNY",
) -> TaxReport:
    """生成月度/季度税务报告."""
    report = TaxReport(
        participant_id=participant_id,
        report_period=period,
        total_income=Decimal("0"),
        total_tax_withheld=Decimal("0"),
        total_tax_owed=Decimal("0"),
        currency=currency,
        status="draft",
    )
    db.add(report)
    db.flush()
    return report
