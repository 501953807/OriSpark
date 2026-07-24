"""税务代理与结算后端测试."""

import pytest
from decimal import Decimal
from sqlalchemy.orm import Session

from app.models.tax_settlement import TaxAgent, TaxReport
from app.models.settlement import TaxCalculation, MultiCurrencySettlement
from app.services.settlement_service import (
    calculate_tax, convert_currency, generate_tax_report,
)


@pytest.fixture
def tax_agent(db_session: Session) -> TaxAgent:
    agent = TaxAgent(
        participant_id="test-participant-001",
        name="Test Tax Agent",
        license_no="TA-2024-001",
        service_areas=["US", "CN"],
        fee_rate=Decimal("0.05"),
        avalara_account_id="avalara-123",
        status="active",
    )
    db_session.add(agent)
    db_session.commit()
    db_session.refresh(agent)
    return agent


@pytest.fixture
def tax_report(db_session: Session, tax_agent: TaxAgent) -> TaxReport:
    report = TaxReport(
        participant_id="test-participant-001",
        agent_id=tax_agent.id,
        report_period="2024-07",
        total_income=Decimal("10000.00"),
        total_tax_withheld=Decimal("700.00"),
        total_tax_owed=Decimal("300.00"),
        currency="CNY",
        status="draft",
    )
    db_session.add(report)
    db_session.commit()
    db_session.refresh(report)
    return report


class TestTaxAgentModel:
    def test_create_tax_agent(self, tax_agent: TaxAgent):
        assert tax_agent.id is not None
        assert tax_agent.name == "Test Tax Agent"
        assert tax_agent.status == "active"
        assert tax_agent.fee_rate == Decimal("0.05")
        assert tax_agent.service_areas == ["US", "CN"]

    def test_update_agent_status(self, db_session: Session, tax_agent: TaxAgent):
        tax_agent.status = "suspended"
        db_session.commit()
        refreshed = db_session.query(TaxAgent).filter(TaxAgent.id == tax_agent.id).first()
        assert refreshed.status == "suspended"


class TestTaxReportModel:
    def test_create_tax_report(self, tax_report: TaxReport):
        assert tax_report.id is not None
        assert tax_report.report_period == "2024-07"
        assert tax_report.total_income == Decimal("10000.00")
        assert tax_report.status == "draft"

    def test_finalize_report(self, db_session: Session, tax_report: TaxReport):
        tax_report.status = "final"
        db_session.commit()
        refreshed = db_session.query(TaxReport).filter(TaxReport.id == tax_report.id).first()
        assert refreshed.status == "final"


class TestTaxCalculationModel:
    def test_create_tax_calculation(self, db_session: Session):
        calc = TaxCalculation(
            contract_id="contract-001",
            seller_location={"country": "US", "state": "CA"},
            buyer_location={"country": "CN", "province": "GD"},
            product_type="digital",
            amount=Decimal("100.00"),
            currency="USD",
            tax_amount=Decimal("0.00"),
            tax_rate=Decimal("0.0"),
            calculated_by="avalara",
        )
        db_session.add(calc)
        db_session.commit()
        db_session.refresh(calc)
        assert calc.id is not None
        assert calc.product_type == "digital"


class TestMultiCurrencySettlement:
    def test_create_settlement(self, db_session: Session):
        mcs = MultiCurrencySettlement(
            contract_id="contract-001",
            participant_id="participant-001",
            source_currency="CNY",
            source_amount=Decimal("1000.00"),
            target_currency="USD",
            target_amount=Decimal("140.00"),
            exchange_rate=Decimal("0.14"),
            status="settled",
        )
        db_session.add(mcs)
        db_session.commit()
        db_session.refresh(mcs)
        assert mcs.id is not None
        assert mcs.source_currency == "CNY"
        assert mcs.target_currency == "USD"


class TestConvertCurrency:
    @pytest.mark.asyncio
    async def test_cny_to_usd(self):
        source, target = await convert_currency(None, "CNY", "USD", 100.0)
        assert target == 14.0

    @pytest.mark.asyncio
    async def test_usd_to_cny(self):
        source, target = await convert_currency(None, "USD", "CNY", 100.0)
        assert target == 714.0

    @pytest.mark.asyncio
    async def test_same_currency(self):
        source, target = await convert_currency(None, "CNY", "CNY", 100.0)
        assert target == 100.0

    @pytest.mark.asyncio
    async def test_unknown_currency_fallback(self):
        source, target = await convert_currency(None, "CNY", "XYZ", 100.0)
        assert target == 100.0  # rate = 1.0 fallback


class TestGenerateTaxReport:
    def test_generate_draft_report(self, db_session: Session):
        report = generate_tax_report(db_session, "participant-001", "2024-08", "CNY")
        assert report.participant_id == "participant-001"
        assert report.report_period == "2024-08"
        assert report.currency == "CNY"
        assert report.status == "draft"
        assert report.id is not None

    def test_report_persisted_in_db(self, db_session: Session):
        generate_tax_report(db_session, "participant-001", "2024-09", "USD")
        count = db_session.query(TaxReport).filter(
            TaxReport.participant_id == "participant-001"
        ).count()
        assert count >= 1
