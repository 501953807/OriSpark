"""作品管理 API 路由 — 对应: docs/modules-v5/01-creative-assets.md
Phase 1.1: 自动元数据提取, Phase 1.3: 视频缩略图修正, Phase 1.5: 存证状态友好化
端点: 25 (works)

业务逻辑已提取至 work_manager_service.py.
"""

import logging
import os
import re
import uuid
from pathlib import Path
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query, Body
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.work import (
    WorkUpdate, WorkTagCreate, HashOnlyUpload, RightsUpdate, AiTagRequest,
)
from app.schemas.common import ApiResponse
from app.services.work_manager_service import WorkManagerService
from app.deps import require_auth
from app.services.work_service import detect_file_type

router = APIRouter()


class RenameTagPayload(BaseModel):
    new_tag: str


class CullBatchRequest(BaseModel):
    work_ids: list[str]
    cull_status: Optional[str] = None
    cull_rating: Optional[int] = None
    color_label: Optional[str] = None


class ProcessRawRequest(BaseModel):
    output_format: str = Field(default="jpeg", pattern="^(jpeg|webp)$")


class CullActionRequest(BaseModel):
    action: str = Field(..., description="keep | reject | rate_1 .. rate_5 | color_red | color_yellow | color_green | color_blue")


# ==============================
# Security sanitization helpers
# ==============================

def sanitize_tag(tag: str) -> str:
    """Sanitize a tag string by removing HTML tags, control characters, and limiting length."""
    if not tag or not isinstance(tag, str):
        return ""
    clean_tag = re.sub(r'<[^>]*>', '', tag)
    clean_tag = re.sub(r'[\x00-\x1f\x7f]', '', clean_tag)
    clean_tag = clean_tag.strip()
    return clean_tag[:100]


def sanitize_filename(filename: str) -> str:
    """Sanitize a filename by removing dangerous characters and path components."""
    if not filename or not isinstance(filename, str):
        return "uploaded_file"
    filename = os.path.basename(filename)
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
    filename = re.sub(r'[\x00-\x1f\x7f]', '', filename)
    filename = filename.strip()
    if not filename:
        filename = "uploaded_file"
    return filename


# ═══════════════════════════════════════════
# Phase 1.1: 自动元数据提取辅助函数 (纯工具函数)
# ═══════════════════════════════════════════

def _extract_title_from_filename(filename: str) -> str:
    cleaned_name = sanitize_filename(filename)
    name = os.path.splitext(cleaned_name)[0]
    name = re.sub(r'^[\d\-_]{6,}', '', name).strip('_ ')
    name = re.sub(r'^(IMG|DSC|PXL|DSCF|MVI|VID)_?\d*[_\-]?', '', name, flags=re.IGNORECASE).strip('_ ')
    return name or "未命名作品"


# ============================================================
# 1. POST /works — create_work
# ============================================================

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
    svc = WorkManagerService(db)
    return await svc.create_work(title, description, tags, project_id, allow_duplicate, file, user_id)


# ============================================================
# 2. GET /works — list_works
# ============================================================

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
    camera: Optional[str] = Query(None, deprecated="Use camera_make or camera_model instead"),
    cull_status: Optional[str] = Query(None),
    cull_rating: Optional[int] = Query(None, ge=0, le=5),
    color_label: Optional[str] = Query(None),
    sort_by: str = Query(default="imported_at"),
    sort_order: str = Query(default="desc"),
    user_id: str = Depends(require_auth),
    db: Session = Depends(get_db),
):
    """获取作品列表 (分页、筛选、搜索)."""
    svc = WorkManagerService(db)
    return svc.list_works(
        page=page, page_size=page_size,
        file_type=file_type, status=status, tag=tag,
        search=search, project_id=project_id, stage=stage,
        license_type=license_type,
        camera_make=camera_make, camera_model=camera_model,
        lens=lens, iso=iso, aperture=aperture,
        focal_length=focal_length, shutter_speed=shutter_speed,
        date_from=date_from, date_to=date_to,
        gps_lat=gps_lat, gps_lon=gps_lon, camera=camera,
        cull_status=cull_status, cull_rating=cull_rating,
        color_label=color_label, sort_by=sort_by, sort_order=sort_order,
    )


# ============================================================
# 3. GET /works/{work_id} — get_work
# ============================================================

@router.get("/works/{work_id}", response_model=ApiResponse)
def get_work(work_id: str, user_id: str = Depends(require_auth), db: Session = Depends(get_db)):
    """获取作品详情."""
    svc = WorkManagerService(db)
    return svc.get_work(work_id)


# ============================================================
# 4. PATCH /works/{work_id} — update_work
# ============================================================

@router.patch("/works/{work_id}", response_model=ApiResponse)
def update_work(work_id: str, data: WorkUpdate, user_id: str = Depends(require_auth), db: Session = Depends(get_db)):
    """更新作品信息."""
    svc = WorkManagerService(db)
    return svc.update_work(work_id, data)


