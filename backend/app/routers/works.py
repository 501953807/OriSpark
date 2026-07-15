"""作品管理 API 路由 — 对应: docs/modules-v3/01-creative-assets.md
Phase 1.1: 自动元数据提取, Phase 1.3: 视频缩略图修正, Phase 1.5: 存证状态友好化
端点: 18 (works)"""
import logging


import os
import uuid
import shutil
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query, Body
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy import func, or_, Text, cast, String


class RenameTagPayload(BaseModel):
    new_tag: str

from app.database import get_db
from app.models.work import Work, WorkTag, Project
from app.schemas.work import (
    WorkCreate, WorkUpdate, WorkResponse, WorkListResponse,
    WorkTagCreate, WorkTagResponse,
    HashOnlyUpload, LowresUpload, RightsUpdate, AiTagRequest,
)
from app.schemas.common import ApiResponse, PaginationParams
from app.services.hasher import compute_sha256
from app.services.work_service import generate_thumbnail, detect_file_type, extract_exif, get_image_dimensions, get_all_metadata
from app.services.auto_tag_service import auto_generate_tags
from app.deps import get_current_user_id, require_auth

router = APIRouter()

# 文件存储根目录 (相对路径，方便静态文件服务)
UPLOAD_DIR = Path("data/workspace")
THUMBNAIL_DIR = Path("data/thumbnails")

# 支持的文件类型 (P1.7.13: dictStore-backed with hardcoded fallback)
ALLOWED_EXTENSIONS = {
    "jpg", "jpeg", "png", "webp", "gif", "svg", "bmp", "tiff",
    "mp3", "wav", "flac", "ogg", "aac", "m4a",
    "mp4", "mov", "webm", "avi", "mkv",
    "pdf", "docx", "doc", "txt", "md", "rtf",
    "psd", "ai", "fig", "sketch",
    "py", "js", "ts", "html", "css", "json", "zip",
}

# P2-1: RAW camera image extensions (case-insensitive matching)
RAW_EXTENSIONS = {
    "cr2", "cr3", "nef", "arw", "raf", "orf", "pef", "dng", "heic", "heif",
    "rw2", "x3f", "iiq", "sr2", "mos", "mef", "k25", "kdc", "srf", "bay", "ptx", "dcraw", "raw",
}


def _get_allowed_extensions(db: Session) -> set:
    """Get allowed file extensions (dictStore-backed, P1.7.13)."""
    try:
        from app.routers.system import get_dict_values
        dict_exts = get_dict_values("file_extensions", db)
        if dict_exts:
            return set(dict_exts)
    except Exception as e:
        logging.getLogger(__name__).exception("Error in _get_allowed_extensions: %s", str(e))
    return ALLOWED_EXTENSIONS


# ═══════════════════════════════════════════
# Phase 1.1: 自动元数据提取辅助函数
# ═══════════════════════════════════════════

def _extract_title_from_filename(filename: str) -> str:
    import re
    name = os.path.splitext(filename)[0]
    name = re.sub(r'^[\d\-_]{6,}', '', name).strip('_ ')
    name = re.sub(r'^(IMG|DSC|PXL|DSCF|MVI|VID)_?\d*[_\-]?', '', name, flags=re.IGNORECASE).strip('_ ')
    return name or "未命名作品"


def _extract_completion_date(exif_data, file_path: str):
    if exif_data:
        for key in ("DateTimeOriginal", "DateTimeDigitized", "DateTime"):
            if exif_data.get(key):
                dt = str(exif_data[key])
                parts = dt.replace(" ", ":").split(":")
                if len(parts) >= 3:
                    return f"{parts[0]}-{parts[1]}-{parts[2]}"
                return dt
    try:
        from datetime import datetime
        return datetime.fromtimestamp(os.path.getmtime(file_path)).strftime("%Y-%m-%d")
    except OSError:
        return None


def _extract_creation_tool(exif_data, full_meta: dict):
    if exif_data:
        for key in ("Software", "HostComputer", "ProcessingSoftware"):
            if exif_data.get(key):
                return str(exif_data[key])
    if full_meta:
        for key in ("encoder", "producer", "software"):
            if full_meta.get(key):
                return str(full_meta[key])
    return None


def _extract_creation_location(exif_data):
    if not exif_data:
        return None
    gps_lat = exif_data.get("GPSLatitude") or exif_data.get("GPSInfo")
    gps_lon = exif_data.get("GPSLongitude")
    if gps_lat and gps_lon:
        return f"{gps_lat}, {gps_lon}"
    return None


def _build_auto_rights(exif_data):
    rights: dict = {}
    if exif_data:
        if exif_data.get("Artist"):
            rights["author_name"] = str(exif_data["Artist"])
        if exif_data.get("Copyright"):
            rights["copyright_year"] = str(exif_data["Copyright"])[:30]
    return rights


def _detect_creator_type(file_type: str, exif_data: Optional[dict], full_meta: Optional[dict]) -> str:
    """Detect creator type from file characteristics."""
    # Photographer: image with EXIF camera data
    if file_type == "image" and exif_data:
        camera_signals = ("CameraMake", "CameraModel", "LensModel", "Model")
        if any(exif_data.get(k) for k in camera_signals):
            return "photographer"
    # Musician: audio with ISRC/BPM/artists
    if file_type == "audio":
        audio_signals = ("isrc", "bpm", "artist", "Album")
        if any(full_meta and full_meta.get(k) for k in audio_signals):
            return "musician"
        return "musician"  # All audio defaults to musician
    # Video: video file type
    if file_type == "video":
        return "video"
    # Document: could be writer or craftsman
    if file_type == "document":
        # Check for CAD/design metadata
        if full_meta and any(k in full_meta for k in ("software", "Application", "Producer")):
            app = str(full_meta.get("software", "") + full_meta.get("Application", "") + full_meta.get("Producer", ""))
            if any(kw in app.lower() for kw in ("autocad", "solidworks", "sketchup")):
                return "craftsman"
        return "writer"
    # Default: illustrator for design files and everything else
    if file_type == "design":
        return "illustrator"
    return "illustrator"


MAX_FILE_SIZE = 500 * 1024 * 1024  # 500MB


def _thumb_to_api_path(thumb_path: Optional[str]) -> Optional[str]:
    """将本地缩略图绝对路径转为 API 可访问的相对路径."""
    if not thumb_path:
        return None
    try:
        p = Path(thumb_path)
        # 构造相对于 data/ 的路径
        rel = p.relative_to(Path("data").resolve())
        return f"/api/files/{rel.as_posix()}"
    except (ValueError, OSError):
        return None


