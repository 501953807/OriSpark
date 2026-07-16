"""案例知识库服务层."""

from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session

from app.models.case_study import CaseStudy, CaseTag


CATEGORIES = {
    "monetization": {"name_zh": "变现策略", "icon": "revenue"},
    "copyright": {"name_zh": "版权保护", "icon": "shield"},
    "platform_growth": {"name_zh": "平台增长", "icon": "trending_up"},
    "brand_collab": {"name_zh": "品牌合作", "icon": "handshake"},
    "failure_lesson": {"name_zh": "失败教训", "icon": "warning"},
}


def list_cases(
    db: Session, user_id: str, category: Optional[str] = None,
    case_type: Optional[str] = None, tag: Optional[str] = None,
) -> list[CaseStudy]:
    q = db.query(CaseStudy).filter(CaseStudy.user_id == user_id)
    if category:
        q = q.filter(CaseStudy.category == category)
    if case_type:
        q = q.filter(CaseStudy.case_type == case_type)
    if tag:
        q = q.filter(CaseStudy.tags.contains([tag]))
    return q.order_by(CaseStudy.created_at.desc()).all()


def create_case(
    db: Session, user_id: str, title: str, category: str,
    description: Optional[str] = None, key_metrics: Optional[dict] = None,
    tags: Optional[list[str]] = None, takeaways: Optional[list[str]] = None,
    source_url: Optional[str] = None, case_type: str = "success",
) -> dict:
    case = CaseStudy(
        user_id=user_id, title=title, category=category,
        description=description, key_metrics=key_metrics,
        tags=tags or [], takeaways=takeaways or [],
        source_url=source_url, case_type=case_type,
    )
    db.add(case)
    db.flush()
    return {"id": case.id, "title": case.title}


def update_case(db: Session, user_id: str, case_id: str, data: dict) -> bool:
    case = db.query(CaseStudy).filter(
        CaseStudy.id == case_id, CaseStudy.user_id == user_id,
    ).first()
    if not case:
        return False
    for key in ("title", "description", "key_metrics", "tags", "takeaways", "source_url", "case_type"):
        if key in data:
            setattr(case, key, data[key])
    db.flush()
    return True


def delete_case(db: Session, user_id: str, case_id: str) -> bool:
    case = db.query(CaseStudy).filter(
        CaseStudy.id == case_id, CaseStudy.user_id == user_id,
    ).first()
    if not case:
        return False
    db.delete(case)
    db.flush()
    return True


def get_case_stats(db: Session, user_id: str) -> dict:
    """获取案例统计: 按分类/类型分布."""
    cases = db.query(CaseStudy).filter(CaseStudy.user_id == user_id).all()

    by_category = {}
    by_type = {"success": 0, "lesson": 0}
    all_tags: dict[str, int] = {}

    for c in cases:
        by_category[c.category] = by_category.get(c.category, 0) + 1
        by_type[c.case_type] = by_type.get(c.case_type, 0) + 1
        for t in (c.tags or []):
            all_tags[t] = all_tags.get(t, 0) + 1

    # 热门标签 Top 10
    top_tags = sorted(all_tags.items(), key=lambda x: -x[1])[:10]

    return {
        "total": len(cases),
        "by_category": by_category,
        "by_type": by_type,
        "top_tags": [{"name": t, "count": n} for t, n in top_tags],
    }


def search_cases(db: Session, user_id: str, query: str) -> list[CaseStudy]:
    """简单搜索: 标题+描述中包含关键词."""
    like_query = f"%{query}%"
    return db.query(CaseStudy).filter(
        CaseStudy.user_id == user_id,
        (CaseStudy.title.like(like_query) | CaseStudy.description.like(like_query)),
    ).order_by(CaseStudy.created_at.desc()).all()
