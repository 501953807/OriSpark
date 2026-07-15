import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

import pytest
from app.services.ip_commercialization_service import (
    calculate_ip_score,
    estimate_brand_premium,
    recommend_trademark_classes,
)


def test_calculate_ip_score():
    # All max → 100
    assert calculate_ip_score(100, 100, 0, 100) == 100.0
    # All avg → 50.0 (50×0.3 + 50×0.3 + 50×0.2 + 50×0.2)
    assert calculate_ip_score(50, 50, 50, 50) == 50.0
    # All min → 0
    assert calculate_ip_score(0, 0, 100, 0) == 0.0


def test_estimate_brand_premium_low():
    # 100 followers, 0.5% engagement → base 15%
    assert estimate_brand_premium(100, 0.5, "illustrator") == 15.0


def test_estimate_brand_premium_high():
    # 200k followers, 8% engagement → base 15 + 10 + 10 = 35%
    assert estimate_brand_premium(200000, 8.0, "illustrator") == 35.0


def test_estimate_brand_premium_cap():
    # Max out at 40% — game_developer has no special bonus, so 15+10+10=35
    assert estimate_brand_premium(500000, 10.0, "game_developer") == 35.0


def test_recommend_trademark_illustrator():
    result = recommend_trademark_classes("illustrator")
    assert len(result) == 3
    assert "第9类" in result[0]


def test_recommend_trademark_unknown():
    # Unknown type → default classes
    result = recommend_trademark_classes("astronaut")
    assert result == ["第9类", "第16类"]
