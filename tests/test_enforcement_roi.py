"""Tests for Enforcement ROI module."""

import pytest
from unittest.mock import MagicMock, patch

from app.services.enforcement_roi_service import (
    get_decision_tree,
    predict_roi,
    get_all_defense_tiers,
)


class TestDecisionTree:
    """Test rights enforcement decision tree."""

    def test_low_loss_recommends_cheapest(self):
        result = get_decision_tree("platform_copy", 2000)
        actions = result["recommended_actions"]
        action_keys = [a["action_key"] for a in actions]
        # Should NOT include expensive options for low loss
        assert "civil_lawsuit" not in action_keys
        assert "criminal_report" not in action_keys

    def test_high_loss_includes_lawsuit(self):
        result = get_decision_tree("commercial_use", 100000)
        actions = result["recommended_actions"]
        action_keys = [a["action_key"] for a in actions]
        assert "civil_lawsuit" in action_keys

    def test_ai_training_priority(self):
        result = get_decision_tree("ai_training", 50000)
        actions = result["recommended_actions"]
        # AI training should prioritize civil lawsuit
        assert actions[0]["action_key"] == "civil_lawsuit"

    def test_decision_has_reasoning(self):
        result = get_decision_tree("platform_copy", 5000)
        assert len(result["reasoning"]) > 0
        assert "内容复制" in result["reasoning"] or "复制" in result["reasoning"]

    def test_primary_recommendation_exists(self):
        result = get_decision_tree("commercial_use", 20000)
        assert "primary_recommendation" in result
        assert result["primary_recommendation"]["action_key"] is not None


class TestRoiPredictor:
    """Test ROI prediction engine."""

    def test_cease_desist_positive_roi(self):
        result = predict_roi(50000, "commercial_use", "taobao", "cease_desist")
        assert result["expected_cost"] > 0
        assert result["win_probability"] > 0
        assert result["roi_percent"] != 0

    def test_civil_lawsuit_longer_duration(self):
        r_cd = predict_roi(50000, "commercial_use", "taobao", "cease_desist")
        r_cl = predict_roi(50000, "commercial_use", "taobao", "civil_lawsuit")
        assert r_cl["expected_duration_days"] > r_cd["expected_duration_days"]

    def test_criminal_highest_cost(self):
        result = predict_roi(200000, "commercial_use", "amazon", "criminal_report")
        assert result["expected_cost"] >= 10000

    def test_risk_levels_exist(self):
        result = predict_roi(10000, "platform_copy", "xiaohongshu", "platform_complaint")
        assert result["risk_level"] in ("low", "medium", "high")

    def test_net_return_formula(self):
        result = predict_roi(100000, "commercial_use", "amazon", "civil_lawsuit")
        # net_return = expected_compensation - expected_cost
        assert abs(result["net_return"] - (result["expected_compensation"] - result["expected_cost"])) < 0.1


class TestDefenseTiers:
    """Test defense budget tier retrieval."""

    def test_four_tiers(self):
        tiers = get_all_defense_tiers()
        assert len(tiers) == 4

    def test_tier_keys(self):
        tiers = get_all_defense_tiers()
        keys = [t["tier_key"] for t in tiers]
        assert keys == ["zero", "low", "mid", "high"]

    def test_zero_tier_free(self):
        tiers = get_all_defense_tiers()
        zero = next(t for t in tiers if t["tier_key"] == "zero")
        assert zero["monthly_cost_low"] == 0
        assert zero["monthly_cost_high"] == 0

    def test_each_tier_has_features(self):
        tiers = get_all_defense_tiers()
        for t in tiers:
            assert len(t["features"]) > 0


class TestInfringementTypes:
    """Test various infringement type handling."""

    @pytest.mark.parametrize("infr_type", [
        "platform_copy", "commercial_use", "ai_training",
        "social_share", "reverse_image",
    ])
    def test_all_infringement_types_work(self, infr_type):
        result = get_decision_tree(infr_type, 10000)
        assert len(result["recommended_actions"]) > 0

    @pytest.mark.parametrize("platform", [
        "xiaohongshu", "taobao", "amazon", "etsy",
        "youtube", "generic",
    ])
    def test_all_platforms_work(self, platform):
        result = predict_roi(50000, "commercial_use", platform, "cease_desist")
        assert result["expected_cost"] >= 0
