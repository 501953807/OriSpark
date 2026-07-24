from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class SCRRatingCreate(BaseModel):
    user_id: str
    rater_id: str
    rating_type: str = "overall"
    initial_score: float = 0.0
    min_consensus: int = 3


class SCRBehaviorAdd(BaseModel):
    rating_id: str
    behavior_type: str
    score_delta: float = 0.0
    description: Optional[str] = None


class SCRTrustLinkUpdate(BaseModel):
    source_user_id: str
    target_user_id: str
    trust_score: float = Field(ge=0.0, le=1.0)
    weight: float = 1.0
    expires_at: Optional[datetime] = None


class SCRRatingSchema(BaseModel):
    id: str
    user_id: str
    rater_id: str
    rating_type: str
    status: str
    tier: str
    raw_score: float
    confidence: float
    consensus_count: int
    min_required_consensus: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None


class SCRBehaviorSchema(BaseModel):
    id: str
    rating_id: str
    user_id: str
    rater_id: str
    behavior_type: str
    score_delta: float
    description: Optional[str] = None
    created_at: Optional[datetime] = None


class SCRTrustLinkSchema(BaseModel):
    id: str
    source_user_id: str
    target_user_id: str
    trust_score: float
    weight: float
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None


class DistributedScoreSchema(BaseModel):
    user_id: str
    total_score: float
    confidence: float
    tier: str
    rating_count: int
