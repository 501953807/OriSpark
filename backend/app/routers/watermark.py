"""水印预设 API 路由。

对应模块设计：水印管理系统
端点：5 (watermark_presets) + 1 (apply) = 6
POST   /api/watermark-presets       - 创建新预设
GET    /api/watermark-presets       - 获取所有预设列表
PUT    /api/watermark-presets/{id} - 更新预设
DELETE /api/watermark-presets/{id} - 删除预设
POST   /api/watermarks/{work_id}/apply - 应用水印到作品（批量操作）
"""

from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Path
from typing import Optional, List

from sqlalchemy.orm import Session

from app.database import get_db
from app.models.watermark_preset import WatermarkPreset, PositionEnum
from app.schemas.watermark_preset import (
    WatermarkPresetCreate,
    WatermarkPresetResponse,
    WatermarkPresetListResponse,
    ApplyWatermarkPayload,
    ApplyWatermarkResult,
    FrequencyWatermarkPayload,
    FrequencyWatermarkResult,
)
from app.services import watermark_service
from app.deps import require_auth
from app.schemas.common import ApiResponse, SuccessResponse

router = APIRouter()


# ============================================================================
# Helpers
# ============================================================================

def _preset_to_response(preset: WatermarkPreset) -> WatermarkPresetResponse:
    """将 SQLAlchemy 模型转换为响应模型."""
    return WatermarkPresetResponse.model_validate(preset)


# ============================================================================
# CRUD Endpoints: /api/watermark-presets
# ============================================================================


@router.get(
    "/watermark-presets",
    response_model=ApiResponse[WatermarkPresetListResponse],
)
def list_watermark_presets(
    db: Session = Depends(get_db),
) -> ApiResponse[WatermarkPresetListResponse]:
    """获取所有水印预设列表，按创建时间降序排列."""
    presets = watermark_service.get_presets(db)
    items = [
        WatermarkPresetResponse.model_validate(p) for p in presets
    ]
    return ApiResponse(
        data=WatermarkPresetListResponse(items=items, total=len(items)),
        message="获取成功"
    )


@router.post(
    "/watermark-presets",
    response_model=ApiResponse[WatermarkPresetResponse],
    dependencies=[Depends(require_auth)],
)
def create_watermark_preset(
    payload: WatermarkPresetCreate,
    db: Session = Depends(get_db),
) -> ApiResponse[WatermarkPresetResponse]:
    """创建新的水印预设."""
    try:
        preset_dict = watermark_service.create_preset(
            db=db,
            name=payload.name,
            position=payload.position,
            opacity=payload.opacity,
            text=payload.text,
            image_path=payload.image_path,
        )
        return ApiResponse(
            data=WatermarkPresetResponse.model_validate(preset_dict),
            message="水印预设创建成功"
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail="水印操作失败，请稍后重试")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建失败: {str(e)}")


@router.put(
    "/watermark-presets/{preset_id}",
    response_model=ApiResponse[WatermarkPresetResponse],
    dependencies=[Depends(require_auth)],
)
def update_watermark_preset(
    preset_id: str = Path(description="水印预设ID"),
    name: Optional[str] = None,
    position: Optional[str] = None,
    opacity: Optional[int] = None,
    text: Optional[str] = None,
    image_path: Optional[str] = None,
    db: Session = Depends(get_db),
) -> ApiResponse[WatermarkPresetResponse]:
    """更新现有水印预设."""
    try:
        preset_dict = watermark_service.update_preset(
            db=db,
            preset_id=preset_id,
            name=name,
            position=position,
            opacity=opacity,
            text=text,
            image_path=image_path,
        )
        return ApiResponse(
            data=WatermarkPresetResponse.model_validate(preset_dict),
            message="水印预设更新成功"
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail="水印操作失败，请稍后重试")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新失败: {str(e)}")


@router.delete(
    "/watermark-presets/{preset_id}",
    response_model=ApiResponse[SuccessResponse],
    dependencies=[Depends(require_auth)],
)
def delete_watermark_preset(
    preset_id: str = Path(description="水印预设ID"),
    db: Session = Depends(get_db),
) -> ApiResponse[SuccessResponse]:
    """删除水印预设."""
    try:
        success = watermark_service.delete_preset(db, preset_id)
        if not success:
            raise HTTPException(status_code=404, detail="预设不存在")
        return ApiResponse(
            data={"success": True, "message": "水印预设已删除"},
            message="删除成功"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除失败: {str(e)}")


# ============================================================================
# Apply Endpoint: /api/watermarks/{work_id}/apply
# ============================================================================


@router.post(
    "/watermarks/{work_id}/apply",
    response_model=ApiResponse[ApplyWatermarkResult],
    dependencies=[Depends(require_auth)],
)
def apply_watermark_to_work(
    payload: ApplyWatermarkPayload,
    work_id: str,  # Path parameter extracted from URL
    db: Session = Depends(get_db),
) -> ApiResponse[ApplyWatermarkResult]:
    """应用水印预设到指定作品（批量操作接口）."""
    # Validate work_id matches the payload's work_id
    if work_id != payload.work_id:
        raise HTTPException(
            status_code=400,
            detail="path中的work_id与payload中的work_id不一致"
        )

    try:
        result = watermark_service.apply_watermark_to_work(
            db=db,
            work_id=work_id,
            preset_id=payload.preset_id,
        )
        return ApiResponse(
            data=ApplyWatermarkResult(
                success=True,
                work_id=result["work_id"],
                preset_id=result["preset_id"],
                message=result["message"],
            ),
            message="水印应用成功"
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail="水印操作失败，请稍后重试")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"水印应用失败: {str(e)}")


# ============================================================================
# Frequency Domain Watermark Endpoints
# ============================================================================


@router.post(
    "/watermarks/frequency/embed",
    response_model=ApiResponse[FrequencyWatermarkResult],
    dependencies=[Depends(require_auth)],
)
def embed_frequency_watermark(
    payload: FrequencyWatermarkPayload,
    db: Session = Depends(get_db),
) -> ApiResponse[FrequencyWatermarkResult]:
    """在图像频域嵌入隐形水印（DCT算法）."""
    try:
        result = watermark_service.apply_frequency_watermark(
            image_path=payload.image_path,
            creator_id=payload.creator_id,
            timestamp=int(datetime.now(timezone.utc).timestamp()),
            contract_id=payload.contract_id,
        )
        return ApiResponse(
            data=FrequencyWatermarkResult(
                success=result["success"],
                psnr=result["psnr"],
                output_path=result["output_path"],
                bits_embedded=result["bits_embedded"],
            ),
            message="频域水印嵌入成功"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"频域水印嵌入失败: {str(e)}")


@router.post(
    "/watermarks/frequency/extract",
    response_model=ApiResponse[dict],
    dependencies=[Depends(require_auth)],
)
def extract_frequency_watermark(
    image_path: str,
    db: Session = Depends(get_db),
) -> ApiResponse[dict]:
    """从图像频域提取隐形水印."""
    try:
        result = watermark_service.extract_watermark(image_path)
        return ApiResponse(
            data=result,
            message="频域水印提取成功"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"频域水印提取失败: {str(e)}")
