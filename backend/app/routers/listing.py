from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime

from app.database import get_db
from app.models.listing import Listing
from app.schemas.listing import ListingCreate, ListingUpdate, ListingResponse
from app.services.listing_service import (
    create_listing,
    update_listing,
    mark_sold,
    calculate_profit,
)
from app.deps import require_auth

router = APIRouter(prefix="/listings", tags=["listings"])


@router.post("", response_model=ListingResponse)
def post_create_listing(body: ListingCreate, seller_id: str, db: Session = Depends(get_db)):
    listing = create_listing(db, seller_id, body.model_dump())
    return ListingResponse(**{k: getattr(listing, k) for k in ListingResponse.model_fields})


@router.get("", response_model=list[ListingResponse])
def get_active_listings(db: Session = Depends(get_db)):
    """获取所有有效挂牌."""
    listings = (
        db.query(Listing)
        .filter(Listing.status == "active")
        .order_by(Listing.created_at.desc())
        .all()
    )
    return [ListingResponse(**{k: getattr(l, k) for k in ListingResponse.model_fields}) for l in listings]


@router.get("/{listing_id}", response_model=ListingResponse)
def get_listing(listing_id: str, db: Session = Depends(get_db)):
    listing = db.query(Listing).filter(Listing.id == listing_id).first()
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
    return ListingResponse(**{k: getattr(listing, k) for k in ListingResponse.model_fields})


@router.patch("/{listing_id}", response_model=ListingResponse)
def patch_update_listing(listing_id: str, body: ListingUpdate, db: Session = Depends(get_db)):
    updates = body.model_dump(exclude_none=True)
    listing = update_listing(db, listing_id, updates)
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
    return ListingResponse(**{k: getattr(listing, k) for k in ListingResponse.model_fields})


@router.post("/{listing_id}/sell")
def post_sell_listing(listing_id: str, buyer_id: str, db: Session = Depends(get_db)):
    listing = mark_sold(db, listing_id, buyer_id)
    if not listing:
        raise HTTPException(status_code=400, detail="Listing not available for sale")
    profit = calculate_profit(listing.asking_price_yuan, listing.platform_fee_rate_bps, listing.profit_split_percent)
    return {"listing": ListingResponse(**{k: getattr(listing, k) for k in ListingResponse.model_fields}), "profit_split": profit}


@router.post("/profit-estimate")
def post_profit_estimate(asking_price: float, fee_rate_bps: int = 200, split_percent: float = 70.0):
    """费用估算器 — 前端展示给买家的分润预览."""
    return calculate_profit(asking_price, fee_rate_bps, split_percent)


# ============================================================================
# v2: 批量操作 + 高级搜索
# ============================================================================


@router.post("/batch-toggle-status")
def batch_toggle_status(ids: list[str], active: bool, seller_id: str = Depends(require_auth),
                        db: Session = Depends(get_db)):
    """批量上下架."""
    if len(ids) > 100:
        raise HTTPException(status_code=400, detail="最多支持 100 个 ID")

    count = 0
    for listing_id in ids:
        listing = db.query(Listing).filter(
            Listing.id == listing_id,
            Listing.seller_id == seller_id
        ).first()
        if listing:
            listing.status = "active" if active else "archived"
            count += 1
    db.commit()
    return {"updated": count}


@router.post("/batch-update-price")
def batch_update_price(ids: list[str], price_yuan: float, seller_id: str = Depends(require_auth),
                       db: Session = Depends(get_db)):
    """批量调价."""
    if len(ids) > 100:
        raise HTTPException(status_code=400, detail="最多支持 100 个 ID")

    count = 0
    for listing_id in ids:
        listing = db.query(Listing).filter(
            Listing.id == listing_id,
            Listing.seller_id == seller_id
        ).first()
        if listing:
            listing.asking_price_yuan = price_yuan
            count += 1
    db.commit()
    return {"updated": count}


@router.post("/batch-expire")
def batch_expire(ids: list[str], expires_at: str, seller_id: str = Depends(require_auth),
                 db: Session = Depends(get_db)):
    """批量设置过期时间."""
    if len(ids) > 100:
        raise HTTPException(status_code=400, detail="最多支持 100 个 ID")

    try:
        dt = datetime.fromisoformat(expires_at)
    except ValueError:
        raise HTTPException(status_code=400, detail="无效的日期格式")

    count = 0
    for listing_id in ids:
        listing = db.query(Listing).filter(
            Listing.id == listing_id,
            Listing.seller_id == seller_id
        ).first()
        if listing:
            listing.expires_at = dt
            count += 1
    db.commit()
    return {"updated": count}


@router.get("/search")
def search_listings(category: str = None, creator_type: str = None,
                    min_price: float = None, max_price: float = None,
                    tags: str = None, sort_by: str = "created_at",
                    limit: int = 20, offset: int = 0,
                    db: Session = Depends(get_db)):
    """高级搜索挂牌."""
    query = db.query(Listing).filter(Listing.status == "active")

    if category:
        query = query.filter(getattr(Listing, 'category', None) == category)
    if creator_type:
        query = query.filter(getattr(Listing, 'creator_type', None) == creator_type)
    if min_price is not None:
        query = query.filter(Listing.asking_price_yuan >= min_price)
    if max_price is not None:
        query = query.filter(Listing.asking_price_yuan <= max_price)
    if tags:
        tag_list = [t.strip() for t in tags.split(",")]
        for tag in tag_list:
            query = query.filter(Listing.tags.contains(tag))

    sort_map = {
        "created_at": Listing.created_at.desc(),
        "price_asc": Listing.asking_price_yuan.asc(),
        "price_desc": Listing.asking_price_yuan.desc(),
        "popularity": Listing.view_count.desc() if hasattr(Listing, 'view_count') else Listing.created_at.desc(),
    }
    order_by = sort_map.get(sort_by, Listing.created_at.desc())
    query = query.order_by(order_by)

    listings = query.limit(limit).offset(offset).all()
    return {
        "listings": [ListingResponse(**{k: getattr(l, k) for k in ListingResponse.model_fields}) for l in listings],
        "total": len(listings),
    }
