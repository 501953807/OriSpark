"""税务代理 Pydantic 模型."""

from datetime import datetime
from typing import Optional, Any

from pydantic import BaseModel, ConfigDict


class TaxAgentCreate(BaseModel):
    participant_id: str
    name: str
    license_no: Optional[str] = None
    service_areas: Optional[list[str]] = None
    fee_rate: float
    avalara_account_id: Optional[str] = None


class TaxAgentUpdate(BaseModel):
    status: Optional[str] = None
    rating: Optional[float] = None
    fee_rate: Optional[float] = None


class TaxAgentSchema(BaseModel):
    id: str
    participant_id: str
    name: str
    license_no: Optional[str] = None
    service_areas: Optional[list[str]] = None
    fee_rate: float
    avalara_account_id: Optional[str] = None
    status: str
    rating: Optional[float] = None
    review_count: int
    created_at: Optional[str] = None
    approved_at: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class TaxReportSchema(BaseModel):
    id: str
    participant_id: str
    agent_id: Optional[str] = None
    report_period: str
    total_income: float
    total_tax_withheld: float
    total_tax_owed: float
    currency: str
    generated_by: Optional[str] = None
    status: str
    file_path: Optional[str] = None
    created_at: Optional[str] = None
    finalized_at: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)
