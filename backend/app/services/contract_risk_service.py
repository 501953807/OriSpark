"""合约风险评估服务层 — 评分引擎 + 条款提取."""

import re
from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session

from app.models.contract_risk import ContractRiskRule, ContractReview, ContractClause


def extract_clauses(text: str) -> list[dict]:
    """按段落分割并识别条款序号，提取合同条款列表."""
    paragraphs = [p.strip() for p in re.split(r'\n\s*\n', text) if p.strip()]

    clause_pattern = re.compile(
        r'^(?:第?[一二三四五六七八九十百]+[条章段]'
        r'|[\(（]?\d+[\.、\)]'
        r'|\([一-鿿])'
    )

    clauses = []
    current_clause = None
    for para in paragraphs:
        if clause_pattern.match(para):
            if current_clause:
                clauses.append(current_clause)
            current_clause = {'text': para, 'index': len(clauses) + 1}
        elif current_clause:
            current_clause['text'] += '\n' + para

    if current_clause:
        clauses.append(current_clause)

    return clauses or [{'text': text, 'index': 1}]


def _severity_multiplier(level: str) -> float:
    """风险级别对应权重系数."""
    weights = {"safe": 0, "low": 1, "medium": 2.5, "high": 5, "critical": 10}
    return weights.get(level, 0)


def _classify_risk(score: float) -> tuple[str, str]:
    """根据分数分类风险级别."""
    if score < 10:
        return "safe", "allow"
    elif score < 30:
        return "low", "warn"
    elif score < 50:
        return "medium", "suggest_fix"
    elif score < 75:
        return "high", "strongly_recommend_fix"
    else:
        return "critical", "block"


def review_contract(
    db: Session,
    user_id: str,
    contract_text: str,
    review_type: str = "general",
    target_type: Optional[str] = None,
    target_id: Optional[str] = None,
) -> dict:
    """审查合同文本，返回风险评分和条款分析."""
    rules = (
        db.query(ContractRiskRule)
        .filter(
            ContractRiskRule.category == review_type,
            ContractRiskRule.is_active == True,
        )
        .all()
    )

    if not rules:
        return {
            "total_score": 0.0,
            "risk_level": "safe",
            "clauses_found": 0,
            "risk_count": 0,
            "clauses": [],
            "suggestions": [],
        }

    max_possible = sum(_severity_multiplier(r.risk_level) * r.weight for r in rules)

    clauses = extract_clauses(contract_text)

    results = []
    total_risk_score = 0.0
    risk_count = 0
    all_suggestions = set()

    for clause_data in clauses:
        clause_text = clause_data["text"]
        matched_rules = []

        for rule in rules:
            pattern = rule.clause_type.replace("_", r"[\_\s]*")
            if re.search(pattern, clause_text, re.IGNORECASE):
                matched_rules.append(rule)

        if matched_rules:
            clause_risk = max(matched_rules, key=lambda r: _severity_multiplier(r.risk_level))
            clause_score = _severity_multiplier(clause_risk.risk_level) * clause_risk.weight
            total_risk_score += clause_score
            risk_count += 1

            results.append({
                "clause_index": clause_data["index"],
                "clause_text": clause_text[:200],
                "clause_category": clause_risk.clause_type,
                "risk_level": clause_risk.risk_level,
                "risk_description": clause_risk.description,
                "suggestion": clause_risk.suggestion,
                "is_flagged": clause_risk.risk_level in ("high", "critical"),
            })

            if clause_risk.suggestion:
                all_suggestions.add(clause_risk.suggestion)

    total_score = min((total_risk_score / max_possible * 100) if max_possible > 0 else 0.0, 100.0)
    risk_level, _ = _classify_risk(total_score)

    review = ContractReview(
        user_id=user_id,
        review_type=review_type,
        target_type=target_type,
        target_id=target_id,
        contract_text=contract_text,
        total_score=round(total_score, 1),
        risk_level=risk_level,
        clauses_found=len(clauses),
        risk_count=risk_count,
    )
    db.add(review)
    db.flush()

    for cr in results:
        clause_record = ContractClause(
            review_id=review.id,
            clause_index=cr["clause_index"],
            clause_text=cr["clause_text"],
            clause_category=cr["clause_category"],
            risk_level=cr["risk_level"],
            risk_description=cr["risk_description"],
            suggestion=cr["suggestion"],
            is_flagged=cr["is_flagged"],
        )
        db.add(clause_record)

    db.commit()
    db.refresh(review)

    return {
        "id": review.id,
        "total_score": round(total_score, 1),
        "risk_level": risk_level,
        "clauses_found": len(clauses),
        "risk_count": risk_count,
        "clauses": results,
        "suggestions": sorted(all_suggestions),
        "created_at": review.created_at,
    }


def check_transaction(
    db: Session,
    user_id: str,
    listing_id: Optional[str] = None,
    custom_terms: Optional[list[str]] = None,
) -> dict:
    """交易合约预检 — 检查授权范围、价格、交付等条款是否合规."""
    result = review_contract(
        db, user_id, "\n".join(custom_terms or []),
        review_type="transaction",
        target_type="listing",
        target_id=listing_id,
    )

    issues = []
    for clause in result["clauses"]:
        if clause.get("risk_level") in ("high", "critical"):
            issues.append({
                "field": clause.get("clause_category", "unknown"),
                "issue": clause.get("risk_description", "未知风险"),
            })

    return {
        "passed": result["risk_level"] not in ("high", "critical"),
        "score": result["total_score"],
        "risk_level": result["risk_level"],
        "issues": issues,
    }
