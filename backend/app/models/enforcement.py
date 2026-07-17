"""维权流水线数据模型."""

from datetime import datetime

from sqlalchemy import (
    Column, String, Text, DateTime, ForeignKey, Index, Float, JSON,
)
from sqlalchemy.orm import relationship

from app.database import Base
from app.models.work import generate_uuid


class EnforcementAction(Base):
    """维权行动表.

    追踪从侵权发现到投诉解决的完整生命周期:
    pending_review → confirmed → evidence_gathered → complaint_filed → resolved
    """
    __tablename__ = "enforcement_actions"

    id = Column(String(32), primary_key=True, default=generate_uuid)
    monitor_result_id = Column(
        String(32), ForeignKey("monitor_results.id", ondelete="CASCADE"), nullable=False
    )
    action_type = Column(
        String(30), nullable=False,
        default="platform_complaint",
    )
    # platform_complaint / dmca_notice / lawyer_letter / litigation
    platform = Column(String(50), nullable=False, default="generic")
    # taobao / instagram / google / xiaohongshu / custom / generic
    status = Column(String(30), nullable=False, default="pending_review")
    # pending_review / confirmed / evidence_gathered / complaint_filed / resolved
    complaint_text = Column(Text, nullable=True)
    template_used = Column(String(64), nullable=True)
    sent_at = Column(DateTime, nullable=True)
    response_text = Column(Text, nullable=True)
    resolved_at = Column(DateTime, nullable=True)
    resolution_type = Column(String(30), nullable=True)
    # takedown / settlement / dismissed / litigation_started
    compensation_amount = Column(Float, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    materials = relationship(
        "ComplaintMaterial", back_populates="action", cascade="all, delete-orphan",
    )

    __table_args__ = (
        Index("idx_enforcement_action_status", "status"),
        Index("idx_enforcement_action_monitor", "monitor_result_id"),
        Index("idx_enforcement_action_platform", "platform"),
    )


class EnforcementTemplate(Base):
    """投诉模板表.

    预置 DMCA / 中国著作权法 / 各平台规则的投诉文案模板，
    支持 {{placeholders}} 变量替换。
    """
    __tablename__ = "enforcement_templates"

    id = Column(String(32), primary_key=True, default=generate_uuid)
    platform = Column(String(50), nullable=False, default="generic")
    jurisdiction = Column(String(10), nullable=False, default="global")
    # cn / us / eu / global
    action_type = Column(String(30), nullable=False, default="copyright")
    # dmca / copyright / trademark / design_right
    title = Column(String(200), nullable=False)
    body_template = Column(Text, nullable=False)
    required_evidence = Column(JSON, nullable=True)
    # ["work_ownership_proof", "infringement_url", ...]
    filing_url = Column(String(2000), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("idx_template_platform", "platform"),
        Index("idx_template_jurisdiction", "jurisdiction"),
        Index("idx_template_action_type", "action_type"),
    )


class ComplaintMaterial(Base):
    """投诉材料表.

    记录每次维权行动生成的材料: PDF 证据包、预填 URL、API 配置等。
    """
    __tablename__ = "complaint_materials"

    id = Column(String(32), primary_key=True, default=generate_uuid)
    enforcement_action_id = Column(
        String(32), ForeignKey("enforcement_actions.id", ondelete="CASCADE"), nullable=False,
    )
    material_type = Column(String(30), nullable=True)
    # pdf_package / prefilled_url / api_config
    material_path = Column(String(2000), nullable=True)
    variables = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    action = relationship("EnforcementAction", back_populates="materials")

    __table_args__ = (
        Index("idx_material_action", "enforcement_action_id"),
    )
