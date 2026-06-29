"""存证确权数据模型."""

from datetime import datetime

from sqlalchemy import (
    Column, String, Text, DateTime, Boolean, ForeignKey, Index, Float, JSON,
)
from sqlalchemy.orm import relationship

from app.database import Base
from app.models.work import generate_uuid


class NotaryRecord(Base):
    """存证记录表."""
    __tablename__ = "notary_records"

    id = Column(String(32), primary_key=True, default=generate_uuid)
    work_id = Column(String(32), ForeignKey("works.id", ondelete="CASCADE"), nullable=False)
    platform = Column(String(50), nullable=False)  # banquanjia/antchain/zhixinchain
    platform_url = Column(String(2000), nullable=True)
    transaction_hash = Column(String(128), nullable=True)  # 区块链交易哈希
    block_height = Column(String(50), nullable=True)
    blockchain = Column(String(50), nullable=True)  # 区块链名称
    certificate_id = Column(String(64), nullable=True)
    status = Column(String(20), nullable=False, default="unverified")
    # unverified/pending/confirmed/failed/expired
    fee = Column(Float, default=0.0)  # 费用(元)
    payment_method = Column(String(50), nullable=True)
    payment_status = Column(String(20), default="unpaid")  # unpaid/paid
    qr_code_url = Column(String(2000), nullable=True)
    evidence_hash = Column(String(64), nullable=True)  # 存证时使用的哈希
    confirmed_at = Column(DateTime, nullable=True)
    expires_at = Column(DateTime, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    work = relationship("Work", back_populates="notary_records")
    certificates = relationship("Certificate", back_populates="notary_record", cascade="all, delete-orphan")
    audit_trails = relationship("NotaryAuditTrail", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_notary_work", "work_id"),
        Index("idx_notary_status", "status"),
        Index("idx_notary_work_platform", "work_id", "platform"),
        Index("idx_notary_platform", "platform"),
    )


class Certificate(Base):
    """证书表."""
    __tablename__ = "certificates"

    id = Column(String(32), primary_key=True, default=generate_uuid)
    notary_record_id = Column(String(32), ForeignKey("notary_records.id", ondelete="CASCADE"), nullable=False)
    cert_path = Column(String(2000), nullable=False)  # PDF 证书文件路径
    qr_code = Column(String(2000), nullable=True)  # 验证二维码数据
    template_name = Column(String(100), default="default")
    issued_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)
    metadata_json = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    notary_record = relationship("NotaryRecord", back_populates="certificates")

    __table_args__ = (
        Index("idx_cert_notary", "notary_record_id"),
    )


class C2PARecord(Base):
    """C2PA 元数据嵌入记录."""
    __tablename__ = "c2pa_records"

    id = Column(String(32), primary_key=True, default=generate_uuid)
    work_id = Column(String(32), ForeignKey("works.id", ondelete="CASCADE"), nullable=False)
    manifest_json = Column(JSON, nullable=True)
    embedded_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    validator_url = Column(String(2000), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("idx_c2pa_work", "work_id"),
    )


class NotaryAuditTrail(Base):
    """存证审计追踪表 (P1.2.7).

    自动记录存证流程每一步的状态变化:
    create → pending → confirm → cert_generate
    """
    __tablename__ = "notary_audit_trails"

    id = Column(String(32), primary_key=True, default=generate_uuid)
    notary_record_id = Column(String(32), ForeignKey("notary_records.id", ondelete="CASCADE"), nullable=False)
    step = Column(String(50), nullable=False)  # create/pending/confirm/cert_generate/fail
    status = Column(String(20), nullable=False, default="success")  # success/failure
    detail = Column(Text, nullable=True)  # 步骤详情
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("idx_audit_notary_record", "notary_record_id"),
        Index("idx_audit_step", "step"),
    )
