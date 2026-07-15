"""风控系统服务层."""

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import Session

from app.models.risk_control import RiskRule, RiskAssessment, BlacklistEntry


def evaluate_risk(
    db: Session,
    user_id: str,
    target_type: str,
    target_id: Optional[str],
    context: dict,
) -> RiskAssessment:
    """根据规则评估用户行为风险."""
    enabled_rules = (
        db.query(RiskRule)
        .filter(RiskRule.enabled == True)
        .all()
    )

    triggered = []
    total_weight = 0
    weighted_score = 0.0

    for rule in enabled_rules:
        if _matches_rule(rule.condition, context):
            triggered.append(rule.id)
            total_weight += rule.weight
            weighted_score += rule.severity_weight() * rule.weight

    # Normalize score to 0-100
    max_possible = sum(r.severity_weight() * r.weight for r in enabled_rules)
    risk_score = min((weighted_score / max_possible * 100) if max_possible > 0 else 0.0, 100.0)

    # Determine risk level and decision
    risk_level, decision = _classify_risk(risk_score)

    assessment = RiskAssessment(
        user_id=user_id,
        target_type=target_type,
        target_id=target_id,
        risk_score=risk_score,
        risk_level=risk_level,
        triggered_rules=triggered,
        decision=decision,
        decision_reason=f"Risk score {risk_score:.1f} exceeds {risk_level} threshold",
    )
    db.add(assessment)
    db.commit()
    db.refresh(assessment)
    return assessment


def _matches_rule(condition: dict, context: dict) -> bool:
    """检查上下文是否匹配规则条件."""
    field = condition.get("field")
    operator = condition.get("operator")
    expected = condition.get("value")

    actual = context.get(field)
    if actual is None:
        return False

    ops = {
        "gt": lambda a, b: a > b,
        "gte": lambda a, b: a >= b,
        "lt": lambda a, b: a < b,
        "lte": lambda a, b: a <= b,
        "eq": lambda a, b: a == b,
        "neq": lambda a, b: a != b,
        "contains": lambda a, b: b in str(a),
        "in_list": lambda a, b: a in (b if isinstance(b, list) else [b]),
    }
    fn = ops.get(operator)
    if fn is None:
        return False

    try:
        return fn(actual, expected)
    except TypeError:
        return False


def _classify_risk(score: float) -> tuple[str, str]:
    """根据分数分类风险级别和决策."""
    if score < 20:
        return "safe", "allow"
    elif score < 40:
        return "low", "allow"
    elif score < 60:
        return "medium", "warn"
    elif score < 80:
        return "high", "review"
    else:
        return "critical", "block"


class SeverityMixin:
    """为 RiskRule 添加 severity_weight 方法."""
    def severity_weight(self) -> float:
        weights = {"low": 1.0, "medium": 2.5, "high": 5.0, "critical": 10.0}
        return weights.get(self.severity, 1.0)


def add_blacklist_entry(
    db: Session,
    user_id: str,
    reason: str,
    category: str,
    added_by: Optional[str] = None,
    expires_at: Optional[datetime] = None,
) -> BlacklistEntry:
    """添加黑名单."""
    entry = BlacklistEntry(
        user_id=user_id,
        reason=reason,
        category=category,
        added_by=added_by,
        expires_at=expires_at,
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


def remove_blacklist_entry(db: Session, user_id: str, category: Optional[str] = None) -> int:
    """移除黑名单."""
    query = db.query(BlacklistEntry).filter(
        BlacklistEntry.user_id == user_id,
        BlacklistEntry.is_active == True,
    )
    if category:
        query = query.filter(BlacklistEntry.category == category)
    result = query.update({"is_active": False})
    db.commit()
    return result


def is_blacklisted(db: Session, user_id: str) -> bool:
    """检查用户是否在黑名单中."""
    now = datetime.utcnow()
    entry = (
        db.query(BlacklistEntry)
        .filter(
            BlacklistEntry.user_id == user_id,
            BlacklistEntry.is_active == True,
            (BlacklistEntry.expires_at == None) | (BlacklistEntry.expires_at > now),
        )
        .first()
    )
    return entry is not None


# Monkey-patch the method onto RiskRule
RiskRule.severity_weight = SeverityMixin.severity_weight
