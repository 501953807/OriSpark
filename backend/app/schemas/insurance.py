"""版权保险市场 Pydantic schemas."""

from pydantic import BaseModel
from datetime import date, datetime
from typing import Optional


class InsuranceProductSchema(BaseModel):
    """保险产品响应."""
    id: str
    product_key: str
    category: str
    tier: str
    name_zh: str
    annual_min_yuan: float
    annual_max_yuan: float
    coverage_description: Optional[str] = None
    max_coverage_yuan: Optional[float] = None
    is_active: bool = True


class InsuranceEstimateRequest(BaseModel):
    """保费估算请求."""
    creator_type: str
    work_count: int
    risk_level: str = "medium"
    categories: list[str]


class InsuranceEstimateResponse(BaseModel):
    """保费估算响应."""
    recommended_products: list[InsuranceProductSchema]
    estimated_annual_premium: float
    tier: str


class PolicyPurchaseRequest(BaseModel):
    """投保请求."""
    product_id: str
    start_date: date
    duration_months: int = 12


class InsurancePolicySchema(BaseModel):
    """保单响应."""
    id: str
    user_id: str
    product_id: str
    product_name: str
    status: str
    annual_premium_yuan: float
    start_date: date
    end_date: date
    policy_number: Optional[str] = None


class ClaimCreateRequest(BaseModel):
    """理赔申请请求."""
    policy_id: str
    claim_type: str
    description: Optional[str] = None
    evidence_urls: Optional[list[str]] = None
    claimed_amount_yuan: Optional[float] = None


class InsuranceClaimSchema(BaseModel):
    """理赔响应."""
    id: str
    policy_id: str
    claim_type: str
    description: Optional[str] = None
    evidence_urls: Optional[list[str]] = None
    claimed_amount_yuan: Optional[float] = None
    status: str
    resolution: Optional[str] = None
    created_at: datetime
    resolved_at: Optional[datetime] = None


class InsuranceProviderSchema(BaseModel):
    """保险公司响应."""
    id: str
    name_zh: str
    name_en: Optional[str] = None
    license_no: Optional[str] = None
    contact_email: Optional[str] = None
    is_active: bool = True
