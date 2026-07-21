import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

import pytest
from app.services.listing_service import calculate_profit


def test_calculate_profit_standard():
    # ¥1000, 2% fee, 70% split → platform ¥20, creator ¥686, net ¥686
    result = calculate_profit(1000, 200, 70)
    assert result["platform_fee_yuan"] == 20.0
    assert result["creator_earning_yuan"] == 686.0
    assert result["net_profit_yuan"] == 686.0


def test_calculate_profit_high_tier():
    # ¥100,000, 0.5% fee, 70% split → platform ¥500, creator ¥99,500×70%=¥69,650
    result = calculate_profit(100000, 50, 70)
    assert result["platform_fee_yuan"] == 500.0
    assert result["creator_earning_yuan"] == 69650.0


def test_calculate_profit_zero():
    result = calculate_profit(0, 200, 70)
    assert result["platform_fee_yuan"] == 0.0
    assert result["creator_earning_yuan"] == 0.0


def test_calculate_profit_custom_split():
    # ¥500, 2% fee, 80% split → platform ¥10, creator ¥490×80%=¥392
    result = calculate_profit(500, 200, 80)
    assert result["platform_fee_yuan"] == 10.0
    assert result["creator_earning_yuan"] == 392.0
