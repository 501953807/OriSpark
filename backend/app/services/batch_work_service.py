# -*- coding: utf-8 -*-
"""批量操作 + 回收站 + 文件夹导入服务层 — 从 batch_works.py 提取的业务逻辑."""

import logging
import os
import re
import uuid
from datetime import datetime, timezone
from typing import Optional, List

from sqlalchemy.orm import Session

from app.models.work import Work, WorkTag, Project
from app.services.hasher import compute_sha256
from app.services.work_service import detect_file_type, generate_thumbnail, get_all_metadata
from app.services.auto_tag_service import auto_generate_tags

logger = logging.getLogger(__name__)

ALLOWED_EXTENSIONS = {
    "png", "jpg", "jpeg", "webp", "gif", "svg", "psd", "tiff",
    "mp4", "mov", "avi", "webm", "mkv",
    "mp3", "wav", "flac", "aac",
    "txt", "md", "pdf", "docx",
}


# ============================================================================
# 辅助函数
# ============================================================================


def _extract_title_from_filename(filename: str) -> str:
    name = os.path.splitext(filename)[0]
    name = re.sub(r'^[\d\-_]{6,}', '', name).strip('_ ')
    name = re.sub(r'^(IMG|DSC|PXL|DSCF|MVI|VID)_?\d*[_\-]?', '', name, flags=re.IGNORECASE).strip('_ ')
    return name or "未命名作品"


# ============================================================================
# 批量编辑
# ============================================================================


def batch_edit_works(db: Session, work_ids: List[str], data: dict) -> int:
    """批量编辑作品标签/项目.

    Returns: number of works updated.
    """
    if not work_ids:
        return 0

    works = db.query(Work).filter(Work.id.in_(work_ids)).all()
    updated = 0

    for work in works:
        if "project_id" in data and data["project_id"] is not None:
            work.project_id = data["project_id"]
        if "current_stage" in data and data["current_stage"] is not None:
            work.current_stage = data["current_stage"]
        if "tags" in data and data["tags"] is not None:
            db.query(WorkTag).filter(WorkTag.work_id == work.id).delete()
            for tag in data["tags"]:
                db.add(WorkTag(work_id=work.id, tag=tag))
        if "custom_metadata" in data and data["custom_metadata"] is not None:
            work.custom_metadata = data["custom_metadata"]
        if "rights" in data and data["rights"] is not None:
            work.rights = data["rights"]
        if "license_type" in data and data["license_type"] is not None:
            work.license_type = data["license_type"]
        updated += 1

    try:
        db.commit()
    except Exception:
        db.rollback()
        raise
    return updated


# ============================================================================
# 自定义元数据更新
# ============================================================================


def update_custom_metadata(db: Session, work_id: str, metadata: Optional[dict]) -> bool:
    """更新作品自定义元数据."""
    work = db.query(Work).filter(Work.id == work_id).first()
    if not work:
        return False
    work.custom_metadata = metadata if metadata is not None else {}
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise
    return True


# ============================================================================
# 批量软删除
# ============================================================================


def batch_delete(db: Session, work_ids: List[str]) -> int:
    """批量软删除.

    Returns: number of works deleted.
    """
    works = db.query(Work).filter(Work.id.in_(work_ids)).all()
    now = datetime.now(timezone.utc)
    for w in works:
        w.status = "trashed"
        w.deleted_at = now
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise
    return len(works)


# ============================================================================
# 永久删除
# ============================================================================


def permanent_delete(db: Session, work_id: str) -> bool:
    """永久删除作品 (包括文件)."""
    work = db.query(Work).filter(Work.id == work_id, Work.status == "trashed").first()
    if not work:
        return False
    if work.file_path and os.path.exists(work.file_path):
        try:
            os.remove(work.file_path)
        except Exception as e:
            logger.exception("Error in permanent_delete: %s", str(e))
    db.delete(work)
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise
    return True


# ============================================================================
# 文件夹批量导入
# ============================================================================


def import_folder(db: Session, folder_path: str,
                  create_projects: bool = True,
                  skip_duplicates: bool = True) -> dict:
    """文件夹批量导入 — 递归读取、去重、自动项目创建、生成缩略图.

    Returns: import stats dict.
    """
    if not folder_path or not os.path.isdir(folder_path):
        return {"error": "文件夹路径无效"}

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
                    completion_date = datetime.fromtimestamp(
                        os.path.getmtime(fpath), tz=timezone.utc
                    ).strftime("%Y-%m-%d")

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
                    rights={"author_name": author_name or ""},
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

    return {
        "imported_count": imported,
        "skipped_count": skipped,
        "failed_count": failed,
        "total_size": total_size,
        "projects_created": projects_created,
        "errors": errors[:20],
    }


# ============================================================================
# 回收站操作
# ============================================================================


def empty_trash(db: Session) -> int:
    """清空回收站.

    Returns: number of works deleted.
    """
    deleted = db.query(Work).filter(Work.status == "trashed").delete()
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise
    return deleted


def restore_work(db: Session, work_id: str) -> bool:
    """从回收站恢复作品."""
    work = db.query(Work).filter(Work.id == work_id, Work.status == "trashed").first()
    if not work:
        return False
    work.status = "active"
    work.deleted_at = None
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise
    return True
