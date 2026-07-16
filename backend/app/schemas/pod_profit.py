"""POD 利润计算器 Pydantic schemas."""

from pydantic import BaseModel
from typing import Optional


class ProductConfigCreate(BaseModel):
    platform: str
    product_type: str
    markup_rate: float = 0.2


class PricingSimulation(BaseModel):
    markup_pct: int
    sale_price_usd: float
    sale_price_cny: float
    profit_usd: float
    profit_cny: float
    margin_pct: float


class SaleRecord(BaseModel):
    platform: str
    product_type: str
    sale_price_usd: float
    base_cost_usd: float
    shipping_cost_usd: float = 0
    platform_fee_pct: float = 0
    exchange_rate: float = 7.2


class ProfitResult(BaseModel):
    sale_price_usd: float
    sale_price_cny: float
    base_cost_usd: float
    shipping_cost_usd: float
    platform_fee_usd: float
    profit_usd: float
    profit_cny: float
    margin_pct: float
    exchange_rate: float


class DesignSummary(BaseModel):
    id: str
    title: str
    status: str
    total_sales: int
    total_revenue_cny: float
    total_profit_cny: float
    avg_margin_pct: float


class PodOverview(BaseModel):
    total_sales: int
    total_revenue_cny: float
    total_cost_cny: float
    total_profit_cny: float
    overall_margin_pct: float
    by_platform: dict
