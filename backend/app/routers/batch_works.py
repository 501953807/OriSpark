"""批量操作 + 回收站 + 文件夹导入 API 路由 — 对应: docs/modules-v3/01-creative-assets.md
Phase 1.2: POST /works/import-folder (递归+去重+自动项目)
端点: 7 (batch_works)"""
import logging
import os
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Optional, List


from app.database import get_db
from app.deps import require_auth
from app.models.work import Work, WorkTag, Project
from app.schemas.common import ApiResponse
from app.services.hasher import compute_sha256
from app.services.work_service import detect_file_type, generate_thumbnail, get_all_metadata
from app.services.auto_tag_service import auto_generate_tags

router = APIRouter()


class BatchEditPayload(BaseModel):
    work_ids: list[str]
    project_id: Optional[str] = None
    current_stage: Optional[str] = None
    tags: Optional[List[str]] = None
    custom_metadata: Optional[dict] = None
    rights: Optional[dict] = None
    license_type: Optional[str] = None


class UpdateCustomMetadataPayload(BaseModel):
    metadata: Optional[dict] = None


class ImportFolderPayload(BaseModel):
    folder_path: str
    create_projects: bool = True
    skip_duplicates: bool = True


class RenameTagPayload(BaseModel):
    new_tag: str


@router.post("/works/batch-edit", response_model=ApiResponse, dependencies=[Depends(require_auth)])
def batch_edit_works(data: BatchEditPayload, db: Session = Depends(get_db)):
    """批量编辑作品标签/项目."""
    if not data.work_ids:
        raise HTTPException(status_code=400, detail="work_ids 不能为空")

    works = db.query(Work).filter(Work.id.in_(data.work_ids)).all()
    updated = 0

    for work in works:
        if data.project_id is not None:
            work.project_id = data.project_id

        if data.current_stage is not None:
            work.current_stage = data.current_stage

        if data.tags is not None:
            tags_data: List[str] = data.tags
            db.query(WorkTag).filter(WorkTag.work_id == work.id).delete()
            for tag in tags_data:
                db.add(WorkTag(work_id=work.id, tag=tag))

        if data.custom_metadata is not None:
            work.custom_metadata = data.custom_metadata

        if data.rights is not None:
            work.rights = data.rights

        if data.license_type is not None:
            work.license_type = data.license_type

        updated += 1

    try:
        db.commit()
    except Exception:
        db.rollback()
        raise
    return ApiResponse(message=f"已更新 {updated} 个作品")


@router.post("/works/{work_id}/metadata", response_model=ApiResponse, dependencies=[Depends(require_auth)])
def update_custom_metadata(work_id: str, data: UpdateCustomMetadataPayload, db: Session = Depends(get_db)):
    """更新作品自定义元数据."""
    work = db.query(Work).filter(Work.id == work_id).first()
    if not work:
        raise HTTPException(status_code=404, detail="作品不存在")

    work.custom_metadata = data.metadata if data.metadata is not None else {}
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise
    return ApiResponse(message="元数据已更新")


@router.post("/works/batch-delete", response_model=ApiResponse, dependencies=[Depends(require_auth)])
def batch_delete(data: List[str], db: Session = Depends(get_db)):
    """批量软删除."""
    works = db.query(Work).filter(Work.id.in_(data)).all()
    now = datetime.now(timezone.utc)
    for w in works:
        w.status = "trashed"
        w.deleted_at = now
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise
    return ApiResponse(message=f"已删除 {len(works)} 个作品")


@router.delete("/works/{work_id}/permanent", response_model=ApiResponse, dependencies=[Depends(require_auth)])
def permanent_delete(work_id: str, db: Session = Depends(get_db)):
    """永久删除作品 (包括文件)."""
    work = db.query(Work).filter(Work.id == work_id, Work.status == "trashed").first()
    if not work:
        raise HTTPException(status_code=404, detail="作品不存在或未在回收站中")
    if work.file_path and os.path.exists(work.file_path):
        try:
            os.remove(work.file_path)
        except Exception as e:
            logging.getLogger(__name__).exception("Error in permanent_delete: %s", str(e))
    db.delete(work)
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise
    return ApiResponse(message="作品已永久删除")


# ═══════════════════════════════════════════
# Phase 1.2: 文件夹批量导入
# ═══════════════════════════════════════════

ALLOWED_EXTENSIONS = {
    "png", "jpg", "jpeg", "webp", "gif", "svg", "psd", "tiff",
    "mp4", "mov", "avi", "webm", "mkv",
    "mp3", "wav", "flac", "aac",
    "txt", "md", "pdf", "docx",
}


def _extract_title_from_filename(filename: str) -> str:
    name = os.path.splitext(filename)[0]
    name = re.sub(r'^[\d\-_]{6,}', '', name).strip('_ ')
    name = re.sub(r'^(IMG|DSC|PXL|DSCF|MVI|VID)_?\d*[_\-]?', '', name, flags=re.IGNORECASE).strip('_ ')
    return name or "未命名作品"