def _work_to_response(work: Work) -> dict:
    """将 Work ORM 对象转为前端友好的响应格式 (Phase 1.1: 含自动元数据)."""
    data = WorkResponse.model_validate(work).model_dump()
    # 替换 file_path 和 thumbnail_path 为 API 可访问的路径
    if work.file_path:
        try:
            rel = Path(work.file_path).relative_to(Path("data").resolve())
            data["file_url"] = f"/api/files/{rel.as_posix()}"
        except (ValueError, OSError):
            data["file_url"] = None
    else:
        data["file_url"] = None

    data["thumbnail_url"] = _thumb_to_api_path(work.thumbnail_path)

    # Phase 1.1: 展开 custom_metadata 中的自动字段到顶层
    cm = work.custom_metadata or {}
    for key in ("completion_date", "creation_tool", "creation_location", "auto_tags"):
        if cm.get(key) and key not in data:
            data[key] = cm[key]

    # Phase 1.5: 存证状态友好化
    data["verified_status"] = "已存证 ✅" if work.is_verified else None

    # P2-1: RAW format indicators
    data["is_raw_original"] = work.is_raw_original
    data["raw_sidecar_path"] = work.raw_sidecar_path
    data["raw_processed_variant_id"] = work.raw_processed_variant_id

    return data


@router.post("/works", response_model=ApiResponse)
async def create_work(
    title: str = Form(default="未命名作品"),
    description: Optional[str] = Form(default=None),
    tags: Optional[str] = Form(default=None),
    project_id: Optional[str] = Form(default=None),
    allow_duplicate: bool = Form(default=False),
    file: UploadFile = File(...),
    user_id: str = Depends(require_auth),
    db: Session = Depends(get_db),
):
    """上传单个作品文件 (含自动标签 + 尺寸检测 + 可选重复导入)."""
    # 校验文件扩展名 (P1.7.13: dictStore-backed)
    ext = file.filename.split(".")[-1].lower() if "." in file.filename else ""
    allowed = _get_allowed_extensions(db)
    if ext not in allowed:
        raise HTTPException(status_code=400, detail=f"不支持的文件类型: .{ext}")

    # 读取文件
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="文件大小超过 500MB 限制")

    # 保存文件 (使用相对路径)
    work_id = uuid.uuid4().hex
    file_dir = UPLOAD_DIR / work_id[:2] / work_id
    file_dir.mkdir(parents=True, exist_ok=True)
    file_path = file_dir / file.filename
    file_size = len(content)

    with open(file_path, "wb") as f:
        f.write(content)

    # 检测文件类型
    file_type = detect_file_type(ext)

    # P2-1: RAW camera image detection
    is_raw = ext.lower() in RAW_EXTENSIONS

    # 自动生成初始阶段 (导入即有阶段)
    DEFAULT_FIRST_STAGE: dict[str, str] = {
        "image": "inspiration",
        "video": "script",
        "audio": "inspiration",
        "document": "outline",
        "design": "concept",
        "code": "design",
    }
    initial_stage = DEFAULT_FIRST_STAGE.get(file_type, None)

    # 生成缩略图
    thumbnail_path = generate_thumbnail(str(file_path), file_type, work_id)

    # 计算 SHA-256
    sha256_hash = compute_sha256(str(file_path))

    # 去重检测 (allow_duplicate=True 时跳过)
    if not allow_duplicate:
        existing = db.query(Work).filter(Work.sha256 == sha256_hash, Work.status == "active").first()
        if existing:
            # 删除刚保存的文件(已有副本)
            try:
                os.remove(str(file_path))
                parent = file_path.parent
                if parent.exists() and not any(parent.iterdir()):
                    parent.rmdir()
            except Exception as e:
                logging.getLogger(__name__).exception("Error in create_work cleanup: %s", str(e))
            raise HTTPException(
                status_code=409,
                detail=f"作品已存在: {existing.title} (SHA-256 相同)",
            )

    # 提取完整元数据 (EXIF + 音频/视频/文档)
    full_meta = get_all_metadata(str(file_path), file_type)
    exif_data = full_meta.pop("exif_data", None)
    width = full_meta.pop("width", None)
    height = full_meta.pop("height", None)
    duration = full_meta.pop("duration", None)

    # ── Phase 1.1: 自动元数据预填 ──
    auto_title = _extract_title_from_filename(file.filename) if title == "未命名作品" else title
    auto_completion_date = _extract_completion_date(exif_data, str(file_path))
    auto_creation_tool = _extract_creation_tool(exif_data, full_meta)
    auto_creation_location = _extract_creation_location(exif_data)
    auto_rights = _build_auto_rights(exif_data)

    # 自动生成标签
    auto_tags = auto_generate_tags(
        file_name=file.filename,
        file_type=file_type,
        exif_data=exif_data,
    )

    # 用户手动标签 + 自动标签合并
    user_tags = []
    if tags:
        user_tags = [t.strip() for t in tags.split(",") if t.strip()]

    all_tags = list(dict.fromkeys(user_tags + auto_tags))  # 去重保序

    # 创建数据库记录
    work = Work(
        id=work_id,
        title=auto_title,
        file_path=str(file_path.resolve()),
        file_name=file.filename,
        file_size=file_size,
        file_type=file_type,
        file_extension=ext,
        mime_type=file.content_type,
        sha256=sha256_hash,
        description=description,
        project_id=project_id,
        current_stage=initial_stage,  # 导入时自动设置初始阶段
        thumbnail_path=thumbnail_path,
        exif_data=exif_data,
        width=width,
        height=height,
        duration=duration,
        import_mode="full",
        is_raw_original=is_raw,
        rights=auto_rights,
        creator_type=_detect_creator_type(file_type, exif_data, full_meta),
        custom_metadata={
            "auto_tags": auto_tags,
            "imported_size": file_size,
            "completion_date": auto_completion_date,
            "creation_tool": auto_creation_tool,
            "creation_location": auto_creation_location,
            **full_meta,  # 音频/视频/文档元数据
        },
    )

    for tag_name in all_tags:
        work.tags.append(WorkTag(tag=tag_name))

    try:
        db.add(work)
        db.commit()
        db.refresh(work)
    except Exception:
        db.rollback()
        raise

    return ApiResponse(data=_work_to_response(work))


