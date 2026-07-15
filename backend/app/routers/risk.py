"""风控系统 API 路由."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.risk_control import (
    RiskRuleCreate, RiskRuleUpdate, RiskRuleSchema,
    RiskAssessmentSchema, BlacklistEntryCreate, BlacklistEntrySchema,
)
from app.services.risk_service import (
    evaluate_risk, add_blacklist_entry, remove_blacklist_entry, is_blacklisted,
)
from app.models.risk_control import RiskRule
from typing import Optional

router = APIRouter(prefix="/api/risk", tags=["risk-control"])


@router.post("/evaluate", response_model=RiskAssessmentSchema)
def post_evaluate_risk(
    user_id: str,
    target_type: str,
    target_id: Optional[str] = None,
    context: dict = {},
    db: Session = Depends(get_db),
):
    """评估用户行为风险."""
    assessment = evaluate_risk(db, user_id, target_type, target_id, context)
    return RiskAssessmentSchema(
        id=assessment.id,
        user_id=assessment.user_id,
        target_type=assessment.target_type,
        target_id=assessment.target_id,
        risk_score=assessment.risk_score,
        risk_level=assessment.risk_level,
        triggered_rules=assessment.triggered_rules,
        decision=assessment.decision,
        decision_reason=assessment.decision_reason,
        created_at=assessment.created_at,
    )


@router.post("/blacklist", response_model=BlacklistEntrySchema)
def post_add_blacklist(
    body: BlacklistEntryCreate,
    db: Session = Depends(get_db),
):
    """添加黑名单."""
    entry = add_blacklist_entry(
        db, body.user_id, body.reason, body.category, body.added_by, body.expires_at,
    )
    return BlacklistEntrySchema(
        id=entry.id, user_id=entry.user_id, reason=entry.reason,
        category=entry.category, created_at=entry.created_at,
    )


@router.delete("/blacklist/{user_id}")
def delete_blacklist(
    user_id: str,
    category: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """移除黑名单."""
    count = remove_blacklist_entry(db, user_id, category)
    return {"removed": count}


@router.get("/blacklist/{user_id}/status")
def get_blacklist_status(user_id: str, db: Session = Depends(get_db)):
    """检查用户是否在黑名单中."""
    blacklisted = is_blacklisted(db, user_id)
    return {"user_id": user_id, "is_blacklisted": blacklisted}


@router.get("/rules", response_model=list[RiskRuleSchema])
def get_rules(
    rule_type: Optional[str] = None,
    enabled_only: bool = True,
    db: Session = Depends(get_db),
):
    """获取风控规则列表."""
    query = db.query(RiskRule)
    if rule_type:
        query = query.filter(RiskRule.rule_type == rule_type)
    if enabled_only:
        query = query.filter(RiskRule.enabled == True)
    return query.all()


@router.post("/rules", response_model=RiskRuleSchema)
def create_rule(body: RiskRuleCreate, db: Session = Depends(get_db)):
    """创建风控规则."""
    rule = RiskRule(
        name=body.name,
        description=body.description,
        rule_type=body.rule_type,
        condition=body.condition,
        severity=body.severity,
        action=body.action,
        weight=body.weight,
        enabled=body.enabled,
    )
    db.add(rule)
    db.commit()
    db.refresh(rule)
    return rule


@router.put("/rules/{rule_id}", response_model=RiskRuleSchema)
def update_rule(rule_id: str, body: RiskRuleUpdate, db: Session = Depends(get_db)):
    """更新风控规则."""
    rule = db.query(RiskRule).filter(RiskRule.id == rule_id).first()
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    for key, value in body.model_dump(exclude_unset=True).items():
        setattr(rule, key, value)
    db.commit()
    db.refresh(rule)
    return rule
