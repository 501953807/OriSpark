"""视频指纹 API 路由 — 对应: docs/modules-v5/01-creative-assets.md
Phase 3: 视频创作者指纹生成与比对
端点: 7 (video_fingerprint)

业务逻辑已提取至 video_fingerprint_config_service.py.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from typing import Optional

from app.database import get_db
from app.schemas.common import ApiResponse
from app.deps import require_auth
from app.services.video_fingerprint_config_service import (
    list_configs, create_config, get_config, update_config, delete_config,
    list_frames, create_frame, get_video_stats,
)

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


@router.get("/video-fingerprint/configs", response_model=ApiResponse)
def list_configs_endpoint(
    is_active: Optional[bool] = None,
    db: Session = Depends(get_db),
):
    """获取视频指纹配置列表."""
    return ApiResponse(data=list_configs(db, is_active))


@router.post("/video-fingerprint/configs", response_model=ApiResponse, dependencies=[Depends(require_auth)])
def create_config_endpoint(payload: CreateConfigPayload, db: Session = Depends(get_db)):
    """创建视频指纹配置."""
    result = create_config(db, payload.model_dump(exclude_unset=True))
    return ApiResponse(data=result, message="配置创建成功")


@router.get("/video-fingerprint/configs/{config_id}", response_model=ApiResponse)
def get_config_endpoint(config_id: str, db: Session = Depends(get_db)):
    """获取单个配置详情."""
    result = get_config(db, config_id)
    if not result:
        raise HTTPException(status_code=404, detail="配置不存在")
    return ApiResponse(data=result)


@router.put("/video-fingerprint/configs/{config_id}", response_model=ApiResponse, dependencies=[Depends(require_auth)])
def update_config_endpoint(config_id: str, payload: UpdateConfigPayload, db: Session = Depends(get_db)):
    """更新视频指纹配置."""
    result = update_config(db, config_id, payload.model_dump(exclude_unset=True))
    if not result:
        raise HTTPException(status_code=404, detail="配置不存在")
    return ApiResponse(data=result, message="配置更新成功")


@router.delete("/video-fingerprint/configs/{config_id}", response_model=ApiResponse, dependencies=[Depends(require_auth)])
def delete_config_endpoint(config_id: str, db: Session = Depends(get_db)):
    """删除视频指纹配置."""
    deleted = delete_config(db, config_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="配置不存在")
    return ApiResponse(data={"success": True}, message="配置已删除")


# ============================================================================
# 13.x 视频帧指纹 CRUD
# ============================================================================


@router.get("/video-fingerprint/frames", response_model=ApiResponse)
def list_frames_endpoint(
    work_id: Optional[str] = None,
    config_id: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """获取视频帧指纹列表."""
    return ApiResponse(data=list_frames(db, work_id, config_id))


@router.post("/video-fingerprint/frames", response_model=ApiResponse, dependencies=[Depends(require_auth)])
def create_frame_endpoint(payload: CreateFramePayload, db: Session = Depends(get_db)):
    """创建视频帧指纹."""
    result = create_frame(db, payload.model_dump(exclude_unset=True))
    return ApiResponse(data=result, message="帧指纹创建成功")


# ============================================================================
# Video creator stats
# ============================================================================


@router.get("/video/stats", response_model=ApiResponse)
def get_video_stats_endpoint(db: Session = Depends(get_db)):
    """获取视频创作者统计."""
    return ApiResponse(data=get_video_stats(db))
