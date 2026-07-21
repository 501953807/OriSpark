"""Tests for Multi-Market Expansion service."""

import pytest
from unittest.mock import MagicMock

from app.services.multi_market_service import (
    calculate_geo_arbitrage,
    get_expansion_phases,
    get_all_markets,
)


class TestCalculateGeoArbitrage:
    """Test geographic arbitrage calculator."""

    def test_single_cn_only(self):
        result = calculate_geo_arbitrage(["cn"], 5000, "illustrator")
        assert result["current_total_monthly"] == 5000
        assert result["total_projected_monthly"] >= 5000
        assert result["increase_percent"] >= 0

    def test_us_addition_increases_revenue(self):
        r1 = calculate_geo_arbitrage(["cn"], 5000, "illustrator")
        r2 = calculate_geo_arbitrage(["cn", "us"], 5000, "illustrator")
        assert r2["total_projected_monthly"] > r1["total_projected_monthly"]

    def test_three_markets_higher_gain(self):
        r3 = calculate_geo_arbitrage(["cn", "us", "eu"], 5000, "illustrator")
        assert r3["increase_percent"] > 100  # At least 100% increase

    def test_recommended_markets_not_empty(self):
        result = calculate_geo_arbitrage(["cn"], 5000)
        assert len(result["recommended_markets"]) > 0
        assert "cn" not in result["recommended_markets"]

    def test_zero_revenue(self):
        result = calculate_geo_arbitrage(["cn"], 0, "illustrator")
        assert result["current_total_monthly"] == 0
        assert result["increase_percent"] == 0


class TestGetExpansionPhases:
    """Test expansion phases retrieval."""

    def test_three_phases(self):
        phases = get_expansion_phases()
        assert len(phases) == 3

    def test_phase_keys(self):
        phases = get_expansion_phases()
        keys = [p["phase_key"] for p in phases]
        assert keys == ["validation", "expansion", "diversified"]

    def test_each_phase_has_actions(self):
        phases = get_expansion_phases()
        for p in phases:
            assert len(p["key_actions"]) > 0
            assert len(p["milestones"]) > 0


class TestGetAllMarkets:
    """Test market listing."""

    def test_four_markets(self):
        result = get_all_markets()
        assert len(result) == 4

    def test_market_codes(self):
        result = get_all_markets()
        codes = [m["market_code"] for m in result]
        assert set(codes) == {"cn", "us", "eu", "jp"}

    def test_us_highest_revenue(self):
        result = get_all_markets()
        us = next(m for m in result if m["market_code"] == "us")
        assert us["revenue_median_yuan"] or 0 >= 250000