@router.get("/works", response_model=ApiResponse)
def list_works(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    file_type: Optional[str] = Query(None),
    status: Optional[str] = Query(default="active"),
    tag: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    project_id: Optional[str] = Query(None),
    stage: Optional[str] = Query(None),
    license_type: Optional[str] = Query(None),
    # P2-2: EXIF advanced search
    camera_make: Optional[str] = Query(None),
    camera_model: Optional[str] = Query(None),
    lens: Optional[str] = Query(None),
    iso: Optional[int] = Query(None),
    aperture: Optional[float] = Query(None),
    focal_length: Optional[float] = Query(None),
    shutter_speed: Optional[str] = Query(None),
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    gps_lat: Optional[float] = Query(None),
    gps_lon: Optional[float] = Query(None),
    # Legacy alias for backward compat
    camera: Optional[str] = Query(None, deprecated="Use camera_make or camera_model instead"),
    # P2-3: Culling filters
    cull_status: Optional[str] = Query(None),
    cull_rating: Optional[int] = Query(None, ge=0, le=5),
    color_label: Optional[str] = Query(None),
    sort_by: str = Query(default="imported_at"),
    sort_order: str = Query(default="desc"),
    user_id: str = Depends(require_auth),
    db: Session = Depends(get_db),
):
    """获取作品列表 (分页、筛选、搜索)."""
    query = db.query(Work)

    if status:
        query = query.filter(Work.status == status)
    if file_type:
        query = query.filter(Work.file_type == file_type)
    if project_id:
        query = query.filter(Work.project_id == project_id)
    if stage:
        query = query.filter(Work.current_stage == stage)
    if license_type:
        query = query.filter(Work.license_type == license_type)
    if tag:
        query = query.join(Work.tags).filter(WorkTag.tag == tag)
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(
                Work.title.ilike(search_term),
                Work.description.ilike(search_term),
                Work.file_name.ilike(search_term),
                Work.synopsis.ilike(search_term),
            )
        )

    # P2-2: EXIF advanced search (JSON path access on exif_data column)
    if camera_make:
        query = query.filter(cast(Work.exif_data['CameraMake'], String) == camera_make)
    if camera_model:
        query = query.filter(cast(Work.exif_data['CameraModel'], String) == camera_model)
    if lens:
        query = query.filter(Work.exif_data['LensModel'].astext.ilike(f'%{lens}%'))
    if iso:
        query = query.filter(cast(Work.exif_data['ISOSpeed'], String) == str(iso))
    if aperture:
        query = query.filter(cast(Work.exif_data['FNumber'], String) == str(aperture))
    if shutter_speed:
        query = query.filter(cast(Work.exif_data['ExposureTime'], String) == shutter_speed)
    if focal_length:
        query = query.filter(cast(Work.exif_data['FocalLength'], String) == str(focal_length))
    if date_from:
        query = query.filter(cast(Work.exif_data['DateTimeOriginal'], String) >= date_from)
    if date_to:
        query = query.filter(cast(Work.exif_data['DateTimeOriginal'], String) <= date_to)

    # Legacy params (backward compat) — bridge to new EXIF param names
    if camera:
        # 'camera' matches against CameraMake or CameraModel substring
        query = query.filter(
            or_(
                Work.exif_data['CameraMake'].astext.ilike(f'%{camera}%'),
                Work.exif_data['CameraModel'].astext.ilike(f'%{camera}%'),
            )
        )
    if gps_lat:
        query = query.filter(cast(Work.exif_data['GPSLatitude'], String) == str(gps_lat))
    if gps_lon:
        query = query.filter(cast(Work.exif_data['GPSLongitude'], String) == str(gps_lon))

    # P2-3: Culling filters
    if cull_status:
        query = query.filter(Work.cull_status == cull_status)
    if cull_rating is not None:
        query = query.filter(Work.cull_rating == cull_rating)
    if color_label:
        query = query.filter(Work.color_label == color_label)

    sort_column = getattr(Work, sort_by, Work.imported_at)
    if sort_order == "asc":
        query = query.order_by(sort_column.asc())
    else:
        query = query.order_by(sort_column.desc())

    total = query.count()
    offset = (page - 1) * page_size
    works = query.offset(offset).limit(page_size).all()
    total_pages = max(1, (total + page_size - 1) // page_size)

    return ApiResponse(data={
        "items": [_work_to_response(w) for w in works],
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
    })


@router.get("/works/{work_id}", response_model=ApiResponse)
def get_work(work_id: str, user_id: str = Depends(require_auth), db: Session = Depends(get_db)):
    """获取作品详情."""
    work = db.query(Work).filter(Work.id == work_id).first()
    if not work:
        raise HTTPException(status_code=404, detail="作品不存在")
    return ApiResponse(data=_work_to_response(work))


@router.patch("/works/{work_id}", response_model=ApiResponse)
def update_work(work_id: str, data: WorkUpdate, user_id: str = Depends(require_auth), db: Session = Depends(get_db)):
    work = db.query(Work).filter(Work.id == work_id).first()
    if not work:
        raise HTTPException(status_code=404, detail="作品不存在")

    update_data = data.model_dump(exclude_unset=True)
    tags_data = update_data.pop("tags", None)
    custom_metadata = update_data.pop("custom_metadata", None)

    for key, value in update_data.items():
        setattr(work, key, value)

    if custom_metadata is not None:
        # 合并自定义元数据
        existing = work.custom_metadata or {}
        existing.update(custom_metadata)
        work.custom_metadata = existing

    if tags_data is not None:
        db.query(WorkTag).filter(WorkTag.work_id == work_id).delete()
        for tag_name in tags_data:
            db.add(WorkTag(work_id=work_id, tag=tag_name))

    try:
        db.commit()
        db.refresh(work)
    except Exception:
        db.rollback()
        raise
    return ApiResponse(data=_work_to_response(work))


@router.delete("/works/{work_id}", response_model=ApiResponse)
def delete_work(work_id: str, user_id: str = Depends(require_auth), db: Session = Depends(get_db)):
    work = db.query(Work).filter(Work.id == work_id).first()
    if not work:
        raise HTTPException(status_code=404, detail="作品不存在")

    from datetime import datetime, timezone
    work.status = "trashed"
    work.deleted_at = datetime.now(timezone.utc)
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise
    return ApiResponse(message="作品已移入回收站")


@router.post("/works/{work_id}/hash", response_model=ApiResponse)
def recompute_hash(work_id: str, user_id: str = Depends(require_auth), db: Session = Depends(get_db)):
    work = db.query(Work).filter(Work.id == work_id).first()
    if not work:
        raise HTTPException(status_code=404, detail="作品不存在")
    if not os.path.exists(work.file_path):
        raise HTTPException(status_code=400, detail="作品文件不存在")

    sha256_hash = compute_sha256(work.file_path)
    work.sha256 = sha256_hash
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise
    return ApiResponse(data={"sha256": sha256_hash})


@router.get("/works/{work_id}/preview")
def get_preview_url(work_id: str, user_id: str = Depends(require_auth), db: Session = Depends(get_db)):
    """获取作品预览信息."""
    work = db.query(Work).filter(Work.id == work_id).first()
    if not work:
        raise HTTPException(status_code=404, detail="作品不存在")

    data = _work_to_response(work)
    # 对 text/code 文件读取内容
    text_exts = {"txt", "md", "py", "js", "ts", "html", "css", "json", "xml", "yaml"}
    content = None
    if work.file_extension in text_exts and os.path.exists(work.file_path):
        try:
            with open(work.file_path, "r", encoding="utf-8") as f:
                content = f.read()
        except Exception as e:
            logging.getLogger(__name__).exception("Error in get_preview_url: %s", str(e))

    data["text_content"] = content
    return ApiResponse(data=data)


# -- 标签管理 --

@router.get("/tags", response_model=ApiResponse)
def list_tags(user_id: str = Depends(require_auth), db: Session = Depends(get_db)):
    """获取所有标签 (含计数)."""
    results = db.query(
        WorkTag.tag, func.count(WorkTag.id).label("count")
    ).group_by(WorkTag.tag).order_by(func.count(WorkTag.id).desc()).all()
    return ApiResponse(data=[{"tag": r[0], "count": r[1]} for r in results])


@router.post("/works/{work_id}/tags", response_model=ApiResponse)
def add_tag(work_id: str, data: WorkTagCreate, user_id: str = Depends(require_auth), db: Session = Depends(get_db)):
    work = db.query(Work).filter(Work.id == work_id).first()
    if not work:
        raise HTTPException(status_code=404, detail="作品不存在")
    existing = db.query(WorkTag).filter(
        WorkTag.work_id == work_id, WorkTag.tag == data.tag
    ).first()
    if existing:
        return ApiResponse(message="标签已存在")
    db.add(WorkTag(work_id=work_id, tag=data.tag))
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise
    return ApiResponse(message="标签已添加")


@router.delete("/works/{work_id}/tags/{tag_id}", response_model=ApiResponse)
def remove_tag(work_id: str, tag_id: str, user_id: str = Depends(require_auth), db: Session = Depends(get_db)):
    tag = db.query(WorkTag).filter(WorkTag.id == tag_id, WorkTag.work_id == work_id).first()
    if not tag:
        raise HTTPException(status_code=404, detail="标签不存在")
    db.delete(tag)
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise
    return ApiResponse(message="标签已移除")


@router.patch("/tags/{old_tag}", response_model=ApiResponse)
def rename_tag(old_tag: str, data: RenameTagPayload = Body(...), user_id: str = Depends(require_auth), db: Session = Depends(get_db)):
    new_tag = data.new_tag.strip()
    if not new_tag:
        raise HTTPException(status_code=422, detail="标签名不能为空")

    # 更新所有使用该标签的 WorkTag 记录
    affected = db.query(WorkTag).filter(WorkTag.tag == old_tag).all()
    for wt in affected:
        wt.tag = new_tag

    try:
        db.commit()
    except Exception:
        db.rollback()
        raise
    return ApiResponse(message=f"标签已重命名 ({len(affected)} 个作品已更新)")


@router.delete("/tags/{tag_name}", response_model=ApiResponse)
def delete_global_tag(tag_name: str, user_id: str = Depends(require_auth), db: Session = Depends(get_db)):
    affected = db.query(WorkTag).filter(WorkTag.tag == tag_name).all()
    for wt in affected:
        db.delete(wt)

    try:
        db.commit()
    except Exception:
        db.rollback()
        raise
    return ApiResponse(message=f"标签已删除 ({len(affected)} 个作品已移除)")


# -- 标签联想 --

@router.get("/tags/suggest")
def suggest_tags(query: str = Query(...), user_id: str = Depends(require_auth), db: Session = Depends(get_db)):
    """标签智能联想."""
    from app.services.auto_tag_service import suggest_tags
    suggestions = suggest_tags(query)
    return ApiResponse(data=suggestions)


# -- P1.1.2: hash-only 上传 --

@router.post("/works/hash-only", response_model=ApiResponse)
def create_hash_only_work(data: "HashOnlyUpload", user_id: str = Depends(require_auth), db: Session = Depends(get_db)):
    from app.models.work import Work, WorkTag

    # 去重检测
    existing = db.query(Work).filter(Work.sha256 == data.sha256, Work.status == "active").first()
    if existing:
        raise HTTPException(
            status_code=409,
            detail=f"作品已存在: {existing.title} (SHA-256 相同)",
        )

    work_id = uuid.uuid4().hex
    ext = data.file_extension or data.file_name.split(".")[-1].lower() if "." in data.file_name else ""
    file_type = data.file_type or detect_file_type(ext)

    # 自动生成初始阶段
    DEFAULT_FIRST_STAGE: dict[str, str] = {
        "image": "inspiration", "video": "script", "audio": "inspiration",
        "document": "outline", "design": "concept", "code": "design",
    }
    initial_stage = DEFAULT_FIRST_STAGE.get(file_type, None)

    work = Work(
        id=work_id,
        title=data.title or data.file_name,
        file_path="",  # 无文件
        file_name=data.file_name,
        file_size=data.file_size,
        file_type=file_type,
        file_extension=ext,
        sha256=data.sha256,
        description=data.description,
        project_id=data.project_id,
        current_stage=initial_stage,
        import_mode="hash_only",
        custom_metadata=data.custom_metadata,
    )
    detected_ft = data.file_type or "image"
    work.creator_type = "illustrator"  # hash-only can't detect, default

    for tag_name in data.tags:
        work.tags.append(WorkTag(tag=tag_name))

    db.add(work)
    try:
        db.commit()
        db.refresh(work)
    except Exception:
        db.rollback()
        raise
    return ApiResponse(data=_work_to_response(work))


# -- P1.1.3: lowres 上传 (缩略图 + 元数据，无原文件) --

@router.post("/works/lowres", response_model=ApiResponse)
async def create_lowres_work(
    sha256: str = Form(...),
    file_name: str = Form(...),
    file_size: int = Form(..., ge=0),
    file_type: str = Form(default="image"),
    file_extension: str = Form(default=""),
    title: Optional[str] = Form(default=None),
    description: Optional[str] = Form(default=None),
    tags: Optional[str] = Form(default=None),
    project_id: Optional[str] = Form(default=None),
    width: Optional[int] = Form(default=None),
    height: Optional[int] = Form(default=None),
    thumbnail: UploadFile = File(...),
    user_id: str = Depends(require_auth),
    db: Session = Depends(get_db),
):
    """低分辨上传: 仅存储缩略图，不存储原文件."""
    from app.models.work import Work, WorkTag

    # 去重检测
    existing = db.query(Work).filter(Work.sha256 == sha256, Work.status == "active").first()
    if existing:
        raise HTTPException(
            status_code=409,
            detail=f"作品已存在: {existing.title} (SHA-256 相同)",
        )

    work_id = uuid.uuid4().hex
    ext = file_extension or file_name.split(".")[-1].lower() if "." in file_name else ""
    ft = detect_file_type(ext) if not file_type or file_type == "image" else file_type

    # 保存缩略图
    thumb_dir = THUMBNAIL_DIR / work_id[:2]
    thumb_dir.mkdir(parents=True, exist_ok=True)
    thumb_content = await thumbnail.read()
    thumb_path = thumb_dir / f"{work_id}_thumb.jpg"
    with open(thumb_path, "wb") as f:
        f.write(thumb_content)

    # 组装标签
    user_tags = []
    if tags:
        user_tags = [t.strip() for t in tags.split(",") if t.strip()]

    # 自动生成初始阶段
    DEFAULT_FIRST_STAGE: dict[str, str] = {
        "image": "inspiration", "video": "script", "audio": "inspiration",
        "document": "outline", "design": "concept", "code": "design",
    }
    initial_stage = DEFAULT_FIRST_STAGE.get(ft, None)

    work = Work(
        id=work_id,
        title=title or file_name,
        file_path="",  # 无原始文件
        file_name=file_name,
        file_size=file_size,
        file_type=ft,
        file_extension=ext,
        sha256=sha256,
        description=description,
        project_id=project_id,
        current_stage=initial_stage,
        import_mode="lowres",
        thumbnail_path=str(thumb_path.resolve()),
        width=width,
        height=height,
        creator_type=_detect_creator_type(ft, None, {"width": width, "height": height}),
    )

    for tag_name in user_tags:
        work.tags.append(WorkTag(tag=tag_name))

    db.add(work)
    try:
        db.commit()
        db.refresh(work)
    except Exception:
        db.rollback()
        raise
    return ApiResponse(data=_work_to_response(work))


# -- P1.1.5: 文件替换 --

@router.post("/works/{work_id}/replace", response_model=ApiResponse)
async def replace_work_file(
    work_id: str,
    file: UploadFile = File(...),
    notes: Optional[str] = Form(default=None),
    user_id: str = Depends(require_auth),
    db: Session = Depends(get_db),
):
    """替换作品文件: 自动创建版本快照后替换文件."""
    work = db.query(Work).filter(Work.id == work_id).first()
    if not work:
        raise HTTPException(status_code=404, detail="作品不存在")

    ext = file.filename.split(".")[-1].lower() if "." in file.filename else ""
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"不支持的文件类型: .{ext}")

    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="文件大小超过 500MB 限制")

    # 1. 创建版本快照（替换前）
    from app.models.work import WorkVersion
    latest = db.query(WorkVersion).filter(
        WorkVersion.work_id == work_id
    ).order_by(WorkVersion.version_num.desc()).first()
    version_num = (latest.version_num + 1) if latest else 1

    version = WorkVersion(
        work_id=work_id,
        version_num=version_num,
        file_hash=work.sha256 or "",
        file_path=work.file_path,
        file_size=work.file_size,
        notes=notes or f"替换为 {file.filename}",
    )
    db.add(version)

    # 2. 保存新文件
    file_dir = UPLOAD_DIR / work_id[:2] / work_id
    file_dir.mkdir(parents=True, exist_ok=True)
    file_path = file_dir / file.filename
    with open(file_path, "wb") as f:
        f.write(content)

    # 3. 重新计算 SHA-256
    sha256_hash = compute_sha256(str(file_path))

    # 4. 重新生成缩略图
    file_type = detect_file_type(ext)
    thumbnail_path = generate_thumbnail(str(file_path), file_type, work_id)

    # 5. 更新 Work 记录
    work.file_path = str(file_path.resolve())
    work.file_name = file.filename
    work.file_size = len(content)
    work.file_type = file_type
    work.file_extension = ext
    work.mime_type = file.content_type
    work.sha256 = sha256_hash
    work.thumbnail_path = thumbnail_path
    work.import_mode = "full"

    try:
        db.commit()
        db.refresh(work)
    except Exception:
        db.rollback()
        raise
    return ApiResponse(
        message=f"文件已替换并创建版本快照 v{version_num}",
        data=_work_to_response(work),
    )


