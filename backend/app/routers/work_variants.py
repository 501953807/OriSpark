"""作品变体组 API 路由 — 对应: docs/modules-v3/01-creative-assets.md
Phase 3: 横竖屏版本管理
端点: 10 (work_variants)"""

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from typing import Optional

from app.database import get_db
from app.models.work_variant import WorkVariantGroup, WorkVariant
from app.schemas.common import ApiResponse
from app.deps import require_auth

router = APIRouter()


# ============================================================================
# Request schemas
# ============================================================================


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
# Helpers
# ============================================================================


def _calc_aspect_ratio(width: int, height: int) -> float:
    import math
    gcd = math.gcd(width, height)
    return round(width / gcd / (height / gcd), 4)


def _group_to_dict(g: WorkVariantGroup) -> dict:
    return {
        "id": g.id,
        "work_id": g.work_id,
        "name": g.name,
        "description": g.description,
        "created_at": g.created_at.isoformat() if g.created_at else None,
        "updated_at": g.updated_at.isoformat() if g.updated_at else None,
    }


def _variant_to_dict(v: WorkVariant) -> dict:
    return {
        "id": v.id,
        "group_id": v.group_id,
        "name": v.name,
        "width": v.width,
        "height": v.height,
        "aspect_ratio": v.aspect_ratio,
        "sort_order": v.sort_order,
        "created_at": v.created_at.isoformat() if v.created_at else None,
    }


# ============================================================================
# Group endpoints
# ============================================================================


