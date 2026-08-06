# -*- coding: utf-8 -*-
"""视频指纹配置 CRUD 服务层 — 扩展自 video_fingerprint_service.py."""

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import Session

from app.models.video_fingerprint import VideoFingerprintConfig, VideoFrameFingerprint
from sqlalchemy import func


# ============================================================================
# 视频指纹配置 CRUD
# ============================================================================


def list_configs(db: Session, is_active: Optional[bool] = None) -> list:
    """获取视频指纹配置列表."""
    q = db.query(VideoFingerprintConfig)
    if is_active is not None:
        q = q.filter(VideoFingerprintConfig.is_active == is_active)
    configs = q.order_by(VideoFingerprintConfig.created_at.desc()).all()
    return [
        {
            "id": c.id,
            "name": c.name,
            "algorithm": c.algorithm,
            "frame_interval": c.frame_interval,
            "threshold": c.threshold,
            "is_active": c.is_active,
            "settings": c.settings or {},
            "created_at": c.created_at.isoformat() if c.created_at else None,
            "updated_at": c.updated_at.isoformat() if c.updated_at else None,
        }
        for c in configs
    ]


def create_config(db: Session, payload: dict) -> Optional[dict]:
    """创建视频指纹配置."""
    config = VideoFingerprintConfig(
        name=payload["name"],
        algorithm=payload.get("algorithm", "pHash"),
        frame_interval=payload.get("frame_interval", 30),
        threshold=payload.get("threshold", 0.85),
        is_active=payload.get("is_active", True),
        settings=payload.get("settings", {}),
    )
    db.add(config)
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise
    db.refresh(config)
    return _config_to_dict(config)


def get_config(db: Session, config_id: str) -> Optional[dict]:
    """获取单个配置详情."""
    config = db.query(VideoFingerprintConfig).filter(VideoFingerprintConfig.id == config_id).first()
    if not config:
        return None
    return _config_to_dict(config)


def update_config(db: Session, config_id: str, payload: dict) -> Optional[dict]:
    """更新视频指纹配置."""
    config = db.query(VideoFingerprintConfig).filter(VideoFingerprintConfig.id == config_id).first()
    if not config:
        return None
    for key, value in payload.items():
        if value is not None:
            setattr(config, key, value)
    config.updated_at = datetime.now(timezone.utc)
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise
    db.refresh(config)
    return _config_to_dict(config)


def delete_config(db: Session, config_id: str) -> bool:
    """删除视频指纹配置."""
    config = db.query(VideoFingerprintConfig).filter(VideoFingerprintConfig.id == config_id).first()
    if not config:
        return False
    db.delete(config)
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise
    return True


# ============================================================================
# 视频帧指纹 CRUD
# ============================================================================


def list_frames(db: Session, work_id: Optional[str] = None,
                config_id: Optional[str] = None) -> list:
    """获取视频帧指纹列表."""
    q = db.query(VideoFrameFingerprint)
    if work_id:
        q = q.filter(VideoFrameFingerprint.work_id == work_id)
    if config_id:
        q = q.filter(VideoFrameFingerprint.config_id == config_id)
    frames = q.order_by(VideoFrameFingerprint.timestamp_ms.desc()).all()
    return [
        {
            "id": f.id,
            "work_id": f.work_id,
            "config_id": f.config_id,
            "frame_hash": f.frame_hash,
            "timestamp_ms": f.timestamp_ms,
            "frame_index": f.frame_index,
            "similarity_score": f.similarity_score,
            "matched_work_id": f.matched_work_id,
            "created_at": f.created_at.isoformat() if f.created_at else None,
        }
        for f in frames
    ]


def create_frame(db: Session, payload: dict) -> Optional[dict]:
    """创建视频帧指纹."""
    frame = VideoFrameFingerprint(
        work_id=payload["work_id"],
        config_id=payload.get("config_id"),
        frame_hash=payload["frame_hash"],
        timestamp_ms=payload.get("timestamp_ms", 0),
        frame_index=payload.get("frame_index", 0),
        similarity_score=payload.get("similarity_score"),
        matched_work_id=payload.get("matched_work_id"),
    )
    db.add(frame)
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise
    db.refresh(frame)
    return _frame_to_dict(frame)


# ============================================================================
# 统计数据
# ============================================================================


def get_video_stats(db: Session) -> dict:
    """获取视频创作者统计."""
    total_frames = db.query(func.count(VideoFrameFingerprint.id)).scalar() or 0
    total_configs = db.query(func.count(VideoFingerprintConfig.id)).scalar() or 0
    total_matches = db.query(func.count(VideoFrameFingerprint.matched_work_id)).filter(
        VideoFrameFingerprint.matched_work_id.isnot(None)
    ).scalar() or 0
    return {
        "total_videos": total_configs,
        "total_frames": total_frames,
        "total_matches": total_matches,
    }


# ============================================================================
# 辅助函数
# ============================================================================


def _config_to_dict(c: VideoFingerprintConfig) -> dict:
    return {
        "id": c.id,
        "name": c.name,
        "algorithm": c.algorithm,
        "frame_interval": c.frame_interval,
        "threshold": c.threshold,
        "is_active": c.is_active,
        "settings": c.settings or {},
        "created_at": c.created_at.isoformat() if c.created_at else None,
        "updated_at": c.updated_at.isoformat() if c.updated_at else None,
    }


def _frame_to_dict(f: VideoFrameFingerprint) -> dict:
    return {
        "id": f.id,
        "work_id": f.work_id,
        "config_id": f.config_id,
        "frame_hash": f.frame_hash,
        "timestamp_ms": f.timestamp_ms,
        "frame_index": f.frame_index,
        "similarity_score": f.similarity_score,
        "matched_work_id": f.matched_work_id,
        "created_at": f.created_at.isoformat() if f.created_at else None,
    }