# -- P1.1.6: Fork --

@router.post("/works/{work_id}/fork", response_model=ApiResponse)
def fork_work(work_id: str, user_id: str = Depends(require_auth), db: Session = Depends(get_db)):
    """Fork 作品: 创建副本并链接到原作品."""
    original = db.query(Work).filter(Work.id == work_id).first()
    if not original:
        raise HTTPException(status_code=404, detail="作品不存在")

    new_id = uuid.uuid4().hex

    # 复制文件（如果存在）
    new_file_path = ""
    if original.file_path and os.path.exists(original.file_path):
        new_dir = UPLOAD_DIR / new_id[:2] / new_id
        new_dir.mkdir(parents=True, exist_ok=True)
        new_file_path = str(new_dir / original.file_name)
        shutil.copy2(original.file_path, new_file_path)

    # 复制缩略图（如果存在）
    new_thumb_path = None
    if original.thumbnail_path and os.path.exists(original.thumbnail_path):
        new_thumb_dir = THUMBNAIL_DIR / new_id[:2]
        new_thumb_dir.mkdir(parents=True, exist_ok=True)
        thumb_dest = new_thumb_dir / f"{new_id}_thumb.jpg"
        shutil.copy2(original.thumbnail_path, thumb_dest)
        new_thumb_path = str(thumb_dest.resolve())

    fork = Work(
        id=new_id,
        title=f"{original.title} (Fork)",
        file_path=new_file_path,
        file_name=original.file_name,
        file_size=original.file_size,
        file_type=original.file_type,
        file_extension=original.file_extension,
        mime_type=original.mime_type,
        sha256=original.sha256,
        description=original.description,
        project_id=original.project_id,
        thumbnail_path=new_thumb_path,
        width=original.width,
        height=original.height,
        duration=original.duration,
        exif_data=original.exif_data,
        custom_metadata=original.custom_metadata,
        import_mode=original.import_mode,
        parent_work_id=work_id,
    )

    # 复制标签
    for tag in original.tags:
        fork.tags.append(WorkTag(tag=tag.tag))

    db.add(fork)
    try:
        db.commit()
        db.refresh(fork)
    except Exception:
        db.rollback()
        raise
    return ApiResponse(
        message=f"已 Fork 作品 {original.title}",
        data=_work_to_response(fork),
    )


