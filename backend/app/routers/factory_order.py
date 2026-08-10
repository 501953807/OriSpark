"""工厂订单 API 路由 — v6.0 运营者视角生产订单管理.

端点:
  POST   /operator/supply/factories        工厂入驻申请
  GET    /operator/supply/factories        工厂列表
  GET    /operator/supply/factories/{id}   工厂详情
  POST   /operator/supply/orders           创建生产订单
  GET    /operator/supply/orders           我的生产订单
  POST   /operator/supply/orders/{id}/confirm  确认订单
  POST   /operator/supply/orders/{id}/start    开始生产
  POST   /operator/supply/orders/{id}/ship     标记发货
  POST   /operator/supply/orders/{id}/inspect    质检确认
  POST   /operator/supply/pod/configs     POD平台配置
  GET    /operator/supply/pod/configs     POD配置列表
"""

from datetime import date, datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.factory_order import FactoryOrder, FactoryQualification, PODConfig
from app.models.supply import Partner, PartnerQualification
from app.models.system import User as UserModel
from app.deps import require_operator
from app.utils.audit import AuditLog

router = APIRouter(prefix="/operator/supply", tags=["factory-supply"])


class FactoryCreate(BaseModel):
    name: str
    location: Optional[str] = None
    contact: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    categories: Optional[list[str]] = None
    product_categories: Optional[list[str]] = None
    material_capabilities: Optional[list[str]] = None
    moq: Optional[int] = None
    typical_lead_time_days: Optional[int] = None
    notes: Optional[str] = None


class FactoryOrderCreate(BaseModel):
    contract_id: Optional[str] = None
    work_id: Optional[str] = None
    factory_id: Optional[str] = None
    product_name: str
    product_category: Optional[str] = None
    quantity: int = 1
    unit_price: float = 0.0
    scope_regions: Optional[list[str]] = None
    scope_channels: Optional[list[str]] = None
    scope_products: Optional[list[str]] = None
    expected_date: Optional[date] = None
    notes: Optional[str] = None


class QualityInspect(BaseModel):
    passed: bool
    notes: Optional[str] = None
    defect_details: Optional[dict] = None


class PODConfigCreate(BaseModel):
    platform: str
    api_key: str
    api_secret: Optional[str] = None
    default_store_id: Optional[str] = None
    settings: Optional[dict] = None


def _gen_order_number() -> str:
    import uuid
    return f"FO-{datetime.now(timezone.utc).strftime('%Y%m%d')}-{uuid.uuid4().hex[:8].upper()}"


# ── 工厂管理 ────────────────────────────────────────────────────────────────


@router.post("/factories", response_model=dict)
def create_factory(
    payload: FactoryCreate,
    db: Session = Depends(get_db),
    operator: UserModel = Depends(require_operator),
):
    """运营者提交工厂入驻申请."""
    factory = Partner(
        name=payload.name,
        company_name=payload.name,
        type="manufacturer",
        contact_person=payload.contact,
        phone=payload.phone,
        email=payload.email,
        address=payload.location,
        categories=payload.categories or [],
        product_categories=payload.product_categories or [],
        material_capabilities=payload.material_capabilities or [],
        moq=payload.moq,
        typical_lead_time_days=payload.typical_lead_time_days,
        status="active",
        notes=payload.notes,
    )
    db.add(factory)
    db.commit()
    db.refresh(factory)
    AuditLog.log(db, "create_factory", f"Operator {operator.id} registered factory {factory.id}", operator.id)
    return {
        "id": factory.id, "name": factory.name, "status": factory.status,
        "created_at": factory.created_at.isoformat() if factory.created_at else None,
    }


@router.get("/factories", response_model=list[dict])
def list_factories(
    category: Optional[str] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    operator: UserModel = Depends(require_operator),
):
    """运营者查看工厂列表."""
    q = db.query(Partner).filter(Partner.type == "manufacturer")
    if status:
        q = q.filter(Partner.status == status)
    if category:
        q = q.filter(Partner.categories.contains([category]))
    factories = q.order_by(Partner.created_at.desc()).all()
    return [
        {
            "id": f.id, "name": f.name, "location": f.address,
            "contact": f.contact_person, "phone": f.phone, "email": f.email,
            "categories": f.categories or [], "product_categories": f.product_categories or [],
            "moq": f.moq, "rating": f.rating,
            "typical_lead_time_days": f.typical_lead_time_days,
            "status": f.status,
            "created_at": f.created_at.isoformat() if f.created_at else None,
        }
        for f in factories
    ]


