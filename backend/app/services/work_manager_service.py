"""作品管理业务服务层 — 对应: docs/modules-v5/01-creative-assets.md

将所有 DB 操作和复杂业务逻辑从 works.py router 中抽出，
router 只保留 DTO 验证 + svc = WorkService(db) + 调用 service 方法。
"""
import hashlib
import json
import logging
import os
import shutil
import uuid
from datetime import datetime, timezone
from io import BytesIO
from pathlib import Path
from typing import Optional

from fastapi import HTTPException
from sqlalchemy import func, or_, cast, String
from sqlalchemy.orm import Session

from app.models.work import Work, WorkTag, WorkVersion, Project
from app.schemas.common import ApiResponse
from app.schemas.work import (
    WorkUpdate, WorkTagCreate, HashOnlyUpload, LowresUpload, RightsUpdate, AiTagRequest,
)
from app.services.hasher import compute_sha256
from app.services.work_service import (
    generate_thumbnail, detect_file_type, get_all_metadata, _get_allowed_extensions,
    sanitize_tag, sanitize_filename, _extract_title_from_filename,
    _extract_completion_date, _extract_creation_tool, _extract_creation_location,
    _build_auto_rights, _detect_creator_type, _thumb_to_api_path, _work_to_response,
    ALLOWED_EXTENSIONS, RAW_EXTENSIONS, MAX_FILE_SIZE, UPLOAD_DIR, THUMBNAIL_DIR,
)

logger = logging.getLogger("oristudio.works")

# Phase 1.1: 自动初始阶段映射
DEFAULT_FIRST_STAGE: dict[str, str] = {
    "image": "inspiration",
    "video": "script",
    "audio": "inspiration",
    "document": "outline",
    "design": "concept",
    "code": "design",
}


