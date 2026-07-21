"""水印预设 API 路由 — 对应: docs/modules-v5/01-creative-assets.md
Phase 2: 摄影师水印预设管理
端点: 6 (watermark)"""

from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, Body
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.orm import Session
from typing import Optional

from app.database import get_db
from app.models.watermark import WatermarkPreset
from app.services import watermark_service
from app.schemas.common import ApiResponse, SuccessResponse
from app.deps import require_auth

router = APIRouter()


class CreatePresetPayload(BaseModel):
    name: str
    watermark_type: str
    config: dict = Field(default_factory=dict)
    description: Optional[str] = None
    is_default: bool = False
    created_by: Optional[str] = None

    @field_validator("watermark_type")
    @classmethod
    def validate_watermark_type(cls, v: str) -> str:
        if v not in ("text", "image", "tiled"):
            raise ValueError("Invalid watermark_type")
        return v


class UpdatePresetPayload(BaseModel):
    name: Optional[str] = None
    watermark_type: Optional[str] = None
    config: Optional[dict] = None
    description: Optional[str] = None
    is_default: Optional[bool] = None
    created_by: Optional[str] = None


class ApplyWatermarkPayload(BaseModel):
    work_path: str
    preset_id: str
    output_path: str


class PreviewWatermarkPayload(BaseModel):
    config: Optional[dict] = Field(default_factory=dict)
    image_path: str


# ============================================================================
# Helpers
# ============================================================================


def _preset_to_dict(p: WatermarkPreset) -> dict:
    return {
        "id": p.id,
        "name": p.name,
        "description": p.description,
        "watermark_type": p.watermark_type,
        "config": p.config or {},
        "is_default": p.is_default,
        "created_by": p.created_by,
        "created_at": p.created_at.isoformat() if p.created_at else None,
        "updated_at": p.updated_at.isoformat() if p.updated_at else None,
    }


# ============================================================================
# CRUD: /api/watermark/presets
# ============================================================================


@router.get(
    "/watermark/presets",
    response_model=ApiResponse[list],
)
def list_presets(
    watermark_type: Optional[str] = Query(None),
    is_default: Optional[bool] = Query(None),
    db: Session = Depends(get_db),
):
    """获取水印预设列表（可筛选）."""
    q = db.query(WatermarkPreset)
    if watermark_type:
        q = q.filter(WatermarkPreset.watermark_type == watermark_type)
    if is_default is not None:
        q = q.filter(WatermarkPreset.is_default == is_default)
    presets = q.order_by(WatermarkPreset.created_at.desc()).all()
    return ApiResponse(data=[_preset_to_dict(p) for p in presets])


@router.post(
    "/watermark/presets",
    response_model=ApiResponse[dict],
    dependencies=[Depends(require_auth)],
)
def create_preset(payload: CreatePresetPayload, db: Session = Depends(get_db)):
    """创建水印预设."""
    config = payload.config or {}
    valid, error = watermark_service.validate_config({**config, "watermark_type": payload.watermark_type})
    if not valid:
        raise HTTPException(status_code=400, detail=error)
    preset = WatermarkPreset(
        name=payload.name,
        description=payload.description,
        watermark_type=payload.watermark_type,
        config=config,
        is_default=payload.is_default,
        created_by=payload.created_by,
    )
    db.add(preset)
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise
    db.refresh(preset)
    return ApiResponse(data=_preset_to_dict(preset), message="预设创建成功")


@router.put(
    "/watermark/presets/{preset_id}",
    response_model=ApiResponse[dict],
    dependencies=[Depends(require_auth)],
)
def update_preset(preset_id: str, payload: UpdatePresetPayload, db: Session = Depends(get_db)):
    """更新水印预设."""
    preset = db.query(WatermarkPreset).filter(WatermarkPreset.id == preset_id).first()
    if not preset:
        raise HTTPException(status_code=404, detail="预设不存在")

    update_data = payload.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(preset, key, value)
    preset.updated_at = datetime.utcnow()
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise
    db.refresh(preset)
    return ApiResponse(data=_preset_to_dict(preset), message="预设更新成功")


@router.delete(
    "/watermark/presets/{preset_id}",
    response_model=ApiResponse[SuccessResponse],
    dependencies=[Depends(require_auth)],
)
def delete_preset(preset_id: str, db: Session = Depends(get_db)):
    """删除水印预设."""
    preset = db.query(WatermarkPreset).filter(WatermarkPreset.id == preset_id).first()
    if not preset:
        raise HTTPException(status_code=404, detail="预设不存在")
    db.delete(preset)
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise
    return ApiResponse(data={"success": True, "message": "预设已删除"})


# ============================================================================
# Apply: POST /api/watermark/apply
# ============================================================================


@router.post(
    "/watermark/apply",
    response_model=ApiResponse[dict],
    dependencies=[Depends(require_auth)],
)
def apply_watermark(payload: ApplyWatermarkPayload, db: Session = Depends(get_db)):
    """将预设应用到作品."""
    preset = db.query(WatermarkPreset).filter(WatermarkPreset.id == payload.preset_id).first()
    if not preset:
        raise HTTPException(status_code=404, detail="预设不存在")

    success = watermark_service.apply_watermark(payload.work_path, preset.config, payload.output_path)
    if not success:
        raise HTTPException(status_code=500, detail="水印应用失败")

    return ApiResponse(data={"output_path": output_path}, message="水印应用成功")


# ============================================================================
# Preview: GET /api/watermark/preview
# ============================================================================


@router.post(
    "/watermark/preview",
    response_model=ApiResponse[dict],
    dependencies=[Depends(require_auth)],
)
def preview_watermark(payload: PreviewWatermarkPayload):
    """生成水印预览图."""
    config = payload.config or {}
    preview_path = watermark_service.generate_watermark_preview(config, payload.image_path)
    return ApiResponse(data={"preview_path": preview_path}, message="预览生成成功")
