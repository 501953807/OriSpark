from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.matching_engine import (
    AuctionCreate, AuctionBidRequest, AuctionResponse,
    LicensingMatchCreate,
)
from app.services.matching_service import (
    place_bid, close_auction, create_licensing_match, negotiate_licensing,
)

router = APIRouter(prefix="/api/matching", tags=["matching"])


# --- Auction endpoints ---
@router.post("/auctions", response_model=AuctionResponse)
def post_create_auction(body: AuctionCreate, db: Session = Depends(get_db)):
    from app.models.matching_engine import AuctionRecord
    record = AuctionRecord(**body.model_dump())
    db.add(record)
    db.commit()
    db.refresh(record)
    return AuctionResponse(
        id=record.id, listing_id=record.listing_id, work_id=record.work_id,
        current_bid_yuan=record.current_bid_yuan, bid_count=record.bid_count,
        ends_at=record.ends_at, status=record.status,
        winner_buyer_id=record.winner_buyer_id,
    )


@router.post("/auctions/{auction_id}/bid")
def post_place_bid(auction_id: str, body: AuctionBidRequest, db: Session = Depends(get_db)):
    bid = place_bid(db, auction_id, body.buyer_id, body.amount_yuan, body.notes)
    if not bid:
        raise HTTPException(status_code=400, detail="Invalid bid: auction closed, insufficient amount, or expired")
    return {"bid_id": bid.id, "amount_yuan": bid.amount_yuan}


@router.post("/auctions/{auction_id}/close")
def post_close_auction(auction_id: str, db: Session = Depends(get_db)):
    auction = close_auction(db, auction_id)
    if not auction:
        raise HTTPException(status_code=400, detail="Cannot close auction")
    return {"auction_id": auction.id, "winner": auction.winner_buyer_id,
            "winning_amount": auction.winner_amount_yuan}


# --- Licensing endpoints ---
@router.post("/licensing", response_model=dict)
def post_create_licensing(body: LicensingMatchCreate, db: Session = Depends(get_db)):
    match = create_licensing_match(db, body.model_dump())
    return {"id": match.id, "status": match.status}


@router.patch("/licensing/{match_id}")
def patch_negotiate_licensing(match_id: str, updates: dict, db: Session = Depends(get_db)):
    match = negotiate_licensing(db, match_id, updates)
    if not match:
        raise HTTPException(status_code=404, detail="Licensing match not found")
    return {"id": match.id, "status": match.status}