@router.get("/factories/{factory_id}", response_model=dict)
def get_factory(
    factory_id: str,
    db: Session = Depends(get_db),
    operator: UserModel = Depends(require_operator),
):
    """工厂详情."""
    factory = (
        db.query(Partner)
        .filter(Partner.id == factory_id, Partner.type == "manufacturer")
        .first()
    )
    if not factory:
        raise HTTPException(404, "工厂不存在")
    quals = (
        db.query(PartnerQualification)
        .filter(PartnerQualification.partner_id == factory_id)
        .all()
    )
    return {
        "id": factory.id, "name": factory.name, "location": factory.address,
        "contact": factory.contact_person, "phone": factory.phone, "email": factory.email,
        "categories": factory.categories or [],
        "product_categories": factory.product_categories or [],
        "material_capabilities": factory.material_capabilities or [],
        "moq": factory.moq, "rating": factory.rating,
        "typical_lead_time_days": factory.typical_lead_time_days,
        "status": factory.status, "notes": factory.notes,
        "qualifications": [
            {
                "type": q.qual_type, "verified": q.verified,
                "expire_date": q.expire_date.isoformat() if q.expire_date else None,
            }
            for q in quals
        ],
        "created_at": factory.created_at.isoformat() if factory.created_at else None,
    }


# ── 生产订单 ────────────────────────────────────────────────────────────────


@router.post("/orders", response_model=dict)
def create_order(
    payload: FactoryOrderCreate,
    db: Session = Depends(get_db),
    operator: UserModel = Depends(require_operator),
):
    """创建生产订单."""
    if not payload.product_name.strip():
        raise HTTPException(400, "产品名称不能为空")
    total_amount = payload.unit_price * payload.quantity
    order = FactoryOrder(
        order_number=_gen_order_number(),
        contract_id=payload.contract_id,
        work_id=payload.work_id,
        operator_id=operator.id,
        factory_id=payload.factory_id,
        product_name=payload.product_name,
        product_category=payload.product_category,
        quantity=payload.quantity,
        unit_price=payload.unit_price,
        total_amount=total_amount,
        scope_regions=payload.scope_regions,
        scope_channels=payload.scope_channels,
        scope_products=payload.scope_products,
        expected_date=payload.expected_date,
        notes=payload.notes,
        status="draft",
    )
    db.add(order)
    db.commit()
    db.refresh(order)
    AuditLog.log(db, "create_factory_order", f"Operator {operator.id} created order {order.id}", operator.id)
    return {
        "id": order.id, "order_number": order.order_number,
        "status": order.status, "total_amount": order.total_amount,
        "created_at": order.created_at.isoformat() if order.created_at else None,
    }


@router.get("/orders", response_model=list[dict])
def list_orders(
    status: Optional[str] = None,
    factory_id: Optional[str] = None,
    db: Session = Depends(get_db),
    operator: UserModel = Depends(require_operator),
):
    """运营者查看我的生产订单."""
    q = db.query(FactoryOrder).filter(FactoryOrder.operator_id == operator.id)
    if status:
        q = q.filter(FactoryOrder.status == status)
    if factory_id:
        q = q.filter(FactoryOrder.factory_id == factory_id)
    orders = q.order_by(FactoryOrder.created_at.desc()).all()
    return [
        {
            "id": o.id, "order_number": o.order_number,
            "contract_id": o.contract_id, "work_id": o.work_id,
            "factory_id": o.factory_id,
            "product_name": o.product_name, "product_category": o.product_category,
            "quantity": o.quantity, "unit_price": o.unit_price, "total_amount": o.total_amount,
            "status": o.status,
            "expected_date": o.expected_date.isoformat() if o.expected_date else None,
            "notes": o.notes,
            "created_at": o.created_at.isoformat() if o.created_at else None,
            "updated_at": o.updated_at.isoformat() if o.updated_at else None,
        }
        for o in orders
    ]


@router.post("/orders/{order_id}/confirm", response_model=dict)
def confirm_order(
    order_id: str,
    db: Session = Depends(get_db),
    operator: UserModel = Depends(require_operator),
):
    """确认生产订单（draft → confirmed）."""
    order = (
        db.query(FactoryOrder)
        .filter(FactoryOrder.id == order_id, FactoryOrder.operator_id == operator.id)
        .first()
    )
    if not order:
        raise HTTPException(404, "订单不存在")
    if order.status != "draft":
        raise HTTPException(400, f"订单状态为 {order.status}，无法确认")
    order.status = "confirmed"
    db.commit()
    AuditLog.log(db, "confirm_factory_order", f"Operator {operator.id} confirmed order {order_id}", operator.id)
    return {"id": order.id, "status": order.status}


