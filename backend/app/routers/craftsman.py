"""手工艺人 API 路由 — Phase 4 Task 1.

端点: 11 (craftsman)

Features:
  - CraftProducts CRUD
  - Factories CRUD
  - RFQs CRUD + status update
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Optional

from app.database import get_db
from app.models.factory import Factory, CraftProduct, RFQ
from app.schemas.common import ApiResponse
from app.deps import require_auth

router = APIRouter()


class CreateCraftProductPayload(BaseModel):
    work_variant_id: Optional[str] = None
    material: Optional[str] = None
    dimensions: Optional[str] = None
    craft_type: Optional[str] = None
    moq: int = 1
    unit_price: Optional[float] = None
    production_time_days: Optional[int] = None


class UpdateCraftProductPayload(BaseModel):
    work_variant_id: Optional[str] = None
    material: Optional[str] = None
    dimensions: Optional[str] = None
    craft_type: Optional[str] = None
    moq: Optional[int] = None
    unit_price: Optional[float] = None
    production_time_days: Optional[int] = None


class CreateFactoryPayload(BaseModel):
    name: str
    location: Optional[str] = None
    contact: Optional[str] = None
    rating: Optional[float] = None
    capabilities: Optional[list] = None


class UpdateFactoryPayload(BaseModel):
    name: Optional[str] = None
    location: Optional[str] = None
    contact: Optional[str] = None
    rating: Optional[float] = None
    capabilities: Optional[list] = None


class CreateRFQPayload(BaseModel):
    craft_product_id: Optional[str] = None
    title: str
    description: Optional[str] = None
    quantity_needed: Optional[int] = None
    material_specs: Optional[str] = None
    target_price: Optional[float] = None
    status: str = "open"
    quoted_factories: Optional[list] = None
    created_by: Optional[str] = None


class UpdateRFQPayload(BaseModel):
    status: Optional[str] = None
    quoted_factories: Optional[list] = None
    quantity_needed: Optional[int] = None
    target_price: Optional[float] = None


# ===========================================================================
# CraftProducts CRUD
# ===========================================================================


@router.get("/craftsman/products", response_model=ApiResponse[list])
def list_craft_products(
    craft_type: Optional[str] = None,
    work_variant_id: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """获取手工艺品列表."""
    q = db.query(CraftProduct)
    if craft_type:
        q = q.filter(CraftProduct.craft_type == craft_type)
    if work_variant_id:
        q = q.filter(CraftProduct.work_variant_id == work_variant_id)
    products = q.order_by(CraftProduct.created_at.desc()).all()
    return ApiResponse(data=[
        {
            "id": p.id,
            "work_variant_id": p.work_variant_id,
            "material": p.material,
            "dimensions": p.dimensions,
            "craft_type": p.craft_type,
            "moq": p.moq,
            "unit_price": p.unit_price,
            "production_time_days": p.production_time_days,
            "created_at": p.created_at.isoformat() if p.created_at else None,
        }
        for p in products
    ])


@router.post("/craftsman/products", response_model=ApiResponse[dict], dependencies=[Depends(require_auth)])
def create_craft_product(payload: CreateCraftProductPayload, db: Session = Depends(get_db)):
    """创建手工艺品."""
    product = CraftProduct(
        work_variant_id=payload.work_variant_id,
        material=payload.material,
        dimensions=payload.dimensions,
        craft_type=payload.craft_type,
        moq=payload.moq,
        unit_price=payload.unit_price,
        production_time_days=payload.production_time_days,
    )
    try:
        db.add(product)
        db.commit()
        db.refresh(product)
    except Exception:
        db.rollback()
        raise
    return ApiResponse(data={"id": product.id}, message="手工艺品创建成功")


@router.get("/craftsman/products/{product_id}", response_model=ApiResponse[dict])
def get_craft_product(product_id: str, db: Session = Depends(get_db)):
    """获取手工艺品详情."""
    p = db.query(CraftProduct).filter(CraftProduct.id == product_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="手工艺品不存在")
    return ApiResponse(data=_product_to_dict(p))


@router.patch("/craftsman/products/{product_id}", response_model=ApiResponse[dict], dependencies=[Depends(require_auth)])
def update_craft_product(product_id: str, payload: UpdateCraftProductPayload, db: Session = Depends(get_db)):
    """更新手工艺品."""
    p = db.query(CraftProduct).filter(CraftProduct.id == product_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="手工艺品不存在")
    update_data = payload.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(p, key, value)
    try:
        db.commit()
        db.refresh(p)
    except Exception:
        db.rollback()
        raise
    return ApiResponse(data=_product_to_dict(p), message="手工艺品更新成功")


@router.delete("/craftsman/products/{product_id}", response_model=ApiResponse[dict], dependencies=[Depends(require_auth)])
def delete_craft_product(product_id: str, db: Session = Depends(get_db)):
    """删除手工艺品."""
    p = db.query(CraftProduct).filter(CraftProduct.id == product_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="手工艺品不存在")
    try:
        db.delete(p)
        db.commit()
    except Exception:
        db.rollback()
        raise
    return ApiResponse(message="手工艺品已删除")


# ===========================================================================
# Factories CRUD
# ===========================================================================


@router.get("/craftsman/factories", response_model=ApiResponse[list])
def list_factories(
    rating_min: Optional[float] = None,
    db: Session = Depends(get_db),
):
    """获取工厂列表."""
    q = db.query(Factory)
    if rating_min is not None:
        q = q.filter(Factory.rating >= rating_min)
    factories = q.order_by(Factory.rating.desc()).all()
    return ApiResponse(data=[
        {
            "id": f.id,
            "name": f.name,
            "location": f.location,
            "contact": f.contact,
            "rating": f.rating,
            "capabilities": f.capabilities or [],
            "created_at": f.created_at.isoformat() if f.created_at else None,
        }
        for f in factories
    ])


@router.post("/craftsman/factories", response_model=ApiResponse[dict], dependencies=[Depends(require_auth)])
def create_factory(payload: CreateFactoryPayload, db: Session = Depends(get_db)):
    """添加工厂."""
    factory = Factory(
        name=payload.name,
        location=payload.location,
        contact=payload.contact,
        rating=payload.rating,
        capabilities=payload.capabilities,
    )
    try:
        db.add(factory)
        db.commit()
        db.refresh(factory)
    except Exception:
        db.rollback()
        raise
    return ApiResponse(data={"id": factory.id}, message="工厂添加成功")


@router.delete("/craftsman/factories/{factory_id}", response_model=ApiResponse, dependencies=[Depends(require_auth)])
def delete_factory(factory_id: str, db: Session = Depends(get_db)):
    """删除工厂."""
    factory = db.query(Factory).filter(Factory.id == factory_id).first()
    if not factory:
        raise HTTPException(status_code=404, detail="工厂不存在")
    try:
        db.delete(factory)
        db.commit()
    except Exception:
        db.rollback()
        raise
    return ApiResponse(message="工厂已删除")


@router.patch("/craftsman/factories/{factory_id}", response_model=ApiResponse[dict], dependencies=[Depends(require_auth)])
def update_factory(factory_id: str, payload: UpdateFactoryPayload, db: Session = Depends(get_db)):
    """更新工厂信息."""
    factory = db.query(Factory).filter(Factory.id == factory_id).first()
    if not factory:
        raise HTTPException(status_code=404, detail="工厂不存在")
    update_data = payload.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(factory, key, value)
    try:
        db.commit()
        db.refresh(factory)
    except Exception:
        db.rollback()
        raise
    return ApiResponse(data={
        "id": factory.id,
        "name": factory.name,
        "location": factory.location,
        "contact": factory.contact,
        "rating": factory.rating,
        "capabilities": factory.capabilities or [],
        "created_at": factory.created_at.isoformat() if factory.created_at else None,
    }, message="工厂更新成功")


@router.delete("/craftsman/rfqs/{rfq_id}", response_model=ApiResponse, dependencies=[Depends(require_auth)])
def delete_rfq(rfq_id: str, db: Session = Depends(get_db)):
    """删除询价单."""
    rfq = db.query(RFQ).filter(RFQ.id == rfq_id).first()
    if not rfq:
        raise HTTPException(status_code=404, detail="询价单不存在")
    try:
        db.delete(rfq)
        db.commit()
    except Exception:
        db.rollback()
        raise
    return ApiResponse(message="询价单已删除")


# ===========================================================================
# RFQs CRUD
# ===========================================================================


@router.get("/craftsman/rfqs", response_model=ApiResponse[list])
def list_rfqs(
    status: Optional[str] = None,
    created_by: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """获取询价单列表."""
    q = db.query(RFQ)
    if status:
        q = q.filter(RFQ.status == status)
    if created_by:
        q = q.filter(RFQ.created_by == created_by)
    rfqs = q.order_by(RFQ.created_at.desc()).all()
    return ApiResponse(data=[
        {
            "id": r.id,
            "craft_product_id": r.craft_product_id,
            "title": r.title,
            "description": r.description,
            "quantity_needed": r.quantity_needed,
            "material_specs": r.material_specs,
            "target_price": r.target_price,
            "status": r.status,
            "quoted_factories": r.quoted_factories or [],
            "created_by": r.created_by,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        }
        for r in rfqs
    ])


@router.post("/craftsman/rfqs", response_model=ApiResponse[dict], dependencies=[Depends(require_auth)])
def create_rfq(payload: CreateRFQPayload, db: Session = Depends(get_db)):
    """创建询价单."""
    rfq = RFQ(
        craft_product_id=payload.craft_product_id,
        title=payload.title,
        description=payload.description,
        quantity_needed=payload.quantity_needed,
        material_specs=payload.material_specs,
        target_price=payload.target_price,
        status=payload.status,
        quoted_factories=payload.quoted_factories,
        created_by=payload.created_by,
    )
    try:
        db.add(rfq)
        db.commit()
        db.refresh(rfq)
    except Exception:
        db.rollback()
        raise
    return ApiResponse(data={"id": rfq.id}, message="询价单创建成功")


@router.patch("/craftsman/rfqs/{rfq_id}", response_model=ApiResponse[dict], dependencies=[Depends(require_auth)])
def update_rfq(rfq_id: str, payload: UpdateRFQPayload, db: Session = Depends(get_db)):
    """更新询价单状态."""
    rfq = db.query(RFQ).filter(RFQ.id == rfq_id).first()
    if not rfq:
        raise HTTPException(status_code=404, detail="询价单不存在")
    update_data = payload.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(rfq, key, value)
    try:
        db.commit()
        db.refresh(rfq)
    except Exception:
        db.rollback()
        raise
    return ApiResponse(data=_rfq_to_dict(rfq), message="询价单更新成功")


# ===========================================================================
# Helpers
# ===========================================================================


def _product_to_dict(p: CraftProduct) -> dict:
    return {
        "id": p.id,
        "work_variant_id": p.work_variant_id,
        "material": p.material,
        "dimensions": p.dimensions,
        "craft_type": p.craft_type,
        "moq": p.moq,
        "unit_price": p.unit_price,
        "production_time_days": p.production_time_days,
        "created_at": p.created_at.isoformat() if p.created_at else None,
        "updated_at": p.updated_at.isoformat() if p.updated_at else None,
    }


def _rfq_to_dict(r: RFQ) -> dict:
    return {
        "id": r.id,
        "craft_product_id": r.craft_product_id,
        "title": r.title,
        "description": r.description,
        "quantity_needed": r.quantity_needed,
        "material_specs": r.material_specs,
        "target_price": r.target_price,
        "status": r.status,
        "quoted_factories": r.quoted_factories or [],
        "created_by": r.created_by,
        "created_at": r.created_at.isoformat() if r.created_at else None,
        "updated_at": r.updated_at.isoformat() if r.updated_at else None,
    }


# ===========================================================================
# Orders (placeholder — aggregates factory quotes)
# ===========================================================================

@router.get("/craftsman/orders", response_model=ApiResponse[list])
def list_craft_orders(db: Session = Depends(get_db)):
    """获取订单列表 — 基于 RFQ 报价聚合."""
    rfqs = db.query(RFQ).order_by(RFQ.created_at.desc()).limit(20).all()
    return ApiResponse(data=[
        {
            "id": r.id,
            "title": r.title,
            "status": r.status,
            "quote_count": len(r.quoted_factories or []),
            "created_at": r.created_at.isoformat() if r.created_at else None,
        }
        for r in rfqs
    ])
