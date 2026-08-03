"""版本管理 + 项目分组 API 路由 — 对应: docs/modules-v5/01-creative-assets.md
端点: 9 (versions)

业务逻辑已提取至 version_service.py.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Optional

from app.database import get_db
from app.schemas.common import ApiResponse
from app.deps import require_auth
from app.services.version_service import (
    list_versions, get_version, create_version, rollback_version,
    list_projects, create_project, update_project, delete_project,
    assign_to_project,
)
from app.schemas.work import ProjectCreate

router = APIRouter()


class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    cover_work_id: Optional[str] = None


# ==================== 版本管理 ====================


@router.get("/works/{work_id}/versions", response_model=ApiResponse)
def list_versions_endpoint(work_id: str, db: Session = Depends(get_db)):
    """获取作品版本列表."""
    result = list_versions(db, work_id)
    if result is None:
        raise HTTPException(status_code=404, detail="作品不存在")
    return ApiResponse(data=result)


@router.get("/works/{work_id}/versions/{version_id}", response_model=ApiResponse)
def get_version_endpoint(work_id: str, version_id: str, db: Session = Depends(get_db)):
    """获取单个版本详情."""
    result = get_version(db, work_id, version_id)
    if not result:
        raise HTTPException(status_code=404, detail="版本不存在")
    return ApiResponse(data=result)


@router.post("/works/{work_id}/versions", response_model=ApiResponse, dependencies=[Depends(require_auth)])
def create_version_endpoint(work_id: str, notes: Optional[str] = None, db: Session = Depends(get_db)):
    """创建作品版本快照."""
    result = create_version(db, work_id, notes)
    if not result:
        raise HTTPException(status_code=404, detail="作品不存在")
    return ApiResponse(data=result, message=result.get("message", "版本创建成功"))


@router.post("/works/{work_id}/rollback/{version_id}", response_model=ApiResponse, dependencies=[Depends(require_auth)])
def rollback_version_endpoint(work_id: str, version_id: str, db: Session = Depends(get_db)):
    """回滚到指定版本."""
    result = rollback_version(db, work_id, version_id)
    if not result:
        raise HTTPException(status_code=404, detail="版本不存在")
    return ApiResponse(message=result)


# ==================== 项目管理 ====================


@router.get("/projects", response_model=ApiResponse)
def list_projects_endpoint(db: Session = Depends(get_db)):
    """获取项目列表."""
    return ApiResponse(data=list_projects(db))


@router.post("/projects", response_model=ApiResponse, dependencies=[Depends(require_auth)])
def create_project_endpoint(data: ProjectCreate, db: Session = Depends(get_db)):
    """创建项目."""
    return ApiResponse(data=create_project(db, data), message="项目创建成功")


@router.patch("/projects/{project_id}", response_model=ApiResponse, dependencies=[Depends(require_auth)])
def update_project_endpoint(project_id: str, data: ProjectUpdate, db: Session = Depends(get_db)):
    """更新项目."""
    result = update_project(db, project_id, data.model_dump(exclude_unset=True))
    if not result:
        raise HTTPException(status_code=404, detail="项目不存在")
    return ApiResponse(message=result)


@router.delete("/projects/{project_id}", response_model=ApiResponse, dependencies=[Depends(require_auth)])
def delete_project_endpoint(project_id: str, db: Session = Depends(get_db)):
    """删除项目 (关联作品的项目字段置空)."""
    result = delete_project(db, project_id)
    if not result:
        raise HTTPException(status_code=404, detail="项目不存在")
    return ApiResponse(message=result)


@router.post("/works/{work_id}/assign-project/{project_id}", response_model=ApiResponse, dependencies=[Depends(require_auth)])
def assign_to_project_endpoint(work_id: str, project_id: str, db: Session = Depends(get_db)):
    """将作品分配到项目."""
    result = assign_to_project(db, work_id, project_id)
    if result is None:
        raise HTTPException(status_code=404, detail="作品或项目不存在")
    return ApiResponse(message="作品已分配到项目")
