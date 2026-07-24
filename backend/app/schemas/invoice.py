"""发票管理 Pydantic 模型."""

from typing import Optional
from datetime import datetime

from pydantic import BaseModel, Field, ConfigDict


class InvoiceCreate(BaseModel):
    user_id: str
    amount_yuan: float = Field(..., gt=0)
    tax_rate: float = Field(default=0.11, ge=0, le=1)
    description: Optional[str] = None
    payment_method: Optional[str] = Field(None, max_length=50)
    payment_proof_path: Optional[str] = Field(None, max_length=500)
    is_auto_renewal: bool = False
    due_date: Optional[datetime] = None


class InvoiceUpdate(BaseModel):
    status: Optional[str] = Field(None, pattern="^(pending|paid|cancelled)$")
    paid_at: Optional[datetime] = None
    payment_method: Optional[str] = None
    payment_proof_path: Optional[str] = None
    description: Optional[str] = None


class InvoiceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    user_id: str
    invoice_number: str
    amount_yuan: float
    tax_rate: float
    subtotal_yuan: float
    tax_amount_yuan: float
    total_yuan: float
    status: str
    due_date: Optional[datetime] = None
    paid_at: Optional[datetime] = None
    description: Optional[str] = None
    payment_method: Optional[str] = None
    payment_proof_path: Optional[str] = None
    is_auto_renewal: bool
    created_at: datetime
    updated_at: datetime
