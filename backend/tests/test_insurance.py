"""版权保险市场模块测试."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

import pytest
from datetime import date

from app.services.insurance_service import (
    estimate_premium,
    create_policy,
    get_user_policies,
    submit_claim,
)


# ── 单元测试 ──────────────────────────────────────────────────────


def test_estimate_premium_returns_tiers():
    from app.services.insurance_service import BASE_RATES
    assert "basic" in BASE_RATES
    assert "advanced" in BASE_RATES
    assert "pro" in BASE_RATES


def test_risk_multipliers_exist():
    from app.services.insurance_service import RISK_MULTIPLIERS
    assert RISK_MULTIPLIERS["low"] == 0.8
    assert RISK_MULTIPLIERS["medium"] == 1.0
    assert RISK_MULTIPLIERS["high"] == 1.5


def test_creator_type_bases_exist():
    from app.services.insurance_service import CREATOR_TYPE_BASES
    assert "illustrator" in CREATOR_TYPE_BASES
    assert CREATOR_TYPE_BASES["default"] == 1.0


# ── 集成测试（需要数据库） ───────────────────────────────────────


@pytest.fixture
def sample_product(db_session):
    """创建测试保险产品 — function-scoped 避免 UNIQUE constraint 冲突."""
    import uuid
    from app.models.insurance import InsuranceProduct
    product = InsuranceProduct(
        id=f"test_prod_{uuid.uuid4().hex[:8]}",
        product_key=f"copyright-test-{uuid.uuid4().hex[:8]}",
        category="training_indemnity",
        tier="basic",
        name_zh="基础版权保护险",
        annual_min_yuan=500.0,
        annual_max_yuan=5000.0,
        coverage_description="基础版权侵权保障",
        max_coverage_yuan=100000.0,
        is_active=True,
    )
    db_session.add(product)
    db_session.commit()
    return product


@pytest.fixture
def sample_provider(db_session):
    """创建测试保险公司."""
    import uuid
    from app.models.insurance import InsuranceProvider
    provider = InsuranceProvider(
        id=f"test_prov_{uuid.uuid4().hex[:8]}",
        name_zh="测试保险公司",
        name_en="Test Insurance Co.",
        license_no="LIC-2026-001",
        contact_email="test@insurer.com",
        is_active=True,
    )
    db_session.add(provider)
    db_session.commit()
    return provider


def test_create_policy_success(db_session, sample_product):
    """成功创建保单."""
    result = create_policy(
        db_session,
        user_id="test_user_001",
        product_id=sample_product.id,
        start_date=date(2026, 1, 1),
        duration_months=12,
    )
    assert "error" not in result
    assert result["status"] == "pending"
    assert result["user_id"] == "test_user_001"


def test_create_policy_not_found(db_session):
    """产品不存在时创建失败."""
    result = create_policy(
        db_session,
        user_id="test_user_001",
        product_id="nonexistent_product",
        start_date=date(2026, 1, 1),
    )
    assert "error" in result
    assert "not found" in result["error"].lower()


def test_get_user_policies_empty(db_session):
    """无保单时返回空列表."""
    result = get_user_policies(db_session, "no_such_user")
    assert result == []


def test_submit_claim_inactive_policy(db_session):
    """非活跃保单不能提交理赔."""
    result = submit_claim(
        db_session,
        policy_id="nonexistent_policy",
        claim_type="infringement",
        description="测试理赔",
    )
    assert "error" in result


def test_estimate_premium_with_db(db_session, sample_product):
    """带 DB 的保费估算."""
    result = estimate_premium(
        db_session,
        creator_type="illustrator",
        work_count=10,
        risk_level="medium",
        categories=["training_indemnity"],
    )
    assert "recommended_products" in result
    assert "estimated_annual_premium" in result
    assert result["tier"] in ("basic", "advanced", "pro")


def test_create_policy_uses_product_premium(db_session, sample_product):
    """保单保费取产品均价."""
    result = create_policy(
        db_session,
        user_id="test_user_002",
        product_id=sample_product.id,
        start_date=date(2026, 1, 1),
        duration_months=12,
    )
    expected_premium = round((500.0 + 5000.0) / 2, 2)
    assert result["annual_premium_yuan"] == expected_premium
