"""批量操作 + 回收站 + 文件夹导入 API 路由 — 对应: docs/modules-v5/01-creative-assets.md
Phase 1.2: POST /works/import-folder (递归+去重+自动项目)
端点: 7 (batch_works)

业务逻辑已提取至 batch_work_service.py.
"""

import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import require_auth
from app.schemas.common import ApiResponse
from app.services.batch_work_service import (
    batch_edit_works, update_custom_metadata, batch_delete,
    permanent_delete, import_folder, empty_trash, restore_work,
)

router = APIRouter()
logger = logging.getLogger(__name__)


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
def batch_edit_works_endpoint(data: BatchEditPayload, db: Session = Depends(get_db)):
    """批量编辑作品标签/项目."""
    if not data.work_ids:
        raise HTTPException(status_code=400, detail="work_ids 不能为空")
    count = batch_edit_works(db, data.work_ids, data.model_dump(exclude_unset=True))
    return ApiResponse(message=f"已更新 {count} 个作品")


@router.post("/works/{work_id}/metadata", response_model=ApiResponse, dependencies=[Depends(require_auth)])
def update_custom_metadata_endpoint(work_id: str, data: UpdateCustomMetadataPayload, db: Session = Depends(get_db)):
    """更新作品自定义元数据."""
    if not update_custom_metadata(db, work_id, data.metadata):
        raise HTTPException(status_code=404, detail="作品不存在")
    return ApiResponse(message="元数据已更新")


@router.post("/works/batch-delete", response_model=ApiResponse, dependencies=[Depends(require_auth)])
def batch_delete_endpoint(data: List[str], db: Session = Depends(get_db)):
    """批量软删除."""
    count = batch_delete(db, data)
    return ApiResponse(message=f"已删除 {count} 个作品")


@router.delete("/works/{work_id}/permanent", response_model=ApiResponse, dependencies=[Depends(require_auth)])
def permanent_delete_endpoint(work_id: str, db: Session = Depends(get_db)):
    """永久删除作品 (包括文件)."""
    if not permanent_delete(db, work_id):
        raise HTTPException(status_code=404, detail="作品不存在或未在回收站中")
    return ApiResponse(message="作品已永久删除")


@router.post("/works/import-folder", response_model=ApiResponse, dependencies=[Depends(require_auth)])
def import_folder_endpoint(data: ImportFolderPayload, db: Session = Depends(get_db)):
    """文件夹批量导入 — 递归读取、去重、自动项目创建、生成缩略图."""
    result = import_folder(db, data.folder_path, data.create_projects, data.skip_duplicates)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return ApiResponse(data=result)


@router.post("/works/empty-trash", response_model=ApiResponse, dependencies=[Depends(require_auth)])
def empty_trash_endpoint(db: Session = Depends(get_db)):
    """清空回收站."""
    count = empty_trash(db)
    return ApiResponse(message=f"已清空 {count} 个作品")


@router.post("/works/{work_id}/restore", response_model=ApiResponse, dependencies=[Depends(require_auth)])
def restore_work_endpoint(work_id: str, db: Session = Depends(get_db)):
    """从回收站恢复作品."""
    if not restore_work(db, work_id):
        raise HTTPException(status_code=404, detail="作品不在回收站中")
    return ApiResponse(message="作品已恢复")
