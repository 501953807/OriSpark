from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class CreditRatingCreate(BaseModel):
    user_id: str
    user_type: str  # creator / merchant


class CreditBehaviorRecord(BaseModel):
    user_id: str
    behavior_type: str
    description: Optional[str] = None
    related_transaction_id: Optional[str] = None


class CreditRatingSchema(BaseModel):
    id: str
    user_id: str
    user_type: str
    total_score: int
    tier: str
    transaction_count: int
    successful_transactions: int
    dispute_count: int
    tier_history: Optional[list[dict]] = None
    created_at: Optional[datetime] = None


class CreditBehaviorSchema(BaseModel):
    id: str
    user_id: str
    behavior_type: str
    score_delta: int
    created_at: Optional[datetime] = None
