"""风控系统 Pydantic schemas."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class RiskRuleCreate(BaseModel):
    name: str
    description: Optional[str] = None
    rule_type: str  # price_anomaly, credit_drop, frequency, blacklist, content_match
    condition: dict  # {field, operator, value}
    severity: str = "medium"  # low/medium/high/critical
    action: str = "flag"  # flag/review/block/notify
    weight: int = 1
    enabled: bool = True


class RiskRuleUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    rule_type: Optional[str] = None
    condition: Optional[dict] = None
    severity: Optional[str] = None
    action: Optional[str] = None
    weight: Optional[int] = None
    enabled: Optional[bool] = None


class RiskRuleSchema(BaseModel):
    id: str
    name: str
    description: Optional[str]
    rule_type: str
    condition: dict
    severity: str
    action: str
    weight: int
    enabled: bool
    created_at: Optional[datetime] = None


class RiskAssessmentSchema(BaseModel):
    id: str
    user_id: str
    target_type: str
    target_id: Optional[str]
    risk_score: float
    risk_level: str  # safe/low/medium/high/critical
    triggered_rules: Optional[list[str]]
    decision: str  # allow/review/block/warn
    decision_reason: Optional[str]
    created_at: Optional[datetime] = None


class BlacklistEntryCreate(BaseModel):
    user_id: str
    reason: str
    category: str  # fraud, copyright, spam, harassment, policy_violation
    added_by: Optional[str] = None
    expires_at: Optional[datetime] = None


class BlacklistEntrySchema(BaseModel):
    id: str
    user_id: str
    reason: str
    category: str
    created_at: Optional[datetime] = None
