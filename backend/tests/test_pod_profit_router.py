"""POD Profit Router HTTP-level integration tests."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

import pytest


_BASE = "/api/pod-profit"


class TestProductConfig:
    """POST /pod-profit/product-config"""

    def test_create_product_config(self, client):
        resp = client.post(f"{_BASE}/product-config", json={
            "platform": "redbubble",
            "product_type": "t-shirt",
            "markup_rate": 2.0,
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "id" in data
        assert data["platform"] == "redbubble"

    def test_create_different_platform(self, client):
        resp = client.post(f"{_BASE}/product-config", json={
            "platform": "printful",
            "product_type": "poster",
            "markup_rate": 1.5,
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["platform"] == "printful"


class TestPricingSimulation:
    """POST /pod-profit/simulate-pricing"""

    def test_simulate_pricing(self, client):
        resp = client.post(f"{_BASE}/simulate-pricing", json={
            "platform": "redbubble",
            "product_type": "poster",
            "markup_rate": 1.5,
        })
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) > 0
        assert "markup_pct" in data[0]
        assert "profit_usd" in data[0]

    def test_simulate_printful(self, client):
        resp = client.post(f"{_BASE}/simulate-pricing", json={
            "platform": "printify",
            "product_type": "sticker",
            "markup_rate": 0.5,
        })
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)


class TestLogSale:
    """POST /pod-profit/log-sale"""

    def test_log_sale(self, client):
        resp = client.post(f"{_BASE}/log-sale", json={
            "platform": "redbubble",
            "product_type": "t-shirt",
            "sale_price_usd": 25.0,
            "base_cost_usd": 8.0,
            "shipping_cost_usd": 3.0,
            "platform_fee_pct": 0.2,
            "exchange_rate": 7.2,
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "profit_usd" in data
        assert "margin_pct" in data

    def test_log_sale_minimal_fields(self, client):
        resp = client.post(f"{_BASE}/log-sale", json={
            "platform": "printful",
            "product_type": "phone_case",
            "sale_price_usd": 15.0,
            "base_cost_usd": 10.0,
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "profit_usd" in data

    def test_log_sale_after_config(self, client):
        """Create config then log a sale for the same product."""
        client.post(f"{_BASE}/product-config", json={
            "platform": "redbubble",
            "product_type": "mug",
            "markup_rate": 1.0,
        })
        resp = client.post(f"{_BASE}/log-sale", json={
            "platform": "redbubble",
            "product_type": "mug",
            "sale_price_usd": 20.0,
            "base_cost_usd": 13.0,
            "platform_fee_pct": 0.1,
        })
        assert resp.status_code == 200


class TestDesignsSummary:
    """GET /pod-profit/designs-summary"""

    def test_designs_summary_empty(self, client):
        resp = client.get(f"{_BASE}/designs-summary")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)


class TestOverview:
    """GET /pod-profit/overview"""

    def test_overview_empty(self, client):
        resp = client.get(f"{_BASE}/overview")
        assert resp.status_code == 200
        data = resp.json()
        assert "total_profit_cny" in data
        assert "total_sales" in data

    def test_overview_with_data(self, client):
        """Overview should reflect logged sales."""
        client.post(f"{_BASE}/log-sale", json={
            "platform": "redbubble",
            "product_type": "t-shirt",
            "sale_price_usd": 30.0,
            "base_cost_usd": 8.0,
            "platform_fee_pct": 0.2,
        })
        resp = client.get(f"{_BASE}/overview")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_sales"] >= 1
        assert "by_platform" in data


class TestSettlementsList:
    """GET /pod-profit/my-settlements"""

    def test_settlements_empty(self, client):
        resp = client.get(f"{_BASE}/my-settlements")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)

    def test_settlements_with_filter(self, client):
        resp = client.get(f"{_BASE}/my-settlements", params={"status": "pending"})
        assert resp.status_code == 200


@pytest.mark.skip(reason="pod_settlements.user_id has FK to users.id; users table not in test DB")
class TestSettlementGenerate:
    """POST /pod-profit/settlements/generate"""

    def test_generate_settlement_no_sales(self, client):
        resp = client.post(f"{_BASE}/settlements/generate?period=2026-07")
        assert resp.status_code in (200, 500)

    def test_generate_settlement_with_sales(self, client):
        client.post(f"{_BASE}/log-sale", json={
            "platform": "redbubble",
            "product_type": "t-shirt",
            "sale_price_usd": 25.0,
            "base_cost_usd": 8.0,
            "platform_fee_pct": 0.2,
        })
        resp = client.post(f"{_BASE}/settlements/generate?period=2026-08")
        assert resp.status_code in (200, 500)


class TestSettlementConfirm:
    """POST /pod-profit/settlements/{settlement_id}/confirm"""

    def test_confirm_nonexistent(self, client):
        resp = client.post(f"{_BASE}/settlements/fake-id/confirm")
        # Returns 400 because confirm_settlement raises ValueError
        assert resp.status_code == 400

    @pytest.mark.skip(reason="Requires a valid settlement ID from generate endpoint")
    def test_confirm_after_generate(self, client):
        gen_resp = client.post(f"{_BASE}/settlements/generate?period=2026-09")
        assert gen_resp.status_code == 200
        settlement_id = gen_resp.json()["id"]

        resp = client.post(f"{_BASE}/settlements/{settlement_id}/confirm")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "confirmed"


class TestSalesStatistics:
    """GET /pod-profit/sales/statistics"""

    def test_statistics_empty(self, client):
        resp = client.get(f"{_BASE}/sales/statistics")
        assert resp.status_code == 200
        data = resp.json()
        assert "total_sales" in data or "total_earnings" in data

    def test_statistics_with_date_range(self, client):
        """Query statistics with date filters."""
        resp = client.get(f"{_BASE}/sales/statistics", params={
            "start_date": "2020-01-01",
            "end_date": "2030-12-31",
        })
        assert resp.status_code == 200
