"""议价协商 API 路由."""

import json
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import require_auth
from app.models.negotiation import TradeNegotiation
from app.schemas.negotiation import (
    NegotiationCreate,
    OfferRequest,
    NegotiationResponse,
)
from app.services.negotiation_service import (
    create_negotiation,
    submit_offer,
    accept_offer,
    complete_negotiation,
    cancel_negotiation,
    list_negotiations,
)

router = APIRouter(prefix="/negotiations", tags=["negotiations"])


def _nego_to_dict(nego: TradeNegotiation) -> dict:
    msg_log = []
    if nego.message_log:
        try:
            msg_log = json.loads(nego.message_log)
        except json.JSONDecodeError:
            pass
    return {
        "id": nego.id,
        "buyer_id": nego.buyer_id,
        "seller_id": nego.seller_id,
        "listing_id": nego.listing_id,
        "match_request_id": nego.match_request_id,
        "description": nego.description,
        "initial_price_yuan": float(nego.initial_price_yuan) if nego.initial_price_yuan else None,
        "current_offer_yuan": float(nego.current_offer_yuan) if nego.current_offer_yuan else None,
        "final_price_yuan": float(nego.final_price_yuan) if nego.final_price_yuan else None,
        "status": nego.status,
        "message_log": msg_log,
        "created_at": nego.created_at.isoformat() if nego.created_at else None,
        "updated_at": nego.updated_at.isoformat() if nego.updated_at else None,
    }


@router.post("", response_model=dict)
def post_create(body: NegotiationCreate, db: Session = Depends(get_db)):
    """发起议价."""
    nego = create_negotiation(db, body.model_dump())
    return {"data": _nego_to_dict(nego), "message": "Negotiation created"}


@router.get("", response_model=list[dict])
def get_list(
    user_id: str = "",
    status: str = None,
    limit: int = 20,
    offset: int = 0,
    db: Session = Depends(get_db),
):
    """我的议价列表."""
    negos = list_negotiations(db, user_id, status, limit, offset)
    return [_nego_to_dict(n) for n in negos]


@router.get("/{negotiation_id}", response_model=dict)
def get_detail(negotiation_id: str, db: Session = Depends(get_db)):
    """议价详情."""
    nego = db.query(TradeNegotiation).filter(TradeNegotiation.id == negotiation_id).first()
    if not nego:
        raise HTTPException(status_code=404, detail="Negotiation not found")
    return {"data": _nego_to_dict(nego)}


@router.post("/{negotiation_id}/offer", response_model=dict)
def post_offer(
    negotiation_id: str,
    body: OfferRequest,
    user_id: str = Depends(require_auth),
    db: Session = Depends(get_db),
):
    """出价/还价."""
    nego = submit_offer(db, negotiation_id, user_id, body.amount_yuan, body.message)
    return {"data": _nego_to_dict(nego), "message": "Offer submitted"}


@router.patch("/{negotiation_id}/accept", response_model=dict)
def patch_accept(
    negotiation_id: str,
    user_id: str = Depends(require_auth),
    db: Session = Depends(get_db),
):
    """接受当前报价."""
    nego = accept_offer(db, negotiation_id, user_id)
    return {"data": _nego_to_dict(nego), "message": "Offer accepted"}


@router.post("/{negotiation_id}/complete", response_model=dict)
def post_complete(
    negotiation_id: str,
    user_id: str = Depends(require_auth),
    db: Session = Depends(get_db),
):
    """确认成交."""
    nego = complete_negotiation(db, negotiation_id, user_id)
    return {"data": _nego_to_dict(nego), "message": "Transaction completed"}


@router.patch("/{negotiation_id}/cancel", response_model=dict)
def patch_cancel(
    negotiation_id: str,
    reason: str = None,
    user_id: str = Depends(require_auth),
    db: Session = Depends(get_db),
):
    """取消议价."""
    nego = cancel_negotiation(db, negotiation_id, user_id, reason)
    return {"data": _nego_to_dict(nego), "message": "Negotiation cancelled"}
