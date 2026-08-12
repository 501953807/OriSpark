# -*- coding: utf-8 -*-
"""作品版本管理服务层."""

from typing import Optional

from sqlalchemy.orm import Session

from app.models.work import Work, WorkVersion


def list_versions(db: Session, work_id: str) -> Optional[list]:
    """列出作品所有版本，按 version_num 升序排列."""
    work = db.query(Work).filter(Work.id == work_id).first()
    if not work:
        return None
    versions = db.query(WorkVersion).filter(
        WorkVersion.work_id == work_id
    ).order_by(WorkVersion.version_num.asc()).all()
    return [
        {
            "id": v.id,
            "work_id": v.work_id,
            "version_num": v.version_num,
            "file_hash": v.file_hash,
            "file_path": v.file_path,
            "file_size": v.file_size,
            "notes": v.notes,
            "created_at": v.created_at.isoformat() if v.created_at else None,
        }
        for v in versions
    ]


def create_version(
    db: Session,
    work_id: str,
    file_path: str,
    file_hash: str,
    file_size: int,
    notes: Optional[str] = None,
) -> Optional[WorkVersion]:
    """创建新版本（自动递增 version_num）."""
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
        file_hash=file_hash,
        file_path=file_path,
        file_size=file_size,
        notes=notes,
    )
    db.add(version)
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise
    db.refresh(version)
    return version


def get_version(db: Session, version_id: str) -> Optional[WorkVersion]:
    """获取单个版本详情."""
    return db.query(WorkVersion).filter(WorkVersion.id == version_id).first()


def delete_version(db: Session, version_id: str, user_id: str) -> dict:
    """软删除版本，不能删除最后一个版本."""
    version = db.query(WorkVersion).filter(WorkVersion.id == version_id).first()
    if not version:
        return {"success": False, "error": "版本不存在"}
    total = db.query(WorkVersion).filter(WorkVersion.work_id == version.work_id).count()
    if total <= 1:
        return {"success": False, "error": "不能删除最后一个版本"}
    db.delete(version)
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise
    return {"success": True, "message": f"已删除版本 {version.version_num}"}


def get_version_history_timeline(
    db: Session, work_id: str
) -> Optional[list]:
    """返回时间线格式的版本列表（含前后版本引用）."""
    versions = db.query(WorkVersion).filter(
        WorkVersion.work_id == work_id
    ).order_by(WorkVersion.version_num.asc()).all()
    if not versions:
        return []
    result = []
    for i, v in enumerate(versions):
        prev = versions[i - 1] if i > 0 else None
        next_v = versions[i + 1] if i < len(versions) - 1 else None
        result.append({
            "version_num": v.version_num,
            "id": v.id,
            "file_hash": v.file_hash,
            "file_path": v.file_path,
            "file_size": v.file_size,
            "notes": v.notes,
            "created_at": v.created_at.isoformat() if v.created_at else None,
            "prev_version": {
                "version_num": prev.version_num,
                "id": prev.id,
            } if prev else None,
            "next_version": {
                "version_num": next_v.version_num,
                "id": next_v.id,
            } if next_v else None,
        })
    return result
