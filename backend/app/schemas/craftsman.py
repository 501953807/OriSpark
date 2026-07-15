"""手工艺人 Pydantic schemas — Phase 4 Task 1."""

from typing import Optional
from datetime import datetime

from pydantic import BaseModel, ConfigDict


# ===========================================================================
# Factory schemas
# ===========================================================================


class FactoryCreate(BaseModel):
    name: str
    location: Optional[str] = None
    contact: Optional[str] = None
    rating: Optional[float] = None
    capabilities: Optional[list] = None


class FactoryUpdate(BaseModel):
    name: Optional[str] = None
    location: Optional[str] = None
    contact: Optional[str] = None
    rating: Optional[float] = None
    capabilities: Optional[list] = None


class FactoryFull(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    name: str
    location: Optional[str] = None
    contact: Optional[str] = None
    rating: Optional[float] = None
    capabilities: Optional[list] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


# ===========================================================================
# CraftProduct schemas
# ===========================================================================


class CraftProductCreate(BaseModel):
    work_variant_id: Optional[str] = None
    material: Optional[str] = None
    dimensions: Optional[dict] = None
    craft_type: Optional[str] = None
    moq: int = 1
    unit_price: Optional[float] = None
    production_time_days: Optional[int] = None


class CraftProductUpdate(BaseModel):
    work_variant_id: Optional[str] = None
    material: Optional[str] = None
    dimensions: Optional[dict] = None
    craft_type: Optional[str] = None
    moq: Optional[int] = None
    unit_price: Optional[float] = None
    production_time_days: Optional[int] = None


class CraftProductFull(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    work_variant_id: Optional[str] = None
    material: Optional[str] = None
    dimensions: Optional[dict] = None
    craft_type: Optional[str] = None
    moq: int
    unit_price: Optional[float] = None
    production_time_days: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


# ===========================================================================
# RFQ (craftsman) schemas
# ===========================================================================


class RFQCreate(BaseModel):
    craft_product_id: Optional[str] = None
    title: str
    description: Optional[str] = None
    quantity_needed: Optional[int] = None
    material_specs: Optional[dict] = None
    target_price: Optional[float] = None
    status: str = "open"
    quoted_factories: Optional[list] = None
    created_by: Optional[str] = None


class RFQUpdate(BaseModel):
    status: Optional[str] = None
    quoted_factories: Optional[list] = None
    quantity_needed: Optional[int] = None
    target_price: Optional[float] = None


class RFQFull(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    craft_product_id: Optional[str] = None
    title: str
    description: Optional[str] = None
    quantity_needed: Optional[int] = None
    material_specs: Optional[dict] = None
    target_price: Optional[float] = None
    status: str
    quoted_factories: Optional[list] = None
    created_by: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
