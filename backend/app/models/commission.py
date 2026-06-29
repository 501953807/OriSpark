"""委托项目管理数据模型."""

from datetime import datetime

from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Index, JSON, Float
from sqlalchemy.orm import relationship

from app.database import Base
from app.models.work import generate_uuid


VALID_STATUSES = ("brief", "proposal", "production", "delivery", "settlement")


class CommissionProject(Base):
    """委托项目."""
    __tablename__ = "commission_projects"

    id = Column(String(32), primary_key=True, default=generate_uuid)
    user_id = Column(String(32), nullable=False)
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    client_name = Column(String(200), nullable=True)
    status = Column(String(20), default="brief")  # brief/proposal/production/delivery/settlement
    milestones = Column(JSON, nullable=True)  # [{title, description, due_date, completed, completed_at}]
    payment_terms = Column(JSON, nullable=True)  # [{stage, percentage, amount, due_date}]
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    orders = relationship(
        "CommissionOrder",
        back_populates="project",
        cascade="all, delete-orphan",
    )
    messages = relationship(
        "CommissionMessage",
        back_populates="project",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        Index("idx_comp_user", "user_id"),
        Index("idx_comp_status", "status"),
    )


class CommissionOrder(Base):
    """委托订单."""
    __tablename__ = "commission_orders"

    id = Column(String(32), primary_key=True, default=generate_uuid)
    project_id = Column(
        String(32),
        ForeignKey("commission_projects.id", ondelete="CASCADE"),
        nullable=False,
    )
    order_type = Column(String(50), nullable=False)
    amount = Column(Float, nullable=False, default=0.0)
    status = Column(String(20), default="pending")  # pending/completed/overdue
    created_at = Column(DateTime, default=datetime.utcnow)

    project = relationship("CommissionProject", back_populates="orders")

    __table_args__ = (
        Index("idx_ord_project", "project_id"),
        Index("idx_ord_status", "status"),
    )


class CommissionMessage(Base):
    """委托沟通消息."""
    __tablename__ = "commission_messages"

    id = Column(String(32), primary_key=True, default=generate_uuid)
    project_id = Column(
        String(32),
        ForeignKey("commission_projects.id", ondelete="CASCADE"),
        nullable=False,
    )
    sender_id = Column(String(32), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    project = relationship("CommissionProject", back_populates="messages")

    __table_args__ = (
        Index("idx_msg_project", "project_id"),
        Index("idx_msg_sender", "sender_id"),
    )
