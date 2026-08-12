# -*- coding: utf-8 -*-
"""项目分组管理服务层."""

from typing import Optional

from sqlalchemy.orm import Session

from app.models.work import Work, Project


def list_projects(db: Session, user_id: Optional[str] = None) -> list:
    """获取项目列表，包含作品计数."""
    projects = db.query(Project).order_by(Project.created_at.desc()).all()
    return [
        {
            "id": p.id,
            "name": p.name,
            "description": p.description,
            "cover_work_id": p.cover_work_id,
            "work_count": db.query(Work).filter(Work.project_id == p.id).count(),
            "created_at": p.created_at.isoformat() if p.created_at else None,
            "updated_at": p.updated_at.isoformat() if p.updated_at else None,
        }
        for p in projects
    ]


def create_project(
    db: Session, user_id: str, name: str, description: Optional[str] = None
) -> Project:
    """创建项目."""
    project = Project(name=name, description=description)
    db.add(project)
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise
    db.refresh(project)
    return project


def add_work_to_project(db: Session, project_id: str, work_id: str) -> dict:
    """添加作品到项目."""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        return {"success": False, "error": "项目不存在"}
    work = db.query(Work).filter(Work.id == work_id).first()
    if not work:
        return {"success": False, "error": "作品不存在"}
    work.project_id = project_id
    project.cover_work_id = project.cover_work_id or work_id
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise
    return {"success": True, "message": "作品已添加到项目"}


def remove_work_from_project(db: Session, project_id: str, work_id: str) -> dict:
    """移除作品（作品项目字段置空）."""
    work = db.query(Work).filter(Work.id == work_id).first()
    if not work:
        return {"success": False, "error": "作品不存在"}
    if work.project_id != project_id:
        return {"success": False, "error": "作品不属于该项目"}
    work.project_id = None
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise
    return {"success": True, "message": "作品已从项目移除"}


def list_project_works(db: Session, project_id: str) -> Optional[list]:
    """列出项目内作品."""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        return None
    works = db.query(Work).filter(
        Work.project_id == project_id,
        Work.status == "active",
    ).order_by(Work.created_at.desc()).all()
    return [
        {
            "id": w.id,
            "title": w.title,
            "file_name": w.file_name,
            "file_type": w.file_type,
            "file_size": w.file_size,
            "sha256": w.sha256,
            "created_at": w.created_at.isoformat() if w.created_at else None,
        }
        for w in works
    ]


def delete_project(db: Session, project_id: str, user_id: str) -> dict:
    """删除项目（不删除作品，作品项目字段置空）."""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        return {"success": False, "error": "项目不存在"}
    db.query(Work).filter(Work.project_id == project_id).update(
        {"project_id": None}, synchronize_session="fetch"
    )
    db.delete(project)
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise
    return {"success": True, "message": "项目已删除"}
