"""合约风险评估 Pydantic schemas."""

from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class ContractReviewRequest(BaseModel):
    """提交合同审查请求."""
    review_type: str = "general"  # 'general' | 'transaction'
    contract_text: str
    target_type: Optional[str] = None
    target_id: Optional[str] = None


class ContractClauseSchema(BaseModel):
    """单条条款分析结果."""
    clause_index: int
    clause_text: str
    clause_category: Optional[str] = None
    risk_level: Optional[str] = None
    risk_description: Optional[str] = None
    suggestion: Optional[str] = None
    is_flagged: bool = False


class ContractReviewResponse(BaseModel):
    """审查结果响应."""
    id: str
    total_score: float
    risk_level: str
    clauses_found: int
    risk_count: int
    clauses: list[ContractClauseSchema]
    suggestions: list[str]
    created_at: datetime


class TransactionCheckRequest(BaseModel):
    """交易合约预检请求."""
    review_type: str = "transaction"
    listing_id: Optional[str] = None
    contract_template: Optional[str] = None
    custom_terms: Optional[list[str]] = None


class TransactionCheckIssue(BaseModel):
    """交易合约问题项."""
    field: str
    issue: str


class TransactionCheckResponse(BaseModel):
    """交易合约预检响应."""
    passed: bool
    score: float
    risk_level: str
    issues: list[TransactionCheckIssue]


class ContractRiskRuleSchema(BaseModel):
    """风险规则响应."""
    id: str
    rule_name: str
    category: str
    clause_type: str
    risk_level: str
    weight: int
    description: Optional[str] = None
    suggestion: Optional[str] = None
    is_active: bool