@router.post("/works/import-folder", response_model=ApiResponse, dependencies=[Depends(require_auth)])
def import_folder(data: ImportFolderPayload, db: Session = Depends(get_db)):
    """文件夹批量导入 — 递归读取、去重、自动项目创建、生成缩略图."""
    folder_path = data.folder_path
    create_projects = data.create_projects
    skip_duplicates = data.skip_duplicates

    if not folder_path or not os.path.isdir(folder_path):
        raise HTTPException(status_code=400, detail="文件夹路径无效")

    imported = 0
    skipped = 0
    failed = 0
    projects_created: list = []
    errors: list = []
    total_size = 0

    for root, dirs, files in os.walk(folder_path):
        rel_depth = root.replace(folder_path, "").count(os.sep)
        if rel_depth > 3:
            dirs[:] = []
            continue

        # Determine project for this folder
        current_project_id: Optional[str] = None
        if create_projects and root != folder_path:
            folder_name = os.path.basename(root)
            existing = db.query(Project).filter(Project.name == folder_name).first()
            if not existing:
                p = Project(id=uuid.uuid4().hex, name=folder_name)
                db.add(p)
                db.flush()
                projects_created.append(folder_name)
                current_project_id = p.id
            else:
                current_project_id = existing.id

        for fname in sorted(files):
            fpath = os.path.join(root, fname)
            ext = fname.rsplit(".", 1)[-1].lower() if "." in fname else ""
            if ext not in ALLOWED_EXTENSIONS:
                continue

            file_size = os.path.getsize(fpath)
            total_size += file_size

            try:
                # Dedup check
                sha = compute_sha256(fpath)
                if skip_duplicates and db.query(Work).filter(
                    Work.sha256 == sha, Work.status == "active"
                ).first():
                    skipped += 1
                    continue

                # File type detection
                file_type = detect_file_type(ext)

                # Generate thumbnail
                thumbnail_path = generate_thumbnail(fpath, file_type, uuid.uuid4().hex)

                # Extract metadata
                full_meta = get_all_metadata(fpath, file_type)
                exif_data = full_meta.pop("exif_data", None)
                width = full_meta.pop("width", None)
                height = full_meta.pop("height", None)
                duration = full_meta.pop("duration", None)

                # Auto title from filename
                auto_title = _extract_title_from_filename(fname)

                # Auto tags
                auto_tags = auto_generate_tags(
                    file_name=fname,
                    file_type=file_type,
                    exif_data=exif_data,
                )

                # Completion date from EXIF or file mtime
                completion_date = None
                if exif_data:
                    for key in ("DateTimeOriginal", "DateTimeDigitized", "DateTime"):
                        if exif_data.get(key):
                            dt = str(exif_data[key])
                            parts = dt.replace(" ", ":").split(":")
                            if len(parts) >= 3:
                                completion_date = f"{parts[0]}-{parts[1]}-{parts[2]}"
                            break
                if not completion_date:
                    completion_date = datetime.fromtimestamp(os.path.getmtime(fpath), tz=timezone.utc).strftime("%Y-%m-%d")

                # Creation tool from EXIF
                creation_tool = None
                if exif_data:
                    for key in ("Software", "HostComputer", "ProcessingSoftware"):
                        if exif_data.get(key):
                            creation_tool = str(exif_data[key])
                            break

                # Author from EXIF
                author_name = None
                if exif_data and exif_data.get("Artist"):
                    author_name = str(exif_data["Artist"])

                # Create Work record
                work_id = uuid.uuid4().hex
                work = Work(
                    id=work_id,
                    title=auto_title,
                    file_path=fpath,
                    file_name=fname,
                    file_size=file_size,
                    file_type=file_type,
                    file_extension=ext,
                    sha256=sha,
                    project_id=current_project_id,
                    thumbnail_path=thumbnail_path,
                    width=width,
                    height=height,
                    duration=duration,
                    exif_data=exif_data,
                    import_mode="full",
                    rights={
                        "author_name": author_name or "",
                    },
                    custom_metadata={
                        "auto_tags": auto_tags,
                        "completion_date": completion_date,
                        "creation_tool": creation_tool,
                        "imported_from": folder_path,
                        **full_meta,
                    },
                )

                for tag_name in auto_tags:
                    work.tags.append(WorkTag(tag=tag_name))

                db.add(work)
                imported += 1

            except Exception as exc:
                failed += 1
                errors.append(f"{fname}: {str(exc)[:200]}")
                continue

    try:
        db.commit()
    except Exception:
        db.rollback()
        raise

    return ApiResponse(data={
        "imported_count": imported,
        "skipped_count": skipped,
        "failed_count": failed,
        "total_size": total_size,
        "projects_created": projects_created,
        "errors": errors[:20],
    })


@router.post("/works/empty-trash", response_model=ApiResponse, dependencies=[Depends(require_auth)])
def empty_trash(db: Session = Depends(get_db)):
    """清空回收站."""
    deleted = db.query(Work).filter(Work.status == "trashed").delete()
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise
    return ApiResponse(message=f"已清空 {deleted} 个作品")


@router.post("/works/{work_id}/restore", response_model=ApiResponse, dependencies=[Depends(require_auth)])
def restore_work(work_id: str, db: Session = Depends(get_db)):
    """从回收站恢复作品."""
    work = db.query(Work).filter(Work.id == work_id, Work.status == "trashed").first()
    if not work:
        raise HTTPException(status_code=404, detail="作品不在回收站中")
    work.status = "active"
    work.deleted_at = None
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise
    return ApiResponse(message="作品已恢复")
