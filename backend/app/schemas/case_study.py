"""案例知识库 Pydantic schemas."""

from pydantic import BaseModel
from typing import Optional


class CaseStudyCreate(BaseModel):
    title: str
    category: str
    description: Optional[str] = None
    key_metrics: Optional[dict] = None
    tags: list[str] = []
    takeaways: list[str] = []
    source_url: Optional[str] = None
    case_type: str = "success"


class CaseStudyUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    key_metrics: Optional[dict] = None
    tags: Optional[list[str]] = None
    takeaways: Optional[list[str]] = None
    source_url: Optional[str] = None
    case_type: Optional[str] = None


class CaseStudyResponse(BaseModel):
    id: str
    title: str
    category: str
    case_type: str
    description: Optional[str] = None
    key_metrics: Optional[dict] = None
    tags: list[str]
    takeaways: list[str]
    source_url: Optional[str] = None
    created_at: str
    updated_at: str


class CaseStats(BaseModel):
    total: int
    by_category: dict
    by_type: dict
    top_tags: list[dict]
