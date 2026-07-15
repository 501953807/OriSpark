from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.work import Work
from app.schemas.certification import (
    CertificationRequest,
    CertificationResponse,
)
from app.services.certification_service import batch_certify, certify_single

router = APIRouter(prefix="/api/certification", tags=["certification"])


@router.post("/single", response_model=CertificationResponse)
def post_single_certification(req: CertificationRequest, db: Session = Depends(get_db)):
    work = db.query(Work).filter(Work.id == req.work_id).first()
    if not work:
        raise HTTPException(404, "作品不存在")
    record = certify_single(db, work)
    return record


@router.post("/batch", response_model=dict)
def post_batch_certification(req: CertificationRequest, db: Session = Depends(get_db)):
    """批量存证接口."""
    if not req.batch:
        raise HTTPException(400, "需要提供work_ids列表")
    result = batch_certify(db, req.batch)
    return result
