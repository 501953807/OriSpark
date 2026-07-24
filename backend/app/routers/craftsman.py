"""手工艺人 API 路由 — Phase 4 Task 1.

端点: 11 (craftsman)

Features:
  - CraftProducts CRUD
  - Factories CRUD
  - RFQs CRUD + status update
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from typing import Optional

from app.database import get_db
from app.models.factory import Factory, CraftProduct, RFQ
from app.models.craftsman_v3 import PhysicalProduct, MaterialInventory, MaterialTransaction, ProductionBatch
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


# ============================================================================
# v2: Physical Product (15.3.1)
# ============================================================================


class PhysicalProductCreate(BaseModel):
    work_id: Optional[str] = None
    title: str = Field(..., min_length=1, max_length=500)
    description: Optional[str] = None
    category: Optional[str] = Field(None, max_length=50)
    dimensions: Optional[dict] = None
    weight_g: Optional[int] = None
    price: float = Field(..., gt=0)
    currency: str = Field("CNY", max_length=10)
    stock_quantity: int = Field(1, ge=0)
    shipping_regions: Optional[list[str]] = None


class PhysicalProductUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    dimensions: Optional[dict] = None
    weight_g: Optional[int] = None
    price: Optional[float] = None
    currency: Optional[str] = None
    stock_quantity: Optional[int] = None
    shipping_regions: Optional[list[str]] = None
    is_active: Optional[bool] = None


@router.get("/craftsman/physical-products", response_model=ApiResponse[list])
def list_physical_products(
    category: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """获取物理产品列表."""
    q = db.query(PhysicalProduct).filter(PhysicalProduct.is_active == True)
    if category:
        q = q.filter(PhysicalProduct.category == category)
    products = q.order_by(PhysicalProduct.created_at.desc()).all()
    return ApiResponse(data=[{
        "id": p.id,
        "work_id": p.work_id,
        "title": p.title,
        "description": p.description,
        "category": p.category,
        "dimensions": p.dimensions,
        "weight_g": p.weight_g,
        "price": p.price,
        "currency": p.currency,
        "stock_quantity": p.stock_quantity,
        "shipping_regions": p.shipping_regions or [],
        "is_active": p.is_active,
        "created_at": p.created_at.isoformat() if p.created_at else None,
        "updated_at": p.updated_at.isoformat() if p.updated_at else None,
    } for p in products])


@router.post("/craftsman/physical-products", response_model=ApiResponse[dict], dependencies=[Depends(require_auth)])
def create_physical_product(payload: PhysicalProductCreate, db: Session = Depends(get_db)):
    """创建物理产品."""
    product = PhysicalProduct(
        user_id="local",
        work_id=payload.work_id,
        title=payload.title,
        description=payload.description,
        category=payload.category,
        dimensions=payload.dimensions,
        weight_g=payload.weight_g,
        price=payload.price,
        currency=payload.currency,
        stock_quantity=payload.stock_quantity,
        shipping_regions=payload.shipping_regions,
    )
    try:
        db.add(product)
        db.commit()
        db.refresh(product)
    except Exception:
        db.rollback()
        raise
    return ApiResponse(data={"id": product.id}, message="物理产品创建成功")


@router.patch("/craftsman/physical-products/{product_id}", response_model=ApiResponse[dict], dependencies=[Depends(require_auth)])
def update_physical_product(product_id: str, payload: PhysicalProductUpdate, db: Session = Depends(get_db)):
    """更新物理产品."""
    product = db.query(PhysicalProduct).filter(PhysicalProduct.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="物理产品不存在")
    update_data = payload.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(product, key, value)
    try:
        db.commit()
        db.refresh(product)
    except Exception:
        db.rollback()
        raise
    return ApiResponse(data={"id": product.id}, message="物理产品已更新")


@router.delete("/craftsman/physical-products/{product_id}", response_model=ApiResponse, dependencies=[Depends(require_auth)])
def delete_physical_product(product_id: str, db: Session = Depends(get_db)):
    """删除物理产品."""
    product = db.query(PhysicalProduct).filter(PhysicalProduct.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="物理产品不存在")
    try:
        db.delete(product)
        db.commit()
    except Exception:
        db.rollback()
        raise
    return ApiResponse(message="物理产品已删除")


# ============================================================================
# v2: Material Inventory (15.3.2)
# ============================================================================


class MaterialInventoryCreate(BaseModel):
    material_name: str = Field(..., min_length=1, max_length=200)
    material_category: Optional[str] = Field(None, max_length=50)
    unit: str = Field(..., min_length=1, max_length=20)
    quantity_on_hand: float = Field(0.0, ge=0)
    quantity_reserved: float = Field(0.0, ge=0)
    reorder_level: Optional[float] = None
    unit_cost: Optional[float] = None
    location: Optional[str] = Field(None, max_length=200)


class MaterialInventoryUpdate(BaseModel):
    material_name: Optional[str] = None
    material_category: Optional[str] = None
    unit: Optional[str] = None
    quantity_on_hand: Optional[float] = None
    quantity_reserved: Optional[float] = None
    reorder_level: Optional[float] = None
    unit_cost: Optional[float] = None
    location: Optional[str] = None


class MaterialTransactionCreate(BaseModel):
    material_id: str = Field(..., min_length=1)
    transaction_type: str = Field(..., pattern="^(purchase|consume|scrap)$")
    quantity: float = Field(..., gt=0)
    reference_type: Optional[str] = None
    reference_id: Optional[str] = None
    notes: Optional[str] = None


@router.get("/craftsman/materials", response_model=ApiResponse[list])
def list_materials(db: Session = Depends(get_db)):
    """获取原料库存列表."""
    items = db.query(MaterialInventory).order_by(MaterialInventory.created_at.desc()).all()
    return ApiResponse(data=[{
        "id": m.id,
        "material_name": m.material_name,
        "material_category": m.material_category,
        "unit": m.unit,
        "quantity_on_hand": m.quantity_on_hand,
        "quantity_reserved": m.quantity_reserved,
        "available_qty": m.quantity_on_hand - (m.quantity_reserved or 0),
        "reorder_level": m.reorder_level,
        "unit_cost": m.unit_cost,
        "location": m.location,
        "last_counted_at": m.last_counted_at.isoformat() if m.last_counted_at else None,
        "created_at": m.created_at.isoformat() if m.created_at else None,
    } for m in items])


@router.post("/craftsman/materials", response_model=ApiResponse[dict], dependencies=[Depends(require_auth)])
def create_material(payload: MaterialInventoryCreate, db: Session = Depends(get_db)):
    """添加原料库存."""
    mat = MaterialInventory(
        user_id="local",
        material_name=payload.material_name,
        material_category=payload.material_category,
        unit=payload.unit,
        quantity_on_hand=payload.quantity_on_hand,
        quantity_reserved=payload.quantity_reserved,
        reorder_level=payload.reorder_level,
        unit_cost=payload.unit_cost,
        location=payload.location,
    )
    try:
        db.add(mat)
        db.commit()
        db.refresh(mat)
    except Exception:
        db.rollback()
        raise
    return ApiResponse(data={"id": mat.id}, message="原料已添加")


@router.patch("/craftsman/materials/{material_id}", response_model=ApiResponse[dict], dependencies=[Depends(require_auth)])
def update_material(material_id: str, payload: MaterialInventoryUpdate, db: Session = Depends(get_db)):
    """更新原料库存."""
    mat = db.query(MaterialInventory).filter(MaterialInventory.id == material_id).first()
    if not mat:
        raise HTTPException(status_code=404, detail="原料不存在")
    update_data = payload.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(mat, key, value)
    try:
        db.commit()
        db.refresh(mat)
    except Exception:
        db.rollback()
        raise
    return ApiResponse(data={"id": mat.id}, message="原料已更新")


@router.delete("/craftsman/materials/{material_id}", response_model=ApiResponse, dependencies=[Depends(require_auth)])
def delete_material(material_id: str, db: Session = Depends(get_db)):
    """删除原料库存."""
    mat = db.query(MaterialInventory).filter(MaterialInventory.id == material_id).first()
    if not mat:
        raise HTTPException(status_code=404, detail="原料不存在")
    try:
        db.delete(mat)
        db.commit()
    except Exception:
        db.rollback()
        raise
    return ApiResponse(message="原料已删除")


@router.post("/craftsman/material-transactions", response_model=ApiResponse[dict], dependencies=[Depends(require_auth)])
def create_material_transaction(payload: MaterialTransactionCreate, db: Session = Depends(get_db)):
    """记录材料出入库流水."""
    mat = db.query(MaterialInventory).filter(MaterialInventory.id == payload.material_id).first()
    if not mat:
        raise HTTPException(status_code=404, detail="原料不存在")

    txn = MaterialTransaction(
        material_id=payload.material_id,
        transaction_type=payload.transaction_type,
        quantity=payload.quantity,
        reference_type=payload.reference_type,
        reference_id=payload.reference_id,
        notes=payload.notes,
    )
    # Update inventory on-hand based on transaction type
    if payload.transaction_type == "purchase":
        mat.quantity_on_hand += payload.quantity
    elif payload.transaction_type in ("consume", "scrap"):
        mat.quantity_on_hand -= payload.quantity
        if mat.quantity_on_hand < 0:
            db.rollback()
            raise HTTPException(status_code=400, detail="库存不足，无法出库或报废")
    try:
        db.add(txn)
        db.commit()
        db.refresh(txn)
    except Exception:
        db.rollback()
        raise
    return ApiResponse(data={"id": txn.id}, message=f"材料{payload.transaction_type}记录成功")


@router.get("/craftsman/material-transactions", response_model=ApiResponse[list])
def list_material_transactions(
    material_id: Optional[str] = None,
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    """获取材料流水记录."""
    q = db.query(MaterialTransaction)
    if material_id:
        q = q.filter(MaterialTransaction.material_id == material_id)
    txns = q.order_by(MaterialTransaction.created_at.desc()).limit(limit).all()
    return ApiResponse(data=[{
        "id": t.id,
        "material_id": t.material_id,
        "transaction_type": t.transaction_type,
        "quantity": t.quantity,
        "reference_type": t.reference_type,
        "reference_id": t.reference_id,
        "notes": t.notes,
        "created_at": t.created_at.isoformat() if t.created_at else None,
    } for t in txns])


# ============================================================================
# v2: Production Batch (15.3.3)
# ============================================================================


class ProductionBatchCreate(BaseModel):
    work_id: Optional[str] = None
    title: str = Field(..., min_length=1, max_length=500)
    planned_quantity: int = Field(..., ge=1)


class ProductionBatchUpdate(BaseModel):
    title: Optional[str] = None
    planned_quantity: Optional[int] = None
    produced_quantity: Optional[int] = None
    sold_quantity: Optional[int] = None
    status: Optional[str] = Field(None, pattern="^(planned|in_production|done|shipped)$")
    started_at: Optional[str] = None
    completed_at: Optional[str] = None


@router.get("/craftsman/production-batches", response_model=ApiResponse[list])
def list_production_batches(
    status: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """获取生产批次列表."""
    q = db.query(ProductionBatch)
    if status:
        q = q.filter(ProductionBatch.status == status)
    batches = q.order_by(ProductionBatch.created_at.desc()).all()
    return ApiResponse(data=[{
        "id": b.id,
        "work_id": b.work_id,
        "title": b.title,
        "planned_quantity": b.planned_quantity,
        "produced_quantity": b.produced_quantity,
        "sold_quantity": b.sold_quantity,
        "status": b.status,
        "started_at": b.started_at.isoformat() if b.started_at else None,
        "completed_at": b.completed_at.isoformat() if b.completed_at else None,
        "created_at": b.created_at.isoformat() if b.created_at else None,
    } for b in batches])


@router.post("/craftsman/production-batches", response_model=ApiResponse[dict], dependencies=[Depends(require_auth)])
def create_production_batch(payload: ProductionBatchCreate, db: Session = Depends(get_db)):
    """创建生产批次."""
    batch = ProductionBatch(
        user_id="local",
        work_id=payload.work_id,
        title=payload.title,
        planned_quantity=payload.planned_quantity,
    )
    try:
        db.add(batch)
        db.commit()
        db.refresh(batch)
    except Exception:
        db.rollback()
        raise
    return ApiResponse(data={"id": batch.id}, message="生产批次已创建")


@router.patch("/craftsman/production-batches/{batch_id}", response_model=ApiResponse[dict], dependencies=[Depends(require_auth)])
def update_production_batch(batch_id: str, payload: ProductionBatchUpdate, db: Session = Depends(get_db)):
    """更新生产批次."""
    batch = db.query(ProductionBatch).filter(ProductionBatch.id == batch_id).first()
    if not batch:
        raise HTTPException(status_code=404, detail="生产批次不存在")
    update_data = payload.model_dump(exclude_unset=True)
    # Auto-set started_at/completed_at based on status transitions
    new_status = update_data.get("status")
    if new_status == "in_production" and not batch.started_at:
        from datetime import datetime as _dt
        update_data["started_at"] = _dt.utcnow()
    if new_status == "done" and batch.started_at and not batch.completed_at:
        from datetime import datetime as _dt
        update_data["completed_at"] = _dt.utcnow()
    for key, value in update_data.items():
        setattr(batch, key, value)
    try:
        db.commit()
        db.refresh(batch)
    except Exception:
        db.rollback()
        raise
    return ApiResponse(data={
        "id": batch.id,
        "title": batch.title,
        "status": batch.status,
        "planned_quantity": batch.planned_quantity,
        "produced_quantity": batch.produced_quantity,
        "sold_quantity": batch.sold_quantity,
    }, message="生产批次已更新")


@router.delete("/craftsman/production-batches/{batch_id}", response_model=ApiResponse, dependencies=[Depends(require_auth)])
def delete_production_batch(batch_id: str, db: Session = Depends(get_db)):
    """删除生产批次."""
    batch = db.query(ProductionBatch).filter(ProductionBatch.id == batch_id).first()
    if not batch:
        raise HTTPException(status_code=404, detail="生产批次不存在")
    try:
        db.delete(batch)
        db.commit()
    except Exception:
        db.rollback()
        raise
    return ApiResponse(message="生产批次已删除")


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