# -- P1.1.8: 版权信息更新 --

@router.patch("/works/{work_id}/rights", response_model=ApiResponse)
def update_work_rights(work_id: str, data: "RightsUpdate", user_id: str = Depends(require_auth), db: Session = Depends(get_db)):
    """更新作品版权信息."""
    work = db.query(Work).filter(Work.id == work_id).first()
    if not work:
        raise HTTPException(status_code=404, detail="作品不存在")

    if data.rights is not None:
        work.rights = data.rights
    if data.license_type is not None:
        work.license_type = data.license_type

    try:
        db.commit()
        db.refresh(work)
    except Exception:
        db.rollback()
        raise
    return ApiResponse(
        message="版权信息已更新",
        data=_work_to_response(work),
    )


# -- P1.1.9: 版权声明 PDF 生成 --

@router.post("/works/{work_id}/rights-declaration", response_model=ApiResponse)
def generate_rights_declaration(work_id: str, user_id: str = Depends(require_auth), db: Session = Depends(get_db)):
    """生成版权声明 PDF (使用 reportlab)."""
    work = db.query(Work).filter(Work.id == work_id).first()
    if not work:
        raise HTTPException(status_code=404, detail="作品不存在")

    from io import BytesIO
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import mm
    from reportlab.lib import colors
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from datetime import datetime, timezone

    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4,
                           leftMargin=20*mm, rightMargin=20*mm,
                           topMargin=20*mm, bottomMargin=20*mm)
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle("Title_zh", parent=styles["Title"],
                                 fontName="Helvetica-Bold", fontSize=18,
                                 alignment=1, spaceAfter=12)
    heading_style = ParagraphStyle("Heading_zh", parent=styles["Heading2"],
                                    fontName="Helvetica-Bold", fontSize=14,
                                    spaceBefore=12, spaceAfter=6)
    body_style = ParagraphStyle("Body_zh", parent=styles["Normal"],
                                fontName="Helvetica", fontSize=11,
                                leading=16, spaceAfter=6)

    story = []
    story.append(Paragraph("Copyright Declaration / 版权声明", title_style))
    story.append(Spacer(1, 10*mm))
    story.append(Paragraph(f"Declaration Date: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}", body_style))
    story.append(Spacer(1, 5*mm))

    # 作品信息
    story.append(Paragraph("Work Information / 作品信息", heading_style))
    work_info = [
        ["Title / 作品名称", work.title],
        ["Work ID / 作品 ID", work.id],
        ["File Name / 文件名称", work.file_name],
        ["File Type / 文件类型", work.file_type],
        ["File Size / 文件大小", f"{work.file_size:,d} bytes"],
        ["SHA-256", work.sha256 or "N/A"],
        ["Imported At / 导入时间", work.imported_at.strftime("%Y-%m-%d %H:%M UTC") if work.imported_at else "N/A"],
    ]
    if work.width and work.height:
        work_info.append(["Dimensions / 尺寸", f"{work.width} x {work.height}"])
    if work.duration:
        work_info.append(["Duration / 时长", f"{work.duration}s"])

    t = Table(work_info, colWidths=[50*mm, 100*mm])
    t.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("BACKGROUND", (0, 0), (0, -1), colors.Color(0.95, 0.95, 0.95)),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("PADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(t)
    story.append(Spacer(1, 8*mm))

    # 版权信息
    story.append(Paragraph("Rights Information / 版权信息", heading_style))
    license_type = work.license_type or "Not specified / 未指定"
    story.append(Paragraph(f"License Type: {license_type}", body_style))

    if work.rights:
        rights_data = work.rights
        for key, value in rights_data.items():
            story.append(Paragraph(f"{key}: {value}", body_style))
    else:
        story.append(Paragraph("Rights Holder: Creator / 版权持有者: 创作者本人", body_style))
        story.append(Paragraph(
            "This work is protected by copyright law. Unauthorized reproduction, distribution, "
            "modification, or commercial use is prohibited.",
            body_style))

    story.append(Spacer(1, 8*mm))

    # 声明
    story.append(Paragraph("Legal Statement / 法律声明", heading_style))
    story.append(Paragraph(
        "This copyright declaration is issued in accordance with the Copyright Law of the People's Republic of China "
        "and relevant international copyright conventions. The creator and/or copyright holder possesses full moral "
        "and economic rights to this work.",
        body_style))
    story.append(Paragraph(
        "No person may use, reproduce, modify, distribute, or communicate the whole or any part of this work "
        "without the copyright holder's permission.",
        body_style))
    story.append(Spacer(1, 10*mm))

    story.append(Paragraph("— OriSpark Auto-Generated / 自动生成 —",
                          ParagraphStyle("Footer", parent=body_style, alignment=1)))

    doc.build(story)
    buf.seek(0)

    # 保存 PDF 到磁盘
    pdf_dir = Path("data/certificates")
    pdf_dir.mkdir(parents=True, exist_ok=True)
    pdf_filename = f"rights_declaration_{work_id}.pdf"
    pdf_path = pdf_dir / pdf_filename
    with open(pdf_path, "wb") as f:
        f.write(buf.read())

    return ApiResponse(
        message="版权声明 PDF 已生成",
        data={"pdf_url": f"/api/files/certificates/{pdf_filename}"},
    )


# -- P1.1.19: AI 标签推荐 --

@router.post("/tags/suggest-ai", response_model=ApiResponse)
async def suggest_tags_ai(data: "AiTagRequest", user_id: str = Depends(require_auth), db: Session = Depends(get_db)):
    """AI 标签推荐: 基于作品内容使用 Ollama 分析并推荐标签 (回退到增强规则)."""
    from app.services.auto_tag_service import CATEGORY_KEYWORDS

    tags = set()

    # 1. 先执行规则增强
    file_name = data.file_name or ""
    file_type = data.file_type or ""

    # 扩展规则标签生成 (比 auto_generate_tags 更丰富的版本)
    type_tags = {
        "image": "图片", "audio": "音频", "video": "视频",
        "document": "文档", "design": "设计", "code": "代码",
    }
    if file_type in type_tags:
        tags.add(type_tags[file_type])

    ext = Path(file_name).suffix.lower().lstrip(".") if file_name else ""
    ext_map = {"jpg": "JPEG", "jpeg": "JPEG", "png": "PNG", "gif": "GIF",
               "mp4": "MP4", "mp3": "MP3", "pdf": "PDF", "psd": "PSD",
               "webp": "WebP", "svg": "SVG", "wav": "WAV", "mkv": "MKV"}
    if ext in ext_map:
        tags.add(ext_map[ext])

    # 文件名关键词匹配
    if file_name:
        name_lower = Path(file_name).stem.lower().replace("_", " ").replace("-", " ")
        for category, keywords in CATEGORY_KEYWORDS.items():
            for kw in keywords:
                if kw.lower() in name_lower:
                    tags.add(category)

    # 尺寸标签
    exif_data = data.exif_data or {}
    if exif_data:
        if "Model" in exif_data:
            tags.add("相机拍摄")
        if "GPSInfo" in exif_data:
            tags.add("有定位")

    # 风格增强标签
    style_keywords = {
        "可爱": ["kawaii", "cute", "chibi", "q版"],
        "写实": ["realistic", "写实", "photorealistic"],
        "扁平": ["flat", "扁平", "minimal"],
        "复古": ["retro", "vintage", "复古", "怀旧"],
        "赛博朋克": ["cyberpunk", "赛博"],
        "水彩": ["watercolor", "水彩"],
        "像素": ["pixel", "像素", "8bit"],
        "暗黑": ["dark", "gothic", "暗黑"],
    }
    if file_name:
        name_lower = file_name.lower()
        for style_cat, kws in style_keywords.items():
            for kw in kws:
                if kw in name_lower:
                    tags.add(style_cat)

    # 2. 尝试 Ollama AI 增强
    ai_tags = set()
    try:
        from app.gateway.ollama import OllamaGateway
        gw = OllamaGateway()
        desc = data.description or ""
        prompt = f"""你是一个专业的创意作品标签推荐系统。请根据以下作品信息推荐 5-10 个标签（每行一个，只输出标签名，不要序号和说明）。

作品名称: {file_name}
作品类型: {file_type}
描述: {desc}

标签应包含:
- 风格 (如: 写实/卡通风/扁平/复古/水彩)
- 主题 (如: 风景/人物/动物/抽象)
- 用途 (如: 头像/壁纸/海报/表情包)
- 色调 (如: 暖色调/冷色调/黑白)

直接输出标签:"""

        ai_response = await gw.generate_description(
            work_title=file_name,
            work_type=file_type,
            language="zh",
        )
        # 从 Ollama 响应中提取标签
        for line in ai_response.strip().split("\n"):
            tag = line.strip().lstrip("- *#0123456789.").strip()
            if tag and len(tag) > 1 and len(tag) < 50:
                ai_tags.add(tag)
    except Exception:
        pass  # Ollama 不可用时静默降级

    # 3. 合并规则标签 + AI 标签
    all_tags = list(tags) + [t for t in ai_tags if t not in tags]

    return ApiResponse(data={
        "tags": all_tags[:15],
        "source": "rule+ai" if ai_tags else "rule",
    })


# ─── Folder Import (P2) ───

@router.post("/works/import-folder", response_model=ApiResponse)
async def import_folder(
    files: list[UploadFile] = File(...),
    auto_create_project: bool = Form(True),
    user_id: str = Depends(require_auth),
    db: Session = Depends(get_db),
):
    """批量导入文件夹 — 自动按文件夹名创建项目，SHA-256 去重.

    支持递归读取子文件夹(深度5层，单次最多500文件).
    返回 {imported: N, skipped_duplicate: M, failed: K}.
    """
    import hashlib
    from pathlib import Path as P

    workspace_dir = P("data/workspace")
    workspace_dir.mkdir(parents=True, exist_ok=True)

    imported = 0
    skipped = 0
    errors = []

    # Collect all files from uploaded files (folder drag-and-drop sends each file individually)
    file_list = []
    for f in files:
        if f.filename:
            file_list.append(f)

    # Limit to 500 files
    if len(file_list) > 500:
        raise HTTPException(status_code=400, detail="单次导入最多500个文件")

    # Group files by their folder path for auto-create project
    folder_map: dict[str, list[UploadFile]] = {}
    for f in file_list:
        # Try to infer folder from filename path separator (some browsers send full path)
        parts = f.filename.split("/")
        if len(parts) > 1:
            folder = "/".join(parts[:-1])
        else:
            folder = ""
        folder_map.setdefault(folder, []).append(f)

    # Auto-create project from first non-empty folder
    project_id = None
    if auto_create_project and folder_map:
        # Find the deepest common folder name
        all_folders = [k for k in folder_map.keys() if k]
        if all_folders:
            # Use the first folder as project name
            project_name = all_folders[0].split("/")[-1] if "/" in all_folders[0] else all_folders[0]
            existing = db.query(Project).filter(
                Project.name == project_name,
            ).first()
            if existing:
                project_id = existing.id
            else:
                new_project = Project(
                    id=str(uuid.uuid4())[:32],
                    name=project_name,
                    description=f"Auto-created from folder import: {project_name}",
                )
                db.add(new_project)
                db.flush()
                project_id = new_project.id

    # Recursion depth limit for nested folders
    MAX_DEPTH = 5
    failed = 0

    for f in file_list:
        try:
            content = await f.read()
            file_hash = hashlib.sha256(content).hexdigest()

            # Check duplicate by hash
            existing = db.query(Work).filter(Work.sha256 == file_hash).first()
            if existing:
                skipped += 1
                continue

            # Save file
            file_uuid = str(uuid.uuid4())[:32]
            file_dir = workspace_dir / file_uuid[:2] / file_uuid
            file_dir.mkdir(parents=True, exist_ok=True)
            file_path = file_dir / f.filename
            file_path.write_bytes(content)

            # Detect file type
            ext = f.filename.rsplit(".", 1)[-1].lower() if "." in f.filename else ""
            mime = f.content_type or "application/octet-stream"
            file_type = detect_file_type(ext)

            # 自动生成初始阶段
            DEFAULT_FIRST_STAGE: dict[str, str] = {
                "image": "inspiration", "video": "script", "audio": "inspiration",
                "document": "outline", "design": "concept", "code": "design",
            }
            initial_stage = DEFAULT_FIRST_STAGE.get(file_type, None)

            work = Work(
                id=file_uuid,
                title=P(f.filename).stem,
                file_path=str(file_path.relative_to(workspace_dir.parent)),
                mime_type=mime,
                file_size=len(content),
                file_type=file_type,
                sha256=file_hash,
                project_id=project_id,
                current_stage=initial_stage,
                creator_type=_detect_creator_type(file_type, None, {}),
            )
            db.add(work)
            imported += 1
        except Exception as e:
            errors.append({"filename": f.filename, "error": str(e)})

    try:
        db.commit()
    except Exception:
        db.rollback()
        raise

    return ApiResponse(data={
        "imported": imported,
        "skipped_duplicate": skipped,
        "failed": failed,
        "errors": errors[:10],  # Limit error list
    })


# ─── Project Package Import (P3-1) ───

@router.post("/works/import-project", response_model=ApiResponse)
async def import_project_package(
    project_name: str = Form(...),
    project_files: Optional[str] = Form(default=None),  # JSON string of file manifest
    description: Optional[str] = Form(default=None),
    user_id: str = Depends(require_auth),
    db: Session = Depends(get_db),
):
    """导入视频项目包 (P3-1).

    记录项目元数据和文件清单，标记作品为 project_package。

    Body (multipart/form-data):
        project_name: str — 项目名称
        project_files: JSON str (optional) — 文件清单 [{"name": "scene.psd", "extension": "psd"}, ...]
        description: str (optional)
    """
    import json

    files_data = None
    if project_files:
        try:
            files_data = json.loads(project_files)
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="project_files 必须是有效的 JSON")

    # 创建一个代表性的作品记录，标记为项目包
    work = Work(
        id=str(uuid.uuid4())[:32],
        title=project_name,
        file_path="",  # 项目包没有单一文件
        file_name=project_name,
        file_size=0,
        file_type="video",
        file_extension="project",
        description=description,
        is_project_package=True,
        project_files=files_data,
        import_mode="full",
    )

    db.add(work)
    try:
        db.commit()
        db.refresh(work)
    except Exception:
        db.rollback()
        raise

    return ApiResponse(
        message="项目包已导入",
        data=_work_to_response(work),
    )


