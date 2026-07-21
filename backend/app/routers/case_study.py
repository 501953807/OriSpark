"""案例知识库路由."""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.case_study import (
    CaseStudyCreate, CaseStudyUpdate, CaseStudyResponse, CaseStats,
)
from app.services.case_study_service import (
    list_cases, create_case, update_case, delete_case,
    get_case_stats, search_cases, CATEGORIES,
)

router = APIRouter(prefix="/case-studies", tags=["case-studies"])


@router.get("/categories")
def get_categories():
    """获取所有分类及其中文名称."""
    return [{"key": k, "name_zh": v["name_zh"], "icon": v["icon"]} for k, v in CATEGORIES.items()]


@router.get("", response_model=list[CaseStudyResponse])
def get_list(
    category: Optional[str] = Query(None),
    case_type: Optional[str] = Query(None),
    tag: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    """获取案例列表，支持按分类/类型/标签过滤."""
    return list_cases(db, "current_user", category, case_type, tag)


@router.post("", response_model=dict)
def create(data: CaseStudyCreate, db: Session = Depends(get_db)):
    """创建新案例."""
    if data.category not in CATEGORIES:
        raise HTTPException(status_code=400, detail=f"Invalid category: {data.category}")
    return create_case(db, "current_user", **data.model_dump())


@router.get("/{case_id}", response_model=CaseStudyResponse)
def get_one(case_id: str, db: Session = Depends(get_db)):
    """获取单个案例详情."""
    case = db.query(CaseStudy).filter(
        CaseStudy.id == case_id, CaseStudy.user_id == "current_user",
    ).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    return case


@router.patch("/{case_id}", response_model=CaseStudyResponse)
def update(case_id: str, data: CaseStudyUpdate, db: Session = Depends(get_db)):
    """更新案例."""
    if not update_case(db, "current_user", case_id, data.model_dump(exclude_none=True)):
        raise HTTPException(status_code=404, detail="Case not found")
    return db.query(CaseStudy).filter(CaseStudy.id == case_id).first()


@router.delete("/{case_id}")
def remove(case_id: str, db: Session = Depends(get_db)):
    """删除案例."""
    if not delete_case(db, "current_user", case_id):
        raise HTTPException(status_code=404, detail="Case not found")
    return {"message": "Deleted"}


@router.get("/stats", response_model=CaseStats)
def stats(db: Session = Depends(get_db)):
    """获取案例统计."""
    return get_case_stats(db, "current_user")


@router.get("/search")
def search(q: str = Query(..., min_length=1), db: Session = Depends(get_db)):
    """搜索案例."""
    return search_cases(db, "current_user", q)
