"""版本管理 + 项目分组 API 路由 — 对应: docs/modules-v5/01-creative-assets.md
端点: 9 (versions)

业务逻辑已提取至 version_service.py.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from typing import Optional

from app.database import get_db
from app.schemas.common import ApiResponse
from app.deps import require_auth, get_current_user_id
from app.services.version_service import (
    list_versions, get_version, create_version, rollback_version,
    list_projects, create_project, update_project, assign_to_project,
)
from app.services.work_version_service import (
    delete_version, get_version_history_timeline,
)
from app.services.project_service import (
    add_work_to_project, remove_work_from_project, list_project_works,
    delete_project,
)
from app.schemas.work import ProjectCreate

router = APIRouter()


class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    cover_work_id: Optional[str] = None


class VersionDeleteResponse(BaseModel):
    success: bool
    message: Optional[str] = None
    error: Optional[str] = None


class VersionCreateRequest(BaseModel):
    notes: Optional[str] = None


class ProjectWorkAddRequest(BaseModel):
    work_id: str = Field(..., min_length=1, max_length=32)


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
def create_version_endpoint(work_id: str, body: VersionCreateRequest = None, db: Session = Depends(get_db)):
    """创建作品版本快照."""
    notes = body.notes if body else None
    result = create_version(db, work_id, notes)
    if not result:
        raise HTTPException(status_code=404, detail="作品不存在")
    return ApiResponse(data=result, message=result.get("message", "版本创建成功"))


@router.delete("/works/{work_id}/versions/{version_id}", response_model=ApiResponse, dependencies=[Depends(require_auth)])
def delete_version_endpoint(work_id: str, version_id: str, db: Session = Depends(get_db)):
    """删除版本（不能删除最后一个）."""
    user_id = get_current_user_id()
    result = delete_version(db, version_id, user_id)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    return ApiResponse(data=result)


@router.get("/works/{work_id}/version-history", response_model=ApiResponse)
def version_history_endpoint(work_id: str, db: Session = Depends(get_db)):
    """获取版本历史时间线."""
    result = get_version_history_timeline(db, work_id)
    if result is None:
        raise HTTPException(status_code=404, detail="作品不存在或无版本")
    return ApiResponse(data=result)


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
    result = delete_project(db, project_id, "current_user")
    if not result["success"]:
        raise HTTPException(status_code=404, detail=result["error"])
    return ApiResponse(message=result["message"])


@router.get("/projects/{project_id}/works", response_model=ApiResponse)
def list_project_works_endpoint(project_id: str, db: Session = Depends(get_db)):
    """列出项目内作品."""
    result = list_project_works(db, project_id)
    if result is None:
        raise HTTPException(status_code=404, detail="项目不存在")
    return ApiResponse(data=result)


@router.post("/projects/{project_id}/works", response_model=ApiResponse, dependencies=[Depends(require_auth)])
def add_work_to_project_endpoint(project_id: str, body: ProjectWorkAddRequest, db: Session = Depends(get_db)):
    """添加作品到项目."""
    result = add_work_to_project(db, project_id, body.work_id)
    if not result["success"]:
        raise HTTPException(status_code=404, detail=result["error"])
    return ApiResponse(data=result)


@router.delete("/projects/{project_id}/works/{work_id}", response_model=ApiResponse, dependencies=[Depends(require_auth)])
def remove_work_from_project_endpoint(project_id: str, work_id: str, db: Session = Depends(get_db)):
    """移除作品."""
    result = remove_work_from_project(db, project_id, work_id)
    if not result["success"]:
        raise HTTPException(status_code=404, detail=result["error"])
    return ApiResponse(data=result)


@router.post("/works/{work_id}/assign-project/{project_id}", response_model=ApiResponse, dependencies=[Depends(require_auth)])
def assign_to_project_endpoint(work_id: str, project_id: str, db: Session = Depends(get_db)):
    """将作品分配到项目."""
    result = assign_to_project(db, work_id, project_id)
    if result is None:
        raise HTTPException(status_code=404, detail="作品或项目不存在")
    return ApiResponse(message="作品已分配到项目")
