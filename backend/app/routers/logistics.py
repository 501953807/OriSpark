"""物流商路由."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.logistics import LogisticsProvider, LogisticsShipment, LogisticsTrackingEvent
from app.services.logistics_service import LogisticsService

router = APIRouter(prefix="/logistics", tags=["logistics"])


@router.post("/providers")
def post_create_provider(
    body: dict,
    db: Session = Depends(get_db),
):
    """创建物流商."""
    try:
        provider = LogisticsService.create_provider(
            db=db,
            name=body["name"],
            contact_email=body.get("contact_email"),
            contact_phone=body.get("contact_phone"),
            description=body.get("description"),
        )
        return {"id": provider.id, "status": "created"}
    except Exception as e:
        raise HTTPException(500, detail=str(e))


@router.get("/providers")
def get_providers(
    status: str | None = None,
    limit: int = Query(default=20, le=100),
    offset: int = 0,
    db: Session = Depends(get_db),
):
    """获取物流商列表."""
    providers = LogisticsService.get_providers(db, status, limit, offset)
    return [p.to_dict() for p in providers]


@router.get("/providers/{provider_id}")
def get_provider(provider_id: str, db: Session = Depends(get_db)):
    """获取物流商详情."""
    provider = LogisticsService.get_provider(db, provider_id)
    if not provider:
        raise HTTPException(404, "物流商不存在")
    return provider.to_dict()


@router.patch("/providers/{provider_id}")
def patch_update_provider(
    provider_id: str,
    body: dict,
    db: Session = Depends(get_db),
):
    """更新物流商信息."""
    try:
        provider = LogisticsService.update_provider(db, provider_id, **body)
        return {"id": provider.id, "status": "updated"}
    except ValueError as e:
        raise HTTPException(400, detail=str(e))


@router.post("/shipments")
def post_create_shipment(
    body: dict,
    db: Session = Depends(get_db),
):
    """创建发货记录."""
    try:
        shipment = LogisticsService.create_shipment(
            db=db,
            contract_id=body["contract_id"],
            provider_id=body["provider_id"],
            tracking_number=body.get("tracking_number"),
            recipient_name=body.get("recipient_name"),
            recipient_address=body.get("recipient_address"),
            sender_name=body.get("sender_name"),
            sender_address=body.get("sender_address"),
            shipping_cost=body.get("shipping_cost"),
            currency=body.get("currency", "CNY"),
            notes=body.get("notes"),
        )
        return {"id": shipment.id, "status": "created"}
    except ValueError as e:
        raise HTTPException(400, detail=str(e))


@router.get("/shipments")
def get_shipments(
    contract_id: str,
    limit: int = Query(default=20, le=100),
    offset: int = 0,
    db: Session = Depends(get_db),
):
    """获取合约的物流发货记录."""
    shipments = LogisticsService.get_shipments_by_contract(db, contract_id, limit, offset)
    return [s.to_dict() for s in shipments]


@router.get("/shipments/{shipment_id}")
def get_shipment(shipment_id: str, db: Session = Depends(get_db)):
    """获取发货详情."""
    shipment = db.query(LogisticsShipment).filter(
        LogisticsShipment.id == shipment_id
    ).first()
    if not shipment:
        raise HTTPException(404, "发货记录不存在")
    return shipment.to_dict()


@router.put("/shipments/{shipment_id}/status")
def put_update_shipment_status(
    shipment_id: str,
    body: dict,
    db: Session = Depends(get_db),
):
    """更新发货状态."""
    try:
        shipment = LogisticsService.update_shipment_status(
            db=db,
            shipment_id=shipment_id,
            status=body["status"],
            location=body.get("location"),
            description=body.get("description"),
        )
        return {"id": shipment.id, "status": shipment.status}
    except ValueError as e:
        raise HTTPException(400, detail=str(e))


@router.get("/shipments/{shipment_id}/tracking")
def get_tracking_events(shipment_id: str, db: Session = Depends(get_db)):
    """获取发货轨迹事件."""
    events = LogisticsService.get_tracking_events(db, shipment_id)
    return [e.to_dict() for e in events]


@router.post("/shipments/{shipment_id}/confirm-delivery")
def post_confirm_delivery(
    shipment_id: str,
    confirmed_by: str,
    db: Session = Depends(get_db),
):
    """确认收货."""
    try:
        shipment = LogisticsService.confirm_delivery(db, shipment_id, confirmed_by)
        return {"id": shipment.id, "status": shipment.status}
    except Exception as e:
        raise HTTPException(500, detail=str(e))
