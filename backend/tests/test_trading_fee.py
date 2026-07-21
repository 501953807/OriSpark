import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

import pytest
from app.services.trading_fee_service import calculate_fee


def test_base_fee_tier_1():
    # ¥5,000 → tier_1, 2% = ¥100 (no discounts)
    result = calculate_fee(5000, monthly_volume_yuan=0, credit_score=0)
    assert result["tier"] == "tier_1"
    assert result["rate_bps"] == 200
    assert result["fee_amount_yuan"] == 100.0
    assert result["is_discounted"] is False


def test_base_fee_tier_2():
    # ¥50,000 → tier_2, 1.5% = ¥750
    result = calculate_fee(50000, monthly_volume_yuan=0, credit_score=0)
    assert result["tier"] == "tier_2"
    assert result["rate_bps"] == 150
    assert result["fee_amount_yuan"] == 750.0


def test_base_fee_tier_3():
    # ¥200,000 → tier_3, 1% = ¥2,000
    result = calculate_fee(200000, monthly_volume_yuan=0, credit_score=0)
    assert result["tier"] == "tier_3"
    assert result["rate_bps"] == 100
    assert result["fee_amount_yuan"] == 2000.0


def test_base_fee_tier_4():
    # ¥1,000,000 → tier_4, 0.5% = ¥5,000
    result = calculate_fee(1000000, monthly_volume_yuan=0, credit_score=0)
    assert result["tier"] == "tier_4"
    assert result["rate_bps"] == 50
    assert result["fee_amount_yuan"] == 5000.0


def test_volume_discount():
    # ¥50K + ¥200K monthly volume → tier_2 (150 bps) + vol (-10 bps) = 140 bps
    result = calculate_fee(50000, monthly_volume_yuan=200000, credit_score=0)
    assert result["rate_bps"] == 140
    assert result["is_discounted"] is True
    assert "volume" in result["discount_reason"]


def test_credit_discount():
    # ¥50K + credit 80 → tier_2 (150 bps) - credit(80×0.5=40, capped 20) = 130 bps
    result = calculate_fee(50000, monthly_volume_yuan=0, credit_score=80)
    assert result["rate_bps"] == 130
    assert result["is_discounted"] is True
    assert "credit" in result["discount_reason"]


def test_combined_discount():
    # ¥5K + vol 50K + credit 60
    # tier_1 (200 bps) + vol(-5) + credit(60×0.5=30→capped 20) = 175 bps
    result = calculate_fee(5000, monthly_volume_yuan=50000, credit_score=60)
    assert result["rate_bps"] == 175
    assert result["is_discounted"] is True
    assert "volume" in result["discount_reason"]
    assert "credit" in result["discount_reason"]


def test_zero_amount():
    result = calculate_fee(0)
    assert result["fee_amount_yuan"] == 0.0