class WorkManagerService:
    """作品管理核心业务逻辑 — 从 works.py 提取."""

    def __init__(self, db: Optional[Session] = None):
        self.db = db

    # ── 核心 CRUD ────────────────────────────────────────────────────

    async def create_work(
        self,
        title: str,
        description: Optional[str],
        tags_str: Optional[str],
        project_id: Optional[str],
        allow_duplicate: bool,
        file,
        user_id: str,
    ) -> ApiResponse:
        """上传单个作品文件 (含自动标签 + 尺寸检测 + 可选重复导入)."""
        ext = Path(file.filename).suffix.lower().lstrip(".") if "." in file.filename else ""
        allowed = _get_allowed_extensions(self.db)
        if ext not in allowed:
            raise HTTPException(status_code=400, detail=f"不支持的文件类型: .{ext}")

        content = await file.read()
        if len(content) > MAX_FILE_SIZE:
            raise HTTPException(status_code=400, detail="文件大小超过 500MB 限制")

        actual_type = detect_file_type(ext, content)
        # 防扩展名绕过校验（当前只做日志记录，实际类型仍用扩展名判断）
        _ = actual_type

        work_id = uuid.uuid4().hex
        file_dir = UPLOAD_DIR / work_id[:2] / work_id
        file_dir.mkdir(parents=True, exist_ok=True)

        safe_filename = f"{work_id}.{ext}" if ext else str(uuid.uuid4())
        file_path = file_dir / safe_filename

        with open(file_path, "wb") as f:
            f.write(content)

        file_type = detect_file_type(ext)
        is_raw = ext.lower() in RAW_EXTENSIONS

        initial_stage = DEFAULT_FIRST_STAGE.get(file_type, None)
        thumbnail_path = generate_thumbnail(str(file_path), file_type, work_id)
        sha256_hash = compute_sha256(str(file_path))

        # 去重检测
        if not allow_duplicate:
            existing = self.db.query(Work).filter(
                Work.sha256 == sha256_hash, Work.status == "active"
            ).first()
            if existing:
                try:
                    os.remove(str(file_path))
                    parent = file_path.parent
                    if parent.exists() and not any(parent.iterdir()):
                        parent.rmdir()
                except Exception as e:
                    logger.exception("Error in create_work cleanup: %s", str(e))
                raise HTTPException(
                    status_code=409,
                    detail=f"作品已存在: {existing.title} (SHA-256 相同)",
                )

        full_meta = get_all_metadata(str(file_path), file_type)
        exif_data = full_meta.pop("exif_data", None)
        width = full_meta.pop("width", None)
        height = full_meta.pop("height", None)
        duration = full_meta.pop("duration", None)

        auto_title = _extract_title_from_filename(file.filename) if title == "未命名作品" else title
        auto_completion_date = _extract_completion_date(exif_data, str(file_path))
        auto_creation_tool = _extract_creation_tool(exif_data, full_meta)
        auto_creation_location = _extract_creation_location(exif_data)
        auto_rights = _build_auto_rights(exif_data)

        auto_tags = []
        try:
            from app.services.auto_tag_service import auto_generate_tags
            auto_tags = auto_generate_tags(
                file_name=file.filename,
                file_type=file_type,
                exif_data=exif_data,
            )
        except Exception:
            pass

        user_tags = []
        if tags_str:
            user_tags = [t.strip() for t in tags_str.split(",") if t.strip()]

        all_tags = list(dict.fromkeys(user_tags + auto_tags))

        work = Work(
            id=work_id,
            title=auto_title,
            file_path=str(file_path.resolve()),
            file_name=file.filename,
            file_size=len(content),
            file_type=file_type,
            file_extension=ext,
            mime_type=file.content_type,
            sha256=sha256_hash,
            description=description,
            project_id=project_id,
            current_stage=initial_stage,
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
                "imported_size": len(content),
                "completion_date": auto_completion_date,
                "creation_tool": auto_creation_tool,
                "creation_location": auto_creation_location,
                **full_meta,
            },
        )

        for tag_name in all_tags:
            work.tags.append(WorkTag(tag=sanitize_tag(tag_name)))

        try:
            self.db.add(work)
            self.db.commit()
            self.db.refresh(work)
        except Exception:
            self.db.rollback()
            raise

        return ApiResponse(data=_work_to_response(work))

    def list_works(
        self,
        page: int,
        page_size: int,
        file_type: Optional[str] = None,
        status: Optional[str] = "active",
        tag: Optional[str] = None,
        search: Optional[str] = None,
        project_id: Optional[str] = None,
        stage: Optional[str] = None,
        license_type: Optional[str] = None,
        camera_make: Optional[str] = None,
        camera_model: Optional[str] = None,
        lens: Optional[str] = None,
        iso: Optional[int] = None,
        aperture: Optional[float] = None,
        focal_length: Optional[float] = None,
        shutter_speed: Optional[str] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        gps_lat: Optional[float] = None,
        gps_lon: Optional[float] = None,
        camera: Optional[str] = None,
        cull_status: Optional[str] = None,
        cull_rating: Optional[int] = None,
        color_label: Optional[str] = None,
        sort_by: str = "imported_at",
        sort_order: str = "desc",
    ) -> ApiResponse:
        """获取作品列表 (分页、筛选、搜索)."""
        query = self.db.query(Work)

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
        if camera:
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

    def get_work(self, work_id: str) -> ApiResponse:
        """获取作品详情."""
        work = self.db.query(Work).filter(Work.id == work_id).first()
        if not work:
            raise HTTPException(status_code=404, detail="作品不存在")
        return ApiResponse(data=_work_to_response(work))

    def get_project_package(self, work_id: str) -> ApiResponse:
        """获取作品的项目包数据 (P3-1)."""
        work = self.db.query(Work).filter(Work.id == work_id).first()
        if not work:
            raise HTTPException(status_code=404, detail="作品不存在")
        if not work.project_files:
            return ApiResponse(data={"timeline": [], "materials": [], "effects": []})
        try:
            files = json.loads(work.project_files) if isinstance(work.project_files, str) else work.project_files
            return ApiResponse(data=files)
        except (json.JSONDecodeError, TypeError):
            return ApiResponse(data={"timeline": [], "materials": [], "effects": []})

    def update_work(self, work_id: str, data: WorkUpdate) -> ApiResponse:
        work = self.db.query(Work).filter(Work.id == work_id).first()
        if not work:
            raise HTTPException(status_code=404, detail="作品不存在")

        update_data = data.model_dump(exclude_unset=True)
        tags_data = update_data.pop("tags", None)
        custom_metadata = update_data.pop("custom_metadata", None)

        for key, value in update_data.items():
            setattr(work, key, value)

        if custom_metadata is not None:
            existing = work.custom_metadata or {}
            existing.update(custom_metadata)
            work.custom_metadata = existing

        if tags_data is not None:
            self.db.query(WorkTag).filter(WorkTag.work_id == work_id).delete()
            for tag_name in tags_data:
                self.db.add(WorkTag(work_id=work_id, tag=sanitize_tag(tag_name)))

        try:
            self.db.commit()
            self.db.refresh(work)
        except Exception:
            self.db.rollback()
            raise
        return ApiResponse(data=_work_to_response(work))

    def delete_work(self, work_id: str) -> ApiResponse:
        work = self.db.query(Work).filter(Work.id == work_id).first()
        if not work:
            raise HTTPException(status_code=404, detail="作品不存在")

        work.status = "trashed"
        work.deleted_at = datetime.now(timezone.utc)
        try:
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise
        return ApiResponse(message="作品已移入回收站")

    def recompute_hash(self, work_id: str) -> ApiResponse:
        work = self.db.query(Work).filter(Work.id == work_id).first()
        if not work:
            raise HTTPException(status_code=404, detail="作品不存在")
        if not os.path.exists(work.file_path):
            raise HTTPException(status_code=400, detail="作品文件不存在")

        sha256_hash = compute_sha256(work.file_path)
        work.sha256 = sha256_hash
        try:
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise
        return ApiResponse(data={"sha256": sha256_hash})

    def get_preview_url(self, work_id: str) -> ApiResponse:
        work = self.db.query(Work).filter(Work.id == work_id).first()
        if not work:
            raise HTTPException(status_code=404, detail="作品不存在")

        data = _work_to_response(work)
        text_exts = {"txt", "md", "py", "js", "ts", "html", "css", "json", "xml", "yaml"}
        content = None
        if work.file_extension in text_exts and os.path.exists(work.file_path):
            try:
                with open(work.file_path, "r", encoding="utf-8") as f:
                    content = f.read()
            except Exception as e:
                logger.exception("Error in get_preview_url: %s", str(e))

        data["text_content"] = content
        return ApiResponse(data=data)

    # ── 标签管理 ─────────────────────────────────────────────────────

    def list_tags(self) -> ApiResponse:
        """获取所有标签 (含计数)."""
        results = self.db.query(
            WorkTag.tag, func.count(WorkTag.id).label("count")
        ).group_by(WorkTag.tag).order_by(func.count(WorkTag.id).desc()).all()
        return ApiResponse(data=[{"tag": r[0], "count": r[1]} for r in results])

    def add_tag(self, work_id: str, data: WorkTagCreate) -> ApiResponse:
        work = self.db.query(Work).filter(Work.id == work_id).first()
        if not work:
            raise HTTPException(status_code=404, detail="作品不存在")
        existing = self.db.query(WorkTag).filter(
            WorkTag.work_id == work_id, WorkTag.tag == data.tag
        ).first()
        if existing:
            return ApiResponse(message="标签已存在")
        self.db.add(WorkTag(work_id=work_id, tag=sanitize_tag(data.tag)))
        try:
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise
        return ApiResponse(message="标签已添加")

    def remove_tag(self, work_id: str, tag_id: str) -> ApiResponse:
        tag = self.db.query(WorkTag).filter(
            WorkTag.id == tag_id, WorkTag.work_id == work_id
        ).first()
        if not tag:
            raise HTTPException(status_code=404, detail="标签不存在")
        self.db.delete(tag)
        try:
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise
        return ApiResponse(message="标签已移除")

    def rename_tag(self, old_tag: str, new_tag: str) -> ApiResponse:
        new_tag = new_tag.strip()
        if not new_tag:
            raise HTTPException(status_code=422, detail="标签名不能为空")

        affected = self.db.query(WorkTag).filter(WorkTag.tag == old_tag).all()
        for wt in affected:
            wt.tag = sanitize_tag(new_tag)

        try:
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise
        return ApiResponse(message=f"标签已重命名 ({len(affected)} 个作品已更新)")

    def delete_global_tag(self, tag_name: str) -> ApiResponse:
        affected = self.db.query(WorkTag).filter(WorkTag.tag == tag_name).all()
        for wt in affected:
            self.db.delete(wt)

        try:
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise
        return ApiResponse(message=f"标签已删除 ({len(affected)} 个作品已移除)")

    # ── hash-only / lowres 上传 ──────────────────────────────────────

    def create_hash_only_work(self, data: HashOnlyUpload) -> ApiResponse:
        existing = self.db.query(Work).filter(
            Work.sha256 == data.sha256, Work.status == "active"
        ).first()
        if existing:
            raise HTTPException(
                status_code=409,
                detail=f"作品已存在: {existing.title} (SHA-256 相同)",
            )

        work_id = uuid.uuid4().hex
        ext = data.file_extension or data.file_name.split(".")[-1].lower() if "." in data.file_name else ""
        file_type = data.file_type or detect_file_type(ext)

        initial_stage = DEFAULT_FIRST_STAGE.get(file_type, None)

        work = Work(
            id=work_id,
            title=data.title or data.file_name,
            file_path="",
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
        work.creator_type = "illustrator"

        for tag_name in data.tags:
            work.tags.append(WorkTag(tag=sanitize_tag(tag_name)))

        try:
            self.db.add(work)
            self.db.commit()
            self.db.refresh(work)
        except Exception:
            self.db.rollback()
            raise
        return ApiResponse(data=_work_to_response(work))

    async def create_lowres_work(
        self,
        sha256: str,
        file_name: str,
        file_size: int,
        file_type: str,
        file_extension: str,
        title: Optional[str],
        description: Optional[str],
        tags_str: Optional[str],
        project_id: Optional[str],
        width: Optional[int],
        height: Optional[int],
        thumbnail,
    ) -> ApiResponse:
        existing = self.db.query(Work).filter(
            Work.sha256 == sha256, Work.status == "active"
        ).first()
        if existing:
            raise HTTPException(
                status_code=409,
                detail=f"作品已存在: {existing.title} (SHA-256 相同)",
            )

        work_id = uuid.uuid4().hex
        ext = file_extension or file_name.split(".")[-1].lower() if "." in file_name else ""
        ft = detect_file_type(ext) if not file_type or file_type == "image" else file_type

        thumb_dir = THUMBNAIL_DIR / work_id[:2]
        thumb_dir.mkdir(parents=True, exist_ok=True)
        thumb_content = await thumbnail.read()
        thumb_path = thumb_dir / f"{work_id}_thumb.jpg"
        with open(thumb_path, "wb") as f:
            f.write(thumb_content)

        user_tags = []
        if tags_str:
            user_tags = [t.strip() for t in tags_str.split(",") if t.strip()]

        initial_stage = DEFAULT_FIRST_STAGE.get(ft, None)

        work = Work(
            id=work_id,
            title=title or file_name,
            file_path="",
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
            work.tags.append(WorkTag(tag=sanitize_tag(tag_name)))

        try:
            self.db.add(work)
            self.db.commit()
            self.db.refresh(work)
        except Exception:
            self.db.rollback()
            raise
        return ApiResponse(data=_work_to_response(work))

    # ── 文件替换 ─────────────────────────────────────────────────────

    async def replace_work_file(
        self,
        work_id: str,
        file,
        notes: Optional[str],
    ) -> ApiResponse:
        work = self.db.query(Work).filter(Work.id == work_id).first()
        if not work:
            raise HTTPException(status_code=404, detail="作品不存在")

        ext = file.filename.split(".")[-1].lower() if "." in file.filename else ""
        if ext not in ALLOWED_EXTENSIONS:
            raise HTTPException(status_code=400, detail=f"不支持的文件类型: .{ext}")

        content = await file.read()
        if len(content) > MAX_FILE_SIZE:
            raise HTTPException(status_code=400, detail="文件大小超过 500MB 限制")

        # 1. 创建版本快照
        latest = self.db.query(WorkVersion).filter(
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
        self.db.add(version)

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
            self.db.commit()
            self.db.refresh(work)
        except Exception:
            self.db.rollback()
            raise
        return ApiResponse(
            message=f"文件已替换并创建版本快照 v{version_num}",
            data=_work_to_response(work),
        )

    # ── Fork ─────────────────────────────────────────────────────────

    def fork_work(self, work_id: str) -> ApiResponse:
        original = self.db.query(Work).filter(Work.id == work_id).first()
        if not original:
            raise HTTPException(status_code=404, detail="作品不存在")

        new_id = uuid.uuid4().hex

        new_file_path = ""
        if original.file_path and os.path.exists(original.file_path):
            new_dir = UPLOAD_DIR / new_id[:2] / new_id
            new_dir.mkdir(parents=True, exist_ok=True)
            new_file_path = str(new_dir / original.file_name)
            shutil.copy2(original.file_path, new_file_path)

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

        for tag in original.tags:
            fork.tags.append(WorkTag(tag=sanitize_tag(tag.tag)))

        self.db.add(fork)
        try:
            self.db.commit()
            self.db.refresh(fork)
        except Exception:
            self.db.rollback()
            raise
        return ApiResponse(
            message=f"已 Fork 作品 {original.title}",
            data=_work_to_response(fork),
        )

    # ── 版权管理 ─────────────────────────────────────────────────────

    def update_work_rights(self, work_id: str, data: RightsUpdate) -> ApiResponse:
        work = self.db.query(Work).filter(Work.id == work_id).first()
        if not work:
            raise HTTPException(status_code=404, detail="作品不存在")

        if data.rights is not None:
            work.rights = data.rights
        if data.license_type is not None:
            work.license_type = data.license_type

        try:
            self.db.commit()
            self.db.refresh(work)
        except Exception:
            self.db.rollback()
            raise
        return ApiResponse(
            message="版权信息已更新",
            data=_work_to_response(work),
        )

    def generate_rights_declaration(self, work_id: str) -> ApiResponse:
        work = self.db.query(Work).filter(Work.id == work_id).first()
        if not work:
            raise HTTPException(status_code=404, detail="作品不存在")

        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import mm
        from reportlab.lib import colors
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle

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
        story.append(Paragraph(
            f"Declaration Date: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}",
            body_style
        ))
        story.append(Spacer(1, 5*mm))

        story.append(Paragraph("Work Information / 作品信息", heading_style))
        work_info = [
            ["Title / 作品名称", work.title],
            ["Work ID / 作品 ID", work.id],
            ["File Name / 文件名称", work.file_name],
            ["File Type / 文件类型", work.file_type],
            ["File Size / 文件大小", f"{work.file_size:,d} bytes"],
            ["SHA-256", work.sha256 or "N/A"],
            ["Imported At / 导入时间",
             work.imported_at.strftime("%Y-%m-%d %H:%M UTC") if work.imported_at else "N/A"],
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

        story.append(Paragraph("Rights Information / 版权信息", heading_style))
        license_type = work.license_type or "Not specified / 未指定"
        story.append(Paragraph(f"License Type: {license_type}", body_style))

        if work.rights:
            for key, value in work.rights.items():
                story.append(Paragraph(f"{key}: {value}", body_style))
        else:
            story.append(Paragraph(
                "Rights Holder: Creator / 版权持有者: 创作者本人", body_style
            ))
            story.append(Paragraph(
                "This work is protected by copyright law. Unauthorized reproduction, "
                "distribution, modification, or commercial use is prohibited.",
                body_style
            ))

        story.append(Spacer(1, 8*mm))
        story.append(Paragraph("Legal Statement / 法律声明", heading_style))
        story.append(Paragraph(
            "This copyright declaration is issued in accordance with the Copyright Law "
            "of the People's Republic of China and relevant international copyright "
            "conventions. The creator and/or copyright holder possesses full moral "
            "and economic rights to this work.",
            body_style
        ))
        story.append(Paragraph(
            "No person may use, reproduce, modify, distribute, or communicate the "
            "whole or any part of this work without the copyright holder's permission.",
            body_style
        ))
        story.append(Spacer(1, 10*mm))

        story.append(Paragraph(
            "— OriSpark Auto-Generated / 自动生成 —",
            ParagraphStyle("Footer", parent=body_style, alignment=1)
        ))

        doc.build(story)
        buf.seek(0)

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

    # ── AI 标签推荐 ──────────────────────────────────────────────────

    async def suggest_tags_ai(self, data: AiTagRequest) -> ApiResponse:
        """AI 标签推荐: 基于作品内容使用 Ollama 分析并推荐标签 (回退到增强规则)."""
        from app.services.auto_tag_service import CATEGORY_KEYWORDS

        tags = set()

        file_name = data.file_name or ""
        file_type = data.file_type or ""

        type_tags = {
            "image": "图片", "audio": "音频", "video": "视频",
            "document": "文档", "design": "设计", "code": "代码",
        }
        if file_type in type_tags:
            tags.add(type_tags[file_type])

        ext = Path(file_name).suffix.lower().lstrip(".") if file_name else ""
        ext_map = {
            "jpg": "JPEG", "jpeg": "JPEG", "png": "PNG", "gif": "GIF",
            "mp4": "MP4", "mp3": "MP3", "pdf": "PDF", "psd": "PSD",
            "webp": "WebP", "svg": "SVG", "wav": "WAV", "mkv": "MKV",
        }
        if ext in ext_map:
            tags.add(ext_map[ext])

        if file_name:
            name_lower = Path(file_name).stem.lower().replace("_", " ").replace("-", " ")
            for category, keywords in CATEGORY_KEYWORDS.items():
                for kw in keywords:
                    if kw.lower() in name_lower:
                        tags.add(category)

        exif_data = data.exif_data or {}
        if exif_data:
            if "Model" in exif_data:
                tags.add("相机拍摄")
            if "GPSInfo" in exif_data:
                tags.add("有定位")

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

        ai_tags = set()
        try:
            from app.gateway.ollama import OllamaGateway
            gw = OllamaGateway()
            desc = data.description or ""
            ai_response = await gw.generate_description(
                work_title=file_name,
                work_type=file_type,
                language="zh",
            )
            for line in ai_response.strip().split("\n"):
                tag = line.strip().lstrip("- *#0123456789.").strip()
                if tag and len(tag) > 1 and len(tag) < 50:
                    ai_tags.add(tag)
        except Exception:
            pass

        all_tags = list(tags) + [t for t in ai_tags if t not in tags]

        return ApiResponse(data={
            "tags": all_tags[:15],
            "source": "rule+ai" if ai_tags else "rule",
        })

    # ── 批量导入 ─────────────────────────────────────────────────────

    async def import_folder(
        self,
        files,
        auto_create_project: bool,
    ) -> ApiResponse:
        """批量导入文件夹 — 自动按文件夹名创建项目，SHA-256 去重."""
        workspace_dir = Path("data/workspace")
        workspace_dir.mkdir(parents=True, exist_ok=True)

        imported = 0
        skipped = 0
        errors = []

        file_list = []
        for f in files:
            if f.filename:
                clean_name = Path(f.filename).name
                if not clean_name or clean_name in (".", ".."):
                    continue
                ext = Path(clean_name).suffix.lower()
                if ext and ext not in set(ALLOWED_EXTENSIONS):
                    continue
                file_list.append({"file": f, "clean_name": clean_name})

        if len(file_list) > 500:
            raise HTTPException(status_code=400, detail="单次导入最多500个文件")

        folder_map: dict[str, list[dict]] = {}
        for item in file_list:
            parts = Path(item["clean_name"]).parts[:-1] if Path(item["clean_name"]).parents else ()
            folder = "/".join(parts) if parts else ""
            folder_map.setdefault(folder, []).append(item)

        project_id = None
        if auto_create_project and folder_map:
            all_folders = [k for k in folder_map.keys() if k]
            if all_folders:
                project_name = all_folders[0].split("/")[-1] if "/" in all_folders[0] else all_folders[0]
                existing = self.db.query(Project).filter(Project.name == project_name).first()
                if existing:
                    project_id = existing.id
                else:
                    new_project = Project(
                        id=str(uuid.uuid4())[:32],
                        name=project_name,
                        description=f"Auto-created from folder import: {project_name}",
                    )
                    self.db.add(new_project)
                    self.db.flush()
                    project_id = new_project.id

        failed = 0
        for f_item in file_list:
            f = f_item["file"]
            clean_name = f_item["clean_name"]
            file_path_local = None
            try:
                content = await f.read()
                file_hash = hashlib.sha256(content).hexdigest()

                existing = self.db.query(Work).filter(Work.sha256 == file_hash).first()
                if existing:
                    skipped += 1
                    continue

                file_uuid = str(uuid.uuid4())[:32]
                file_dir = workspace_dir / file_uuid[:2] / file_uuid
                file_dir.mkdir(parents=True, exist_ok=True)

                ext = Path(clean_name).suffix.lower().lstrip(".") if "." in clean_name else ""
                safe_filename = f"{file_uuid}.{ext}" if ext else f"{file_uuid}.dat"
                file_path_local = file_dir / safe_filename
                file_path_local.write_bytes(content)

                if ext not in ALLOWED_EXTENSIONS:
                    file_path_local.unlink()
                    raise ValueError(f"Unsupported extension: {ext}")

                mime = f.content_type or "application/octet-stream"
                file_type = detect_file_type(ext)
                initial_stage = DEFAULT_FIRST_STAGE.get(file_type, None)

                work = Work(
                    id=file_uuid,
                    title=Path(clean_name).stem,
                    file_path=str(file_path_local.relative_to(workspace_dir.parent)),
                    mime_type=mime,
                    file_size=len(content),
                    file_type=file_type,
                    sha256=file_hash,
                    project_id=project_id,
                    current_stage=initial_stage,
                    creator_type=_detect_creator_type(file_type, None, {}),
                )
                self.db.add(work)
                imported += 1
            except Exception as e:
                errors.append({"filename": clean_name, "error": str(e)})
                if file_path_local and file_path_local.exists():
                    file_path_local.unlink()
                failed += 1

        try:
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise

        return ApiResponse(data={
            "imported": imported,
            "skipped_duplicate": skipped,
            "failed": failed,
            "errors": errors[:10],
        })

    async def import_project_package(
        self,
        project_name: str,
        project_files: Optional[str],
        description: Optional[str],
    ) -> ApiResponse:
        """导入视频项目包 (P3-1)."""
        files_data = None
        if project_files:
            try:
                files_data = json.loads(project_files)
            except json.JSONDecodeError:
                raise HTTPException(status_code=400, detail="project_files 必须是有效的 JSON")

        work = Work(
            id=str(uuid.uuid4())[:32],
            title=project_name,
            file_path="",
            file_name=project_name,
            file_size=0,
            file_type="video",
            file_extension="project",
            description=description,
            is_project_package=True,
            project_files=files_data,
            import_mode="full",
        )

        self.db.add(work)
        try:
            self.db.commit()
            self.db.refresh(work)
        except Exception:
            self.db.rollback()
            raise

        return ApiResponse(
            message="项目包已导入",
            data=_work_to_response(work),
        )

    # ── Culling ──────────────────────────────────────────────────────

    async def batch_cull(self, work_ids: list[str], cull_status: Optional[str],
                         cull_rating: Optional[int], color_label: Optional[str]) -> ApiResponse:
        """批量策展 (P2-3). 更新作品的策展状态、评分和颜色标签."""
        updated = 0
        for wid in work_ids:
            work = self.db.query(Work).filter(Work.id == wid).first()
            if not work:
                continue
            if cull_status is not None:
                work.cull_status = cull_status
            if cull_rating is not None:
                work.cull_rating = cull_rating
            if color_label is not None:
                work.color_label = color_label
            updated += 1
        try:
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise
        return ApiResponse(message=f"已更新 {updated} 个作品", data={"updated": updated})

    def process_raw(self, work_id: str, output_format: str) -> ApiResponse:
        """Process a RAW photo into a standard JPEG/WebP variant (stub)."""
        work = self.db.query(Work).filter(Work.id == work_id).first()
        if not work:
            raise HTTPException(status_code=404, detail="作品不存在")
        if not work.is_raw_original:
            raise HTTPException(status_code=400, detail="该作品不是 RAW 格式")

        variant_id = uuid.uuid4().hex[:32]
        work.raw_processed_variant_id = variant_id
        try:
            self.db.commit()
            self.db.refresh(work)
        except Exception:
            self.db.rollback()
            raise

        return ApiResponse(
            message=f"RAW 处理任务已创建 (variant: {variant_id})",
            data=_work_to_response(work),
        )

    def single_cull(self, work_id: str, action: str) -> ApiResponse:
        """Update culling state for a single work (P2-3)."""
        work = self.db.query(Work).filter(Work.id == work_id).first()
        if not work:
            raise HTTPException(status_code=404, detail="作品不存在")

        action = action.strip().lower()

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
                raise HTTPException(status_code=422, detail=f"Invalid action: {action}")
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
                raise HTTPException(status_code=422, detail=f"Invalid action: {action}")
            if label not in ("red", "yellow", "green", "blue"):
                raise HTTPException(status_code=422, detail=f"Invalid color: {label}")
            work.color_label = label
        else:
            raise HTTPException(status_code=422, detail=f"Unknown action: {action}")

        try:
            self.db.commit()
            self.db.refresh(work)
        except Exception:
            self.db.rollback()
            raise
        return ApiResponse(message=f"Cull state updated ({action})", data=_work_to_response(work))
