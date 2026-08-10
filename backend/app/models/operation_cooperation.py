"""运营合作模型 — 创作者 ↔ 运营者合作撮合."""

from datetime import datetime, timezone

from sqlalchemy import Column, String, Text, DateTime, Boolean, Index, JSON, ForeignKey
from sqlalchemy.orm import relationship

from app.database import Base
from app.models.work import generate_uuid


class OperationCooperation(Base):
    """运营合作要约表.

    运营者向创作者发起合作要约，创作者接受后自动生成 ContractInstance.
    """
    __tablename__ = "operation_cooperations"

    id = Column(String(32), primary_key=True, default=generate_uuid)
    work_id = Column(String(32), ForeignKey("works.id", ondelete="CASCADE"), nullable=False, index=True)
    operator_id = Column(String(32), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    creator_id = Column(String(32), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    contract_id = Column(String(32), nullable=True, index=True)  # 接受后关联的合约

    # 授权范围
    scope = Column(JSON, nullable=False, default=dict)
    # scope schema:
    # {
    #   "regions": ["CN", "JP", "US"],
    #   "channels": ["ecommerce", "social", "print"],
    #   "products": ["physical", "digital"],
    #   "transform_rights": ["3d_model", "figure", "merchandise"],
    #   "duration_months": 12
    # }

    status = Column(String(20), nullable=False, default="pending")
    # pending / accepted / rejected / expired / cancelled

    notes = Column(Text, nullable=True)  # 合作备注
    operator_notes = Column(Text, nullable=True)  # 运营者内部备注

    created_at = Column(DateTime, default=datetime.now(timezone.utc))
    accepted_at = Column(DateTime, nullable=True)
    rejected_at = Column(DateTime, nullable=True)
    expires_at = Column(DateTime, nullable=True)  # 过期时间（默认30天）

    __table_args__ = (
        Index("idx_oc_operator", "operator_id", "status"),
        Index("idx_oc_creator", "creator_id", "status"),
    )

    operator = relationship("User", foreign_keys=[operator_id])
    creator = relationship("User", foreign_keys=[creator_id])
    work = relationship("Work", foreign_keys=[work_id])
