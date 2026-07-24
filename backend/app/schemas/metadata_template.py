"""元数据模板 Pydantic 模型."""

from typing import Optional, Any
from datetime import datetime

from pydantic import BaseModel, Field, ConfigDict


class MetadataTemplateCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    fields: Optional[list[dict]] = None
    is_default: bool = False


class MetadataTemplateUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = None
    fields: Optional[list[dict]] = None
    is_default: Optional[bool] = None


class MetadataTemplateResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    name: str
    description: Optional[str] = None
    fields: Optional[list[dict]] = None
    is_default: bool
    created_by: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class TemplateFieldCreate(BaseModel):
    template_id: str
    field_key: str = Field(..., min_length=1, max_length=100)
    label: str = Field(..., min_length=1, max_length=200)
    field_type: str = Field(..., pattern="^(string|number|date|boolean|text|choice)$")
    required: bool = False
    default_value: Optional[Any] = None
    choices: Optional[list[str]] = None
    sort_order: int = 0


class TemplateFieldUpdate(BaseModel):
    field_key: Optional[str] = None
    label: Optional[str] = None
    field_type: Optional[str] = None
    required: Optional[bool] = None
    default_value: Optional[Any] = None
    choices: Optional[list[str]] = None
    sort_order: Optional[int] = None


class TemplateFieldResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    template_id: str
    field_key: str
    label: str
    field_type: str
    required: bool
    default_value: Optional[Any] = None
    choices: Optional[list[str]] = None
    sort_order: int
    created_at: datetime
    updated_at: datetime
