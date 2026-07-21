"""摄影师 API Pydantic 模型.

覆盖端点:
- GET  /api/photographer/shots
- POST /api/photographer/shots/{id}/shot-status
- GET  /api/photographer/exif/search
- GET  /api/photographer/gps/map
- POST /api/photographer/stock/channels
- DELETE /api/photographer/stock/channels/{channel}
- GET  /api/photographer/stats
"""

from typing import Optional, Any
from datetime import datetime

from pydantic import BaseModel, Field


# ============================================================================
# Shot (WorkVariant with photographer extensions)
# ============================================================================


class ShotResponse(BaseModel):
    """单个作品变体 (含摄影师扩展字段)."""
    model_config = {"from_attributes": True}

    id: str
    group_id: str
    name: str
    width: int
    height: int
    aspect_ratio: float
    sort_order: int
    created_at: datetime

    # 摄影师扩展字段
    camera_model: Optional[str] = None
    lens: Optional[str] = None
    iso: Optional[int] = None
    aperture: Optional[str] = None
    shutter_speed: Optional[str] = None
    focal_length: Optional[str] = None
    gps_latitude: Optional[float] = None
    gps_longitude: Optional[float] = None
    gps_altitude: Optional[float] = None
    raw_file_path: Optional[str] = None
    shot_status: str = "unreviewed"
    shot_notes: Optional[str] = None
    stock_channels: Optional[list[dict[str, Any]]] = None


