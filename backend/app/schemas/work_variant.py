"""作品变体组/变体表 Pydantic 模型."""

from typing import Optional, Any
from datetime import datetime

from pydantic import BaseModel, Field, ConfigDict


# -- WorkVariantGroup --

class VariantGroupCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)


class VariantGroupUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = Field(None, max_length=500)


class VariantGroupResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    work_id: str
    name: str
    description: Optional[str] = None
    created_at: datetime
    updated_at: datetime


# -- WorkVariant --

class WorkVariantCreate(BaseModel):
    group_id: str
    name: str = Field(..., min_length=1, max_length=100)
    width: int = Field(..., gt=0)
    height: int = Field(..., gt=0)
    aspect_ratio: float = Field(..., gt=0)
    sort_order: int = Field(default=0)
    # Photographer v2 optional fields
    camera_model: Optional[str] = Field(None, max_length=100)
    lens: Optional[str] = Field(None, max_length=200)
    iso: Optional[int] = None
    aperture: Optional[str] = Field(None, max_length=20)
    shutter_speed: Optional[str] = Field(None, max_length=30)
    focal_length: Optional[str] = Field(None, max_length=30)
    gps_latitude: Optional[float] = None
    gps_longitude: Optional[float] = None
    gps_altitude: Optional[float] = None
    raw_file_path: Optional[str] = Field(None, max_length=500)
    shot_status: Optional[str] = None
    shot_notes: Optional[str] = None
    stock_channels: Optional[dict] = None


class WorkVariantUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=100)
    width: Optional[int] = Field(None, gt=0)
    height: Optional[int] = Field(None, gt=0)
    aspect_ratio: Optional[float] = Field(None, gt=0)
    sort_order: Optional[int] = None
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
    shot_status: Optional[str] = None
    shot_notes: Optional[str] = None
    stock_channels: Optional[dict] = None


class WorkVariantResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    group_id: str
    name: str
    width: int
    height: int
    aspect_ratio: float
    sort_order: int
    created_at: datetime
    # Photographer v2 fields
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
    shot_status: Optional[str] = None
    shot_notes: Optional[str] = None
    stock_channels: Optional[dict] = None
