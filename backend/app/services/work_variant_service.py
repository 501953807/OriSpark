# -*- coding: utf-8 -*-
"""作品变体组服务层 — 从 work_variants.py 提取的业务逻辑."""

import math
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import Session

from app.models.work_variant import WorkVariantGroup, WorkVariant
from app.models.work import Work


# ============================================================================
# 辅助函数
# ============================================================================


def _calc_aspect_ratio(width: int, height: int) -> float:
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
# Group CRUD
# ============================================================================


def list_groups(db: Session, work_id: Optional[str] = None) -> list:
    """获取所有变体组列表，可按 work_id 过滤."""
    q = db.query(WorkVariantGroup)
    if work_id:
        q = q.filter(WorkVariantGroup.work_id == work_id)
    groups = q.order_by(WorkVariantGroup.created_at.desc()).all()
    return [_group_to_dict(g) for g in groups]


def get_group(db: Session, group_id: str) -> Optional[dict]:
    """获取指定变体组及其变体."""
    group = db.query(WorkVariantGroup).filter(WorkVariantGroup.id == group_id).first()
    if not group:
        return None
    result = _group_to_dict(group)
    result["variants"] = [
        _variant_to_dict(v)
        for v in db.query(WorkVariant)
        .filter(WorkVariant.group_id == group_id)
        .order_by(WorkVariant.sort_order.asc())
        .all()
    ]
    return result


def create_group(db: Session, work_id: str, name: str, description: Optional[str] = None) -> Optional[dict]:
    """创建新的变体组."""
    if work_id:
        if not db.query(Work).filter(Work.id == work_id).first():
            return None
    group = WorkVariantGroup(
        work_id=work_id,
        name=name,
        description=description,
    )
    db.add(group)
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise
    db.refresh(group)
    return _group_to_dict(group)


def update_group(db: Session, group_id: str, payload: dict) -> Optional[dict]:
    """更新变体组."""
    group = db.query(WorkVariantGroup).filter(WorkVariantGroup.id == group_id).first()
    if not group:
        return None
    for key in ("name", "description"):
        if key in payload:
            setattr(group, key, payload[key])
    group.updated_at = datetime.now(timezone.utc)
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise
    db.refresh(group)
    return _group_to_dict(group)


def delete_group(db: Session, group_id: str) -> bool:
    """删除变体组及其所有变体."""
    group = db.query(WorkVariantGroup).filter(WorkVariantGroup.id == group_id).first()
    if not group:
        return False
    db.delete(group)
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise
    return True


# ============================================================================
# Variant CRUD
# ============================================================================


def list_variants(db: Session, group_id: str) -> Optional[list]:
    """获取变体组内所有变体."""
    group = db.query(WorkVariantGroup).filter(WorkVariantGroup.id == group_id).first()
    if not group:
        return None
    variants = (
        db.query(WorkVariant)
        .filter(WorkVariant.group_id == group_id)
        .order_by(WorkVariant.sort_order.asc())
        .all()
    )
    return [_variant_to_dict(v) for v in variants]


def add_variant(db: Session, group_id: str, payload: dict) -> Optional[dict]:
    """向变体组添加新变体."""
    group = db.query(WorkVariantGroup).filter(WorkVariantGroup.id == group_id).first()
    if not group:
        return None
    variant = WorkVariant(
        group_id=group_id,
        name=payload["name"],
        width=payload["width"],
        height=payload["height"],
        aspect_ratio=_calc_aspect_ratio(payload["width"], payload["height"]),
        sort_order=payload.get("sort_order", 0),
    )
    db.add(variant)
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise
    db.refresh(variant)
    return _variant_to_dict(variant)


def update_variant(db: Session, group_id: str, variant_id: str, payload: dict) -> Optional[dict]:
    """更新变体信息."""
    variant = db.query(WorkVariant).filter(
        WorkVariant.id == variant_id,
        WorkVariant.group_id == group_id,
    ).first()
    if not variant:
        return None
    for key in ("name", "width", "height", "sort_order"):
        if key in payload:
            setattr(variant, key, payload[key])
    # Recalculate aspect ratio if dimensions changed
    if "width" in payload or "height" in payload:
        w = payload.get("width", variant.width)
        h = payload.get("height", variant.height)
        variant.aspect_ratio = _calc_aspect_ratio(w, h)
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise
    db.refresh(variant)
    return _variant_to_dict(variant)


def delete_variant(db: Session, group_id: str, variant_id: str) -> bool:
    """删除变体."""
    variant = db.query(WorkVariant).filter(
        WorkVariant.id == variant_id,
        WorkVariant.group_id == group_id,
    ).first()
    if not variant:
        return False
    db.delete(variant)
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise
    return True


# ============================================================================
# Generate variants
# ============================================================================


def generate_variants(db: Session, work_id: str, group_id: str) -> dict:
    """为作品生成标准宽高比变体.

    支持的标准宽高比: 16:9, 9:16, 1:1, 4:3, 3:4, 4:5, 5:4
    """
    if not db.query(Work).filter(Work.id == work_id).first():
        return {"error": "作品不存在"}

    group = db.query(WorkVariantGroup).filter(
        WorkVariantGroup.id == group_id,
        WorkVariantGroup.work_id == work_id,
    ).first()
    if not group:
        group = WorkVariantGroup(
            work_id=work_id,
            name=group_id,
        )
        db.add(group)
        db.flush()

    standard_ratios = [
        ("16:9", 16, 9),
        ("9:16", 9, 16),
        ("1:1", 1, 1),
        ("4:3", 4, 3),
        ("3:4", 3, 4),
        ("4:5", 4, 5),
        ("5:4", 5, 4),
    ]

    base_width = 1920
    variants_created = 0
    now = datetime.now(timezone.utc)

    for name, w_num, h_num in standard_ratios:
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

    return {
        "success": True,
        "message": f"生成了 {variants_created} 个新变体" if variants_created > 0 else "变体已存在，无需新建",
        "group_id": group.id,
        "variants_created": variants_created,
    }
