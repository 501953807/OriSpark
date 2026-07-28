"""水印预设 Pydantic 模型."""

from typing import Optional, Dict
from datetime import datetime
from pydantic import BaseModel, Field, field_validator, ConfigDict

# PositionEnum values for validation
POSITION_OPTIONS = ["top-left", "top-right", "bottom-left", "bottom-right"]


class WatermarkPresetCreate(BaseModel):
    """创建水印预设请求体."""

    name: str = Field(..., min_length=1, max_length=100, description="预设名称")
    position: str = Field(..., description="水印位置")
    opacity: int = Field(default=100, ge=0, le=100, description="透明度 0-100")
    text: Optional[str] = Field(None, description="水印文本内容（可选）")
    image_path: Optional[str] = Field(None, description="水印图片路径（可选）")

    @field_validator("position")
    def validate_position(cls, v: str) -> str:
        if v not in POSITION_OPTIONS:
            raise ValueError(f"无效的枚举值，必须是 {POSITION_OPTIONS}")
        return v


class WatermarkPresetUpdate(BaseModel):
    """更新水印预设请求体."""

    name: Optional[str] = Field(None, description="预设名称")
    position: Optional[str] = Field(None, description="水印位置")
    opacity: Optional[int] = Field(None, ge=0, le=100, description="透明度 0-100")
    text: Optional[str] = Field(None, description="水印文本内容（可选）")
    image_path: Optional[str] = Field(None, description="水印图片路径（可选）")

    @field_validator("position", mode="before")
    def validate_position(cls, v: str) -> str:
        if v is not None and v not in POSITION_OPTIONS:
            raise ValueError(f"无效的枚举值，必须是 {POSITION_OPTIONS}")
        return v


class WatermarkPresetSchema(BaseModel):
    """水印预设基础模型（包含 id 和创建时间）."""

    id: str = Field(..., description="预设ID")
    name: str = Field(..., description="预设名称")
    position: str = Field(..., description="水印位置")
    opacity: int = Field(..., description="透明度 0-100")
    text: Optional[str] = Field(None, description="水印文本内容")
    image_path: Optional[str] = Field(None, description="水印图片路径")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: Optional[datetime] = Field(None, description="更新时间")


class WatermarkPresetResponse(BaseModel):
    """水印预设完整响应模型."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    position: str
    opacity: int
    text: Optional[str]
    image_path: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]


class WatermarkPresetListResponse(BaseModel):
    """水印预设列表响应."""

    items: list[WatermarkPresetResponse]
    total: int


class ApplyWatermarkPayload(BaseModel):
    """应用水印到作品的负载."""

    work_id: str = Field(..., description="作品ID")
    preset_id: str = Field(..., description="水印预设ID")


class ApplyWatermarkResult(BaseModel):
    """水印应用结果."""

    success: bool
    work_id: str
    preset_id: str
    message: str