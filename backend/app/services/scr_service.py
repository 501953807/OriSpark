"""SCR 分布式信誉系统服务."""

import uuid
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy.orm import Session

from app.models.scr import (
    SCRRating, SCRBehavior, SCRTrustLink, apply_scr_behavior, calculate_scr_tier
)


class SCRRatingService:
    """SCR 分布式信誉评级服务."""

    @classmethod
    def create_rating(
        cls, db: Session, user_id: str, rater_id: str,
        rating_type: str = "overall", initial_score: float = 0.0,
        min_consensus: int = 3,
    ) -> SCRRating:
        """创建新的 SCR 评级."""
        rating = SCRRating(
            id=str(uuid.uuid4().hex), user_id=user_id, rater_id=rater_id,
            rating_type=rating_type, status="active", tier="draft",
            raw_score=initial_score, confidence=0.0, consensus_count=0,
            min_required_consensus=min_consensus,
            expires_at=datetime.utcnow() + timedelta(days=90),
        )
        db.add(rating)
        db.commit()
        db.refresh(rating)
        return rating

    @classmethod
    def get_rating(cls, db: Session, rating_id: str) -> Optional[SCRRating]:
        """获取评级详情."""
        return db.query(SCRRating).filter(SCRRating.id == rating_id).first()

    @classmethod
    def get_ratings_by_user(cls, db: Session, user_id: str) -> list[SCRRating]:
        """获取用户的所有活跃评级."""
        return db.query(SCRRating).filter(
            SCRRating.user_id == user_id, SCRRating.status == "active"
        ).order_by(SCRRating.updated_at.desc()).all()

    @classmethod
    def add_behavior(
        cls, db: Session, rating_id: str, behavior_type: str,
        score_delta: float, description: Optional[str] = None,
    ) -> tuple[SCRRating, SCRBehavior]:
        """添加行为记录并更新评分."""
        rating = cls.get_rating(db, rating_id)
        if not rating:
            raise ValueError("评级不存在")

        if rating.expires_at and rating.expires_at < datetime.utcnow():
            rating.status = "suspended"

        behavior = SCRBehavior(
            id=str(uuid.uuid4().hex), rating_id=rating_id,
            user_id=rating.user_id, rater_id=rating.rater_id,
            behavior_type=behavior_type, score_delta=score_delta,
            description=description, created_at=datetime.utcnow(),
        )
        db.add(behavior)

        rating = apply_scr_behavior(rating, behavior_type, score_delta)
        rating.consensus_count += 1
        rating.confidence = min(1.0, rating.consensus_count / rating.min_required_consensus)

        if rating.consensus_count >= rating.min_required_consensus:
            rating.tier = "confirmed"

        db.commit()
        db.refresh(rating)
        return rating, behavior

    @classmethod
    def update_trust_link(
        cls, db: Session, source_user_id: str, target_user_id: str,
        trust_score: float, weight: float = 1.0,
        expires_at: Optional[datetime] = None,
        rating_id: Optional[str] = None,
    ) -> SCRTrustLink:
        """更新信任链接."""
        link = db.query(SCRTrustLink).filter(
            SCRTrustLink.source_user_id == source_user_id,
            SCRTrustLink.target_user_id == target_user_id,
        ).first()

        if not link:
            link = SCRTrustLink(
                id=str(uuid.uuid4().hex), rating_id=rating_id or "unknown",
                source_user_id=source_user_id, target_user_id=target_user_id,
                trust_score=trust_score, weight=weight, created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(), expires_at=expires_at,
            )
            db.add(link)
        else:
            link.trust_score = trust_score
            link.weight = weight
            link.updated_at = datetime.utcnow()
            link.expires_at = expires_at

        db.commit()
        db.refresh(link)
        return link

    @classmethod
    def get_trust_links(cls, db: Session, user_id: str) -> list[SCRTrustLink]:
        """获取用户的信任链接."""
        return db.query(SCRTrustLink).filter(
            SCRTrustLink.source_user_id == user_id
        ).order_by(SCRTrustLink.trust_score.desc()).all()

    @classmethod
    def calculate_distributed_score(cls, db: Session, user_id: str) -> dict:
        """计算分布式信誉分数."""
        ratings = cls.get_ratings_by_user(db, user_id)
        if not ratings:
            return {"user_id": user_id, "total_score": 0.0, "confidence": 0.0, "tier": "unrated", "rating_count": 0}

        total_score = sum(r.raw_score * r.confidence for r in ratings)
        total_confidence = sum(r.confidence for r in ratings)
        avg_confidence = total_confidence / len(ratings) if ratings else 0.0
        weighted_score = total_score / total_confidence if total_confidence > 0 else 0.0

        return {
            "user_id": user_id, "total_score": round(weighted_score, 2),
            "confidence": round(avg_confidence, 2), "tier": calculate_scr_tier(weighted_score),
            "rating_count": len(ratings),
        }

    @classmethod
    def propagate_trust(
        cls, db: Session, source_user_id: str, target_user_id: str,
        propagation_factor: float = 0.5,
    ) -> float:
        """传播信任关系."""
        source_links = cls.get_trust_links(db, source_user_id)
        if not source_links:
            return 0.0

        avg_trust = sum(link.trust_score for link in source_links) / len(source_links)
        propagated_score = avg_trust * propagation_factor
        cls.update_trust_link(db, source_user_id, target_user_id, propagated_score)
        return propagated_score

    @classmethod
    def revoke_rating(cls, db: Session, rating_id: str) -> SCRRating:
        """撤销评级."""
        rating = cls.get_rating(db, rating_id)
        if not rating:
            raise ValueError("评级不存在")
        rating.status = "revoked"
        rating.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(rating)
        return rating

    @classmethod
    def suspend_rating(cls, db: Session, rating_id: str) -> SCRRating:
        """暂停评级."""
        rating = cls.get_rating(db, rating_id)
        if not rating:
            raise ValueError("评级不存在")
        rating.status = "suspended"
        rating.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(rating)
        return rating
