"""发票与自动续费路由."""

from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.common import ApiResponse
from app.deps import require_auth
from app.services.invoice_service import (
    create_invoice,
    list_invoices,
    mark_invoice_paid,
    update_auto_renewal,
    get_auto_renewal,
    process_renewal_attempt,
)

router = APIRouter(prefix="/subscriptions", tags=["invoices-auto-renewal"])


class CreateInvoicePayload(BaseModel):
    amount_yuan: float = Field(..., gt=0)
    tax_rate: float = Field(default=0.11, ge=0, le=1)
    description: str | None = None
    payment_method: str | None = None
    due_date: datetime | None = None
    is_auto_renewal: bool = False


class MarkPaidPayload(BaseModel):
    invoice_id: str


class AutoRenewalPayload(BaseModel):
    enabled: bool


@router.post("/invoices", response_model=ApiResponse[dict], dependencies=[Depends(require_auth)])
def create(payload: CreateInvoicePayload, user_id: str = Depends(require_auth), db: Session = Depends(get_db)):
    """创建发票."""
    result = create_invoice(
        user_id=user_id,
        amount_yuan=payload.amount_yuan,
        tax_rate=payload.tax_rate,
        description=payload.description,
        payment_method=payload.payment_method,
        due_date=payload.due_date,
        is_auto_renewal=payload.is_auto_renewal,
        db=db,
    )
    return ApiResponse(data=result, message="发票创建成功")


@router.get("/invoices", response_model=ApiResponse[list], dependencies=[Depends(require_auth)])
def list_my_invoices(
    status: str | None = None,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    user_id: str = Depends(require_auth),
    db: Session = Depends(get_db),
):
    """获取我的发票列表."""
    return ApiResponse(data=list_invoices(user_id, status, limit, offset, db))


@router.post("/invoices/mark-paid", response_model=ApiResponse[dict], dependencies=[Depends(require_auth)])
def pay(payload: MarkPaidPayload, db: Session = Depends(get_db)):
    """标记发票已支付."""
    try:
        result = mark_invoice_paid(payload.invoice_id, db)
        return ApiResponse(data=result, message="发票已标记为已支付")
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/auto-renewal/{subscriber_id}", response_model=ApiResponse[dict | None], dependencies=[Depends(require_auth)])
def get_renewal(subscriber_id: str, db: Session = Depends(get_db)):
    """获取自动续费配置."""
    return ApiResponse(data=get_auto_renewal(subscriber_id, db))


@router.patch("/auto-renewal/{subscriber_id}", response_model=ApiResponse[dict], dependencies=[Depends(require_auth)])
def set_renewal(subscriber_id: str, payload: AutoRenewalPayload, db: Session = Depends(get_db)):
    """更新自动续费配置."""
    result = update_auto_renewal(subscriber_id, payload.enabled, db)
    return ApiResponse(data=result, message="自动续费配置已更新")


@router.post("/auto-renewal/process", response_model=ApiResponse[dict], dependencies=[Depends(require_auth)])
def process(payload: dict, db: Session = Depends(get_db)):
    """处理续费扣款尝试."""
    subscriber_id = payload.get("subscriber_id")
    success = payload.get("success", False)
    if not subscriber_id:
        raise HTTPException(status_code=400, detail="缺少 subscriber_id")
    result = process_renewal_attempt(subscriber_id, success, db)
    return ApiResponse(data=result)
