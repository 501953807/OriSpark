from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.listing import ListingCreate, ListingUpdate, ListingResponse
from app.services.listing_service import (
    create_listing,
    update_listing,
    mark_sold,
    calculate_profit,
)

router = APIRouter(prefix="/api/listings", tags=["listings"])


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
