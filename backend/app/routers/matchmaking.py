from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.matchmaking import MatchRequestCreate, MatchRequestSchema, MatchTransactionSchema
from app.services.matchmaking_service import (
    create_match_request, match_creators, award_match, update_delivery,
)
from app.services.matchmaker_service import auto_match, get_match_score

router = APIRouter(prefix="/matchmaking", tags=["matchmaking"])


@router.post("", response_model=MatchRequestSchema)
def post_create(body: MatchRequestCreate, db: Session = Depends(get_db)):
    mr = create_match_request(db, body.model_dump())
    return MatchRequestSchema(id=mr.id, buyer_id=mr.buyer_id, title=mr.title,
                              category=mr.category, status=mr.status,
                              matched_seller_ids=mr.matched_seller_ids,
                              created_at=mr.created_at)


@router.get("", response_model=list[MatchRequestSchema])
def get_all(db: Session = Depends(get_db)):
    mrs = db.query(MatchRequest).order_by(MatchRequest.created_at.desc()).all()
    return [MatchRequestSchema(id=m.id, buyer_id=m.buyer_id, title=m.title,
                               category=m.category, status=m.status,
                               matched_seller_ids=m.matched_seller_ids,
                               created_at=m.created_at) for m in mrs]


@router.post("/{request_id}/match")
def post_match(request_id: str, seller_ids: list[str], db: Session = Depends(get_db)):
    mr = match_creators(db, request_id, seller_ids)
    if not mr:
        raise HTTPException(status_code=404, detail="Match request not found")
    return {"id": mr.id, "matched_count": len(mr.matched_seller_ids or [])}


@router.post("/{request_id}/award")
def post_award(request_id: str, seller_id: str, amount_yuan: float, db: Session = Depends(get_db)):
    tx = award_match(db, request_id, seller_id, amount_yuan)
    if not tx:
        raise HTTPException(status_code=400, detail="Cannot award match")
    return MatchTransactionSchema(
        id=tx.id, match_request_id=tx.match_request_id,
        buyer_id=tx.buyer_id, seller_id=tx.seller_id,
        agreed_amount_yuan=tx.agreed_amount_yuan,
        payment_status=tx.payment_status, delivery_status=tx.delivery_status,
        created_at=tx.created_at,
    )


@router.patch("/transactions/{tx_id}/delivery")
def patch_delivery(tx_id: str, delivery_status: str, db: Session = Depends(get_db)):
    tx = update_delivery(db, tx_id, delivery_status)
    if not tx:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return {"id": tx.id, "delivery_status": tx.delivery_status}


@router.post("/auto-match/{request_id}")
def post_auto_match(request_id: str, db: Session = Depends(get_db)):
    """自动匹配候选卖家."""
    try:
        results = auto_match(db, request_id)
        return {"results": results, "total": len(results)}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/match-score")
def get_match_score_endpoint(listing_id: str, request_id: str, db: Session = Depends(get_db)):
    """查询单个挂牌对某需求的匹配度."""
    try:
        result = get_match_score(db, listing_id, request_id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
