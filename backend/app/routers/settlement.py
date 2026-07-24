"""结算 API 路由."""

from typing import Optional
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.common import ApiResponse
from app.schemas.settlement import (
    TaxCalculationCreate,
    TaxCalculationSchema,
    CurrencyConvertRequest,
    MultiCurrencySettlementSchema,
)
from app.models.settlement import TaxCalculation as TaxCalcModel, MultiCurrencySettlement as MCSModel
from app.services.settlement_service import calculate_tax, convert_currency

router = APIRouter()


def _calc_to_dict(c: TaxCalcModel) -> dict:
    return {
        "id": c.id,
        "contract_id": c.contract_id,
        "transaction_id": c.transaction_id,
        "seller_location": c.seller_location or {},
        "buyer_location": c.buyer_location or {},
        "product_type": c.product_type,
        "amount": float(c.amount),
        "tax_amount": float(c.tax_amount) if c.tax_amount else None,
        "tax_rate": float(c.tax_rate) if c.tax_rate else None,
        "tax_jurisdiction": c.tax_jurisdiction,
        "exemption_status": c.exemption_status,
        "calculated_by": c.calculated_by,
        "calculated_at": c.calculated_at.isoformat() if c.calculated_at else None,
    }


def _mcs_to_dict(m: MCSModel) -> dict:
    return {
        "id": m.id,
        "contract_id": m.contract_id,
        "participant_id": m.participant_id,
        "source_currency": m.source_currency,
        "source_amount": float(m.source_amount),
        "target_currency": m.target_currency,
        "target_amount": float(m.target_amount),
        "exchange_rate": float(m.exchange_rate),
        "exchange_source": m.exchange_source,
        "settled_at": m.settled_at.isoformat() if m.settled_at else None,
        "status": m.status,
        "error_message": m.error_message,
        "created_at": m.created_at.isoformat() if m.created_at else None,
    }


@router.post("/settlement/calculate-tax", response_model=ApiResponse)
async def calc_tax(body: TaxCalculationCreate, db: Session = Depends(get_db)):
    result = await calculate_tax(
        db,
        seller_location=body.seller_location,
        buyer_location=body.buyer_location,
        product_type=body.product_type,
        amount=body.amount,
        currency=body.currency,
        contract_id=body.contract_id,
        transaction_id=body.transaction_id,
    )
    return ApiResponse(data=_calc_to_dict(result), message="税务计算完成")


@router.get("/settlement/calculations", response_model=ApiResponse)
def list_calculations(product_type: Optional[str] = None, db: Session = Depends(get_db)):
    q = db.query(TaxCalcModel)
    if product_type:
        q = q.filter(TaxCalcModel.product_type == product_type)
    items = q.order_by(TaxCalcModel.calculated_at.desc()).all()
    return ApiResponse(data=[_calc_to_dict(i) for i in items])


@router.post("/settlement/convert-currency", response_model=ApiResponse)
async def do_convert(body: CurrencyConvertRequest):
    source_amt, target_amt = await convert_currency(
        None, body.source_currency, body.target_currency, body.amount,
    )
    return ApiResponse(data={
        "source_currency": body.source_currency,
        "target_currency": body.target_currency,
        "source_amount": source_amt,
        "target_amount": target_amt,
    }, message="汇率转换完成")
