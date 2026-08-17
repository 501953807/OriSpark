"""议价协商服务层 — 含状态机."""

import json
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy.orm import Session

from app.models.negotiation import TradeNegotiation
from app.utils.errors import BusinessException

# 状态流转规则
_STATUS_TRANSITIONS = {
    "pending": ["negotiating", "cancelled"],
    "negotiating": ["negotiating", "agreed", "cancelled"],
    "agreed": ["completed", "cancelled"],
    "completed": [],
    "cancelled": [],
}


def _append_message(nego: TradeNegotiation, sender_id: str, role: str, content: str) -> None:
    """追加消息到 message_log."""
    messages = []
    if nego.message_log:
        try:
            messages = json.loads(nego.message_log)
        except json.JSONDecodeError:
            messages = []
    messages.append({
        "sender_id": sender_id,
        "role": role,
        "content": content,
        "created_at": datetime.now(timezone.utc).isoformat(),
    })
    nego.message_log = json.dumps(messages, ensure_ascii=False)


def create_negotiation(db: Session, data: dict) -> TradeNegotiation:
    """创建议价协商."""
    nego = TradeNegotiation(
        buyer_id=data["buyer_id"],
        seller_id=data["seller_id"],
        listing_id=data.get("listing_id"),
        match_request_id=data.get("match_request_id"),
        description=data.get("description"),
        initial_price_yuan=data.get("initial_price_yuan"),
        current_offer_yuan=data.get("initial_price_yuan"),
        status="pending",
        message_log=json.dumps([], ensure_ascii=False),
    )
    db.add(nego)
    db.commit()
    db.refresh(nego)
    return nego


def list_negotiations(db: Session, user_id: str, status: str = None, limit: int = 20, offset: int = 0) -> list[TradeNegotiation]:
    """查询我的议价列表."""
    query = db.query(TradeNegotiation).filter(
        (TradeNegotiation.buyer_id == user_id) | (TradeNegotiation.seller_id == user_id)
    )
    if status:
        query = query.filter(TradeNegotiation.status == status)
    return query.order_by(TradeNegotiation.created_at.desc()).limit(limit).offset(offset).all()


def submit_offer(db: Session, nego_id: str, buyer_id: str, amount_yuan: float, message: str = None) -> TradeNegotiation:
    """提交出价/还价."""
    nego = db.query(TradeNegotiation).filter(TradeNegotiation.id == nego_id).first()
    if not nego:
        raise BusinessException(f"议价 {nego_id} 不存在", status_code=404)

    if amount_yuan <= 0:
        raise BusinessException("报价金额必须大于零")

    if buyer_id != nego.buyer_id:
        raise BusinessException("只有买家可以提交出价")

    if nego.status == "pending":
        nego.status = "negotiating"
    elif nego.status != "negotiating":
        raise BusinessException(f"当前状态 {nego.status} 不允许提交出价")

    nego.current_offer_yuan = Decimal(str(amount_yuan))
    _append_message(nego, buyer_id, "offer", f"{message or 'Out bid'} ¥{amount_yuan}")
    db.commit()
    db.refresh(nego)
    return nego


def accept_offer(db: Session, nego_id: str, user_id: str) -> TradeNegotiation:
    """接受当前报价."""
    nego = db.query(TradeNegotiation).filter(TradeNegotiation.id == nego_id).first()
    if not nego:
        raise BusinessException(f"议价 {nego_id} 不存在", status_code=404)

    if user_id not in (nego.buyer_id, nego.seller_id):
        raise BusinessException("只有议价参与方可以接受报价")

    allowed = _STATUS_TRANSITIONS.get(nego.status, [])
    if "agreed" not in allowed:
        raise BusinessException(f"当前状态 {nego.status} 不允许接受报价")

    nego.final_price_yuan = nego.current_offer_yuan
    nego.status = "agreed"
    _append_message(nego, user_id, "system", "Offer accepted")
    db.commit()
    db.refresh(nego)
    return nego


def complete_negotiation(db: Session, nego_id: str, user_id: str) -> TradeNegotiation:
    """确认成交."""
    nego = db.query(TradeNegotiation).filter(TradeNegotiation.id == nego_id).first()
    if not nego:
        raise BusinessException(f"议价 {nego_id} 不存在", status_code=404)

    if user_id not in (nego.buyer_id, nego.seller_id):
        raise BusinessException("只有议价参与方可以确认成交")

    allowed = _STATUS_TRANSITIONS.get(nego.status, [])
    if "completed" not in allowed:
        raise BusinessException(f"当前状态 {nego.status} 不允许确认成交")

    nego.status = "completed"
    _append_message(nego, user_id, "system", "Transaction completed")
    db.commit()
    db.refresh(nego)
    return nego


def cancel_negotiation(db: Session, nego_id: str, user_id: str, reason: str = None) -> TradeNegotiation:
    """取消议价."""
    nego = db.query(TradeNegotiation).filter(TradeNegotiation.id == nego_id).first()
    if not nego:
        raise BusinessException(f"议价 {nego_id} 不存在", status_code=404)

    if user_id not in (nego.buyer_id, nego.seller_id):
        raise BusinessException("只有议价参与方可以取消")

    allowed = _STATUS_TRANSITIONS.get(nego.status, [])
    if "cancelled" not in allowed:
        raise BusinessException(f"当前状态 {nego.status} 不允许取消")

    nego.status = "cancelled"
    _append_message(nego, user_id, "system", f"Cancelled: {reason or 'No reason provided'}")
    db.commit()
    db.refresh(nego)
    return nego
