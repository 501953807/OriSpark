from sqlalchemy.orm import Session

from app.models.matchmaking import MatchRequest, MatchTransaction


def create_match_request(db: Session, req: dict) -> MatchRequest:
    """创建撮合请求."""
    mr = MatchRequest(**{k: v for k, v in req.items()})
    db.add(mr)
    db.commit()
    db.refresh(mr)
    return mr


def match_creators(db: Session, request_id: str, candidate_seller_ids: list[str]) -> MatchRequest | None:
    """匹配创作者 — 将候选创作者ID关联到撮合请求."""
    mr = db.query(MatchRequest).filter(MatchRequest.id == request_id).first()
    if not mr:
        return None
    mr.matched_seller_ids = candidate_seller_ids
    mr.status = "matching"
    db.commit()
    db.refresh(mr)
    return mr


def award_match(db: Session, request_id: str, seller_id: str, amount_yuan: float) -> MatchTransaction | None:
    """确认撮合成交，生成交易记录."""
    mr = db.query(MatchRequest).filter(MatchRequest.id == request_id).first()
    if not mr or mr.status != "matching":
        return None
    mr.status = "awarded"
    mr.awarded_to = seller_id
    tx = MatchTransaction(
        match_request_id=request_id,
        buyer_id=mr.buyer_id,
        seller_id=seller_id,
        agreed_amount_yuan=amount_yuan,
    )
    db.add(tx)
    db.commit()
    db.refresh(tx)
    return tx


def update_delivery(db: Session, transaction_id: str, delivery_status: str,
                    delivery_date=None) -> MatchTransaction | None:
    """更新交付状态."""
    tx = db.query(MatchTransaction).filter(MatchTransaction.id == transaction_id).first()
    if not tx:
        return None
    tx.delivery_status = delivery_status
    if delivery_date:
        tx.delivery_date = delivery_date
    db.commit()
    db.refresh(tx)
    return tx
