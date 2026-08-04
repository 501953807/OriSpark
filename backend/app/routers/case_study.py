"""案例知识库路由."""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user_id
from app.models.case_study import CaseStudy
from app.schemas.case_study import (
    CaseStudyCreate, CaseStudyUpdate, CaseStudyResponse, CaseStats,
)
from app.services.case_study_service import (
    list_cases, create_case, update_case, delete_case,
    get_case_stats, search_cases, CATEGORIES,
)
from app.utils.audit import AuditLog

router = APIRouter(prefix="/case-studies", tags=["case-studies"])


@router.get("/categories")
def get_categories():
    """获取所有分类及其中文名称."""
    return [{"key": k, "name_zh": v["name_zh"], "icon": v["icon"]} for k, v in CATEGORIES.items()]


@router.get("/stats", response_model=CaseStats)
def stats(actor_id: str = Depends(get_current_user_id), db: Session = Depends(get_db)):
    """获取案例统计."""
    result = get_case_stats(db, actor_id)
    AuditLog.log(db, "view_case_stats", f"Viewed stats by {actor_id}", actor_id)
    return result


@router.get("/search")
def search(q: str = Query(..., min_length=1), actor_id: str = Depends(get_current_user_id), db: Session = Depends(get_db)):
    """搜索案例."""
    results = search_cases(db, actor_id, q)
    AuditLog.log(db, "search_cases", f"Searched '{q}' by {actor_id}", actor_id)
    return results


@router.get("", response_model=list[CaseStudyResponse])
def get_list(
    category: Optional[str] = Query(None),
    case_type: Optional[str] = Query(None),
    tag: Optional[str] = Query(None),
    actor_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """获取案例列表，支持按分类/类型/标签过滤."""
    result = list_cases(db, actor_id, category, case_type, tag)
    AuditLog.log(db, "list_cases", f"Listed cases by {actor_id}", actor_id)
    return result


@router.post("", response_model=dict)
def create(data: CaseStudyCreate, actor_id: str = Depends(get_current_user_id), db: Session = Depends(get_db)):
    """创建新案例."""
    if data.category not in CATEGORIES:
        raise HTTPException(status_code=400, detail=f"Invalid category: {data.category}")
    if data.category and data.category not in CATEGORIES:
        raise HTTPException(status_code=400, detail="Invalid category")
    result = create_case(db, actor_id, **data.model_dump())
    AuditLog.log(db, "create_case", f"Created case by {actor_id}", actor_id)
    return result


@router.get("/{case_id}", response_model=CaseStudyResponse)
def get_one(case_id: str, actor_id: str = Depends(get_current_user_id), db: Session = Depends(get_db)):
    """获取单个案例详情."""
    case = db.query(CaseStudy).filter(
        CaseStudy.id == case_id, CaseStudy.user_id == actor_id,
    ).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found or unauthorized")
    # 🔑 Log view
    AuditLog.log(db, "view_case", f"Viewed case {case_id} by {actor_id}", actor_id)
    return case


@router.patch("/{case_id}", response_model=CaseStudyResponse)
def update(case_id: str, data: CaseStudyUpdate, actor_id: str = Depends(get_current_user_id), db: Session = Depends(get_db)):
    """更新案例."""
    # 🔑 权限校验：只有创建者可更新
    case = db.query(CaseStudy).filter(
        CaseStudy.id == case_id, CaseStudy.user_id == actor_id
    ).first()
    if not case:
        raise HTTPException(404, "Case not found or unauthorized")

    if not update_case(db, actor_id, case_id, data.model_dump(exclude_none=True)):
        raise HTTPException(status_code=404, detail="Case not found or failed to update")
    # 🔑 Log update
    AuditLog.log(db, "update_case", f"Updated case {case_id} by {actor_id}", actor_id)
    return db.query(CaseStudy).filter(CaseStudy.id == case_id).first()


@router.delete("/{case_id}")
def remove(case_id: str, actor_id: str = Depends(get_current_user_id), db: Session = Depends(get_db)):
    """删除案例."""
    # 🔑 权限校验：只有创建者可删除
    case = db.query(CaseStudy).filter(
        CaseStudy.id == case_id, CaseStudy.user_id == actor_id
    ).first()
    if not case:
        raise HTTPException(404, "Case not found or unauthorized")

    if not delete_case(db, actor_id, case_id):
        raise HTTPException(status_code=404, detail="Case not found or failed to delete")
    # 🔑 Log delete
    AuditLog.log(db, "delete_case", f"Deleted case {case_id} by {actor_id}", actor_id)
    return {"message": "Deleted"}
