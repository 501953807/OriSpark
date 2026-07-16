"""版权保险服务层 — 保费估算引擎 + 保单管理."""

import math
from datetime import date, timedelta
from typing import Optional

from sqlalchemy.orm import Session

from app.models.insurance import (
    InsuranceProduct,
    InsurancePolicy,
    InsuranceClaim,
    InsuranceProvider,
)
from app.schemas.insurance import InsuranceProductSchema


# 保费估算基准费率（按 tier）
BASE_RATES = {
    "basic": 500.0,
    "advanced": 3000.0,
    "pro": 25000.0,
}

# 风险系数
RISK_MULTIPLIERS = {
    "low": 0.8,
    "medium": 1.0,
    "high": 1.5,
}

# 创作者类型基础系数
CREATOR_TYPE_BASES = {
    "illustrator": 1.0,
    "photographer": 1.2,
    "musician": 0.9,
    "writer": 0.7,
    "video_creator": 1.1,
    "craftsman": 0.8,
    "default": 1.0,
}

# 每类保险的权重
CATEGORY_WEIGHTS = {
    "training_indemnity": 1.0,
    "style_copy": 0.8,
    "deepfake": 1.2,
    "unintentional_infringement": 0.9,
    "voice_portrait_theft": 0.7,
}


def estimate_premium(
    db: Session,
    creator_type: str,
    work_count: int,
    risk_level: str = "medium",
    categories: Optional[list[str]] = None,
) -> dict:
    """
    保费估算公式：
    base_rate × work_factor × risk_multiplier × category_weight

    - base_rate: 按 tier 不同（basic=500, advanced=3000, pro=25000）
    - work_factor: sqrt(work_count) / 10（作品越多单价越低）
    - risk_multiplier: low=0.8, medium=1.0, high=1.5
    - category_weight: 每类保险权重不同
    """
    if not categories:
        categories = [p.category for p in db.query(InsuranceProduct)
                       .filter(InsuranceProduct.is_active == True)
                       .distinct(InsuranceProduct.category)
                       .all()]

    creator_base = CREATOR_TYPE_BASES.get(creator_type, CREATOR_TYPE_BASES["default"])
    risk_mult = RISK_MULTIPLIERS.get(risk_level, 1.0)
    work_factor = min(math.sqrt(max(work_count, 1)) / 10.0, 2.0)  # 上限 2x

    # 按 tier 分别估算
    recommendations = []
    best_tier = "basic"
    best_premium = float("inf")

    for tier in ("basic", "advanced", "pro"):
        base = BASE_RATES[tier]
        tier_premium = base * creator_base * work_factor * risk_mult

        # 多类别叠加（取最大的 3 个权重）
        weights = [CATEGORY_WEIGHTS.get(c, 1.0) for c in categories[:3]]
        if weights:
            tier_premium *= sum(weights) / len(weights)

        tier_premium = round(tier_premium, 2)

        # 获取该 tier 的产品
        products = db.query(InsuranceProduct).filter(
            InsuranceProduct.tier == tier,
            InsuranceProduct.is_active == True,
        ).all()

        if products:
            recommendations.append({
                "tier": tier,
                "estimated_premium": tier_premium,
                "products": [p for p in products if p.category in categories],
            })
            if tier_premium < best_premium:
                best_premium = tier_premium
                best_tier = tier

    return {
        "recommended_products": recommendations,
        "estimated_annual_premium": best_premium,
        "tier": best_tier,
    }


def create_policy(
    db: Session,
    user_id: str,
    product_id: str,
    start_date: date,
    duration_months: int = 12,
) -> dict:
    """创建保单（模拟投保流程）."""
    product = db.query(InsuranceProduct).filter(
        InsuranceProduct.id == product_id,
        InsuranceProduct.is_active == True,
    ).first()
    if not product:
        return {"error": "Product not found or inactive"}

    end_date = start_date + timedelta(days=duration_months * 30)

    policy = InsurancePolicy(
        user_id=user_id,
        product_id=product_id,
        provider_id=product.provider_id,
        status="pending",
        annual_premium_yuan=(product.annual_min_yuan + product.annual_max_yuan) / 2,
        start_date=start_date,
        end_date=end_date,
    )
    db.add(policy)
    db.commit()
    db.refresh(policy)

    return {
        "id": policy.id,
        "user_id": policy.user_id,
        "product_id": policy.product_id,
        "product_name": product.name_zh,
        "status": policy.status,
        "annual_premium_yuan": policy.annual_premium_yuan,
        "start_date": policy.start_date,
        "end_date": policy.end_date,
        "policy_number": policy.policy_number,
    }


def get_user_policies(db: Session, user_id: str) -> list[dict]:
    """获取用户所有保单."""
    policies = db.query(InsurancePolicy).filter(
        InsurancePolicy.user_id == user_id
    ).order_by(InsurancePolicy.created_at.desc()).all()

    result = []
    for p in policies:
        product = db.query(InsuranceProduct).filter(
            InsuranceProduct.id == p.product_id
        ).first()
        result.append({
            "id": p.id,
            "user_id": p.user_id,
            "product_id": p.product_id,
            "product_name": product.name_zh if product else "Unknown",
            "status": p.status,
            "annual_premium_yuan": p.annual_premium_yuan,
            "start_date": p.start_date,
            "end_date": p.end_date,
            "policy_number": p.policy_number,
        })
    return result


def submit_claim(
    db: Session,
    policy_id: str,
    claim_type: str,
    description: Optional[str] = None,
    evidence_urls: Optional[list[str]] = None,
    claimed_amount_yuan: Optional[float] = None,
) -> dict:
    """提交理赔申请."""
    policy = db.query(InsurancePolicy).filter(
        InsurancePolicy.id == policy_id,
        InsurancePolicy.status == "active",
    ).first()
    if not policy:
        return {"error": "Active policy not found"}

    claim = InsuranceClaim(
        policy_id=policy_id,
        claim_type=claim_type,
        description=description,
        evidence_urls=str(evidence_urls) if evidence_urls else None,
        claimed_amount_yuan=claimed_amount_yuan,
        status="submitted",
    )
    db.add(claim)
    db.commit()
    db.refresh(claim)

    return {
        "id": claim.id,
        "policy_id": claim.policy_id,
        "claim_type": claim.claim_type,
        "status": claim.status,
        "created_at": claim.created_at,
    }


def get_claim_status(db: Session, claim_id: str) -> Optional[dict]:
    """查询理赔状态."""
    claim = db.query(InsuranceClaim).filter(InsuranceClaim.id == claim_id).first()
    if not claim:
        return None
    return {
        "id": claim.id,
        "policy_id": claim.policy_id,
        "claim_type": claim.claim_type,
        "status": claim.status,
        "description": claim.description,
        "evidence_urls": claim.evidence_urls,
        "claimed_amount_yuan": claim.claimed_amount_yuan,
        "resolution": claim.resolution,
        "created_at": claim.created_at,
        "resolved_at": claim.resolved_at,
    }


def get_active_policies_for_user(db: Session, user_id: str) -> list[InsuranceProduct]:
    """获取用户当前有效保单关联的产品."""
    policies = db.query(InsurancePolicy).filter(
        InsurancePolicy.user_id == user_id,
        InsurancePolicy.status == "active",
        InsurancePolicy.end_date >= date.today(),
    ).all()

    product_ids = [p.product_id for p in policies]
    if not product_ids:
        return []

    return db.query(InsuranceProduct).filter(
        InsuranceProduct.id.in_(product_ids)
    ).all()
