"""合约风险评估模块测试."""

import pytest
import sys
from pathlib import Path

# Ensure backend is on the path for service imports
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from app.services.contract_risk_service import (
    extract_clauses,
    _severity_multiplier,
    _classify_risk,
    review_contract,
)
from app.models.contract_risk import ContractRiskRule


# ========== 单元测试 ==========


def test_extract_clauses_with_chinese_numbers():
    text = "第一条 版权归属\n\n第二条 付款条件\n\n第三条 违约责任"
    clauses = extract_clauses(text)
    assert len(clauses) == 3
    assert clauses[0]["index"] == 1
    assert clauses[2]["text"].startswith("第三条")


def test_extract_clauses_with_arabic_numbers():
    text = "1. 授权范围\n\n2. 授权期限\n\n3. 分成比例"
    clauses = extract_clauses(text)
    assert len(clauses) == 3


def test_extract_clauses_no_markers():
    text = "这是一份没有序号标记的合同文本，所有内容连在一起。"
    clauses = extract_clauses(text)
    assert len(clauses) == 1
    assert clauses[0]["index"] == 1


def test_severity_multiplier():
    assert _severity_multiplier("safe") == 0
    assert _severity_multiplier("low") == 1
    assert _severity_multiplier("medium") == 2.5
    assert _severity_multiplier("high") == 5
    assert _severity_multiplier("critical") == 10
    assert _severity_multiplier("unknown") == 0


def test_classify_risk_safe():
    level, decision = _classify_risk(5)
    assert level == "safe"
    assert decision == "allow"


def test_classify_risk_low():
    level, _ = _classify_risk(20)
    assert level == "low"


def test_classify_risk_medium():
    level, _ = _classify_risk(40)
    assert level == "medium"


def test_classify_risk_high():
    level, _ = _classify_risk(60)
    assert level == "high"


def test_classify_risk_critical():
    level, _ = _classify_risk(90)
    assert level == "critical"


# ========== 集成测试（需要数据库） ==========


@pytest.fixture
def sample_general_rule(db_session):
    """Each test function gets its own unique rule name."""
    import uuid
    rule_id = f"test_copyright_transfer_{uuid.uuid4().hex[:8]}"
    rule = ContractRiskRule(
        rule_name=rule_id,
        category="general",
        clause_type="copyright_ownership",
        risk_level="critical",
        weight=10,
        description="版权全权转让风险",
        suggestion="建议保留完整著作权",
    )
    db_session.add(rule)
    db_session.commit()
    return rule


@pytest.fixture
def sample_transaction_rule(db_session):
    import uuid
    rule_id = f"test_usage_scope_{uuid.uuid4().hex[:8]}"
    rule = ContractRiskRule(
        rule_name=rule_id,
        category="transaction",
        clause_type="usage_scope",
        risk_level="high",
        weight=8,
        description="授权用途超出挂牌描述",
        suggestion="建议与挂牌描述保持一致",
    )
    db_session.add(rule)
    db_session.commit()
    return rule


def test_review_contract_matches_risk(db_session, sample_general_rule):
    # Text must contain the clause_type keyword for matching
    text = "Copyright ownership belongs to Party A."
    result = review_contract(
        db_session, "test_user", text, review_type="general"
    )
    assert result["risk_count"] >= 1
    assert result["total_score"] > 0
    assert result["clauses_found"] >= 1


def test_review_contract_no_match(db_session, sample_general_rule):
    text = "This contract becomes effective upon signing by both parties."
    result = review_contract(
        db_session, "test_user", text, review_type="general"
    )
    assert result["total_score"] == 0.0
    assert result["risk_level"] == "safe"
    assert result["risk_count"] == 0


def test_review_contract_empty_text(db_session, sample_general_rule):
    result = review_contract(
        db_session, "test_user", "", review_type="general"
    )
    assert result["total_score"] == 0.0
    assert result["risk_level"] == "safe"


def test_review_transaction_check(db_session, sample_transaction_rule):
    text = "Usage scope allows commercial use and sublicensing."
    result = review_contract(
        db_session, "test_user", text, review_type="transaction"
    )
    assert result["clauses_found"] >= 1


def test_review_creates_database_record(db_session, sample_general_rule):
    from app.models.contract_risk import ContractReview

    text = "Copyright ownership transferred."
    result = review_contract(
        db_session, "test_user", text, review_type="general"
    )

    review = db_session.query(ContractReview).filter(
        ContractReview.id == result["id"]
    ).first()

    assert review is not None
    assert review.user_id == "test_user"
    assert review.review_type == "general"
    assert review.total_score > 0


def test_review_with_target_info(db_session, sample_general_rule):
    text = "Copyright ownership transferred."
    result = review_contract(
        db_session,
        "test_user",
        text,
        review_type="general",
        target_type="listing",
        target_id="abc123",
    )
    assert result["total_score"] > 0

    from app.models.contract_risk import ContractReview

    # Verify target info was saved
    review = db_session.query(ContractReview).filter(
        ContractReview.id == result["id"]
    ).first()
    assert review.target_type == "listing"
    assert review.target_id == "abc123"


# ========== Task 8: 扩展集成测试 ==========


@pytest.fixture(scope="function")
def sample_rule(db_session):
    """Function-scoped to avoid UNIQUE constraint errors."""
    import uuid as _uuid
    rule = ContractRiskRule(
        rule_name=f"test_copyright_transfer_{_uuid.uuid4().hex[:8]}",
        category="general",
        clause_type="copyright_ownership",
        risk_level="critical",
        weight=10,
        description="版权全权转让风险",
        suggestion="建议保留完整著作权",
    )
    db_session.add(rule)
    db_session.commit()
    return rule


def test_review_contract_with_risk(db_session, sample_rule):
    # Use English text that matches the "copyright_ownership" clause_type pattern
    text = "Copyright ownership belongs to Party A."
    result = review_contract(db_session, "test_user", text, review_type="general")
    assert result["risk_count"] >= 1
    assert result["total_score"] > 0


def test_review_contract_empty(db_session):
    result = review_contract(db_session, "test_user", "", review_type="general")
    assert result["total_score"] == 0.0
    assert result["risk_level"] == "safe"


# Note: API-level integration tests via FastAPI TestClient are not included
# because the db_session fixture uses an in-memory SQLite DB that is isolated
# from app.database.get_db() (which binds to ./data/oristudio.db).
# The 6 service-layer integration tests above already verify the full
# review_contract / check_transaction workflows with a real DB session.
# For API-level testing, see tests/test_enforcement.py which uses a similar
# direct-service-call pattern.