# ============================================================
# 5. DELETE /works/{work_id} — delete_work
# ============================================================

@router.delete("/works/{work_id}", response_model=ApiResponse)
def delete_work(work_id: str, user_id: str = Depends(require_auth), db: Session = Depends(get_db)):
    """软删除作品 (移入回收站)."""
    svc = WorkManagerService(db)
    return svc.delete_work(work_id)


# ============================================================
# 6. POST /works/{work_id}/hash — recompute_hash
# ============================================================

@router.post("/works/{work_id}/hash", response_model=ApiResponse)
def recompute_hash(work_id: str, user_id: str = Depends(require_auth), db: Session = Depends(get_db)):
    """重新计算作品 SHA-256 哈希."""
    svc = WorkManagerService(db)
    return svc.recompute_hash(work_id)


# ============================================================
# 7. GET /works/{work_id}/preview — get_preview_url
# ============================================================

@router.get("/works/{work_id}/preview")
def get_preview_url(work_id: str, user_id: str = Depends(require_auth), db: Session = Depends(get_db)):
    """获取作品预览信息."""
    svc = WorkManagerService(db)
    return svc.get_preview_url(work_id)


# ============================================================
# 8. GET /tags — list_tags
# ============================================================

@router.get("/tags", response_model=ApiResponse)
def list_tags(user_id: str = Depends(require_auth), db: Session = Depends(get_db)):
    """获取所有标签 (含计数)."""
    svc = WorkManagerService(db)
    return svc.list_tags()


# ============================================================
# 9. POST /works/{work_id}/tags — add_tag
# ============================================================

@router.post("/works/{work_id}/tags", response_model=ApiResponse)
def add_tag(work_id: str, data: WorkTagCreate, user_id: str = Depends(require_auth), db: Session = Depends(get_db)):
    """为作品添加标签."""
    svc = WorkManagerService(db)
    return svc.add_tag(work_id, data)


# ============================================================
# 10. DELETE /works/{work_id}/tags/{tag_id} — remove_tag
# ============================================================

@router.delete("/works/{work_id}/tags/{tag_id}", response_model=ApiResponse)
def remove_tag(work_id: str, tag_id: str, user_id: str = Depends(require_auth), db: Session = Depends(get_db)):
    """移除作品标签."""
    svc = WorkManagerService(db)
    return svc.remove_tag(work_id, tag_id)


# ============================================================
# 11. PATCH /tags/{old_tag} — rename_tag
# ============================================================

@router.patch("/tags/{old_tag}", response_model=ApiResponse)
def rename_tag(old_tag: str, data: RenameTagPayload = Body(...), user_id: str = Depends(require_auth), db: Session = Depends(get_db)):
    """重命名全局标签."""
    svc = WorkManagerService(db)
    return svc.rename_tag(old_tag, data.new_tag.strip())


# ============================================================
# 12. DELETE /tags/{tag_name} — delete_global_tag
# ============================================================

@router.delete("/tags/{tag_name}", response_model=ApiResponse)
def delete_global_tag(tag_name: str, user_id: str = Depends(require_auth), db: Session = Depends(get_db)):
    """删除全局标签 (移除所有使用该标签的作品记录)."""
    svc = WorkManagerService(db)
    return svc.delete_global_tag(tag_name)


# ============================================================
# 13. GET /tags/suggest — suggest_tags (纯函数，无需 DB)
# ============================================================

@router.get("/tags/suggest")
def suggest_tags(query: str = Query(...), user_id: str = Depends(require_auth), db: Session = Depends(get_db)):
    """标签智能联想."""
    from app.services.auto_tag_service import suggest_tags
    suggestions = suggest_tags(query)
    return ApiResponse(data=suggestions)


# ============================================================
# 14. POST /works/hash-only — create_hash_only_work
# ============================================================

@router.post("/works/hash-only", response_model=ApiResponse)
def create_hash_only_work(data: HashOnlyUpload, user_id: str = Depends(require_auth), db: Session = Depends(get_db)):
    """仅存储 SHA-256 哈希的作品记录."""
    svc = WorkManagerService(db)
    return svc.create_hash_only_work(data)


# ============================================================
# 15. POST /works/lowres — create_lowres_work
# ============================================================

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
    svc = WorkManagerService(db)
    return await svc.create_lowres_work(
        sha256=sha256, file_name=file_name, file_size=file_size,
        file_type=file_type, file_extension=file_extension,
        title=title, description=description, tags_str=tags,
        project_id=project_id, width=width, height=height,
        thumbnail=thumbnail,
    )


# ============================================================
# 16. POST /works/{work_id}/replace — replace_work_file
# ============================================================

