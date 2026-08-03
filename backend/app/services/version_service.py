# -*- coding: utf-8 -*-
"""版本管理 + 项目分组服务层 — 从 versions.py 提取的业务逻辑."""

from typing import Optional

from sqlalchemy.orm import Session

from app.models.work import Work, WorkVersion, Project
from app.schemas.work import ProjectCreate
from app.services.hasher import compute_sha256


# ============================================================================
# 版本管理
# ============================================================================


def list_versions(db: Session, work_id: str) -> Optional[list]:
    """获取作品版本列表."""
    work = db.query(Work).filter(Work.id == work_id).first()
    if not work:
        return None

    versions = db.query(WorkVersion).filter(
        WorkVersion.work_id == work_id
    ).order_by(WorkVersion.version_num.desc()).all()

    return [
        {
            "id": v.id, "version_num": v.version_num,
            "file_hash": v.file_hash, "file_path": v.file_path,
            "file_size": v.file_size,
            "notes": v.notes,
            "created_at": v.created_at.isoformat() if v.created_at else None,
        }
        for v in versions
    ]


def get_version(db: Session, work_id: str, version_id: str) -> Optional[dict]:
    """获取单个版本详情."""
    version = db.query(WorkVersion).filter(
        WorkVersion.id == version_id,
        WorkVersion.work_id == work_id,
    ).first()
    if not version:
        return None
    return {
        "id": version.id,
        "work_id": version.work_id,
        "version_num": version.version_num,
        "file_hash": version.file_hash,
        "file_path": version.file_path,
        "file_size": version.file_size,
        "notes": version.notes,
        "created_at": version.created_at.isoformat() if version.created_at else None,
    }


def create_version(db: Session, work_id: str, notes: Optional[str] = None) -> Optional[dict]:
    """创建作品版本快照."""
    work = db.query(Work).filter(Work.id == work_id).first()
    if not work:
        return None

    latest = db.query(WorkVersion).filter(
        WorkVersion.work_id == work_id
    ).order_by(WorkVersion.version_num.desc()).first()

    version_num = (latest.version_num + 1) if latest else 1

    version = WorkVersion(
        work_id=work_id,
        version_num=version_num,
        file_hash=work.sha256 or compute_sha256(work.file_path),
        file_path=work.file_path,
        file_size=work.file_size,
        notes=notes,
    )
    db.add(version)
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise
    db.refresh(version)

    return {"id": version.id, "version_num": version_num, "message": f"版本 {version_num} 已创建"}


def rollback_version(db: Session, work_id: str, version_id: str) -> Optional[str]:
    """回滚到指定版本 (更新作品文件哈希和路径)."""
    work = db.query(Work).filter(Work.id == work_id).first()
    if not work:
        return None

    version = db.query(WorkVersion).filter(
        WorkVersion.id == version_id,
        WorkVersion.work_id == work_id,
    ).first()
    if not version:
        return None

    work.sha256 = version.file_hash
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise

    return f"已回滚到版本 {version.version_num}"


# ============================================================================
# 项目管理
# ============================================================================


def list_projects(db: Session) -> list:
    """获取项目列表."""
    projects = db.query(Project).order_by(Project.created_at.desc()).all()

    return [
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
    ]


def create_project(db: Session, data: ProjectCreate) -> Optional[dict]:
    """创建项目."""
    project = Project(
        name=data.name,
        description=data.description,
        cover_work_id=data.cover_work_id,
    )
    db.add(project)
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise
    db.refresh(project)

    return {"id": project.id, "name": project.name}


def update_project(db: Session, project_id: str, data: dict) -> Optional[str]:
    """更新项目."""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        return None

    for key in ["name", "description", "cover_work_id"]:
        val = data.get(key)
        if val is not None:
            setattr(project, key, val)
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise

    return "项目已更新"


def delete_project(db: Session, project_id: str) -> Optional[str]:
    """删除项目 (关联作品的项目字段置空)."""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        return None

    # 解除关联
    db.query(Work).filter(Work.project_id == project_id).update(
        {"project_id": None}
    )
    db.delete(project)
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise

    return "项目已删除"


def assign_to_project(db: Session, work_id: str, project_id: str) -> Optional[str]:
    """将作品分配到项目."""
    work = db.query(Work).filter(Work.id == work_id).first()
    if not work:
        return None

    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        return None

    work.project_id = project_id
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise

    return None
