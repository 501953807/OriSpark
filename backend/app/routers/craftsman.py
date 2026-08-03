"""手工艺人 API 路由 — Phase 4 Task 1.

端点: 11 (craftsman)

所有 DB 操作已提取至 craftsman_manager_service.py.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import require_auth
from app.schemas.common import ApiResponse
from app.services.craftsman_manager_service import CraftsmanManagerService

router = APIRouter()


class CreateCraftProductPayload(BaseModel):
    work_variant_id: str = None
    material: str = None
    dimensions: str = None
    craft_type: str = None
    moq: int = 1
    unit_price: float = None
    production_time_days: int = None


class UpdateCraftProductPayload(BaseModel):
    work_variant_id: str = None
    material: str = None
    dimensions: str = None
    craft_type: str = None
    moq: int = None
    unit_price: float = None
    production_time_days: int = None


class CreateFactoryPayload(BaseModel):
    name: str
    location: str = None
    contact: str = None
    rating: float = None
    capabilities: list = None


class UpdateFactoryPayload(BaseModel):
    name: str = None
    location: str = None
    contact: str = None
    rating: float = None
    capabilities: list = None


class CreateRFQPayload(BaseModel):
    craft_product_id: str = None
    title: str
    description: str = None
    quantity_needed: int = None
    material_specs: str = None
    target_price: float = None
    status: str = "open"
    quoted_factories: list = None
    created_by: str = None


class UpdateRFQPayload(BaseModel):
    status: str = None
    quoted_factories: list = None
    quantity_needed: int = None
    target_price: float = None


# ===========================================================================
# CraftProducts CRUD
# ===========================================================================


@router.get("/craftsman/products", response_model=ApiResponse[list])
def list_craft_products(
    craft_type: str = None,
    work_variant_id: str = None,
    db: Session = Depends(get_db),
):
    """获取手工艺品列表."""
    svc = CraftsmanManagerService(db)
    return ApiResponse(data=svc.list_craft_products(craft_type, work_variant_id))


@router.post("/craftsman/products", response_model=ApiResponse[dict], dependencies=[Depends(require_auth)])
def create_craft_product(payload: CreateCraftProductPayload, db: Session = Depends(get_db)):
    """创建手工艺品."""
    svc = CraftsmanManagerService(db)
    result = svc.create_craft_product(
        payload.work_variant_id, payload.material, payload.dimensions,
        payload.craft_type, payload.moq, payload.unit_price,
        payload.production_time_days,
    )
    return ApiResponse(data=result, message="手工艺品创建成功")


@router.get("/craftsman/products/{product_id}", response_model=ApiResponse[dict])
def get_craft_product(product_id: str, db: Session = Depends(get_db)):
    """获取手工艺品详情."""
    svc = CraftsmanManagerService(db)
    return ApiResponse(data=svc.get_craft_product(product_id))


@router.patch("/craftsman/products/{product_id}", response_model=ApiResponse[dict], dependencies=[Depends(require_auth)])
def update_craft_product(product_id: str, payload: UpdateCraftProductPayload, db: Session = Depends(get_db)):
    """更新手工艺品."""
    svc = CraftsmanManagerService(db)
    result = svc.update_craft_product(product_id, payload.model_dump(exclude_unset=True))
    return ApiResponse(data=result, message="手工艺品更新成功")


@router.delete("/craftsman/products/{product_id}", response_model=ApiResponse[dict], dependencies=[Depends(require_auth)])
def delete_craft_product(product_id: str, db: Session = Depends(get_db)):
    """删除手工艺品."""
    svc = CraftsmanManagerService(db)
    svc.delete_craft_product(product_id)
    return ApiResponse(message="手工艺品已删除")


# ===========================================================================
# Factories CRUD
# ===========================================================================


@router.get("/craftsman/factories", response_model=ApiResponse[list])
def list_factories(
    rating_min: float = None,
    db: Session = Depends(get_db),
):
    """获取工厂列表."""
    svc = CraftsmanManagerService(db)
    return ApiResponse(data=svc.list_factories(rating_min))


@router.post("/craftsman/factories", response_model=ApiResponse[dict], dependencies=[Depends(require_auth)])
def create_factory(payload: CreateFactoryPayload, db: Session = Depends(get_db)):
    """添加工厂."""
    svc = CraftsmanManagerService(db)
    result = svc.create_factory(
        payload.name, payload.location, payload.contact,
        payload.rating, payload.capabilities,
    )
    return ApiResponse(data=result, message="工厂添加成功")


@router.delete("/craftsman/factories/{factory_id}", response_model=ApiResponse, dependencies=[Depends(require_auth)])
def delete_factory(factory_id: str, db: Session = Depends(get_db)):
    """删除工厂."""
    svc = CraftsmanManagerService(db)
    svc.delete_factory(factory_id)
    return ApiResponse(message="工厂已删除")


@router.patch("/craftsman/factories/{factory_id}", response_model=ApiResponse[dict], dependencies=[Depends(require_auth)])
def update_factory(factory_id: str, payload: UpdateFactoryPayload, db: Session = Depends(get_db)):
    """更新工厂信息."""
    svc = CraftsmanManagerService(db)
    result = svc.update_factory(factory_id, payload.model_dump(exclude_unset=True))
    return ApiResponse(data=result, message="工厂更新成功")


@router.delete("/craftsman/rfqs/{rfq_id}", response_model=ApiResponse, dependencies=[Depends(require_auth)])
def delete_rfq(rfq_id: str, db: Session = Depends(get_db)):
    """删除询价单."""
    svc = CraftsmanManagerService(db)
    svc.delete_rfq(rfq_id)
    return ApiResponse(message="询价单已删除")


# ===========================================================================
# RFQs CRUD
# ===========================================================================


@router.get("/craftsman/rfqs", response_model=ApiResponse[list])
def list_rfqs(
    status: str = None,
    created_by: str = None,
    db: Session = Depends(get_db),
):
    """获取询价单列表."""
    svc = CraftsmanManagerService(db)
    return ApiResponse(data=svc.list_rfqs(status, created_by))


@router.post("/craftsman/rfqs", response_model=ApiResponse[dict], dependencies=[Depends(require_auth)])
def create_rfq(payload: CreateRFQPayload, db: Session = Depends(get_db)):
    """创建询价单."""
    svc = CraftsmanManagerService(db)
    result = svc.create_rfq(
        payload.craft_product_id, payload.title, payload.description,
        payload.quantity_needed, payload.material_specs, payload.target_price,
        payload.status, payload.quoted_factories, payload.created_by,
    )
    return ApiResponse(data=result, message="询价单创建成功")


@router.patch("/craftsman/rfqs/{rfq_id}", response_model=ApiResponse[dict], dependencies=[Depends(require_auth)])
def update_rfq(rfq_id: str, payload: UpdateRFQPayload, db: Session = Depends(get_db)):
    """更新询价单状态."""
    svc = CraftsmanManagerService(db)
    result = svc.update_rfq(rfq_id, payload.model_dump(exclude_unset=True))
    return ApiResponse(data=result, message="询价单更新成功")


# ===========================================================================
# v2: Physical Product (15.3.1)
# ===========================================================================


class PhysicalProductCreate(BaseModel):
    work_id: str = None
    title: str = Field(..., min_length=1, max_length=500)
    description: str = None
    category: str = Field(None, max_length=50)
    dimensions: dict = None
    weight_g: int = None
    price: float = Field(..., gt=0)
    currency: str = Field("CNY", max_length=10)
    stock_quantity: int = Field(1, ge=0)
    shipping_regions: list = None


class PhysicalProductUpdate(BaseModel):
    title: str = None
    description: str = None
    category: str = None
    dimensions: dict = None
    weight_g: int = None
    price: float = None
    currency: str = None
    stock_quantity: int = None
    shipping_regions: list = None
    is_active: bool = None


@router.get("/craftsman/physical-products", response_model=ApiResponse[list])
def list_physical_products(
    category: str = None,
    db: Session = Depends(get_db),
):
    """获取物理产品列表."""
    svc = CraftsmanManagerService(db)
    return ApiResponse(data=svc.list_physical_products(category))


@router.post("/craftsman/physical-products", response_model=ApiResponse[dict], dependencies=[Depends(require_auth)])
def create_physical_product(payload: PhysicalProductCreate, db: Session = Depends(get_db)):
    """创建物理产品."""
    svc = CraftsmanManagerService(db)
    result = svc.create_physical_product(
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
    return ApiResponse(data=result, message="物理产品创建成功")


@router.patch("/craftsman/physical-products/{product_id}", response_model=ApiResponse[dict], dependencies=[Depends(require_auth)])
def update_physical_product(product_id: str, payload: PhysicalProductUpdate, db: Session = Depends(get_db)):
    """更新物理产品."""
    svc = CraftsmanManagerService(db)
    svc.update_physical_product(product_id, payload.model_dump(exclude_unset=True))
    return ApiResponse(data={"id": product_id}, message="物理产品已更新")


@router.delete("/craftsman/physical-products/{product_id}", response_model=ApiResponse, dependencies=[Depends(require_auth)])
def delete_physical_product(product_id: str, db: Session = Depends(get_db)):
    """删除物理产品."""
    svc = CraftsmanManagerService(db)
    svc.delete_physical_product(product_id)
    return ApiResponse(message="物理产品已删除")


# ===========================================================================
# v2: Material Inventory (15.3.2)
# ===========================================================================


class MaterialInventoryCreate(BaseModel):
    material_name: str = Field(..., min_length=1, max_length=200)
    material_category: str = Field(None, max_length=50)
    unit: str = Field(..., min_length=1, max_length=20)
    quantity_on_hand: float = Field(0.0, ge=0)
    quantity_reserved: float = Field(0.0, ge=0)
    reorder_level: float = None
    unit_cost: float = None
    location: str = Field(None, max_length=200)


class MaterialInventoryUpdate(BaseModel):
    material_name: str = None
    material_category: str = None
    unit: str = None
    quantity_on_hand: float = None
    quantity_reserved: float = None
    reorder_level: float = None
    unit_cost: float = None
    location: str = None


class MaterialTransactionCreate(BaseModel):
    material_id: str = Field(..., min_length=1)
    transaction_type: str = Field(..., pattern="^(purchase|consume|scrap)$")
    quantity: float = Field(..., gt=0)
    reference_type: str = None
    reference_id: str = None
    notes: str = None


@router.get("/craftsman/materials", response_model=ApiResponse[list])
def list_materials(db: Session = Depends(get_db)):
    """获取原料库存列表."""
    svc = CraftsmanManagerService(db)
    return ApiResponse(data=svc.list_materials())


@router.post("/craftsman/materials", response_model=ApiResponse[dict], dependencies=[Depends(require_auth)])
def create_material(payload: MaterialInventoryCreate, db: Session = Depends(get_db)):
    """添加原料库存."""
    svc = CraftsmanManagerService(db)
    result = svc.create_material(
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
    return ApiResponse(data=result, message="原料已添加")


@router.patch("/craftsman/materials/{material_id}", response_model=ApiResponse[dict], dependencies=[Depends(require_auth)])
def update_material(material_id: str, payload: MaterialInventoryUpdate, db: Session = Depends(get_db)):
    """更新原料库存."""
    svc = CraftsmanManagerService(db)
    svc.update_material(material_id, payload.model_dump(exclude_unset=True))
    return ApiResponse(data={"id": material_id}, message="原料已更新")


@router.delete("/craftsman/materials/{material_id}", response_model=ApiResponse, dependencies=[Depends(require_auth)])
def delete_material(material_id: str, db: Session = Depends(get_db)):
    """删除原料库存."""
    svc = CraftsmanManagerService(db)
    svc.delete_material(material_id)
    return ApiResponse(message="原料已删除")


@router.post("/craftsman/material-transactions", response_model=ApiResponse[dict], dependencies=[Depends(require_auth)])
def create_material_transaction(payload: MaterialTransactionCreate, db: Session = Depends(get_db)):
    """记录材料出入库流水."""
    svc = CraftsmanManagerService(db)
    result = svc.create_material_transaction(
        payload.material_id, payload.transaction_type, payload.quantity,
        payload.reference_type, payload.reference_id, payload.notes,
    )
    return ApiResponse(data=result, message=f"材料{payload.transaction_type}记录成功")


@router.get("/craftsman/material-transactions", response_model=ApiResponse[list])
def list_material_transactions(
    material_id: str = None,
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    """获取材料流水记录."""
    svc = CraftsmanManagerService(db)
    return ApiResponse(data=svc.list_material_transactions(material_id, limit))


# ===========================================================================
# v2: Production Batch (15.3.3)
# ===========================================================================


class ProductionBatchCreate(BaseModel):
    work_id: str = None
    title: str = Field(..., min_length=1, max_length=500)
    planned_quantity: int = Field(..., ge=1)


class ProductionBatchUpdate(BaseModel):
    title: str = None
    planned_quantity: int = None
    produced_quantity: int = None
    sold_quantity: int = None
    status: str = Field(None, pattern="^(planned|in_production|done|shipped)$")
    started_at: str = None
    completed_at: str = None


@router.get("/craftsman/production-batches", response_model=ApiResponse[list])
def list_production_batches(
    status: str = None,
    db: Session = Depends(get_db),
):
    """获取生产批次列表."""
    svc = CraftsmanManagerService(db)
    return ApiResponse(data=svc.list_production_batches(status))


@router.post("/craftsman/production-batches", response_model=ApiResponse[dict], dependencies=[Depends(require_auth)])
def create_production_batch(payload: ProductionBatchCreate, db: Session = Depends(get_db)):
    """创建生产批次."""
    svc = CraftsmanManagerService(db)
    result = svc.create_production_batch(
        user_id="local",
        work_id=payload.work_id,
        title=payload.title,
        planned_quantity=payload.planned_quantity,
    )
    return ApiResponse(data=result, message="生产批次已创建")


@router.patch("/craftsman/production-batches/{batch_id}", response_model=ApiResponse[dict], dependencies=[Depends(require_auth)])
def update_production_batch(batch_id: str, payload: ProductionBatchUpdate, db: Session = Depends(get_db)):
    """更新生产批次."""
    svc = CraftsmanManagerService(db)
    result = svc.update_production_batch(batch_id, payload.model_dump(exclude_unset=True))
    return ApiResponse(data=result, message="生产批次已更新")


@router.delete("/craftsman/production-batches/{batch_id}", response_model=ApiResponse, dependencies=[Depends(require_auth)])
def delete_production_batch(batch_id: str, db: Session = Depends(get_db)):
    """删除生产批次."""
    svc = CraftsmanManagerService(db)
    svc.delete_production_batch(batch_id)
    return ApiResponse(message="生产批次已删除")


# ===========================================================================
# Orders (placeholder — aggregates factory quotes)
# ===========================================================================

@router.get("/craftsman/orders", response_model=ApiResponse[list])
def list_craft_orders(db: Session = Depends(get_db)):
    """获取订单列表 — 基于 RFQ 报价聚合."""
    svc = CraftsmanManagerService(db)
    return ApiResponse(data=svc.list_craft_orders())
