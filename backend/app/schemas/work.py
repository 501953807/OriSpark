"""作品管理 Pydantic 模型."""

from typing import Optional, Any
from datetime import datetime

from pydantic import BaseModel, Field, ConfigDict


class WorkTagCreate(BaseModel):
    tag: str = Field(..., min_length=1, max_length=100)


class WorkTagResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    tag: str
    created_at: datetime


class WorkCreate(BaseModel):
    title: str = Field(default="未命名作品", max_length=500)
    description: Optional[str] = None
    project_id: Optional[str] = None
    tags: list[str] = Field(default_factory=list)
    custom_metadata: Optional[dict] = None


class WorkUpdate(BaseModel):
    title: Optional[str] = Field(None, max_length=500)
    description: Optional[str] = None
    project_id: Optional[str] = None
    tags: Optional[list[str]] = None
    status: Optional[str] = None
    custom_metadata: Optional[dict] = None
    # New fields
    synopsis: Optional[str] = None
    completion_date: Optional[str] = None
    current_stage: Optional[str] = None
    copyright_year: Optional[int] = None
    rights: Optional[dict] = None
    license_type: Optional[str] = Field(None, max_length=50)


class WorkResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    title: str
    file_name: str
    file_size: int
    file_type: str
    file_extension: str
    mime_type: Optional[str] = None
    sha256: Optional[str] = None
    md5: Optional[str] = None
    description: Optional[str] = None
    project_id: Optional[str] = None
    status: str
    is_verified: bool
    thumbnail_path: Optional[str] = None
    thumbnail_url: Optional[str] = None
    file_url: Optional[str] = None
    width: Optional[int] = None
    height: Optional[int] = None
    duration: Optional[float] = None
    import_mode: str = "full"
    parent_work_id: Optional[str] = None
    rights: Optional[dict] = None
    license_type: Optional[str] = None
    custom_metadata: Optional[dict] = None
    exif_data: Optional[dict] = None
    creator_type: str = "illustrator"
    tags: list[WorkTagResponse] = []
    created_at: datetime
    imported_at: datetime
    updated_at: datetime
    # New fields
    synopsis: Optional[str] = None
    completion_date: Optional[str] = None
    current_stage: Optional[str] = None
    copyright_year: Optional[int] = None


class WorkListResponse(BaseModel):
    items: list[WorkResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class ProjectCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    cover_work_id: Optional[str] = None


class ProjectResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    name: str
    description: Optional[str] = None
    cover_work_id: Optional[str] = None
    work_count: int = 0
    created_at: datetime


# -- P1.1.2-P1.1.3: hash-only / lowres upload --

class HashOnlyUpload(BaseModel):
    sha256: str = Field(..., min_length=64, max_length=64)
    file_name: str = Field(..., min_length=1, max_length=500)
    file_size: int = Field(..., ge=0)
    file_type: Optional[str] = "image"
    file_extension: Optional[str] = ""
    title: Optional[str] = Field(None, max_length=500)
    description: Optional[str] = None
    tags: list[str] = Field(default_factory=list)
    project_id: Optional[str] = None
    custom_metadata: Optional[dict] = None


class LowresUpload(BaseModel):
    sha256: str = Field(..., min_length=64, max_length=64)
    file_name: str = Field(..., min_length=1, max_length=500)
    file_size: int = Field(..., ge=0)
    file_type: Optional[str] = "image"
    file_extension: Optional[str] = ""
    title: Optional[str] = Field(None, max_length=500)
    description: Optional[str] = None
    tags: list[str] = Field(default_factory=list)
    project_id: Optional[str] = None
    custom_metadata: Optional[dict] = None
    width: Optional[int] = None
    height: Optional[int] = None


# -- P1.1.8: 版权更新 --

class RightsUpdate(BaseModel):
    rights: Optional[dict] = None
    license_type: Optional[str] = Field(None, max_length=50)


# -- P1.1.19: AI 标签推荐 --

class AiTagRequest(BaseModel):
    file_name: Optional[str] = None
    file_type: Optional[str] = None
    description: Optional[str] = None
    exif_data: Optional[dict] = None
