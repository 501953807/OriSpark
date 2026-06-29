"""版本管理 + 项目分组 API 路由 — 对应: docs/modules-v3/01-creative-assets.md
端点: 9 (versions)"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime
import shutil
from pathlib import Path

from app.database import get_db
from app.models.work import Work, WorkVersion, WorkTag, Project
from app.services.hasher import compute_sha256
from app.schemas.common import ApiResponse
from app.schemas.work import ProjectCreate, ProjectResponse

# 使用独立 router 前缀，在 main.py 中挂载到 /api
router = APIRouter()

# ==================== 版本管理 ====================

@router.get("/works/{work_id}/versions", response_model=ApiResponse[list])
def list_versions(work_id: str, db: Session = Depends(get_db)):
    """获取作品版本列表."""
    work = db.query(Work).filter(Work.id == work_id).first()
    if not work:
        raise HTTPException(status_code=404, detail="作品不存在")

    versions = db.query(WorkVersion).filter(
        WorkVersion.work_id == work_id
    ).order_by(WorkVersion.version_num.desc()).all()

    return ApiResponse(data=[
        {
            "id": v.id, "version_num": v.version_num,
            "file_hash": v.file_hash, "file_path": v.file_path,
            "file_size": v.file_size,
            "notes": v.notes,
            "created_at": v.created_at.isoformat() if v.created_at else None,
        }
        for v in versions
    ])


@router.get("/works/{work_id}/versions/{version_id}", response_model=ApiResponse[dict])
def get_version(work_id: str, version_id: str, db: Session = Depends(get_db)):
    """获取单个版本详情."""
    version = db.query(WorkVersion).filter(
        WorkVersion.id == version_id,
        WorkVersion.work_id == work_id,
    ).first()
    if not version:
        raise HTTPException(status_code=404, detail="版本不存在")
    return ApiResponse(data={
        "id": version.id,
        "work_id": version.work_id,
        "version_num": version.version_num,
        "file_hash": version.file_hash,
        "file_path": version.file_path,
        "file_size": version.file_size,
        "notes": version.notes,
        "created_at": version.created_at.isoformat() if version.created_at else None,
    })


@router.post("/works/{work_id}/versions", response_model=ApiResponse)
def create_version(work_id: str, notes: Optional[str] = None, db: Session = Depends(get_db)):
    """创建作品版本快照."""
    work = db.query(Work).filter(Work.id == work_id).first()
    if not work:
        raise HTTPException(status_code=404, detail="作品不存在")

    # 获取当前版本号
    latest = db.query(WorkVersion).filter(
        WorkVersion.work_id == work_id
    ).order_by(WorkVersion.version_num.desc()).first()

    version_num = (latest.version_num + 1) if latest else 1

    # 创建版本
    version = WorkVersion(
        work_id=work_id,
        version_num=version_num,
        file_hash=work.sha256 or compute_sha256(work.file_path),
        file_path=work.file_path,
        file_size=work.file_size,
        notes=notes,
    )
    db.add(version)
    db.commit()
    db.refresh(version)

    return ApiResponse(
        message=f"版本 {version_num} 已创建",
        data={"id": version.id, "version_num": version_num},
    )


@router.post("/works/{work_id}/rollback/{version_id}", response_model=ApiResponse)
def rollback_version(work_id: str, version_id: str, db: Session = Depends(get_db)):
    """回滚到指定版本 (更新作品文件哈希和路径)."""
    work = db.query(Work).filter(Work.id == work_id).first()
    if not work:
        raise HTTPException(status_code=404, detail="作品不存在")

    version = db.query(WorkVersion).filter(
        WorkVersion.id == version_id,
        WorkVersion.work_id == work_id,
    ).first()
    if not version:
        raise HTTPException(status_code=404, detail="版本不存在")

    # 回滚文件哈希
    work.sha256 = version.file_hash
    db.commit()

    return ApiResponse(message=f"已回滚到版本 {version.version_num}")


# ==================== 项目管理 ====================

@router.get("/projects", response_model=ApiResponse[list])
def list_projects(db: Session = Depends(get_db)):
    """获取项目列表."""
    projects = db.query(Project).order_by(Project.created_at.desc()).all()

    return ApiResponse(data=[
        {
            "id": p.id, "name": p.name, "description": p.description,
            "cover_work_id": p.cover_work_id,
            "work_count": db.query(Work).filter(
                Work.project_id == p.id
            ).count(),
            "created_at": p.created_at.isoformat() if p.created_at else None,
            "updated_at": p.updated_at.isoformat() if p.updated_at else None,
        }
        for p in projects
    ])


@router.post("/projects", response_model=ApiResponse)
def create_project(data: ProjectCreate, db: Session = Depends(get_db)):
    """创建项目."""
    project = Project(
        name=data.name,
        description=data.description,
        cover_work_id=data.cover_work_id,
    )
    db.add(project)
    db.commit()
    db.refresh(project)

    return ApiResponse(data={"id": project.id, "name": project.name})


@router.patch("/projects/{project_id}", response_model=ApiResponse)
def update_project(project_id: str, data: dict, db: Session = Depends(get_db)):
    """更新项目."""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    for key in ["name", "description", "cover_work_id"]:
        if key in data:
            setattr(project, key, data[key])
    db.commit()

    return ApiResponse(message="项目已更新")


@router.delete("/projects/{project_id}", response_model=ApiResponse)
def delete_project(project_id: str, db: Session = Depends(get_db)):
    """删除项目 (关联作品的项目字段置空)."""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    # 解除关联
    db.query(Work).filter(Work.project_id == project_id).update(
        {"project_id": None}
    )
    db.delete(project)
    db.commit()

    return ApiResponse(message="项目已删除")


@router.post("/works/{work_id}/assign-project/{project_id}", response_model=ApiResponse)
def assign_to_project(work_id: str, project_id: str, db: Session = Depends(get_db)):
    """将作品分配到项目."""
    work = db.query(Work).filter(Work.id == work_id).first()
    if not work:
        raise HTTPException(status_code=404, detail="作品不存在")

    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    work.project_id = project_id
    db.commit()

    return ApiResponse(message=f"已分配到项目: {project.name}")
