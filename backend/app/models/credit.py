import enum
import uuid
from datetime import datetime

from sqlalchemy import Column, String, DateTime, Float, ForeignKey, Integer, Text, JSON
from app.database import Base


class CreditTier(enum.StrEnum):
    NEWBIE = "newbie"           # 新手
    GOOD = "good"               # 良好
    EXCELLENT = "excellent"     # 优秀
    DIAMOND = "diamond"         # 钻石


class BehaviorType(enum.StrEnum):
    TRANSACTION_COMPLETED = "transaction_completed"
    TRANSACTION_CANCELLED = "transaction_cancelled"
    DISPUTE_RAISED = "dispute_raised"
    DISPUTE_LOST = "dispute_lost"
    ON_TIME_DELIVERY = "on_time_delivery"
    LATE_DELIVERY = "late_delivery"
    PAYMENT_ON_TIME = "payment_on_time"
    PAYMENT_LATE = "payment_late"
    REVIEW_RECEIVED = "review_received"
    BAD_REVIEW = "bad_review"
    CONTRACT_SIGNED = "contract_signed"
    CERTIFICATION_CREATED = "certification_created"


class CreditRating(Base):
    """创作者/商家信用评级表."""
    __tablename__ = "credit_ratings"

    id = Column(String(32), primary_key=True, default=lambda: uuid.uuid4().hex)
    user_id = Column(String(32), nullable=False, index=True)
    user_type = Column(String(20), nullable=False)  # creator / merchant
    total_score = Column(Integer, default=100)  # 基础分100
    transaction_count = Column(Integer, default=0)
    successful_transactions = Column(Integer, default=0)
    dispute_count = Column(Integer, default=0)
    late_delivery_count = Column(Integer, default=0)
    avg_response_hours = Column(Float, nullable=True)
    tier = Column(String(20), default=CreditTier.NEWBIE)
    tier_history = Column(JSON, nullable=True)  # [{"tier": "good", "at": "..."}]
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class CreditBehavior(Base):
    """信用行为记录 — 每次交易/履约事件产生一条行为记录."""
    __tablename__ = "credit_behaviors"

    id = Column(String(32), primary_key=True, default=lambda: uuid.uuid4().hex)
    rating_id = Column(String(32), ForeignKey("credit_ratings.id"), nullable=True, index=True)
    user_id = Column(String(32), nullable=False, index=True)
    behavior_type = Column(String(50), nullable=False)
    score_delta = Column(Integer, default=0)  # +5, -10, etc.
    related_transaction_id = Column(String(32), nullable=True)
    description = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


# 行为分数权重
BEHAVIOR_SCORES = {
    BehaviorType.TRANSACTION_COMPLETED: 5,
    BehaviorType.TRANSACTION_CANCELLED: -3,
    BehaviorType.DISPUTE_RAISED: -2,
    BehaviorType.DISPUTE_LOST: -10,
    BehaviorType.ON_TIME_DELIVERY: 3,
    BehaviorType.LATE_DELIVERY: -5,
    BehaviorType.PAYMENT_ON_TIME: 2,
    BehaviorType.PAYMENT_LATE: -5,
    BehaviorType.REVIEW_RECEIVED: 1,
    BehaviorType.BAD_REVIEW: -8,
    BehaviorType.CONTRACT_SIGNED: 3,
    BehaviorType.CERTIFICATION_CREATED: 2,
}

# 信用等级阈值
TIER_THRESHOLDS = {
    CreditTier.DIAMOND: 180,
    CreditTier.EXCELLENT: 140,
    CreditTier.GOOD: 100,
    CreditTier.NEWBIE: 0,
}


def calculate_tier(score: int) -> str:
    """根据总分确定信用等级."""
    for tier, threshold in TIER_THRESHOLDS.items():
        if score >= threshold:
            return tier
    return CreditTier.NEWBIE


def apply_behavior(rating: CreditRating, behavior_type: str, score_delta: int) -> CreditRating:
    """应用一条行为到信用评分."""
    rating.total_score += score_delta
    rating.updated_at = datetime.utcnow()

    if behavior_type == BehaviorType.TRANSACTION_COMPLETED:
        rating.transaction_count += 1
        rating.successful_transactions += 1
    elif behavior_type == BehaviorType.TRANSACTION_CANCELLED:
        rating.transaction_count += 1
    elif behavior_type == BehaviorType.DISPUTE_LOST:
        rating.dispute_count += 1
    elif behavior_type == BehaviorType.LATE_DELIVERY:
        rating.late_delivery_count += 1

    new_tier = calculate_tier(rating.total_score)
    if new_tier != rating.tier:
        history = rating.tier_history or []
        history.append({"tier": new_tier, "at": datetime.utcnow().isoformat()})
        rating.tier_history = history
        rating.tier = new_tier

    return rating
