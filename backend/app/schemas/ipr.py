"""IP 登记 Pydantic 模型."""

from typing import Optional, Any
from datetime import datetime, date

from pydantic import BaseModel, ConfigDict


# ── IP 登记 CRUD ──────────────────────────────────────────

class IPRegistrationCreate(BaseModel):
    work_id: Optional[str] = None
    ip_type: str = "copyright"  # copyright/trademark/design_patent/utility_patent
    jurisdiction: str = "cn"  # cn/us/eu/jp/kr/wipo
    application_no: Optional[str] = None
    registration_no: Optional[str] = None
    filing_date: Optional[date] = None
    registration_date: Optional[date] = None
    expiration_date: Optional[date] = None
    next_action_date: Optional[date] = None
    next_action_type: Optional[str] = None
    status: str = "draft"
    category_info: Optional[dict] = None
    official_fee: float = 0
    total_cost: float = 0
    agent_name: Optional[str] = None
    agent_fee: float = 0
    official_url: Optional[str] = None
    notes: Optional[str] = None


class IPRegistrationUpdate(BaseModel):
    work_id: Optional[str] = None
    ip_type: Optional[str] = None
    jurisdiction: Optional[str] = None
    application_no: Optional[str] = None
    registration_no: Optional[str] = None
    filing_date: Optional[date] = None
    registration_date: Optional[date] = None
    expiration_date: Optional[date] = None
    next_action_date: Optional[date] = None
    next_action_type: Optional[str] = None
    status: Optional[str] = None
    category_info: Optional[dict] = None
    official_fee: Optional[float] = None
    total_cost: Optional[float] = None
    agent_name: Optional[str] = None
    agent_fee: Optional[float] = None
    official_url: Optional[str] = None
    reminder_date: Optional[datetime] = None
    notes: Optional[str] = None


class IPRegistrationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    work_id: Optional[str] = None
    ip_type: str
    jurisdiction: str = "cn"
    application_no: Optional[str] = None
    registration_no: Optional[str] = None
    filing_date: Optional[date] = None
    registration_date: Optional[date] = None
    expiration_date: Optional[date] = None
    next_action_date: Optional[date] = None
    next_action_type: Optional[str] = None
    status: str
    category_info: Optional[dict] = None
    official_fee: float
    total_cost: float = 0
    agent_name: Optional[str] = None
    agent_fee: float = 0
    application_package_path: Optional[str] = None
    application_form_path: Optional[str] = None
    official_url: Optional[str] = None
    certificate_path: Optional[str] = None
    reminder_date: Optional[datetime] = None
    notes: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


# ── 智能助手 ──────────────────────────────────────────────

class PrefillRequest(BaseModel):
    work_id: str
    ip_type: str  # copyright/trademark/design_patent/utility_patent
    jurisdiction: str = "cn"


class PrefillField(BaseModel):
    official_field: str
    label_zh: str
    value: Optional[Any] = None
    source: str  # "work" / "user" / "notary" / "manual"
    editable: bool = True
    required: bool = False


class PrefillResponse(BaseModel):
    work_title: str
    ip_type: str
    jurisdiction: str
    fields: list[PrefillField]
    completeness: int  # 0-100
    missing_fields: list[str]


class CategoryRecommendRequest(BaseModel):
    tags: list[str] = []
    description: Optional[str] = None
    creator_type: Optional[str] = None
    jurisdiction: str = "cn"


class CategoryRecommendation(BaseModel):
    class_no: int
    class_name_zh: str
    priority: int  # 1-5 stars
    reason: str
    fee_estimate: float = 300


class CategoryRecommendResponse(BaseModel):
    recommendations: list[CategoryRecommendation]
    estimated_total_fee: float
    strategy_note: str


class ValidateRequest(BaseModel):
    ip_type: str
    jurisdiction: str
    fields: dict  # field_name -> value


class ValidationIssue(BaseModel):
    field: str
    level: str  # error/warning
    message: str


class ValidateResponse(BaseModel):
    valid: bool
    completeness: int
    issues: list[ValidationIssue]


# ── 仪表盘 & 提醒 ────────────────────────────────────────

class IPStats(BaseModel):
    ip_type: str
    label: str
    total: int
    by_status: dict[str, int]  # status -> count


class RenewalItem(BaseModel):
    id: str
    ip_type: str
    jurisdiction: str
    application_no: Optional[str] = None
    registration_no: Optional[str] = None
    status: str
    expiration_date: Optional[date] = None
    next_action_date: Optional[date] = None
    next_action_type: Optional[str] = None
    days_remaining: Optional[int] = None
    urgency: str  # red/orange/yellow


class IPPortfolioResponse(BaseModel):
    stats: list[IPStats]
    renewals: list[RenewalItem]
    total_ips: int
    registered_count: int
    pending_count: int


class DashboardStatsResponse(BaseModel):
    total: int
    by_type: dict[str, int]
    by_status: dict[str, int]
    by_jurisdiction: dict[str, int]
    upcoming_renewals: list[RenewalItem]
    total_annual_cost: float
