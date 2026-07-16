"""Tests for Creator Capability Assessment service."""

import pytest
from unittest.mock import MagicMock

from app.services.capability_service import (
    calculate_overall_score,
    calculate_skill_premium,
    assess_ai_risk,
    get_stage_recommendation,
)


class TestCalculateOverallScore:
    """Test weighted average scoring."""

    def test_equal_weights(self):
        scores = {"a": 80, "b": 60}
        dims = []  # No dimensions = uniform weight
        result = calculate_overall_score(scores, dims)
        assert result == 70.0  # (80+60)/2

    def test_weighted_scores(self):
        scores = {"a": 100, "b": 50}
        dim_a = MagicMock()
        dim_a.dimension_key = "a"
        dim_a.weight = 2.0
        dim_b = MagicMock()
        dim_b.dimension_key = "b"
        dim_b.weight = 1.0
        dims = [dim_a, dim_b]
        result = calculate_overall_score(scores, dims)
        # (100*2 + 50*1) / (2+1) = 250/3 = 83.3
        assert result == 83.3

    def test_empty_scores(self):
        assert calculate_overall_score({}, []) == 0.0


class TestCalculateSkillPremium:
    """Test skill premium calculation."""

    def test_single_skill(self):
        result = calculate_skill_premium({"drawing": 80})
        assert result["total"] > 0
        assert result["total"] <= 60.0  # Cap

    def test_multiple_skills_diversity_bonus(self):
        r1 = calculate_skill_premium({"drawing": 60})
        r2 = calculate_skill_premium({"drawing": 60, "painting": 60, "sculpture": 60})
        assert r2["total"] > r1["total"]  # More skills = higher premium

    def test_high_score_bonus(self):
        r1 = calculate_skill_premium({"a": 50, "b": 50})
        r2 = calculate_skill_premium({"a": 90, "b": 90})
        assert r2["total"] > r1["total"]

    def test_empty_skills(self):
        result = calculate_skill_premium({})
        assert result["total"] == 0.0


class TestAssessAIRisk:
    """Test AI risk assessment."""

    def test_high_execution_low_creative(self):
        result = assess_ai_risk({
            "basic_drawing": 90,
            "color_mixing": 85,
        })
        assert result["risk_level"] in ("high", "medium")

    def test_high_creative_skills(self):
        result = assess_ai_risk({
            "brand_identity": 90,
            "art_direction": 85,
        })
        assert result["risk_level"] in ("low", "medium")

    def test_empty_scores(self):
        result = assess_ai_risk({})
        assert result["risk_level"] == "unknown"


class TestGetStageRecommendation:
    """Test stage recommendation."""

    def test_beginner(self):
        stage = get_stage_recommendation(15)
        assert stage["stage_key"] == "beginner"

    def test_intermediate(self):
        stage = get_stage_recommendation(40)
        assert stage["stage_key"] == "intermediate"

    def test_advanced(self):
        stage = get_stage_recommendation(60)
        assert stage["stage_key"] == "advanced"

    def test_expert(self):
        stage = get_stage_recommendation(90)
        assert stage["stage_key"] == "expert"
