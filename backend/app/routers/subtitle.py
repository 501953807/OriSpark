"""字幕管理 API 路由 — 对应: docs/modules-v3/01-creative-assets.md
Phase 3: 视频创作者字幕管理
端点: 7 (subtitle)"""

from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Optional

from app.database import get_db
from app.models.subtitle import Subtitle, ProjectFileFormat
from app.schemas.common import ApiResponse
from app.deps import require_auth

router = APIRouter()


class CreateSubtitlePayload(BaseModel):
    work_id: str
    language: str
    format: str = "srt"
    content: Optional[str] = None
    file_path: Optional[str] = None
    is_default: bool = False
    word_count: Optional[int] = None
    duration_seconds: Optional[int] = None


class UpdateSubtitlePayload(BaseModel):
    language: Optional[str] = None
    format_type: Optional[str] = None
    content: Optional[str] = None
    file_path: Optional[str] = None
    is_default: Optional[bool] = None
    word_count: Optional[int] = None
    duration_seconds: Optional[int] = None


class CreateFormatPayload(BaseModel):
    extension: str
    mime_type: str
    category: str = "other"
    name_zh: Optional[str] = None
    supports_metadata: bool = False
    is_active: bool = True


# ============================================================================
# 12.x 字幕 CRUD
# ============================================================================


@router.get("/subtitles", response_model=ApiResponse[list])
def list_subtitles(
    work_id: Optional[str] = None,
    language: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """获取字幕列表."""
    q = db.query(Subtitle)
    if work_id:
        q = q.filter(Subtitle.work_id == work_id)
    if language:
        q = q.filter(Subtitle.language == language)
    subtitles = q.order_by(Subtitle.created_at.desc()).all()
    return ApiResponse(data=[
        {
            "id": s.id,
            "work_id": s.work_id,
            "language": s.language,
            "format": s.format_type,
            "content": s.content,
            "file_path": s.file_path,
            "is_default": s.is_default,
            "word_count": s.word_count,
            "duration_seconds": s.duration_seconds,
            "created_at": s.created_at.isoformat() if s.created_at else None,
            "updated_at": s.updated_at.isoformat() if s.updated_at else None,
        }
        for s in subtitles
    ])


@router.post("/subtitles", response_model=ApiResponse[dict], dependencies=[Depends(require_auth)])
def create_subtitle(payload: CreateSubtitlePayload, db: Session = Depends(get_db)):
    """创建字幕."""
    subtitle = Subtitle(
        work_id=payload.work_id,
        language=payload.language,
        format_type=payload.format,
        content=payload.content,
        file_path=payload.file_path,
        is_default=payload.is_default,
        word_count=payload.word_count,
        duration_seconds=payload.duration_seconds,
    )
    db.add(subtitle)
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise
    db.refresh(subtitle)
    return ApiResponse(data=_to_dict(subtitle), message="字幕创建成功")


@router.get("/subtitles/{subtitle_id}", response_model=ApiResponse[dict])
def get_subtitle(subtitle_id: str, db: Session = Depends(get_db)):
    """获取单个字幕详情."""
    subtitle = db.query(Subtitle).filter(Subtitle.id == subtitle_id).first()
    if not subtitle:
        raise HTTPException(status_code=404, detail="字幕不存在")
    return ApiResponse(data=_to_dict(subtitle))


@router.put("/subtitles/{subtitle_id}", response_model=ApiResponse[dict], dependencies=[Depends(require_auth)])
def update_subtitle(subtitle_id: str, payload: UpdateSubtitlePayload, db: Session = Depends(get_db)):
    """更新字幕."""
    subtitle = db.query(Subtitle).filter(Subtitle.id == subtitle_id).first()
    if not subtitle:
        raise HTTPException(status_code=404, detail="字幕不存在")
    update_data = payload.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(subtitle, key, value)
    subtitle.updated_at = datetime.utcnow()
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise
    db.refresh(subtitle)
    return ApiResponse(data=_to_dict(subtitle), message="字幕更新成功")


@router.delete("/subtitles/{subtitle_id}", response_model=ApiResponse[dict], dependencies=[Depends(require_auth)])
def delete_subtitle(subtitle_id: str, db: Session = Depends(get_db)):
    """删除字幕."""
    subtitle = db.query(Subtitle).filter(Subtitle.id == subtitle_id).first()
    if not subtitle:
        raise HTTPException(status_code=404, detail="字幕不存在")
    db.delete(subtitle)
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise
    return ApiResponse(data={"success": True}, message="字幕已删除")


# ============================================================================
# 12.x 项目文件格式注册表
# ============================================================================


@router.get("/subtitles/formats", response_model=ApiResponse[list])
def list_formats(db: Session = Depends(get_db)):
    """获取支持的项目文件格式列表."""
    formats = db.query(ProjectFileFormat).all()
    return ApiResponse(data=[
        {
            "id": f.id,
            "extension": f.extension,
            "mime_type": f.mime_type,
            "category": f.category,
            "name_zh": f.name_zh,
            "supports_metadata": f.supports_metadata,
            "is_active": f.is_active,
        }
        for f in formats
    ])


@router.post("/subtitles/formats", response_model=ApiResponse[dict], dependencies=[Depends(require_auth)])
def create_format(payload: CreateFormatPayload, db: Session = Depends(get_db)):
    """注册新的文件格式."""
    fmt = ProjectFileFormat(
        extension=payload.extension.lower().lstrip("."),
        mime_type=payload.mime_type,
        category=payload.category,
        name_zh=payload.name_zh,
        supports_metadata=payload.supports_metadata,
        is_active=payload.is_active,
    )
    db.add(fmt)
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise
    db.refresh(fmt)
    return ApiResponse(data=_format_to_dict(fmt), message="格式注册成功")


def _to_dict(s: Subtitle) -> dict:
    return {
        "id": s.id,
        "work_id": s.work_id,
        "language": s.language,
        "format": s.format_type,
        "content": s.content,
        "file_path": s.file_path,
        "is_default": s.is_default,
        "word_count": s.word_count,
        "duration_seconds": s.duration_seconds,
        "created_at": s.created_at.isoformat() if s.created_at else None,
        "updated_at": s.updated_at.isoformat() if s.updated_at else None,
    }


def _format_to_dict(f: ProjectFileFormat) -> dict:
    return {
        "id": f.id,
        "extension": f.extension,
        "mime_type": f.mime_type,
        "category": f.category,
        "name_zh": f.name_zh,
        "supports_metadata": f.supports_metadata,
        "is_active": f.is_active,
        "created_at": f.created_at.isoformat() if f.created_at else None,
    }
