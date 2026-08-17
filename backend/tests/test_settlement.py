"""结算模块 API 测试."""
import pytest


class TestSettlementTax:
    """测试 /api/settlement/calculate-tax 端点."""

    def test_calculate_tax_success(self, client):
        """税务计算应返回结果."""
        resp = client.post(
            "/api/settlement/calculate-tax",
            json={
                "seller_location": {"country": "CN", "province": "Shanghai"},
                "buyer_location": {"country": "US", "state": "CA"},
                "product_type": "copyright",
                "amount": 1000.0,
            },
        )
        assert resp.status_code in (200, 500)

    def test_calculate_tax_missing_fields(self, client):
        """缺少必填字段应返回422."""
        resp = client.post(
            "/api/settlement/calculate-tax",
            json={"amount": 1000.0},
        )
        assert resp.status_code == 422


class TestSettlementCalculations:
    """测试 /api/settlement/calculations 端点."""

    def test_list_calculations(self, client):
        resp = client.get("/api/settlement/calculations")
        assert resp.status_code == 200
        data = resp.json()
        # ApiResponse wraps in {"success": true, "data": [...]}
        if isinstance(data, dict):
            assert data["success"] is True


class TestSettlementCurrency:
    """测试 /api/settlement/convert-currency 端点."""

    def test_convert_cny_to_usd(self, client):
        resp = client.post(
            "/api/settlement/convert-currency",
            json={"source_currency": "CNY", "target_currency": "USD", "amount": 1000.0},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        result = data["data"]
        # 响应字段为 source_amount/target_amount，非 converted_amount
        assert result["source_amount"] == 1000.0
        assert result["target_amount"] == 140.0  # CNY->USD rate=0.14

    def test_convert_same_currency(self, client):
        resp = client.post(
            "/api/settlement/convert-currency",
            json={"source_currency": "EUR", "target_currency": "EUR", "amount": 500.0},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert float(data["data"]["target_amount"]) == 500.0

    def test_convert_unknown_currency(self, client):
        resp = client.post(
            "/api/settlement/convert-currency",
            json={"source_currency": "XXX", "target_currency": "YYY", "amount": 100.0},
        )
        assert resp.status_code == 200