class ShotListResponse(BaseModel):
    """作品列表分页响应."""
    items: list[ShotResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


# ============================================================================
# Shot status update
# ============================================================================


SHOT_STATUS_CHOICES = ("unreviewed", "pass", "hold", "reject", "shortlist")


class ShotStatusUpdate(BaseModel):
    """更新选片状态请求."""
    shot_status: str = Field(..., pattern="^(unreviewed|pass|hold|reject|shortlist)$")
    shot_notes: Optional[str] = None


# ============================================================================
# EXIF search
# ============================================================================


class EXIFSearchParams(BaseModel):
    """EXIF 高级搜索参数."""
    camera_model: Optional[str] = None
    lens: Optional[str] = None
    iso_min: Optional[int] = None
    iso_max: Optional[int] = None
    aperture: Optional[str] = None
    shutter_speed: Optional[str] = None
    focal_length: Optional[str] = None
    page: int = 1
    page_size: int = 20


# ============================================================================
# GPS map
# ============================================================================


class GPSPoint(BaseModel):
    """单个 GPS 坐标点."""
    id: str
    name: str
    latitude: float
    longitude: float
    altitude: Optional[float] = None
    camera_model: Optional[str] = None


class GPSMapResponse(BaseModel):
    """GPS 地图数据响应."""
    points: list[GPSPoint]
    total: int


# ============================================================================
# Stock photo platform schemas
# ============================================================================


# Platform registry used by stock_service
STOCK_PLATFORM_INFO = [
    {
        "name": "shutterstock",
        "display_name": "Shutterstock",
        "auth_type": "api_key+jwt",
        "required_specs": {
            "formats": ["JPEG", "PNG", "TIFF"],
            "min_resolution": "1500px on shortest edge",
            "min_file_size_kb": 500,
        },
    },
    {
        "name": "adobe",
        "display_name": "Adobe Stock",
        "auth_type": "oauth2",
        "required_specs": {
            "formats": ["JPEG"],
            "min_resolution": "1000px on shortest edge",
            "min_file_size_kb": 100,
        },
    },
    {
        "name": "getty",
        "display_name": "Getty Images",
        "auth_type": "oauth2",
        "required_specs": {
            "formats": ["JPEG"],
            "min_resolution": "4096px on shortest edge (recommended)",
            "min_file_size_kb": 500,
        },
    },
    {
        "name": "500px",
        "display_name": "500px",
        "auth_type": "oauth2",
        "required_specs": {
            "formats": ["JPEG", "PNG"],
            "min_resolution": "1200px on shortest edge (recommended)",
            "min_file_size_kb": 100,
        },
    },
    {
        "name": "tuchong",
        "display_name": "图虫 (Tuchong)",
        "auth_type": "oauth2",
        "required_specs": {
            "formats": ["JPEG", "PNG", "WebP"],
            "min_resolution": "None",
            "min_file_size_kb": 0,
        },
        "notes": "API is limited; manual submission recommended",
    },
]


class StockChannelAdd(BaseModel):
    """添加图库渠道请求 (legacy — kept for backward compat)."""
    channel: str = Field(..., min_length=1, max_length=100)
    status: str = Field(default="submitted", pattern="^(submitted|active|rejected)$")
    remote_id: Optional[str] = None


class StockChannelInfo(BaseModel):
    """图库渠道信息 (legacy — kept for backward compat)."""
    channel: str
    status: str
    remote_id: Optional[str] = None
    updated_at: Optional[datetime] = None


# New stock gateway schemas
class StockUploadRequest(BaseModel):
    """Upload work to a stock platform."""
    work_id: str = Field(..., min_length=1)
    channel_id: str = Field(..., min_length=1)
    file_path: str = Field(..., min_length=1)
    keywords: list[str] = Field(default_factory=list)
    categories: list[str] = Field(default_factory=list)


class StockUploadResult(BaseModel):
    """Result of a stock upload."""
    id: str
    channel_id: str
    work_id: str
    remote_id: str
    status: str
    uploaded_at: Optional[str] = None


class StockSalesResponse(BaseModel):
    """Sales summary for a channel + date range."""
    channel_name: str
    total_sales: int = 0
    total_revenue: float = 0.0
    currency: str = "USD"
    records: list[dict] = Field(default_factory=list)


class StockPlatformInfo(BaseModel):
    """Metadata about a supported stock platform."""
    name: str
    display_name: str
    auth_type: str
    required_specs: dict
    notes: Optional[str] = None


class StockValidateRequest(BaseModel):
    """Pre-validate a file against platform upload specs."""
    channel_name: str = Field(..., min_length=1)
    file_path: str = Field(..., min_length=1)


class StockValidateResult(BaseModel):
    """Result of file-spec validation."""
    valid: bool
    file_path: Optional[str] = None
    width_px: Optional[int] = None
    height_px: Optional[int] = None
    file_size_bytes: Optional[int] = None
    file_format: Optional[str] = None
    warnings: list[str] = Field(default_factory=list)
    blocks: list[str] = Field(default_factory=list)


# ============================================================================
# Stats
# ============================================================================


class ShotStats(BaseModel):
    """摄影师统计数据."""
    total_variants: int = 0
    pass_count: int = 0
    hold_count: int = 0
    reject_count: int = 0
    shortlist_count: int = 0
    unreviewed_count: int = 0
    raw_file_count: int = 0
    stock_channel_count: int = 0
    gps_tracked_count: int = 0


class PhotographerStatsResponse(BaseModel):
    """摄影师统计响应."""
    stats: ShotStats
    recent_activity: list[dict[str, Any]] = []


# ============================================================================
# RAW Format management (v2)
# ============================================================================


class RawFormatSchema(BaseModel):
    """RAW 格式记录."""
    model_config = {"from_attributes": True}

    id: str
    work_id: str
    file_extension: str
    file_size_bytes: Optional[int] = None
    sensor_width: Optional[int] = None
    sensor_height: Optional[int] = None
    color_space: Optional[str] = None
    created_at: Optional[datetime] = None


class RawFormatCreate(BaseModel):
    """创建 RAW 格式记录请求."""
    work_id: str = Field(..., min_length=1)
    file_extension: str = Field(..., min_length=1, max_length=10)
    file_size_bytes: Optional[int] = None
    sensor_width: Optional[int] = None
    sensor_height: Optional[int] = None
    color_space: Optional[str] = None


class RawFormatUpdate(BaseModel):
    """更新 RAW 格式记录请求."""
    file_extension: Optional[str] = None
    file_size_bytes: Optional[int] = None
    sensor_width: Optional[int] = None
    sensor_height: Optional[int] = None
    color_space: Optional[str] = None


# ============================================================================
# Digital Download (v2)
# ============================================================================


class DigitalDownloadSchema(BaseModel):
    """数字预设包."""
    model_config = {"from_attributes": True}

    id: str
    work_id: str
    product_id: Optional[str] = None
    download_url: Optional[str] = None
    max_downloads: Optional[int] = None
    download_count: int = 0
    created_at: Optional[datetime] = None


class DigitalDownloadCreate(BaseModel):
    """创建数字预设包请求."""
    work_id: str = Field(..., min_length=1)
    product_id: Optional[str] = None
    download_url: Optional[str] = None
    max_downloads: Optional[int] = None


class DigitalDownloadUpdate(BaseModel):
    """更新数字预设包请求."""
    download_url: Optional[str] = None
    max_downloads: Optional[int] = None


# ============================================================================
# Fine Art Print (v2)
# ============================================================================


class FineArtPrintConfigSchema(BaseModel):
    """艺术微喷配置."""
    model_config = {"from_attributes": True}

    id: str
    work_id: str
    paper_type: str
    max_width_cm: Optional[float] = None
    max_height_cm: Optional[float] = None
    framing_available: bool = False
    price_multiplier: float = 1.0
    is_active: bool = True
    created_at: Optional[datetime] = None


class FineArtPrintConfigCreate(BaseModel):
    """创建艺术微喷配置请求."""
    work_id: str = Field(..., min_length=1)
    paper_type: str = Field(..., min_length=1, max_length=50)
    max_width_cm: Optional[float] = None
    max_height_cm: Optional[float] = None
    framing_available: bool = False
    price_multiplier: float = 1.0


class FineArtPrintConfigUpdate(BaseModel):
    """更新艺术微喷配置请求."""
    paper_type: Optional[str] = None
    max_width_cm: Optional[float] = None
    max_height_cm: Optional[float] = None
    framing_available: Optional[bool] = None
    price_multiplier: Optional[float] = None
    is_active: Optional[bool] = None