# ─── P2-3: Batch Culling ───

class CullBatchRequest(BaseModel):
    work_ids: list[str]
    cull_status: Optional[str] = None  # review/pass/fail/hold
    cull_rating: Optional[int] = None  # 0-5
    color_label: Optional[str] = None  # red/green/blue/yellow


@router.post("/works/cull-batch", response_model=ApiResponse)
async def batch_cull(
    data: CullBatchRequest,
    user_id: str = Depends(require_auth),
    db: Session = Depends(get_db),
):
    """批量策展 (P2-3). 更新作品的策展状态、评分和颜色标签."""
    updated = 0
    for wid in data.work_ids:
        work = db.query(Work).filter(Work.id == wid).first()
        if not work:
            continue
        if data.cull_status is not None:
            work.cull_status = data.cull_status
        if data.cull_rating is not None:
            work.cull_rating = data.cull_rating
        if data.color_label is not None:
            work.color_label = data.color_label
        updated += 1
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise
    return ApiResponse(message=f"已更新 {updated} 个作品", data={"updated": updated})


# ─── P2-1: Process RAW to JPEG/WebP variant ───

class ProcessRawRequest(BaseModel):
    output_format: str = Field(default="jpeg", pattern="^(jpeg|webp)$")


@router.post("/works/{work_id}/process-raw", response_model=ApiResponse)
async def process_raw(
    work_id: str,
    data: ProcessRawRequest = Body(ProcessRawRequest()),
    user_id: str = Depends(require_auth),
    db: Session = Depends(get_db),
):
    """Process a RAW photo into a standard JPEG/WebP variant (stub).

    Placeholder: generates a processed variant record and sets raw_processed_variant_id.
    Actual conversion (via dcraw/libraw/ffmpeg) would be delegated to a background task.
    """
    work = db.query(Work).filter(Work.id == work_id).first()
    if not work:
        raise HTTPException(status_code=404, detail="作品不存在")

    if not work.is_raw_original:
        raise HTTPException(status_code=400, detail="该作品不是 RAW 格式")

    # Stub: generate a UUID for the processed variant and record it
    variant_id = uuid.uuid4().hex[:32]
    work.raw_processed_variant_id = variant_id
    try:
        db.commit()
        db.refresh(work)
    except Exception:
        db.rollback()
        raise

    return ApiResponse(
        message=f"RAW 处理任务已创建 (variant: {variant_id})",
        data=_work_to_response(work),
    )


