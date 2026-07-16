"""版权保险市场数据模型."""

import uuid
from datetime import date, datetime
from sqlalchemy import Column, String, DateTime, Float, Boolean, Text, Date, ForeignKey, CheckConstraint
from app.database import Base


class InsuranceProvider(Base):
    """保险公司/经纪商表."""

    __tablename__ = "insurance_providers"

    id = Column(String(32), primary_key=True, default=lambda: uuid.uuid4().hex)
    name_zh = Column(String(200), nullable=False)
    name_en = Column(String(200), nullable=True)
    license_no = Column(String(100), nullable=True)  # 保险经纪牌照号
    api_base_url = Column(String(500), nullable=True)
    webhook_secret = Column(String(255), nullable=True)
    contact_email = Column(String(200), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class InsuranceProduct(Base):
    """保险产品目录表 — 5 类 × 3 层 = 15 种产品."""

    __tablename__ = "insurance_products"

    __table_args__ = (
        CheckConstraint("tier IN ('basic', 'advanced', 'pro')", name="check_tier"),
    )

    id = Column(String(32), primary_key=True, default=lambda: uuid.uuid4().hex)
    product_key = Column(String(100), nullable=False, unique=True, index=True)
    provider_id = Column(String(32), ForeignKey("insurance_providers.id"), nullable=True)
    category = Column(String(100), nullable=False, index=True)  # 5 类保险类型
    tier = Column(String(20), nullable=False)  # basic / advanced / pro
    name_zh = Column(String(200), nullable=False)
    annual_min_yuan = Column(Float, nullable=False)
    annual_max_yuan = Column(Float, nullable=False)
    coverage_description = Column(Text, nullable=True)
    max_coverage_yuan = Column(Float, nullable=True)  # 最高赔付金额
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class InsurancePolicy(Base):
    """用户保单表."""

    __tablename__ = "insurance_policies"

    __table_args__ = (
        CheckConstraint("status IN ('pending', 'active', 'expired', 'cancelled', 'claiming')", name="check_policy_status"),
    )

    id = Column(String(32), primary_key=True, default=lambda: uuid.uuid4().hex)
    user_id = Column(String(32), nullable=False, index=True)
    product_id = Column(String(32), ForeignKey("insurance_products.id"), nullable=False)
    provider_id = Column(String(32), ForeignKey("insurance_providers.id"), nullable=True)
    policy_number = Column(String(100), nullable=True)  # 保险公司保单号
    status = Column(String(20), default="pending")
    annual_premium_yuan = Column(Float, nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    external_policy_ref = Column(String(255), nullable=True)  # 外部系统保单引用
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class InsuranceClaim(Base):
    """理赔记录表."""

    __tablename__ = "insurance_claims"

    __table_args__ = (
        CheckConstraint("status IN ('submitted', 'under_review', 'approved', 'denied', 'paid')", name="check_claim_status"),
        CheckConstraint("claim_type IN ('infringement', 'deepfake', 'theft', 'style_copy', 'other')", name="check_claim_type"),
    )

    id = Column(String(32), primary_key=True, default=lambda: uuid.uuid4().hex)
    policy_id = Column(String(32), ForeignKey("insurance_policies.id"), nullable=False, index=True)
    claim_type = Column(String(50), nullable=False)
    description = Column(Text, nullable=True)
    evidence_urls = Column(Text, nullable=True)  # JSON array of URLs
    claimed_amount_yuan = Column(Float, nullable=True)
    status = Column(String(20), default="submitted")
    resolution = Column(Text, nullable=True)
    resolved_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
