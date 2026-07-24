"""物流商管理服务."""

import uuid
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy.orm import Session

from app.models.logistics import LogisticsProvider, LogisticsShipment, LogisticsTrackingEvent


class LogisticsService:
    """物流商接入服务 — 支持物流商作为独立参与者."""

    @classmethod
    def create_provider(
        cls,
        db: Session,
        name: str,
        contact_email: Optional[str] = None,
        contact_phone: Optional[str] = None,
        description: Optional[str] = None,
    ) -> LogisticsProvider:
        """创建物流商."""
        provider = LogisticsProvider(
            id=uuid.uuid4().hex,
            name=name,
            contact_email=contact_email,
            contact_phone=contact_phone,
            description=description,
        )
        db.add(provider)
        db.flush()
        db.refresh(provider)
        return provider

    @classmethod
    def get_providers(
        cls,
        db: Session,
        status: Optional[str] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> list[LogisticsProvider]:
        """获取物流商列表."""
        query = db.query(LogisticsProvider)
        if status:
            query = query.filter(LogisticsProvider.status == status)
        return query.order_by(LogisticsProvider.created_at.desc()).offset(offset).limit(limit).all()

    @classmethod
    def get_provider(cls, db: Session, provider_id: str) -> Optional[LogisticsProvider]:
        """获取物流商详情."""
        return db.query(LogisticsProvider).filter(
            LogisticsProvider.id == provider_id
        ).first()

    @classmethod
    def update_provider(
        cls,
        db: Session,
        provider_id: str,
        **kwargs,
    ) -> LogisticsProvider:
        """更新物流商信息."""
        provider = cls.get_provider(db, provider_id)
        if not provider:
            raise ValueError("物流商不存在")

        for key, value in kwargs.items():
            if hasattr(provider, key):
                setattr(provider, key, value)

        provider.updated_at = datetime.utcnow()
        db.flush()
        db.refresh(provider)
        return provider

    @classmethod
    def create_shipment(
        cls,
        db: Session,
        contract_id: str,
        provider_id: str,
        tracking_number: Optional[str] = None,
        recipient_name: Optional[str] = None,
        recipient_address: Optional[str] = None,
        sender_name: Optional[str] = None,
        sender_address: Optional[str] = None,
        shipping_cost: Optional[float] = None,
        currency: str = "CNY",
        notes: Optional[str] = None,
    ) -> LogisticsShipment:
        """创建发货记录."""
        from app.models.contract import ContractInstance
        contract_obj = db.query(ContractInstance).filter(
            ContractInstance.id == contract_id
        ).first()
        if not contract_obj:
            raise ValueError("合约不存在")

        shipment = LogisticsShipment(
            id=uuid.uuid4().hex,
            contract_id=contract_id,
            provider_id=provider_id,
            tracking_number=tracking_number or f"SHIP_{uuid.uuid4().hex[:12].upper()}",
            recipient_name=recipient_name,
            recipient_address=recipient_address,
            sender_name=sender_name,
            sender_address=sender_address,
            shipping_cost=shipping_cost,
            currency=currency,
            notes=notes,
        )
        db.add(shipment)

        # 添加初始事件
        event = LogisticsTrackingEvent(
            id=uuid.uuid4().hex,
            shipment_id=shipment.id,
            event_type="created",
            description=f"物流发货记录创建，由 {provider_id} 承运",
        )
        db.add(event)

        # 更新物流商合同计数
        provider = db.query(LogisticsProvider).filter(
            LogisticsProvider.id == provider_id
        ).first()
        if provider:
            provider.contract_count += 1

        db.flush()
        db.refresh(shipment)
        return shipment

    @classmethod
    def update_shipment_status(
        cls,
        db: Session,
        shipment_id: str,
        status: str,
        location: Optional[str] = None,
        description: Optional[str] = None,
    ) -> LogisticsShipment:
        """更新发货状态并添加轨迹事件."""
        shipment = db.query(LogisticsShipment).filter(
            LogisticsShipment.id == shipment_id
        ).first()
        if not shipment:
            raise ValueError("发货记录不存在")

        valid_statuses = {"pending", "shipped", "in_transit", "delivered", "returned", "cancelled"}
        if status not in valid_statuses:
            raise ValueError(f"无效状态: {status}")

        old_status = shipment.status
        shipment.status = status
        shipment.updated_at = datetime.utcnow()

        # 设置时间戳
        if status == "shipped":
            shipment.shipped_at = datetime.utcnow()
        elif status == "delivered":
            shipment.delivered_at = datetime.utcnow()
        elif status == "returned":
            shipment.delivered_at = datetime.utcnow()

        # 添加轨迹事件
        event = LogisticsTrackingEvent(
            id=uuid.uuid4().hex,
            shipment_id=shipment_id,
            event_type=status,
            location=location,
            description=description or f"状态变更：{old_status} -> {status}",
        )
        db.add(event)

        db.flush()
        db.refresh(shipment)
        return shipment

    @classmethod
    def get_shipments_by_contract(
        cls,
        db: Session,
        contract_id: str,
        limit: int = 20,
        offset: int = 0,
    ) -> list[LogisticsShipment]:
        """获取合约的物流发货记录."""
        return db.query(LogisticsShipment).filter(
            LogisticsShipment.contract_id == contract_id
        ).order_by(LogisticsShipment.created_at.desc()).offset(offset).limit(limit).all()

    @classmethod
    def get_tracking_events(
        cls,
        db: Session,
        shipment_id: str,
    ) -> list[LogisticsTrackingEvent]:
        """获取发货轨迹事件."""
        return db.query(LogisticsTrackingEvent).filter(
            LogisticsTrackingEvent.shipment_id == shipment_id
        ).order_by(LogisticsTrackingEvent.occurred_at.asc()).all()

    @classmethod
    def confirm_delivery(
        cls,
        db: Session,
        shipment_id: str,
        confirmed_by: str,
    ) -> LogisticsShipment:
        """确认收货."""
        shipment = cls.update_shipment_status(
            db,
            shipment_id,
            "delivered",
            location="收货地址",
            description=f"收货人 {confirmed_by} 确认收货",
        )

        # 如果合约处于执行中，自动进入验收状态
        from app.models.contract import ContractInstance
        from app.services.contract_state_service import ContractStateService
        contract_obj = db.query(ContractInstance).filter(
            ContractInstance.id == shipment.contract_id
        ).first()
        if contract_obj:
            try:
                ContractStateService.start_execution(db, shipment.contract_id, confirmed_by)
            except Exception:
                pass

        return shipment
