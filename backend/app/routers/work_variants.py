"""作品变体组 API 路由 — 对应: docs/modules-v5/01-creative-assets.md
Phase 3: 横竖屏版本管理
端点: 10 (work_variants)

业务逻辑已提取至 work_variant_service.py.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from typing import Optional

from app.database import get_db
from app.schemas.common import ApiResponse
from app.deps import require_auth
from app.services.work_variant_service import (
    list_groups, get_group, create_group, update_group, delete_group,
    list_variants, add_variant, update_variant, delete_variant,
    generate_variants,
)

router = APIRouter()


class GroupCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    work_id: str = Field(..., min_length=1, max_length=32)


class GroupUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None


class VariantCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    width: int = Field(..., gt=0)
    height: int = Field(..., gt=0)
    sort_order: int = Field(default=0)


class VariantUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    width: Optional[int] = Field(None, gt=0)
    height: Optional[int] = Field(None, gt=0)
    sort_order: Optional[int] = None


class GenerateVariantsRequest(BaseModel):
    work_id: str = Field(..., min_length=1, max_length=32)
    group_id: str = Field(..., min_length=1, max_length=32)


# ============================================================================
# Group endpoints
# ============================================================================


@router.get("/work-variants/groups", response_model=ApiResponse)
def list_groups_endpoint(
    work_id: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    """获取所有变体组列表，可按 work_id 过滤."""
    return ApiResponse(data=list_groups(db, work_id))


@router.get("/work-variants/groups/{group_id}", response_model=ApiResponse)
def get_group_endpoint(group_id: str, db: Session = Depends(get_db)):
    """获取指定变体组及其变体."""
    result = get_group(db, group_id)
    if not result:
        raise HTTPException(status_code=404, detail="变体组不存在")
    return ApiResponse(data=result)


@router.post("/work-variants/groups", response_model=ApiResponse, dependencies=[Depends(require_auth)])
def create_group_endpoint(payload: GroupCreate, db: Session = Depends(get_db)):
    """创建新的变体组."""
    result = create_group(db, payload.work_id, payload.name, payload.description)
    if not result:
        raise HTTPException(status_code=404, detail="作品不存在")
    return ApiResponse(data=result, message="变体组创建成功")


@router.put("/work-variants/groups/{group_id}", response_model=ApiResponse, dependencies=[Depends(require_auth)])
def update_group_endpoint(group_id: str, payload: GroupUpdate, db: Session = Depends(get_db)):
    """更新变体组."""
    result = update_group(db, group_id, payload.model_dump(exclude_unset=True))
    if not result:
        raise HTTPException(status_code=404, detail="变体组不存在")
    return ApiResponse(data=result, message="变体组更新成功")


@router.delete("/work-variants/groups/{group_id}", response_model=ApiResponse, dependencies=[Depends(require_auth)])
def delete_group_endpoint(group_id: str, db: Session = Depends(get_db)):
    """删除变体组及其所有变体."""
    deleted = delete_group(db, group_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="变体组不存在")
    return ApiResponse(data={"success": True, "message": "变体组已删除"})


# ============================================================================
# Group → Variant endpoints
# ============================================================================


@router.get("/work-variants/groups/{group_id}/variants", response_model=ApiResponse)
def list_variants_endpoint(
    group_id: str,
    db: Session = Depends(get_db),
):
    """获取变体组内所有变体."""
    result = list_variants(db, group_id)
    if not result:
        raise HTTPException(status_code=404, detail="变体组不存在")
    return ApiResponse(data=result)


@router.post("/work-variants/groups/{group_id}/variants", response_model=ApiResponse, dependencies=[Depends(require_auth)])
def add_variant_endpoint(group_id: str, payload: VariantCreate, db: Session = Depends(get_db)):
    """向变体组添加新变体."""
    result = add_variant(db, group_id, payload.model_dump(exclude_unset=True))
    if not result:
        raise HTTPException(status_code=404, detail="变体组不存在")
    return ApiResponse(data=result, message="变体创建成功")


@router.put("/work-variants/groups/{group_id}/variants/{variant_id}", response_model=ApiResponse, dependencies=[Depends(require_auth)])
def update_variant_endpoint(
    group_id: str,
    variant_id: str,
    payload: VariantUpdate,
    db: Session = Depends(get_db),
):
    """更新变体信息."""
    result = update_variant(db, group_id, variant_id, payload.model_dump(exclude_unset=True))
    if not result:
        raise HTTPException(status_code=404, detail="变体不存在")
    return ApiResponse(data=result, message="变体更新成功")


@router.delete("/work-variants/groups/{group_id}/variants/{variant_id}", response_model=ApiResponse, dependencies=[Depends(require_auth)])
def delete_variant_endpoint(group_id: str, variant_id: str, db: Session = Depends(get_db)):
    """删除变体."""
    deleted = delete_variant(db, group_id, variant_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="变体不存在")
    return ApiResponse(data={"success": True, "message": "变体已删除"})


# ============================================================================
# Generate aspect ratio variants
# ============================================================================


class GenerateResponse(BaseModel):
    success: bool
    message: str
    group_id: str
    variants_created: int


@router.post("/work-variants/{work_id}/generate", response_model=ApiResponse, dependencies=[Depends(require_auth)])
def generate_variants_endpoint(payload: GenerateVariantsRequest, db: Session = Depends(get_db)):
    """为作品生成标准宽高比变体."""
    result = generate_variants(db, payload.work_id, payload.group_id)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return ApiResponse(data=GenerateResponse(**result))
