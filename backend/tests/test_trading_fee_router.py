"""Trading Fee Router HTTP-level integration tests — covers all 5 endpoints."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

import pytest


_BASE = "/api/trading-fees"


class TestCalculateFee:
    """POST /trading-fees/calculate"""

    def test_tier1_small_amount(self, client):
        """Schema default credit_score=0 → no discount. 200 bps = 2.0%."""
        resp = client.post(f"{_BASE}/calculate", json={
            "amount_yuan": 5000.0,
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["tier"] == "tier_1"
        assert data["fee_rate_percent"] == 2.0
        assert data["fee_amount_yuan"] == 100.0
        assert data["is_discounted"] is False

    def test_tier2_medium_amount(self, client):
        resp = client.post(f"{_BASE}/calculate", json={
            "amount_yuan": 50000.0,
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["tier"] == "tier_2"
        assert data["fee_rate_percent"] == 1.5

    def test_tier3_large_amount(self, client):
        resp = client.post(f"{_BASE}/calculate", json={
            "amount_yuan": 200000.0,
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["tier"] == "tier_3"
        assert data["fee_rate_percent"] == 1.0

    def test_tier4_huge_amount(self, client):
        resp = client.post(f"{_BASE}/calculate", json={
            "amount_yuan": 1000000.0,
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["tier"] == "tier_4"
        assert data["fee_rate_percent"] == 0.5

    def test_credit_discount(self, client):
        resp = client.post(f"{_BASE}/calculate", json={
            "amount_yuan": 5000.0,
            "credit_score": 100,
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["is_discounted"] is True
        assert data["discount_reason"] == "credit"
        # 200 - min(100*0.5, 20) = 200 - 20 = 180 bps = 1.8%
        assert data["fee_rate_percent"] == 1.8

    def test_no_credit_discount(self, client):
        resp = client.post(f"{_BASE}/calculate", json={
            "amount_yuan": 5000.0,
            "credit_score": 0,
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["fee_rate_percent"] == 2.0

    def test_volume_discount(self, client):
        resp = client.post(f"{_BASE}/calculate", json={
            "amount_yuan": 5000.0,
            "monthly_volume_yuan": 50000.0,
            "credit_score": 0,
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["is_discounted"] is True
        assert data["discount_reason"] == "volume"
        # 200 - 5 = 195 bps = 1.95%
        assert data["fee_rate_percent"] == 1.95

    def test_combined_discounts(self, client):
        resp = client.post(f"{_BASE}/calculate", json={
            "amount_yuan": 5000.0,
            "monthly_volume_yuan": 500000.0,
            "credit_score": 100,
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["is_discounted"] is True
        assert data["discount_reason"] == "volume,credit"
        # 200 - 20(vol) - 20(credit) = 160 bps = 1.6%
        assert data["fee_rate_percent"] == 1.6


class TestRecordTransaction:
    """POST /trading-fees/record"""

    def test_record_with_transaction_id(self, client):
        resp = client.post(
            f"{_BASE}/record?transaction_id=test_txn_001",
            json={"amount_yuan": 10001.0},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["transaction_id"] == "test_txn_001"
        assert data["tier"] == "tier_2"

    def test_record_generates_id(self, client):
        resp = client.post(
            _BASE + "/record",
            json={"amount_yuan": 1000.0},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "id" in data
        assert "transaction_id" in data


class TestEstimator:
    """GET /trading-fees/estimator"""

    def test_estimator_basic(self, client):
        resp = client.get(f"{_BASE}/estimator", params={
            "amount_yuan": 5000.0,
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "amount_yuan" in data
        assert "fee_yuan" in data
        assert "rate_percent" in data
        assert "tier" in data
        assert "is_discounted" in data

    def test_estimator_with_credit(self, client):
        resp = client.get(f"{_BASE}/estimator", params={
            "amount_yuan": 5000.0,
            "credit_score": 80,
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["is_discounted"] is True


class TestFeeConfig:
    """GET/PUT /trading-fees/config*"""

    def test_get_fee_config(self, client):
        resp = client.get(f"{_BASE}/config")
        assert resp.status_code == 200
        data = resp.json()
        assert data["base_rate_bps"] == 300
        assert data["vip_threshold"] == 10000

    def test_update_fee_config(self, client):
        resp = client.put(f"{_BASE}/config/vip_001", json={
            "base_rate_bps": 250,
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["updated"] is True
        assert data["config_id"] == "vip_001"
