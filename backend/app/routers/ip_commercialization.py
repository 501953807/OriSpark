from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.ip_commercialization_service import create_ip_assessment, estimate_brand_premium

router = APIRouter(prefix="/api/ip-commercialization", tags=["ip-commercialization"])


@router.post("/assess", response_model=dict)
def post_ip_assessment(data: dict, db: Session = Depends(get_db)):
    asset = create_ip_assessment(db, data)
    return {"id": asset.id, "overall_score": asset.overall_score}


@router.post("/brand-premium")
def calc_brand_premium(follower_count: int, engagement_rate: float, category: str):
    premium = estimate_brand_premium(follower_count, engagement_rate, category)
    return {"estimated_premium_percent": premium}
