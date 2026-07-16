"""多市场扩展 Pydantic schemas."""

from pydantic import BaseModel
from datetime import date
from typing import Optional


class MarketInfoSchema(BaseModel):
    """市场信息响应."""
    id: str
    market_code: str
    name_zh: str
    name_en: str
    total_creators: Optional[float] = None
    revenue_median_yuan: Optional[float] = None
    avg_rpm_yuan: Optional[float] = None
    growth_rate_yoy: Optional[float] = None
    is_open_to_foreign_creators: bool = True
    copyright_protection_level: str
    language_barrier: str


class GeoArbitrageRequest(BaseModel):
    """地理套利计算器请求."""
    current_markets: list[str]  # ["cn"]
    creator_type: str
    monthly_revenue_yuan: float


class GeoArbitrageResponse(BaseModel):
    """地理套利计算响应."""
    current_total_monthly: float
    projected_with_targets: dict[str, float]  # {market_code: monthly_revenue}
    total_projected_monthly: float
    increase_percent: float
    recommended_markets: list[str]


class ExpansionPhase(BaseModel):
    """出海阶段信息."""
    phase_key: str
    phase_name_zh: str
    duration_months: int
    key_actions: list[str]
    milestones: list[str]


class ExpansionPlanCreate(BaseModel):
    """创建出海规划请求."""
    target_markets: list[str]
    phase: str
    start_date: Optional[date] = None
    notes: Optional[str] = None


class TaxGuideSchema(BaseModel):
    """税务指南响应."""
    id: str
    source_market: str
    target_market: str
    withholding_tax_rate: Optional[float] = None
    tax_treaty_reduction: Optional[float] = None
    recommended_entity: Optional[str] = None
    required_forms: Optional[list[str]] = None
    description_zh: Optional[str] = None
