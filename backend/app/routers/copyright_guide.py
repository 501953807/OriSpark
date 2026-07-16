"""版权登记指南路由."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.copyright_guide import (
    RegistrationCreate, RegistrationUpdate, RegistrationResponse,
    RegistrationGuide as GuideSchema, RegistrationSummary,
)
from app.services.copyright_guide_service import (
    get_or_create_guides, get_guide, create_registration,
    update_registration, list_registrations, get_registration_summary,
)

router = APIRouter(prefix="/api/copyright-guide", tags=["copyright-guide"])


@router.get("/guides")
def get_all_guides(db: Session = Depends(get_db)):
    """获取所有登记指南."""
    return get_or_create_guides(db)


@router.get("/guides/{work_type}")
def get_guide(work_type: str, db: Session = Depends(get_db)):
    """获取特定作品类型的登记指南."""
    guide = get_guide(db, work_type)
    if not guide:
        raise HTTPException(status_code=404, detail="Guide not found")
    return guide


@router.post("/registrations", response_model=dict)
def create(data: RegistrationCreate, db: Session = Depends(get_db)):
    """创建版权登记申请."""
    return create_registration(db, "current_user", data.title, data.work_type, data.registration_type)


@router.get("/registrations", response_model=list[RegistrationResponse])
def get_list(db: Session = Depends(get_db)):
    """获取登记记录列表."""
    return list_registrations(db, "current_user")


@router.patch("/registrations/{reg_id}", response_model=RegistrationResponse)
def update(reg_id: str, data: RegistrationUpdate, db: Session = Depends(get_db)):
    """更新登记申请."""
    if not update_registration(db, "current_user", reg_id, data.model_dump(exclude_none=True)):
        raise HTTPException(status_code=404, detail="Registration not found")
    return db.query(CopyrightRegistration).filter(
        CopyrightRegistration.id == reg_id,
    ).first()


@router.get("/summary", response_model=RegistrationSummary)
def summary(db: Session = Depends(get_db)):
    """获取登记概览统计."""
    return get_registration_summary(db, "current_user")
