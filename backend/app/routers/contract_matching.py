"""合约撮合路由 — 挂牌合约发现与推荐推送."""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.contract_matching_service import ContractMatchingService

router = APIRouter(prefix="/contracts", tags=["contract-matching"])


class MatchPushRequest(BaseModel):
    participant_type: str
    participant_id: str
    match_score: float
    match_reason: str = ""


class MatchResponseRequest(BaseModel):
    response: str  # accepted | declined | counter_offer
    counter_offer_json: Optional[str] = None


@router.get("/matches/listed")
async def get_listed_contracts(
    participant_type: str = Query(default="operator"),
    limit: int = Query(default=20, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    """获取可撮合的挂牌合约列表."""
    service = ContractMatchingService()
    return await service.get_listed_contracts(db, participant_type, limit, offset)


@router.post("/{contract_id}/matches/push")
async def push_match(
    contract_id: str,
    body: MatchPushRequest,
    db: Session = Depends(get_db),
):
    """推送撮合推荐给参与方."""
    service = ContractMatchingService()
    matching = await service.push_match(
        db,
        contract_id=contract_id,
        participant_type=body.participant_type,
        participant_id=body.participant_id,
        match_score=body.match_score,
        match_reason=body.match_reason,
    )
    return {"id": matching.id, "status": "pushed"}


@router.post("/matches/{matching_id}/view")
async def record_view(
    matching_id: str,
    db: Session = Depends(get_db),
):
    """记录查看行为."""
    service = ContractMatchingService()
    matching = await service.record_view(db, matching_id)
    return {"id": matching.id, "viewed_at": matching.viewed_at.isoformat()}


@router.post("/matches/{matching_id}/respond")
async def record_response(
    matching_id: str,
    body: MatchResponseRequest,
    db: Session = Depends(get_db),
):
    """记录参与方响应（接受/拒绝/反提案）."""
    service = ContractMatchingService()
    matching = await service.record_response(
        db, matching_id, body.response, body.counter_offer_json
    )
    return {"id": matching.id, "response": matching.response}


@router.get("/participants/{participant_id}/matches")
async def get_participant_matches(
    participant_id: str,
    participant_type: str = Query(default="operator"),
    limit: int = Query(default=20, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    """获取某参与方的所有撮合记录."""
    service = ContractMatchingService()
    return await service.get_participant_matches(
        db, participant_id, participant_type, limit, offset
    )
