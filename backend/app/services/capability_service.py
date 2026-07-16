"""创作者能力评估服务层 — 8维雷达图 + 技能溢价 + AI护城河."""

from datetime import date
from typing import Optional

from sqlalchemy.orm import Session

from app.models.capability import CapabilityDimension, CreatorAssessment, LearningPath


# AI 替代风险等级 — 哪些技能容易被 AI 替代
AI_VULNERABILITY = {
    "illustrator": {
        "high_risk": ["basic_drawing", "color_mixing"],
        "medium_risk": ["composition", "concept_art"],
        "low_risk": ["brand_identity", "art_direction", "storytelling"],
    },
    "photographer": {
        "high_risk": ["basic_portrait", "product_photo"],
        "medium_risk": ["lighting_setup", "editing"],
        "low_risk": ["creative_directing", "brand_photography"],
    },
    "musician": {
        "high_risk": ["basic_composition", "standard_arrangement"],
        "medium_risk": ["mixing", "mastering"],
        "low_risk": ["live_performance", "unique_sound_design"],
    },
    "writer": {
        "high_risk": ["copywriting", "seo_content"],
        "medium_risk": ["article_writing", "translation"],
        "low_risk": ["creative_writing", "editorial_strategy"],
    },
    "default": {
        "high_risk": ["routine_tasks"],
        "medium_risk": ["standard_execution"],
        "low_risk": ["creative_vision", "strategic_thinking"],
    },
}

# 阶段定义
STAGES = [
    {"stage_key": "beginner", "name_zh": "新手期", "min_score": 0, "max_score": 25},
    {"stage_key": "intermediate", "name_zh": "成长期", "min_score": 25, "max_score": 50},
    {"stage_key": "advanced", "name_zh": "成熟期", "min_score": 50, "max_score": 75},
    {"stage_key": "expert", "name_zh": "专家期", "min_score": 75, "max_score": None},
]


def calculate_overall_score(dimension_scores: dict[str, float],
                             dimensions: list[CapabilityDimension]) -> float:
    """加权平均分."""
    if not dimension_scores:
        return 0.0

    dim_map = {d.dimension_key: d.weight for d in dimensions}
    total_weight = 0
    weighted_sum = 0

    for key, score in dimension_scores.items():
        weight = dim_map.get(key, 1.0)
        weighted_sum += score * weight
        total_weight += weight

    return round(weighted_sum / total_weight, 1) if total_weight > 0 else 0.0


def create_assessment(db: Session, user_id: str,
                       dimension_scores: dict[str, float]) -> dict:
    """创建创作者能力评估."""
    dimensions = db.query(CapabilityDimension).filter(
        CapabilityDimension.is_active == True
    ).all()

    overall = calculate_overall_score(dimension_scores, dimensions)

    # 技能组合溢价
    premium = calculate_skill_premium(dimension_scores)

    # AI 替代风险
    ai_result = assess_ai_risk(dimension_scores)

    assessment = CreatorAssessment(
        user_id=user_id,
        overall_score=overall,
        dimension_scores=dimension_scores,
        skill_premium_percent=premium["total"],
        ai_risk_level=ai_result["risk_level"],
        ai_risk_description=ai_result["description"],
    )
    db.add(assessment)
    db.commit()
    db.refresh(assessment)

    return {
        "id": assessment.id,
        "user_id": assessment.user_id,
        "overall_score": assessment.overall_score,
        "dimension_scores": assessment.dimension_scores,
        "skill_premium_percent": assessment.skill_premium_percent,
        "ai_risk_level": assessment.ai_risk_level,
        "ai_risk_description": assessment.ai_risk_description,
        "created_at": assessment.created_at,
    }


def calculate_skill_premium(dimension_scores: dict[str, float]) -> dict:
    """
    技能组合溢价计算：
    - 单一技能溢价低，多技能组合溢价高
    - 稀缺技能（低供给高需求）溢价更高
    """
    if not dimension_scores:
        return {"total": 0.0, "breakdown": {}}

    # 基础溢价 = 平均分的 30%
    avg_score = sum(dimension_scores.values()) / len(dimension_scores)
    base_premium = avg_score * 0.3

    # 技能多样性加成（每多一个技能维度 +5%）
    diversity_bonus = min(len(dimension_scores) * 5.0, 25.0)

    # 高分技能加成（>80 分的技能额外 +3%）
    high_score_bonus = sum(1 for s in dimension_scores.values() if s > 80) * 3.0

    total = round(base_premium + diversity_bonus + high_score_bonus, 1)
    total = min(total, 60.0)  # 上限 60%

    breakdown = {
        "base": round(base_premium, 1),
        "diversity": round(diversity_bonus, 1),
        "high_score": round(high_score_bonus, 1),
    }

    return {"total": total, "breakdown": breakdown}


def assess_ai_risk(dimension_scores: dict[str, float]) -> dict:
    """
    AI 替代风险评估：
    - 高分的基础执行类技能更容易被替代
    - 创意/战略类技能风险低
    """
    if not dimension_scores:
        return {"risk_level": "unknown", "risk_score": 0, "description": ""}

    # 计算 AI 可替代性分数
    # 基础执行类技能（假设 weight < 0.5 的维度）更容易被替代
    execution_score = sum(
        s for k, s in dimension_scores.items()
        if k in ("basic_drawing", "color_mixing", "basic_portrait", "copywriting")
    )
    creative_score = sum(
        s for k, s in dimension_scores.items()
        if k in ("brand_identity", "art_direction", "creative_writing", "storytelling")
    )

    avg_execution = execution_score / max(len([k for k in dimension_scores if k in ("basic_drawing", "color_mixing", "basic_portrait", "copywriting")]), 1)
    avg_creative = creative_score / max(len([k for k in dimension_scores if k in ("brand_identity", "art_direction", "creative_writing", "storytelling")]), 1)

    # 风险分数 = 执行分 × 1.5 - 创意分 × 0.5
    risk_score = round(avg_execution * 1.5 - avg_creative * 0.5, 1)
    risk_score = max(0, min(risk_score, 100))

    if risk_score >= 60:
        risk_level = "high"
        description = "您的部分核心技能存在较高 AI 替代风险，建议加强创意和战略方向的能力"
    elif risk_score >= 30:
        risk_level = "medium"
        description = "您的技能组合有一定 AI 替代风险，建议发展差异化能力"
    else:
        risk_level = "low"
        description = "您的技能组合具有良好的抗 AI 替代能力"

    return {"risk_level": risk_level, "risk_score": risk_score, "description": description}


def get_stage_recommendation(overall_score: float) -> Optional[dict]:
    """根据综合评分获取阶段推荐."""
    for stage in STAGES:
        min_s = stage["min_score"]
        max_s = stage["max_score"] or float("inf")
        if min_s <= overall_score < max_s:
            return stage
    return None


def get_learning_paths(db: Session) -> list[dict]:
    """获取所有学习路径."""
    return db.query(LearningPath).order_by(LearningPath.min_score).all()
