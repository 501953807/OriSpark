"""Settlement Router HTTP-level integration tests."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

import pytest


_BASE = "/api"


class TestCalculateTax:
    """POST /settlement/calculate-tax"""

    def test_calculate_tax(self, client):
        resp = client.post(f"{_BASE}/settlement/calculate-tax", json={
            "seller_location": {"country": "CN"},
            "buyer_location": {"country": "US"},
            "product_type": "digital",
            "amount": 1000.0,
            "currency": "USD",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "data" in data
        assert "message" in data

    def test_calculate_tax_minimal(self, client):
        resp = client.post(f"{_BASE}/settlement/calculate-tax", json={
            "amount": 100.0,
            "product_type": "physical",
            "seller_location": {"country": "CN"},
            "buyer_location": {"country": "US"},
        })
        assert resp.status_code in (200, 422)


class TestListCalculations:
    """GET /settlement/calculations"""

    def test_list_calculations_empty(self, client):
        resp = client.get(f"{_BASE}/settlement/calculations")
        assert resp.status_code == 200
        data = resp.json()
        assert "data" in data

    def test_list_calculations_filter(self, client):
        resp = client.get(f"{_BASE}/settlement/calculations", params={
            "product_type": "digital",
        })
        assert resp.status_code == 200


class TestConvertCurrency:
    """POST /settlement/convert-currency"""

    def test_convert_currency(self, client):
        resp = client.post(f"{_BASE}/settlement/convert-currency", json={
            "source_currency": "USD",
            "target_currency": "CNY",
            "amount": 100.0,
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "data" in data