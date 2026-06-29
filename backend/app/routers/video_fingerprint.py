"""视频指纹 API 路由 — 对应: docs/modules-v3/01-creative-assets.md
Phase 3: 视频创作者指纹生成与比对
端点: 7 (video_fingerprint)"""

from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional

from app.database import get_db
from app.models.video_fingerprint import VideoFingerprintConfig, VideoFrameFingerprint
from app.schemas.common import ApiResponse
from app.deps import require_auth

router = APIRouter()


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
def create_config(payload: dict, db: Session = Depends(get_db)):
    """创建视频指纹配置."""
    name = payload.get("name")
    algorithm = payload.get("algorithm", "pHash")
    if not name:
        raise HTTPException(status_code=400, detail="name is required")
    config = VideoFingerprintConfig(
        name=name,
        algorithm=algorithm,
        frame_interval=payload.get("frame_interval", 30),
        threshold=payload.get("threshold", 0.85),
        is_active=payload.get("is_active", True),
        settings=payload.get("settings", {}),
    )
    db.add(config)
    db.commit()
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
def update_config(config_id: str, payload: dict, db: Session = Depends(get_db)):
    """更新视频指纹配置."""
    config = db.query(VideoFingerprintConfig).filter(VideoFingerprintConfig.id == config_id).first()
    if not config:
        raise HTTPException(status_code=404, detail="配置不存在")
    for key in ("name", "algorithm", "frame_interval", "threshold", "is_active", "settings"):
        if key in payload:
            setattr(config, key, payload[key])
    config.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(config)
    return ApiResponse(data=_config_to_dict(config), message="配置更新成功")


@router.delete("/video-fingerprint/configs/{config_id}", response_model=ApiResponse[dict], dependencies=[Depends(require_auth)])
def delete_config(config_id: str, db: Session = Depends(get_db)):
    """删除视频指纹配置."""
    config = db.query(VideoFingerprintConfig).filter(VideoFingerprintConfig.id == config_id).first()
    if not config:
        raise HTTPException(status_code=404, detail="配置不存在")
    db.delete(config)
    db.commit()
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
def create_frame(payload: dict, db: Session = Depends(get_db)):
    """创建视频帧指纹."""
    work_id = payload.get("work_id")
    frame_hash = payload.get("frame_hash")
    if not work_id or not frame_hash:
        raise HTTPException(status_code=400, detail="work_id and frame_hash are required")
    frame = VideoFrameFingerprint(
        work_id=work_id,
        config_id=payload.get("config_id"),
        frame_hash=frame_hash,
        timestamp_ms=payload.get("timestamp_ms", 0),
        frame_index=payload.get("frame_index", 0),
        similarity_score=payload.get("similarity_score"),
        matched_work_id=payload.get("matched_work_id"),
    )
    db.add(frame)
    db.commit()
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
