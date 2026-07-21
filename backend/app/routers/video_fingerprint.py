"""视频指纹 API 路由 — 对应: docs/modules-v5/01-creative-assets.md
Phase 3: 视频创作者指纹生成与比对
端点: 7 (video_fingerprint)"""

from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import func
from sqlalchemy.orm import Session
from typing import Optional

from app.database import get_db
from app.models.video_fingerprint import VideoFingerprintConfig, VideoFrameFingerprint
from app.schemas.common import ApiResponse
from app.deps import require_auth

router = APIRouter()


class CreateConfigPayload(BaseModel):
    name: str
    algorithm: str = "pHash"
    frame_interval: int = 30
    threshold: float = 0.85
    is_active: bool = True
    settings: dict = Field(default_factory=dict)


class UpdateConfigPayload(BaseModel):
    name: Optional[str] = None
    algorithm: Optional[str] = None
    frame_interval: Optional[int] = None
    threshold: Optional[float] = None
    is_active: Optional[bool] = None
    settings: Optional[dict] = None


class CreateFramePayload(BaseModel):
    work_id: str
    frame_hash: str
    config_id: Optional[str] = None
    timestamp_ms: int = 0
    frame_index: int = 0
    similarity_score: Optional[float] = None
    matched_work_id: Optional[str] = None


# ============================================================================
# 13.x 视频指纹配置 CRUD
# ============================================================================


@router.get("/video-fingerprint/configs", response_model=ApiResponse[list])
def list_configs(
    is_active: Optional[bool] = None,
    db: Session = Depends(get_db),
):
    """获取视频指纹配置列表."""
    q = db.query(VideoFingerprintConfig)
    if is_active is not None:
        q = q.filter(VideoFingerprintConfig.is_active == is_active)
    configs = q.order_by(VideoFingerprintConfig.created_at.desc()).all()
    return ApiResponse(data=[
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
    ])


@router.post("/video-fingerprint/configs", response_model=ApiResponse[dict], dependencies=[Depends(require_auth)])
def create_config(payload: CreateConfigPayload, db: Session = Depends(get_db)):
    """创建视频指纹配置."""
    config = VideoFingerprintConfig(
        name=payload.name,
        algorithm=payload.algorithm,
        frame_interval=payload.frame_interval,
        threshold=payload.threshold,
        is_active=payload.is_active,
        settings=payload.settings,
    )
    db.add(config)
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise
    db.refresh(config)
    return ApiResponse(data=_config_to_dict(config), message="配置创建成功")


@router.get("/video-fingerprint/configs/{config_id}", response_model=ApiResponse[dict])
def get_config(config_id: str, db: Session = Depends(get_db)):
    """获取单个配置详情."""
    config = db.query(VideoFingerprintConfig).filter(VideoFingerprintConfig.id == config_id).first()
    if not config:
        raise HTTPException(status_code=404, detail="配置不存在")
    return ApiResponse(data=_config_to_dict(config))


@router.put("/video-fingerprint/configs/{config_id}", response_model=ApiResponse[dict], dependencies=[Depends(require_auth)])
def update_config(config_id: str, payload: UpdateConfigPayload, db: Session = Depends(get_db)):
    """更新视频指纹配置."""
    config = db.query(VideoFingerprintConfig).filter(VideoFingerprintConfig.id == config_id).first()
    if not config:
        raise HTTPException(status_code=404, detail="配置不存在")
    update_data = payload.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(config, key, value)
    config.updated_at = datetime.utcnow()
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise
    db.refresh(config)
    return ApiResponse(data=_config_to_dict(config), message="配置更新成功")


@router.delete("/video-fingerprint/configs/{config_id}", response_model=ApiResponse[dict], dependencies=[Depends(require_auth)])
def delete_config(config_id: str, db: Session = Depends(get_db)):
    """删除视频指纹配置."""
    config = db.query(VideoFingerprintConfig).filter(VideoFingerprintConfig.id == config_id).first()
    if not config:
        raise HTTPException(status_code=404, detail="配置不存在")
    db.delete(config)
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise
    return ApiResponse(data={"success": True}, message="配置已删除")


# ============================================================================
# 13.x 视频帧指纹 CRUD
# ============================================================================


@router.get("/video-fingerprint/frames", response_model=ApiResponse[list])
def list_frames(
    work_id: Optional[str] = None,
    config_id: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """获取视频帧指纹列表."""
    q = db.query(VideoFrameFingerprint)
    if work_id:
        q = q.filter(VideoFrameFingerprint.work_id == work_id)
    if config_id:
        q = q.filter(VideoFrameFingerprint.config_id == config_id)
    frames = q.order_by(VideoFrameFingerprint.timestamp_ms.desc()).all()
    return ApiResponse(data=[
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
    ])


@router.post("/video-fingerprint/frames", response_model=ApiResponse[dict], dependencies=[Depends(require_auth)])
def create_frame(payload: CreateFramePayload, db: Session = Depends(get_db)):
    """创建视频帧指纹."""
    frame = VideoFrameFingerprint(
        work_id=payload.work_id,
        config_id=payload.config_id,
        frame_hash=payload.frame_hash,
        timestamp_ms=payload.timestamp_ms,
        frame_index=payload.frame_index,
        similarity_score=payload.similarity_score,
        matched_work_id=payload.matched_work_id,
    )
    db.add(frame)
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise
    db.refresh(frame)
    return ApiResponse(data=_frame_to_dict(frame), message="帧指纹创建成功")


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


# ============================================================================
# Video creator stats
# ============================================================================

@router.get("/video/stats", response_model=ApiResponse)
def get_video_stats(db: Session = Depends(get_db)):
    """获取视频创作者统计."""
    total_frames = db.query(func.count(VideoFrameFingerprint.id)).scalar() or 0
    total_configs = db.query(func.count(VideoFingerprintConfig.id)).scalar() or 0
    total_matches = db.query(func.count(VideoFrameFingerprint.matched_work_id)).filter(
        VideoFrameFingerprint.matched_work_id.isnot(None)
    ).scalar() or 0
    return ApiResponse(data={
        "total_videos": total_configs,
        "total_frames": total_frames,
        "total_matches": total_matches,
    })