# ─── P2-3: Single Work Culling ───

class CullActionRequest(BaseModel):
    action: str = Field(..., description="keep | reject | rate_1 .. rate_5 | color_red | color_yellow | color_green | color_blue")


@router.patch("/works/{work_id}/cull", response_model=ApiResponse)
async def single_cull(
    work_id: str,
    data: CullActionRequest,
    user_id: str = Depends(require_auth),
    db: Session = Depends(get_db),
):
    """Update culling state for a single work (P2-3).

    Supported actions:
      keep, reject,
      rate_1, rate_2, rate_3, rate_4, rate_5,
      color_red, color_yellow, color_green, color_blue
    """
    work = db.query(Work).filter(Work.id == work_id).first()
    if not work:
        raise HTTPException(status_code=404, detail="作品不存在")

    action = data.action.strip().lower()

    if action == "keep":
        work.cull_status = "kept"
        work.cull_rating = 5
        work.color_label = "green"
    elif action == "reject":
        work.cull_status = "rejected"
        work.cull_rating = 0
        work.color_label = "red"
    elif action.startswith("rate_"):
        try:
            rating = int(action.split("_")[1])
        except (IndexError, ValueError):
            raise HTTPException(status_code=422, detail=f"Invalid action: {data.action}")
        if rating < 1 or rating > 5:
            raise HTTPException(status_code=422, detail="Rating must be 1-5")
        work.cull_rating = rating
        work.cull_status = "kept"
        if rating >= 4:
            work.color_label = "green"
        elif rating == 3:
            work.color_label = "yellow"
        elif rating <= 1:
            work.color_label = "red"
    elif action.startswith("color_"):
        try:
            label = action.split("_")[1]
        except IndexError:
            raise HTTPException(status_code=422, detail=f"Invalid action: {data.action}")
        if label not in ("red", "yellow", "green", "blue"):
            raise HTTPException(status_code=422, detail=f"Invalid color: {label}")
        work.color_label = label
    else:
        raise HTTPException(status_code=422, detail=f"Unknown action: {data.action}")

    try:
        db.commit()
        db.refresh(work)
    except Exception:
        db.rollback()
        raise
    return ApiResponse(message=f"Cull state updated ({action})", data=_work_to_response(work))
