"""音乐人 API 路由.

Musician v4: Albums, Music Releases, Split Sheets CRUD endpoints.
"""

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.album import Album
from app.models.music_release import MusicRelease
from app.models.split_sheet import SplitSheet
from app.schemas.common import ApiResponse
from app.schemas.musician import (
    AlbumCreate,
    AlbumSchema,
    MusicReleaseCreate,
    MusicReleaseUpdate,
    MusicReleaseSchema,
    SplitSheetCreate,
    SplitSheetUpdate,
    SplitSheetSchema,
)
from app.deps import require_auth

router = APIRouter()


# ============================================================================
# Music Releases
# ============================================================================


@router.get("/musician/releases", response_model=ApiResponse[dict])
def list_releases(
    album_id: Optional[str] = Query(None),
    distribution_status: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """获取音乐发行列表.

    支持按 album_id、distribution_status 过滤，分页返回.
    """
    q = db.query(MusicRelease)
    if album_id:
        q = q.filter(MusicRelease.album_id == album_id)
    if distribution_status:
        q = q.filter(MusicRelease.distribution_status == distribution_status)

    total = q.count()
    items = (
        q.order_by(MusicRelease.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    total_pages = max(1, (total + page_size - 1) // page_size)

    return ApiResponse(
        data={
            "items": [MusicReleaseSchema.model_validate(r).model_dump() for r in items],
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
        }
    )


@router.post("/musician/releases", response_model=ApiResponse[MusicReleaseSchema], dependencies=[Depends(require_auth)])
def create_release(
    payload: MusicReleaseCreate,
    db: Session = Depends(get_db),
):
    """创建音乐发行."""
    release = MusicRelease(
        title=payload.title,
        album_id=payload.album_id,
        work_variant_id=payload.work_variant_id,
        isrc=payload.isrc,
        audio_file_path=payload.audio_file_path,
        duration_seconds=payload.duration_seconds,
        bitrate=payload.bitrate,
        format=payload.format,
        genre=payload.genre,
        mood=payload.mood,
        bpm=payload.bpm,
        distribution_status=payload.distribution_status,
    )
    db.add(release)
    db.commit()
    db.refresh(release)

    return ApiResponse(
        data=MusicReleaseSchema.model_validate(release),
        message="音乐发行已创建",
    )


@router.get("/musician/releases/{release_id}", response_model=ApiResponse[MusicReleaseSchema])
def get_release(
    release_id: str,
    db: Session = Depends(get_db),
):
    """获取音乐发行详情."""
    release = db.query(MusicRelease).filter(MusicRelease.id == release_id).first()
    if not release:
        raise HTTPException(status_code=404, detail="音乐发行不存在")

    return ApiResponse(
        data=MusicReleaseSchema.model_validate(release),
    )


@router.patch("/musician/releases/{release_id}", response_model=ApiResponse[MusicReleaseSchema], dependencies=[Depends(require_auth)])
def update_release(
    release_id: str,
    payload: MusicReleaseUpdate,
    db: Session = Depends(get_db),
):
    """更新音乐发行."""
    release = db.query(MusicRelease).filter(MusicRelease.id == release_id).first()
    if not release:
        raise HTTPException(status_code=404, detail="音乐发行不存在")

    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(release, field, value)

    release.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(release)

    return ApiResponse(
        data=MusicReleaseSchema.model_validate(release),
        message="音乐发行已更新",
    )


@router.delete("/musician/releases/{release_id}", response_model=ApiResponse, dependencies=[Depends(require_auth)])
def delete_release(
    release_id: str,
    db: Session = Depends(get_db),
):
    """删除音乐发行."""
    release = db.query(MusicRelease).filter(MusicRelease.id == release_id).first()
    if not release:
        raise HTTPException(status_code=404, detail="音乐发行不存在")

    db.delete(release)
    db.commit()

    return ApiResponse(data=None, message="音乐发行已删除")


# ============================================================================
# Albums
# ============================================================================


@router.get("/musician/albums", response_model=ApiResponse[dict])
def list_albums(
    album_type: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """获取专辑列表.

    支持按 album_type 过滤，分页返回.
    """
    q = db.query(Album)
    if album_type:
        q = q.filter(Album.album_type == album_type)

    total = q.count()
    items = (
        q.order_by(Album.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    total_pages = max(1, (total + page_size - 1) // page_size)

    return ApiResponse(
        data={
            "items": [AlbumSchema.model_validate(a).model_dump() for a in items],
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
        }
    )


@router.post("/musician/albums", response_model=ApiResponse[AlbumSchema], dependencies=[Depends(require_auth)])
def create_album(
    payload: AlbumCreate,
    db: Session = Depends(get_db),
):
    """创建专辑."""
    album = Album(
        title=payload.title,
        album_type=payload.album_type,
        release_date=payload.release_date,
        cover_art_path=payload.cover_art_path,
        label=payload.label,
        total_tracks=payload.total_tracks,
        duration_seconds=payload.duration_seconds,
    )
    db.add(album)
    db.commit()
    db.refresh(album)

    return ApiResponse(
        data=AlbumSchema.model_validate(album),
        message="专辑已创建",
    )


# ============================================================================
# Split Sheets
# ============================================================================


@router.get("/musician/split-sheets", response_model=ApiResponse[dict])
def list_split_sheets(
    music_release_id: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """获取分成协议列表.

    支持按 music_release_id、status 过滤，分页返回.
    """
    q = db.query(SplitSheet)
    if music_release_id:
        q = q.filter(SplitSheet.music_release_id == music_release_id)
    if status:
        q = q.filter(SplitSheet.status == status)

    total = q.count()
    items = (
        q.order_by(SplitSheet.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    total_pages = max(1, (total + page_size - 1) // page_size)

    return ApiResponse(
        data={
            "items": [SplitSheetSchema.model_validate(s).model_dump() for s in items],
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
        }
    )


@router.post("/musician/split-sheets", response_model=ApiResponse[SplitSheetSchema], dependencies=[Depends(require_auth)])
def create_split_sheet(
    payload: SplitSheetCreate,
    db: Session = Depends(get_db),
):
    """创建分成协议."""
    sheet = SplitSheet(
        music_release_id=payload.music_release_id,
        title=payload.title,
        splits=payload.splits,
        publishing_share=payload.publishing_share,
        master_share=payload.master_share,
        status=payload.status,
    )
    db.add(sheet)
    db.commit()
    db.refresh(sheet)

    return ApiResponse(
        data=SplitSheetSchema.model_validate(sheet),
        message="分成协议已创建",
    )


@router.patch("/musician/split-sheets/{sheet_id}", response_model=ApiResponse[SplitSheetSchema], dependencies=[Depends(require_auth)])
def update_split_sheet(
    sheet_id: str,
    payload: SplitSheetUpdate,
    db: Session = Depends(get_db),
):
    """更新分成协议."""
    sheet = db.query(SplitSheet).filter(SplitSheet.id == sheet_id).first()
    if not sheet:
        raise HTTPException(status_code=404, detail="分成协议不存在")

    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(sheet, field, value)

    if "signed_at" in update_data and update_data["signed_at"] is not None:
        sheet.status = "signed"

    sheet.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(sheet)

    return ApiResponse(
        data=SplitSheetSchema.model_validate(sheet),
        message="分成协议已更新",
    )
