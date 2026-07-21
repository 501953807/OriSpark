"""Etsy 平台集成 API 路由 — v3b (15.3.4-15.3.6).

端点: 8
Features:
  - EtsyShop CRUD + OAuth connect
  - EtsyListing CRUD + sync
  - EtsyOrder list
"""

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.etsy import EtsyListing, EtsyOrder, EtsyShop
from app.schemas.common import ApiResponse
from app.deps import require_auth
from app.services.etsy_service import EtsyService

router = APIRouter()


class EtsyConnectPayload(BaseModel):
    authorization_code: str
    shop_id: Optional[str] = None
    shop_name: Optional[str] = None


class EtsyListingCreate(BaseModel):
    title: str
    description: Optional[str] = None
    price: float
    currency: str = "USD"
    quantity: int = 1
    tags: Optional[list[str]] = None
    materials: Optional[list[str]] = None
    variations: Optional[list[dict]] = None
    status: str = "draft"
    product_id: Optional[str] = None
    etsy_listing_id: Optional[str] = None
    shipping_cost: Optional[float] = None
    free_shipping: bool = False


class EtsyListingUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    quantity: Optional[int] = None
    tags: Optional[list[str]] = None
    materials: Optional[list[str]] = None
    status: Optional[str] = None
    etsy_status: Optional[str] = None


# ============================================================================
# Etsy Shop
# ============================================================================


@router.post("/etsy/connect", response_model=ApiResponse[dict], dependencies=[Depends(require_auth)])
def connect_etsy_shop(payload: EtsyConnectPayload, db: Session = Depends(get_db)):
    """连接 Etsy 店铺."""
    svc = EtsyService(db)
    result = svc.connect_shop(user_id="local", authorization_code=payload.authorization_code)
    return ApiResponse(data=result, message="Etsy 店铺已连接")


@router.get("/etsy/shops", response_model=ApiResponse[list])
def list_etsy_shops(db: Session = Depends(get_db)):
    """获取已连接的 Etsy 店铺列表."""
    shops = db.query(EtsyShop).filter(EtsyShop.is_active == True).all()
    return ApiResponse(data=[{
        "id": s.id,
        "shop_name": s.shop_name,
        "shop_id": s.shop_id,
        "is_active": s.is_active,
        "created_at": s.created_at.isoformat() if s.created_at else None,
    } for s in shops])


@router.delete("/etsy/shops/{shop_id}", response_model=ApiResponse, dependencies=[Depends(require_auth)])
def disconnect_etsy_shop(shop_id: str, db: Session = Depends(get_db)):
    """断开 Etsy 店铺连接."""
    shop = db.query(EtsyShop).filter(EtsyShop.id == shop_id).first()
    if not shop:
        raise HTTPException(status_code=404, detail="店铺未找到")
    shop.is_active = False
    db.commit()
    return ApiResponse(message="店铺已断开")


# ============================================================================
# Etsy Listings
# ============================================================================


@router.get("/etsy/listings", response_model=ApiResponse[list])
def list_etsy_listings(
    status: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """获取 Etsy 商品列表."""
    q = db.query(EtsyListing)
    if status:
        q = q.filter(EtsyListing.status == status)
    total = q.count()
    items = q.order_by(EtsyListing.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return ApiResponse(data=[{
        "id": l.id,
        "title": l.title,
        "price": l.price,
        "currency": l.currency,
        "quantity": l.quantity,
        "status": l.status,
        "etsy_status": l.etsy_status,
        "views_count": l.views_count,
        "sales_count": l.sales_count,
        "revenue": l.revenue,
        "created_at": l.created_at.isoformat() if l.created_at else None,
    } for l in items], meta={"total": total, "page": page, "page_size": page_size})


@router.post("/etsy/listings", response_model=ApiResponse[dict], dependencies=[Depends(require_auth)])
def create_etsy_listing(payload: EtsyListingCreate, db: Session = Depends(get_db)):
    """发布 Etsy 商品."""
    listing = EtsyListing(
        user_id="local",
        title=payload.title,
        description=payload.description,
        price=payload.price,
        currency=payload.currency,
        quantity=payload.quantity,
        tags=payload.tags,
        materials=payload.materials,
        variations=payload.variations,
        status=payload.status,
        product_id=payload.product_id,
        shipping_cost=payload.shipping_cost,
        free_shipping=payload.free_shipping,
    )
    try:
        db.add(listing)
        db.commit()
        db.refresh(listing)
    except Exception:
        db.rollback()
        raise
    return ApiResponse(data={"id": listing.id}, message="Etsy 商品已创建")


@router.patch("/etsy/listings/{listing_id}", response_model=ApiResponse[dict], dependencies=[Depends(require_auth)])
def update_etsy_listing(listing_id: str, payload: EtsyListingUpdate, db: Session = Depends(get_db)):
    """更新 Etsy 商品."""
    listing = db.query(EtsyListing).filter(EtsyListing.id == listing_id).first()
    if not listing:
        raise HTTPException(status_code=404, detail="商品不存在")
    update_data = payload.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(listing, key, value)
    try:
        db.commit()
        db.refresh(listing)
    except Exception:
        db.rollback()
        raise
    return ApiResponse(data={"id": listing.id}, message="商品已更新")


@router.delete("/etsy/listings/{listing_id}", response_model=ApiResponse, dependencies=[Depends(require_auth)])
def delete_etsy_listing(listing_id: str, db: Session = Depends(get_db)):
    """删除 Etsy 商品."""
    listing = db.query(EtsyListing).filter(EtsyListing.id == listing_id).first()
    if not listing:
        raise HTTPException(status_code=404, detail="商品不存在")
    try:
        db.delete(listing)
        db.commit()
    except Exception:
        db.rollback()
        raise
    return ApiResponse(message="商品已删除")


# ============================================================================
# Etsy Orders
# ============================================================================


@router.get("/etsy/orders", response_model=ApiResponse[list])
def list_etsy_orders(
    status: Optional[str] = Query(None),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """获取 Etsy 订单列表."""
    q = db.query(EtsyOrder)
    if status:
        q = q.filter(EtsyOrder.status == status)
    orders = q.order_by(EtsyOrder.order_date.desc()).limit(limit).all()
    return ApiResponse(data=[{
        "id": o.id,
        "etsy_order_id": o.etsy_order_id,
        "buyer_name": o.buyer_name,
        "order_total": o.order_total,
        "shipping_cost": o.shipping_cost,
        "status": o.status,
        "order_date": o.order_date.isoformat() if o.order_date else None,
        "tracking_number": o.tracking_number,
    } for o in orders])
