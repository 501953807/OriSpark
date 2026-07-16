"""版权登记指南 Pydantic schemas."""

from pydantic import BaseModel
from typing import Optional


class RegistrationCreate(BaseModel):
    title: str
    work_type: str
    registration_type: str = "domestic"


class RegistrationUpdate(BaseModel):
    status: Optional[str] = None
    application_number: Optional[str] = None
    fee_yuan: Optional[float] = None
    notes: Optional[str] = None
    certificate_url: Optional[str] = None


class RegistrationResponse(BaseModel):
    id: str
    title: str
    work_type: str
    registration_type: str
    status: str
    application_number: Optional[str] = None
    registration_date: Optional[str] = None
    fee_yuan: Optional[float] = None
    notes: Optional[str] = None
    created_at: str
    updated_at: str


class GuideStep(BaseModel):
    step: int
    title: str
    description: str
    required_files: list[str]


class RegistrationGuide(BaseModel):
    id: str
    work_type: str
    title_zh: str
    steps: list[GuideStep]
    estimated_days: int
    estimated_fee_yuan: float


class RegistrationSummary(BaseModel):
    total: int
    by_status: dict
    by_type: dict
    total_fees_yuan: float
