"""物流商数据模型."""

import uuid
from datetime import datetime

from sqlalchemy import Column, String, Float, Integer, DateTime, ForeignKey, Index, Text
from sqlalchemy.orm import relationship

from app.database import Base


class LogisticsProvider(Base):
    """物流商表 — v5.0 9 方参与者之一."""

    __tablename__ = "logistics_providers"

    id = Column(String(32), primary_key=True, default=lambda: uuid.uuid4().hex)
    name = Column(String(200), nullable=False)
    contact_email = Column(String(100), nullable=True)
    contact_phone = Column(String(20), nullable=True)
    logo_url = Column(String(500), nullable=True)
    description = Column(Text, nullable=True)
    status = Column(String(20), default="active")
    rating = Column(Float, default=0.0)
    contract_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index("idx_logistics_status", "status"),
        Index("idx_logistics_rating", "rating"),
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "contact_email": self.contact_email,
            "contact_phone": self.contact_phone,
            "logo_url": self.logo_url,
            "description": self.description,
            "status": self.status,
            "rating": self.rating,
            "contract_count": self.contract_count,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class LogisticsShipment(Base):
    """物流发货记录表 — 关联合约履约状态."""

    __tablename__ = "logistics_shipments"

    id = Column(String(32), primary_key=True, default=lambda: uuid.uuid4().hex)
    contract_id = Column(
        String(32),
        ForeignKey("contract_instances.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    provider_id = Column(
        String(32),
        ForeignKey("logistics_providers.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    tracking_number = Column(String(100), nullable=True)
    carrier = Column(String(50), nullable=True)
    status = Column(String(30), default="pending")
    shipped_at = Column(DateTime, nullable=True)
    delivered_at = Column(DateTime, nullable=True)
    estimated_delivery = Column(DateTime, nullable=True)
    recipient_name = Column(String(100), nullable=True)
    recipient_address = Column(Text, nullable=True)
    sender_name = Column(String(100), nullable=True)
    sender_address = Column(Text, nullable=True)
    weight_kg = Column(Float, nullable=True)
    dimensions_cm = Column(String(50), nullable=True)
    shipping_cost = Column(Float, nullable=True)
    currency = Column(String(10), default="CNY")
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index("idx_shipment_contract", "contract_id"),
        Index("idx_shipment_provider", "provider_id"),
        Index("idx_shipment_status", "status"),
        Index("idx_shipment_tracking", "tracking_number"),
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "contract_id": self.contract_id,
            "provider_id": self.provider_id,
            "tracking_number": self.tracking_number,
            "carrier": self.carrier,
            "status": self.status,
            "shipped_at": self.shipped_at.isoformat() if self.shipped_at else None,
            "delivered_at": self.delivered_at.isoformat() if self.delivered_at else None,
            "estimated_delivery": self.estimated_delivery.isoformat() if self.estimated_delivery else None,
            "recipient_name": self.recipient_name,
            "recipient_address": self.recipient_address,
            "sender_name": self.sender_name,
            "sender_address": self.sender_address,
            "weight_kg": self.weight_kg,
            "dimensions_cm": self.dimensions_cm,
            "shipping_cost": self.shipping_cost,
            "currency": self.currency,
            "notes": self.notes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class LogisticsTrackingEvent(Base):
    """物流轨迹事件表."""

    __tablename__ = "logistics_tracking_events"

    id = Column(String(32), primary_key=True, default=lambda: uuid.uuid4().hex)
    shipment_id = Column(
        String(32),
        ForeignKey("logistics_shipments.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    event_type = Column(String(30), nullable=False)
    location = Column(String(200), nullable=True)
    description = Column(Text, nullable=True)
    occurred_at = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("idx_tracking_event_shipment", "shipment_id"),
        Index("idx_tracking_event_time", "occurred_at"),
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "shipment_id": self.shipment_id,
            "event_type": self.event_type,
            "location": self.location,
            "description": self.description,
            "occurred_at": self.occurred_at.isoformat() if self.occurred_at else None,
        }