@router.post("/works/{work_id}/replace", response_model=ApiResponse)
async def replace_work_file(
    work_id: str,
    file: UploadFile = File(...),
    notes: Optional[str] = Form(default=None),
    user_id: str = Depends(require_auth),
    db: Session = Depends(get_db),
):
    """替换作品文件: 自动创建版本快照后替换文件."""
    svc = WorkManagerService(db)
    return await svc.replace_work_file(work_id, file, notes)


# ============================================================
# 17. POST /works/{work_id}/fork — fork_work
# ============================================================

@router.post("/works/{work_id}/fork", response_model=ApiResponse)
def fork_work(work_id: str, user_id: str = Depends(require_auth), db: Session = Depends(get_db)):
    """Fork 作品: 创建副本并链接到原作品."""
    svc = WorkManagerService(db)
    return svc.fork_work(work_id)


# ============================================================
# 18. PATCH /works/{work_id}/rights — update_work_rights
# ============================================================

@router.patch("/works/{work_id}/rights", response_model=ApiResponse)
def update_work_rights(work_id: str, data: RightsUpdate, user_id: str = Depends(require_auth), db: Session = Depends(get_db)):
    """更新作品版权信息."""
    svc = WorkManagerService(db)
    return svc.update_work_rights(work_id, data)


# ============================================================
# 19. POST /works/{work_id}/rights-declaration — generate_rights_declaration
# ============================================================

@router.post("/works/{work_id}/rights-declaration", response_model=ApiResponse)
def generate_rights_declaration(work_id: str, user_id: str = Depends(require_auth), db: Session = Depends(get_db)):
    """生成版权声明 PDF."""
    svc = WorkManagerService(db)
    return svc.generate_rights_declaration(work_id)


# ============================================================
# 20. POST /tags/suggest-ai — suggest_tags_ai (纯业务逻辑)
# ============================================================

@router.post("/tags/suggest-ai", response_model=ApiResponse)
async def suggest_tags_ai(data: AiTagRequest, user_id: str = Depends(require_auth), db: Session = Depends(get_db)):
    """AI 标签推荐: 基于作品内容使用 Ollama 分析并推荐标签 (回退到增强规则)."""
    svc = WorkManagerService(db)
    return await svc.suggest_tags_ai(data)


# ============================================================
# 21. POST /works/import-folder — import_folder
# ============================================================

@router.post("/works/import-folder", response_model=ApiResponse)
async def import_folder(
    files: list[UploadFile] = File(...),
    auto_create_project: bool = Form(True),
    user_id: str = Depends(require_auth),
    db: Session = Depends(get_db),
):
    """批量导入文件夹."""
    svc = WorkManagerService(db)
    return await svc.import_folder(files, auto_create_project)


# ============================================================
# 22. POST /works/import-project — import_project_package
# ============================================================

@router.post("/works/import-project", response_model=ApiResponse)
async def import_project_package(
    project_name: str = Form(...),
    project_files: Optional[str] = Form(default=None),
    description: Optional[str] = Form(default=None),
    user_id: str = Depends(require_auth),
    db: Session = Depends(get_db),
):
    """导入视频项目包."""
    svc = WorkManagerService(db)
    return svc.import_project_package(project_name, project_files, description)


# ============================================================
# 23. POST /works/cull-batch — batch_cull
# ============================================================

@router.post("/works/cull-batch", response_model=ApiResponse)
async def batch_cull(
    data: CullBatchRequest,
    user_id: str = Depends(require_auth),
    db: Session = Depends(get_db),
):
    """批量策展 (P2-3)."""
    svc = WorkManagerService(db)
    return svc.batch_cull(data.work_ids, data.cull_status, data.cull_rating, data.color_label)


# ============================================================
# 24. POST /works/{work_id}/process-raw — process_raw
# ============================================================

@router.post("/works/{work_id}/process-raw", response_model=ApiResponse)
def process_raw(
    work_id: str,
    data: ProcessRawRequest = Body(ProcessRawRequest()),
    user_id: str = Depends(require_auth),
    db: Session = Depends(get_db),
):
    """处理 RAW 照片为 JPEG/WebP 变体."""
    svc = WorkManagerService(db)
    return svc.process_raw(work_id, data.output_format)


# ============================================================
# 25. PATCH /works/{work_id}/cull — single_cull
# ============================================================

@router.patch("/works/{work_id}/cull", response_model=ApiResponse)
def single_cull(
    work_id: str,
    data: CullActionRequest,
    user_id: str = Depends(require_auth),
    db: Session = Depends(get_db),
):
    """单个作品策展操作 (P2-3)."""
    svc = WorkManagerService(db)
    return svc.single_cull(work_id, data.action)


# ============================================================
# 26. GET /works/{work_id}/project-package — get_project_package
# ============================================================

@router.get("/works/{work_id}/project-package", response_model=ApiResponse)
def get_project_package(
    work_id: str,
    user_id: str = Depends(require_auth),
    db: Session = Depends(get_db),
):
    """获取视频项目包数据 (timeline/materials/effects)."""
    svc = WorkManagerService(db)
    return svc.get_project_package(work_id)