@router.post("/orders/{order_id}/start", response_model=dict)
def start_production(
    order_id: str,
    db: Session = Depends(get_db),
    operator: UserModel = Depends(require_operator),
):
    """开始生产（confirmed → in_production）."""
    order = (
        db.query(FactoryOrder)
        .filter(FactoryOrder.id == order_id, FactoryOrder.operator_id == operator.id)
        .first()
    )
    if not order:
        raise HTTPException(404, "订单不存在")
    if order.status != "confirmed":
        raise HTTPException(400, f"订单状态为 {order.status}，无法开始生产")
    order.status = "in_production"
    db.commit()
    return {"id": order.id, "status": order.status}


@router.post("/orders/{order_id}/ship", response_model=dict)
def ship_order(
    order_id: str,
    shipping_method: Optional[str] = None,
    tracking_number: Optional[str] = None,
    db: Session = Depends(get_db),
    operator: UserModel = Depends(require_operator),
):
    """标记发货."""
    order = (
        db.query(FactoryOrder)
        .filter(FactoryOrder.id == order_id, FactoryOrder.operator_id == operator.id)
        .first()
    )
    if not order:
        raise HTTPException(404, "订单不存在")
    if order.status not in ("in_production", "quality_check"):
        raise HTTPException(400, f"订单状态为 {order.status}，无法发货")
    order.status = "shipped"
    order.shipping_method = shipping_method
    order.tracking_number = tracking_number
    order.actual_ship_date = date.today()
    db.commit()
    return {"id": order.id, "status": order.status, "shipping_method": shipping_method, "tracking_number": tracking_number}


@router.post("/orders/{order_id}/inspect", response_model=dict)
def inspect_order(
    order_id: str,
    payload: QualityInspect,
    db: Session = Depends(get_db),
    operator: UserModel = Depends(require_operator),
):
    """质检确认."""
    order = (
        db.query(FactoryOrder)
        .filter(FactoryOrder.id == order_id, FactoryOrder.operator_id == operator.id)
        .first()
    )
    if not order:
        raise HTTPException(404, "订单不存在")
    if order.status not in ("in_production", "quality_check", "shipped"):
        raise HTTPException(400, f"订单状态为 {order.status}，无法质检")
    order.quality_passed = payload.passed
    order.quality_notes = payload.notes
    if payload.passed:
        order.status = "completed"
        order.actual_deliver_date = date.today()
    else:
        order.status = "quality_check"
    db.commit()
    AuditLog.log(db, "inspect_factory_order", f"Operator {operator.id} inspected order {order_id}: {'pass' if payload.passed else 'fail'}", operator.id)
    return {
        "id": order.id, "status": order.status,
        "quality_passed": order.quality_passed, "quality_notes": order.quality_notes,
    }


# ── POD 平台配置 ─────────────────────────────────────────────────────────────


@router.post("/pod/configs", response_model=dict)
def create_pod_config(
    payload: PODConfigCreate,
    db: Session = Depends(get_db),
    operator: UserModel = Depends(require_operator),
):
    """配置 POD 平台对接."""
    existing = (
        db.query(PODConfig)
        .filter(PODConfig.platform == payload.platform, PODConfig.operator_id == operator.id)
        .first()
    )
    if existing:
        raise HTTPException(400, f"平台 {payload.platform} 已有配置")
    config = PODConfig(
        platform=payload.platform,
        operator_id=operator.id,
        api_key_encrypted=payload.api_key,
        api_secret_encrypted=payload.api_secret,
        default_store_id=payload.default_store_id,
        settings=payload.settings,
    )
    db.add(config)
    db.commit()
    db.refresh(config)
    return {
        "id": config.id, "platform": config.platform,
        "is_active": config.is_active,
        "created_at": config.created_at.isoformat() if config.created_at else None,
    }


@router.get("/pod/configs", response_model=list[dict])
def list_pod_configs(
    db: Session = Depends(get_db),
    operator: UserModel = Depends(require_operator),
):
    """查看 POD 平台配置列表（脱敏）."""
    configs = (
        db.query(PODConfig)
        .filter(PODConfig.operator_id == operator.id)
        .order_by(PODConfig.created_at.desc())
        .all()
    )
    return [
        {
            "id": c.id, "platform": c.platform,
            "is_active": c.is_active, "default_store_id": c.default_store_id,
            "created_at": c.created_at.isoformat() if c.created_at else None,
            "updated_at": c.updated_at.isoformat() if c.updated_at else None,
        }
        for c in configs
    ]
