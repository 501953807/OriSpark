"""SCR 分布式信誉系统 API 路由."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.scr import (
    SCRRatingCreate,
    SCRBehaviorAdd,
    SCRTrustLinkUpdate,
    SCRRatingSchema,
    SCRBehaviorSchema,
    SCRTrustLinkSchema,
    DistributedScoreSchema,
)
from app.services.scr_service import SCRRatingService

router = APIRouter(prefix="/scr", tags=["SCR"])


@router.post("/rating", response_model=SCRRatingSchema)
def post_create_rating(body: SCRRatingCreate, db: Session = Depends(get_db)):
    """创建新的 SCR 评级."""
    rating = SCRRatingService.create_rating(
        db=db,
        user_id=body.user_id,
        rater_id=body.rater_id,
        rating_type=body.rating_type,
        initial_score=body.initial_score,
        min_consensus=body.min_consensus,
    )
    return SCRRatingSchema(
        id=rating.id, user_id=rating.user_id, rater_id=rating.rater_id,
        rating_type=rating.rating_type, status=rating.status, tier=rating.tier,
        raw_score=rating.raw_score, confidence=rating.confidence,
        consensus_count=rating.consensus_count,
        min_required_consensus=rating.min_required_consensus,
        created_at=rating.created_at, updated_at=rating.updated_at,
        expires_at=rating.expires_at,
    )


@router.get("/rating/{rating_id}", response_model=SCRRatingSchema)
def get_rating(rating_id: str, db: Session = Depends(get_db)):
    """获取 SCR 评级详情."""
    rating = SCRRatingService.get_rating(db, rating_id)
    if not rating:
        raise HTTPException(status_code=404, detail="SCR rating not found")
    return SCRRatingSchema(
        id=rating.id, user_id=rating.user_id, rater_id=rating.rater_id,
        rating_type=rating.rating_type, status=rating.status, tier=rating.tier,
        raw_score=rating.raw_score, confidence=rating.confidence,
        consensus_count=rating.consensus_count,
        min_required_consensus=rating.min_required_consensus,
        created_at=rating.created_at, updated_at=rating.updated_at,
        expires_at=rating.expires_at,
    )


@router.get("/ratings/user/{user_id}", response_model=list[SCRRatingSchema])
def get_user_ratings(user_id: str, db: Session = Depends(get_db)):
    """获取用户的所有活跃 SCR 评级."""
    ratings = SCRRatingService.get_ratings_by_user(db, user_id)
    return [
        SCRRatingSchema(
            id=r.id, user_id=r.user_id, rater_id=r.rater_id,
            rating_type=r.rating_type, status=r.status, tier=r.tier,
            raw_score=r.raw_score, confidence=r.confidence,
            consensus_count=r.consensus_count,
            min_required_consensus=r.min_required_consensus,
            created_at=r.created_at, updated_at=r.updated_at,
            expires_at=r.expires_at,
        )
        for r in ratings
    ]


@router.post("/behavior", response_model=dict)
def post_add_behavior(body: SCRBehaviorAdd, db: Session = Depends(get_db)):
    """添加 SCR 行为记录并更新评分."""
    rating, behavior = SCRRatingService.add_behavior(
        db=db, rating_id=body.rating_id, behavior_type=body.behavior_type,
        score_delta=body.score_delta, description=body.description,
    )
    return {
        "rating": {
            "id": rating.id, "user_id": rating.user_id, "tier": rating.tier,
            "raw_score": rating.raw_score, "confidence": rating.confidence,
            "consensus_count": rating.consensus_count,
        },
        "behavior": {
            "id": behavior.id, "behavior_type": behavior.behavior_type,
            "score_delta": behavior.score_delta,
        },
    }


@router.put("/trust-link", response_model=SCRTrustLinkSchema)
def put_update_trust_link(body: SCRTrustLinkUpdate, db: Session = Depends(get_db)):
    """更新信任链接."""
    link = SCRRatingService.update_trust_link(
        db=db, source_user_id=body.source_user_id, target_user_id=body.target_user_id,
        trust_score=body.trust_score, weight=body.weight, expires_at=body.expires_at,
    )
    return SCRTrustLinkSchema(
        id=link.id, source_user_id=link.source_user_id,
        target_user_id=link.target_user_id, trust_score=link.trust_score,
        weight=link.weight, created_at=link.created_at,
        updated_at=link.updated_at, expires_at=link.expires_at,
    )


@router.get("/trust-links/{user_id}", response_model=list[SCRTrustLinkSchema])
def get_trust_links(user_id: str, db: Session = Depends(get_db)):
    """获取用户的信任链接列表."""
    links = SCRRatingService.get_trust_links(db, user_id)
    return [
        SCRTrustLinkSchema(
            id=l.id, source_user_id=l.source_user_id, target_user_id=l.target_user_id,
            trust_score=l.trust_score, weight=l.weight, created_at=l.created_at,
            updated_at=l.updated_at, expires_at=l.expires_at,
        )
        for l in links
    ]


@router.get("/distributed-score/{user_id}", response_model=DistributedScoreSchema)
def get_distributed_score(user_id: str, db: Session = Depends(get_db)):
    """计算用户的分布式信誉分数."""
    result = SCRRatingService.calculate_distributed_score(db, user_id)
    return DistributedScoreSchema(
        user_id=result["user_id"], total_score=result["total_score"],
        confidence=result["confidence"], tier=result["tier"],
        rating_count=result["rating_count"],
    )


@router.post("/revoke/{rating_id}", response_model=SCRRatingSchema)
def revoke_rating(rating_id: str, db: Session = Depends(get_db)):
    """撤销 SCR 评级."""
    rating = SCRRatingService.revoke_rating(db, rating_id)
    return SCRRatingSchema(
        id=rating.id, user_id=rating.user_id, rater_id=rating.rater_id,
        rating_type=rating.rating_type, status=rating.status, tier=rating.tier,
        raw_score=rating.raw_score, confidence=rating.confidence,
        consensus_count=rating.consensus_count,
        min_required_consensus=rating.min_required_consensus,
        created_at=rating.created_at, updated_at=rating.updated_at,
        expires_at=rating.expires_at,
    )


@router.post("/suspend/{rating_id}", response_model=SCRRatingSchema)
def suspend_rating(rating_id: str, db: Session = Depends(get_db)):
    """暂停 SCR 评级."""
    rating = SCRRatingService.suspend_rating(db, rating_id)
    return SCRRatingSchema(
        id=rating.id, user_id=rating.user_id, rater_id=rating.rater_id,
        rating_type=rating.rating_type, status=rating.status, tier=rating.tier,
        raw_score=rating.raw_score, confidence=rating.confidence,
        consensus_count=rating.consensus_count,
        min_required_consensus=rating.min_required_consensus,
        created_at=rating.created_at, updated_at=rating.updated_at,
        expires_at=rating.expires_at,
    )
