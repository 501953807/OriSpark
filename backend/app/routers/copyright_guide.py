"""版权登记指南路由."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user_id, is_admin
from app.models.copyright_guide import GuideRegistration
from app.schemas.copyright_guide import (
    RegistrationCreate, RegistrationUpdate, RegistrationResponse,
    RegistrationGuide, RegistrationSummary,
)
from app.services.copyright_guide_service import (
    get_or_create_guides, get_guide, create_registration,
    update_registration, list_registrations, get_registration_summary,
)
from app.utils.audit import AuditLog

router = APIRouter(prefix="/copyright-guide", tags=["copyright-guide"])


@router.get("/guides")
def get_all_guides(db: Session = Depends(get_db)):
    """获取所有登记指南."""
    guides = get_or_create_guides(db)
    return [
        {
            "id": g.id,
            "work_type": g.work_type,
            "title_zh": g.title_zh,
            "steps": g.steps,
            "estimated_days": g.estimated_days,
            "estimated_fee_yuan": g.estimated_fee_yuan,
        }
        for g in guides
    ]


@router.get("/guides/{work_type}")
def get_guide(work_type: str, db: Session = Depends(get_db)):
    """获取特定作品类型的登记指南."""
    guide = get_guide(db, work_type)
    if not guide:
        raise HTTPException(status_code=404, detail="Guide not found")
    return {
        "id": guide.id,
        "work_type": guide.work_type,
        "title_zh": guide.title_zh,
        "steps": guide.steps,
        "estimated_days": guide.estimated_days,
        "estimated_fee_yuan": guide.estimated_fee_yuan,
    }


@router.post("/registrations", response_model=dict)
def create(data: RegistrationCreate, actor_id: str = Depends(get_current_user_id), db: Session = Depends(get_db)):
    """创建版权登记申请."""
    return create_registration(db, actor_id, data.title, data.work_type, data.registration_type)


@router.get("/registrations", response_model=list[RegistrationResponse])
def get_list(actor_id: str = Depends(get_current_user_id), db: Session = Depends(get_db)):
    """获取登记记录列表."""
    result = list_registrations(db, actor_id)
    AuditLog.log(db, "list_registrations", f"Listed registrations for user {actor_id}", actor_id)
    return result


@router.patch("/registrations/{reg_id}", response_model=RegistrationResponse)
def update(reg_id: str, data: RegistrationUpdate, actor_id: str = Depends(get_current_user_id), db: Session = Depends(get_db)):
    """更新登记申请."""
    # 🔑 权限校验：只有用户自己或管理员可更新自己的登记
    reg = db.query(GuideRegistration).filter(GuideRegistration.id == reg_id).first()
    if not reg:
        raise HTTPException(status_code=404, detail="Registration not found")
    if reg.actor_id != actor_id and not is_admin(actor_id):
        raise HTTPException(403, "Forbidden: You cannot update this registration")
    if not update_registration(db, actor_id, reg_id, data.model_dump(exclude_none=True)):
        raise HTTPException(status_code=404, detail="Registration not found")
    # 🔑 Log update
    AuditLog.log(db, "update_registration", f"Updated registration {reg_id}", actor_id)
    return db.query(GuideRegistration).filter(
        GuideRegistration.id == reg_id,
    ).first()


@router.get("/summary", response_model=RegistrationSummary)
def summary(actor_id: str = Depends(get_current_user_id), db: Session = Depends(get_db)):
    """获取登记概览统计."""
    # 🔑 Log view summary
    AuditLog.log(db, "view_registration_summary", f"Viewed summary for user {actor_id}", actor_id)
    return get_registration_summary(db, actor_id)
