from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.ai_training_license import AITrainingLicense
from app.schemas.ai_training import AILicenseUpdate, AILicenseResponse
from app.services.ai_training_service import upsert_ai_license

router = APIRouter(prefix="/ai-training", tags=["ai-training"])


@router.put("/{work_id}", response_model=AILicenseResponse)
def update_ai_license(work_id: str, req: AILicenseUpdate, db: Session = Depends(get_db)):
    license = upsert_ai_license(
        db, work_id=req.work_id,
        enabled=req.enabled,
        cc_protocol=req.cc_protocol,
        price_per_use_cents=req.price_per_use_cents or 5,
    )
    return license


@router.get("/{work_id}", response_model=AILicenseResponse)
def get_ai_license(work_id: str, db: Session = Depends(get_db)):
    license = db.query(AITrainingLicense).filter(
        AITrainingLicense.work_id == work_id
    ).first()
    if not license:
        raise HTTPException(404, "未找到AI授权配置")
    return license
