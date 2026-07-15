from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from app.models.listing import Listing, ListingStatus


def create_listing(db: Session, seller_id: str, req: dict) -> Listing:
    """创建挂牌."""
    expires_at = None
    if req.get("expires_days"):
        expires_at = datetime.utcnow() + timedelta(days=req["expires_days"])

    listing = Listing(
        work_id=req["work_id"],
        seller_id=seller_id,
        title=req["title"],
        description=req.get("description"),
        asking_price_yuan=req["asking_price_yuan"],
        original_cost_yuan=req.get("original_cost_yuan"),
        min_price_yuan=req.get("min_price_yuan"),
        max_discount_percent=req.get("max_discount_percent", 10.0),
        quantity_total=req.get("quantity_total", 1),
        expires_at=expires_at,
        profit_split_percent=req.get("profit_split_percent", 70.0),
        platform_fee_rate_bps=int(req.get("platform_fee_rate_bps", 200)),
        tags=req.get("tags"),
    )
    db.add(listing)
    db.commit()
    db.refresh(listing)
    return listing


def update_listing(db: Session, listing_id: str, updates: dict) -> Listing | None:
    """更新挂牌信息."""
    listing = db.query(Listing).filter(Listing.id == listing_id).first()
    if not listing:
        return None
    for key, value in updates.items():
        if hasattr(listing, key) and key not in ("id", "work_id", "seller_id", "created_at"):
            setattr(listing, key, value)
    listing.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(listing)
    return listing


def mark_sold(db: Session, listing_id: str, buyer_id: str) -> Listing | None:
    """标记挂牌成交."""
    listing = db.query(Listing).filter(Listing.id == listing_id).first()
    if not listing or listing.status != ListingStatus.ACTIVE:
        return None
    listing.status = ListingStatus.SOLD
    listing.buyer_id = buyer_id
    listing.sold_at = datetime.utcnow()
    listing.quantity_sold += 1
    db.commit()
    db.refresh(listing)
    return listing


def calculate_profit(asking_price: float, fee_rate_bps: int, split_percent: float) -> dict:
    """计算成交后各方分润.

    Returns: {platform_fee, creator_earning, net_profit}
    """
    platform_fee = round(asking_price * fee_rate_bps / 10000, 2)
    creator_earning = round((asking_price - platform_fee) * split_percent / 100, 2)
    net_profit = round(creator_earning, 2)
    return {
        "platform_fee_yuan": platform_fee,
        "creator_earning_yuan": net_profit,
        "net_profit_yuan": net_profit,
    }


def expire_expired_listings(db: Session):
    """过期处理 — 将过期的挂牌标记为 expired."""
    now = datetime.utcnow()
    result = (
        db.query(Listing)
        .filter(
            Listing.status == ListingStatus.ACTIVE,
            Listing.expires_at < now,
        )
        .update({"status": ListingStatus.EXPIRED})
    )
    db.commit()
    return result
