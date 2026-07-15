from datetime import datetime
from sqlalchemy.orm import Session

from app.models.matching_engine import AuctionRecord, Bid, LicensingMatch, BidStatus


def place_bid(db: Session, auction_id: str, buyer_id: str, amount_yuan: float,
              notes: str | None = None) -> Bid | None:
    """提交竞价出价."""
    auction = db.query(AuctionRecord).filter(AuctionRecord.id == auction_id).first()
    if not auction or auction.status != "active":
        return None
    if amount_yuan < auction.current_bid_yuan + auction.min_increment_yuan:
        return None
    if auction.ends_at and datetime.utcnow() > auction.ends_at:
        return None

    bid = Bid(
        auction_id=auction_id,
        buyer_id=buyer_id,
        amount_yuan=amount_yuan,
        status=BidStatus.OPEN,
        notes=notes,
    )
    db.add(bid)
    auction.current_bid_yuan = amount_yuan
    auction.bid_count += 1
    db.commit()
    db.refresh(bid)
    return bid


def close_auction(db: Session, auction_id: str) -> AuctionRecord | None:
    """关闭竞价，确定中标者."""
    auction = db.query(AuctionRecord).filter(AuctionRecord.id == auction_id).first()
    if not auction or auction.status != "active":
        return None
    auction.status = "closed"
    highest = (
        db.query(Bid)
        .filter(Bid.auction_id == auction_id, Bid.status == BidStatus.OPEN)
        .order_by(Bid.amount_yuan.desc())
        .first()
    )
    if highest:
        auction.winner_buyer_id = highest.buyer_id
        auction.winner_amount_yuan = highest.amount_yuan
        highest.status = BidStatus.ACCEPTED
    db.commit()
    db.refresh(auction)
    return auction


def create_licensing_match(db: Session, req: dict) -> LicensingMatch:
    """创建授权撮合要约."""
    match = LicensingMatch(**{k: v for k, v in req.items()})
    db.add(match)
    db.commit()
    db.refresh(match)
    return match


def negotiate_licensing(db: Session, match_id: str, updates: dict) -> LicensingMatch | None:
    """议价更新."""
    match = db.query(LicensingMatch).filter(LicensingMatch.id == match_id).first()
    if not match:
        return None
    for key, value in updates.items():
        if hasattr(match, key):
            setattr(match, key, value)
    db.commit()
    db.refresh(match)
    return match
