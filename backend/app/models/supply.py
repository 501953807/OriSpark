"""供应链协作数据模型."""

from datetime import datetime, date

from sqlalchemy import (
    Column, String, Text, DateTime, Date, Boolean, ForeignKey, Index, Float, Integer, JSON,
)
from sqlalchemy.orm import relationship

from app.database import Base
from app.models.work import generate_uuid


class Partner(Base):
    """合作伙伴 (工厂联系人 — P1.5 增强)."""
    __tablename__ = "partners"

    id = Column(String(32), primary_key=True, default=generate_uuid)
    name = Column(String(200), nullable=False)
    company_name = Column(String(500), nullable=True)
    type = Column(String(50), default="manufacturer")  # ★ manufacturer / supplier / pod_platform / fulfillment
    contact_person = Column(String(200), nullable=True)
    phone = Column(String(500), nullable=True)  # AES 加密存储
    email = Column(String(500), nullable=True)
    address = Column(Text, nullable=True)
    website = Column(String(500), nullable=True)
    categories = Column(JSON, nullable=True)  # 工厂类型: printing/clothing/accessories/...

    # ★ P1.5: 制造能力
    product_categories = Column(JSON, nullable=True)       # 可制造品类: [pin, sticker, plush_toy, ...]
    material_capabilities = Column(JSON, nullable=True)    # 材质能力: [metal, acrylic, textile, ...]
    moq_per_category = Column(JSON, nullable=True)         # 每种品类的最低起订量
    typical_lead_time_days = Column(Integer, nullable=True) # 典型交付周期(天)

    # ★ P1.5: 价格参考
    price_range = Column(JSON, nullable=True)              # [{category, unit_price_range, moq}]

    moq = Column(Integer, nullable=True)  # 最小起订量 (保留兼容)
    rating = Column(Integer, default=0)  # 评分 1-5
    tags = Column(JSON, nullable=True)
    status = Column(String(20), default="active")  # active/inactive
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    orders = relationship("Order", back_populates="partner")
    qualifications = relationship("PartnerQualification", back_populates="partner", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_partner_name", "name"),
        Index("idx_partner_status", "status"),
        Index("idx_partner_type", "type"),
    )


class PartnerQualification(Base):
    """供应商资质文件."""
    __tablename__ = "partner_qualifications"

    id = Column(String(32), primary_key=True, default=generate_uuid)
    partner_id = Column(String(32), ForeignKey("partners.id", ondelete="CASCADE"), nullable=False)
    qual_type = Column(String(50), nullable=False)  # business_license/iso/cert
    file_path = Column(String(2000), nullable=False)
    expire_date = Column(Date, nullable=True)
    verified = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    partner = relationship("Partner", back_populates="qualifications")


class Order(Base):
    """订单表 (P1.5 增强)."""
    __tablename__ = "orders"

    id = Column(String(32), primary_key=True, default=generate_uuid)
    order_number = Column(String(50), nullable=False, unique=True)

    # ★ P1.5: 订单类型
    order_type = Column(String(30), default="custom_mfg")   # custom_mfg / pod_bulk / crowdfunding_fulfillment / sample

    partner_id = Column(String(32), ForeignKey("partners.id", ondelete="SET NULL"), nullable=True)
    campaign_id = Column(String(32), ForeignKey("campaigns.id", ondelete="SET NULL"), nullable=True)
    product_id = Column(String(32), nullable=True)
    listing_id = Column(String(32), ForeignKey("design_listings.id", ondelete="SET NULL"), nullable=True)  # P2
    product_name = Column(String(500), nullable=False)
    product_category = Column(String(100), nullable=True)    # ★ t_shirt / pin / plush_toy / ...
    quantity = Column(Integer, nullable=False, default=1)
    specifications = Column(Text, nullable=True)
    design_file_path = Column(String(2000), nullable=True)   # ★ 发给工厂的设计文件

    # 费用
    unit_price = Column(Float, default=0.0)
    total_amount = Column(Float, default=0.0)
    deposit_percent = Column(Float, default=30.0)  # 定金比例
    deposit_paid = Column(Float, default=0.0)  # 已付定金
    balance_due = Column(Float, default=0.0)  # 尾款
    shipping_cost = Column(Float, default=0.0)  # ★ 运费

    # 状态
    status = Column(String(20), default="draft")
    # draft/quoting/confirmed/in_production/quality_check/shipped/completed/cancelled

    # 时间线
    expected_date = Column(Date, nullable=True)
    actual_date = Column(Date, nullable=True)

    # ★ P1.5: 样品管理
    sample_requested = Column(Integer, default=0)
    sample_received = Column(Integer, default=0)
    sample_approved = Column(Integer, default=0)

    # 物流
    shipping_method = Column(String(100), nullable=True)
    tracking_number = Column(String(200), nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    partner = relationship("Partner", back_populates="orders")
    listing = relationship("DesignListing", back_populates="orders")  # P2
    payments = relationship("OrderPayment", back_populates="order", cascade="all, delete-orphan")
    communications = relationship("OrderCommunication", back_populates="order", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_order_partner", "partner_id"),
        Index("idx_order_status", "status"),
        Index("idx_order_expected_date", "expected_date"),
        Index("idx_order_type", "order_type"),
        Index("idx_order_campaign", "campaign_id"),
    )


class OrderPayment(Base):
    """订单支付记录."""
    __tablename__ = "order_payments"

    id = Column(String(32), primary_key=True, default=generate_uuid)
    order_id = Column(String(32), ForeignKey("orders.id", ondelete="CASCADE"), nullable=False)
    amount = Column(Float, nullable=False)
    payment_type = Column(String(30), default="deposit")  # deposit/progress/balance/other
    payment_date = Column(Date, default=date.today)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    order = relationship("Order", back_populates="payments")

    __table_args__ = (
        Index("idx_payment_order", "order_id"),
    )


class OrderCommunication(Base):
    """订单沟通记录."""
    __tablename__ = "order_communications"

    id = Column(String(32), primary_key=True, default=generate_uuid)
    order_id = Column(String(32), ForeignKey("orders.id", ondelete="CASCADE"), nullable=False)
    content = Column(Text, nullable=False)
    attachment_path = Column(String(2000), nullable=True)
    direction = Column(String(10), default="out")  # out/in
    created_at = Column(DateTime, default=datetime.utcnow)

    order = relationship("Order", back_populates="communications")


class Reminder(Base):
    """提醒表."""
    __tablename__ = "reminders"

    id = Column(String(32), primary_key=True, default=generate_uuid)
    type = Column(String(30), nullable=False)  # order/key_event/certificate_expiry/renewal
    related_id = Column(String(32), nullable=False)
    title = Column(String(500), nullable=False)
    remind_at = Column(DateTime, nullable=False)
    status = Column(String(20), default="pending")  # pending/sent/dismissed
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("idx_reminder_status", "status"),
        Index("idx_reminder_at", "remind_at"),
    )
