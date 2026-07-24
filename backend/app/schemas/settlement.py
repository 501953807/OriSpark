"""结算 Pydantic 模型."""

from datetime import datetime
from typing import Optional, Any

from pydantic import BaseModel, ConfigDict


class TaxCalculationCreate(BaseModel):
    contract_id: Optional[str] = None
    transaction_id: Optional[str] = None
    seller_location: dict[str, str]
    buyer_location: dict[str, str]
    product_type: str
    amount: float
    currency: str = "CNY"
    calculated_by: str = "manual"


class TaxCalculationSchema(BaseModel):
    id: str
    contract_id: Optional[str] = None
    transaction_id: Optional[str] = None
    seller_location: dict[str, str]
    buyer_location: dict[str, str]
    product_type: str
    amount: float
    tax_amount: Optional[float] = None
    tax_rate: Optional[float] = None
    tax_jurisdiction: Optional[str] = None
    exemption_status: Optional[str] = None
    calculated_by: str
    calculated_at: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class CurrencyConvertRequest(BaseModel):
    source_currency: str
    target_currency: str
    amount: float
    exchange_source: Optional[str] = None


class MultiCurrencySettlementSchema(BaseModel):
    id: str
    contract_id: str
    participant_id: str
    source_currency: str
    source_amount: float
    target_currency: str
    target_amount: float
    exchange_rate: float
    exchange_source: Optional[str] = None
    settled_at: Optional[str] = None
    status: str
    error_message: Optional[str] = None
    created_at: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)