@router.get("/work-variants/groups", response_model=ApiResponse[list])
def list_groups(
    work_id: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    """获取所有变体组列表，可按 work_id 过滤."""
    q = db.query(WorkVariantGroup)
    if work_id:
        q = q.filter(WorkVariantGroup.work_id == work_id)
    groups = q.order_by(WorkVariantGroup.created_at.desc()).all()
    return ApiResponse(data=[_group_to_dict(g) for g in groups])


@router.get("/work-variants/groups/{group_id}", response_model=ApiResponse[dict])
def get_group(group_id: str, db: Session = Depends(get_db)):
    """获取指定变体组及其变体."""
    group = db.query(WorkVariantGroup).filter(WorkVariantGroup.id == group_id).first()
    if not group:
        raise HTTPException(status_code=404, detail="变体组不存在")
    result = _group_to_dict(group)
    result["variants"] = [
        _variant_to_dict(v)
        for v in db.query(WorkVariant)
        .filter(WorkVariant.group_id == group_id)
        .order_by(WorkVariant.sort_order.asc())
        .all()
    ]
    return ApiResponse(data=result)


@router.post("/work-variants/groups", response_model=ApiResponse[dict], dependencies=[Depends(require_auth)])
def create_group(payload: GroupCreate, db: Session = Depends(get_db)):
    """创建新的变体组."""
    # Verify work exists
    if payload.work_id:
        from app.models.work import Work
        if not db.query(Work).filter(Work.id == payload.work_id).first():
            raise HTTPException(status_code=404, detail="作品不存在")
    group = WorkVariantGroup(
        work_id=payload.work_id,
        name=payload.name,
        description=payload.description,
    )
    db.add(group)
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise
    db.refresh(group)
    return ApiResponse(data=_group_to_dict(group), message="变体组创建成功")


@router.put("/work-variants/groups/{group_id}", response_model=ApiResponse[dict], dependencies=[Depends(require_auth)])
def update_group(group_id: str, payload: GroupUpdate, db: Session = Depends(get_db)):
    """更新变体组."""
    group = db.query(WorkVariantGroup).filter(WorkVariantGroup.id == group_id).first()
    if not group:
        raise HTTPException(status_code=404, detail="变体组不存在")
    for key in ("name", "description"):
        if key in payload.model_fields_set:
            setattr(group, key, getattr(payload, key))
    group.updated_at = datetime.utcnow()
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise
    db.refresh(group)
    return ApiResponse(data=_group_to_dict(group), message="变体组更新成功")


@router.delete("/work-variants/groups/{group_id}", response_model=ApiResponse[dict], dependencies=[Depends(require_auth)])
def delete_group(group_id: str, db: Session = Depends(get_db)):
    """删除变体组及其所有变体."""
    group = db.query(WorkVariantGroup).filter(WorkVariantGroup.id == group_id).first()
    if not group:
        raise HTTPException(status_code=404, detail="变体组不存在")
    db.delete(group)
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise
    return ApiResponse(data={"success": True, "message": "变体组已删除"})


# ============================================================================
# Group → Variant endpoints
# ============================================================================


@router.get("/work-variants/groups/{group_id}/variants", response_model=ApiResponse[list])
def list_variants(
    group_id: str,
    db: Session = Depends(get_db),
):
    """获取变体组内所有变体."""
    group = db.query(WorkVariantGroup).filter(WorkVariantGroup.id == group_id).first()
    if not group:
        raise HTTPException(status_code=404, detail="变体组不存在")
    variants = (
        db.query(WorkVariant)
        .filter(WorkVariant.group_id == group_id)
        .order_by(WorkVariant.sort_order.asc())
        .all()
    )
    return ApiResponse(data=[_variant_to_dict(v) for v in variants])


@router.post("/work-variants/groups/{group_id}/variants", response_model=ApiResponse[dict], dependencies=[Depends(require_auth)])
def add_variant(group_id: str, payload: VariantCreate, db: Session = Depends(get_db)):
    """向变体组添加新变体."""
    group = db.query(WorkVariantGroup).filter(WorkVariantGroup.id == group_id).first()
    if not group:
        raise HTTPException(status_code=404, detail="变体组不存在")
    variant = WorkVariant(
        group_id=group_id,
        name=payload.name,
        width=payload.width,
        height=payload.height,
        aspect_ratio=_calc_aspect_ratio(payload.width, payload.height),
        sort_order=payload.sort_order,
    )
    db.add(variant)
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise
    db.refresh(variant)
    return ApiResponse(data=_variant_to_dict(variant), message="变体创建成功")


@router.put("/work-variants/groups/{group_id}/variants/{variant_id}", response_model=ApiResponse[dict], dependencies=[Depends(require_auth)])
def update_variant(
    group_id: str,
    variant_id: str,
    payload: VariantUpdate,
    db: Session = Depends(get_db),
):
    """更新变体信息."""
    variant = db.query(WorkVariant).filter(
        WorkVariant.id == variant_id,
        WorkVariant.group_id == group_id,
    ).first()
    if not variant:
        raise HTTPException(status_code=404, detail="变体不存在")
    for key in ("name", "width", "height", "sort_order"):
        if key in payload.model_fields_set:
            setattr(variant, key, getattr(payload, key))
    # Recalculate aspect ratio if dimensions changed
    if "width" in payload.model_fields_set or "height" in payload.model_fields_set:
        w = payload.width if payload.width is not None else variant.width
        h = payload.height if payload.height is not None else variant.height
        variant.aspect_ratio = _calc_aspect_ratio(w, h)
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise
    db.refresh(variant)
    return ApiResponse(data=_variant_to_dict(variant), message="变体更新成功")


@router.delete("/work-variants/groups/{group_id}/variants/{variant_id}", response_model=ApiResponse[dict], dependencies=[Depends(require_auth)])
def delete_variant(group_id: str, variant_id: str, db: Session = Depends(get_db)):
    """删除变体."""
    variant = db.query(WorkVariant).filter(
        WorkVariant.id == variant_id,
        WorkVariant.group_id == group_id,
    ).first()
    if not variant:
        raise HTTPException(status_code=404, detail="变体不存在")
    db.delete(variant)
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise
    return ApiResponse(data={"success": True, "message": "变体已删除"})


# ============================================================================
# Generate aspect ratio variants
# ============================================================================


class GenerateResponse(BaseModel):
    success: bool
    message: str
    group_id: str
    variants_created: int


@router.post("/work-variants/{work_id}/generate", response_model=ApiResponse[GenerateResponse], dependencies=[Depends(require_auth)])
def generate_variants(payload: GenerateVariantsRequest, db: Session = Depends(get_db)):
    """为作品生成标准宽高比变体。

    支持的标准宽高比: 16:9, 9:16, 1:1, 4:3, 3:4, 4:5, 5:4
    """
    # Verify work exists
    from app.models.work import Work
    work = db.query(Work).filter(Work.id == payload.work_id).first()
    if not work:
        raise HTTPException(status_code=404, detail="作品不存在")

    # Get or create group
    group = db.query(WorkVariantGroup).filter(
        WorkVariantGroup.id == payload.group_id,
        WorkVariantGroup.work_id == payload.work_id,
    ).first()
    if not group:
        group = WorkVariantGroup(
            work_id=payload.work_id,
            name=payload.group_id,
        )
        db.add(group)
        db.flush()

    # Standard aspect ratios to generate
    standard_ratios = [
        ("16:9", 16, 9),
        ("9:16", 9, 16),
        ("1:1", 1, 1),
        ("4:3", 4, 3),
        ("3:4", 3, 4),
        ("4:5", 4, 5),
        ("5:4", 5, 4),
    ]

    # Use the work's width as base, scale heights accordingly
    base_width = 1920
    variants_created = 0
    now = datetime.utcnow()

    for name, w_num, h_num in standard_ratios:
        # Already exists? skip
        existing = db.query(WorkVariant).filter(
            WorkVariant.group_id == group.id,
            WorkVariant.name == name,
        ).first()
        if existing:
            continue

        scaled_width = base_width * w_num
        scaled_height = base_width * h_num // w_num
        variant = WorkVariant(
            group_id=group.id,
            name=name,
            width=scaled_width,
            height=scaled_height,
            aspect_ratio=w_num / h_num,
            sort_order=w_num + h_num,
            created_at=now,
        )
        db.add(variant)
        variants_created += 1

    if variants_created > 0:
        try:
            db.commit()
        except Exception:
            db.rollback()
            raise
    else:
        db.refresh(group)

    return ApiResponse(
        data=GenerateResponse(
            success=True,
            message=f"生成了 {variants_created} 个新变体" if variants_created > 0 else "变体已存在，无需新建",
            group_id=group.id,
            variants_created=variants_created,
        )
    )
