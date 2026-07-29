"""无罪证明数据模型。

该模块存储作品创作无罪证明的相关信息，用于版权保护场景中的反侵权证据链生成。
"""

import uuid
from datetime import datetime

from sqlalchemy import (
    Column, String, Text, DateTime, Enum, ForeignKey, Index,
)
from sqlalchemy.orm import relationship

from app.database import Base


def generate_uuid():
    """生成唯一ID."""
    return uuid.uuid4().hex


class InnocenceProof(Base):
    """作品无罪证明表。

    记录作品创作过程的存证、时间戳和相关证明文件，用于在侵权纠纷中证明创作者的原始权利。
    """
    __tablename__ = "innocence_proofs"

    id = Column(String(32), primary_key=True, default=generate_uuid)
    work_id = Column(String(32), ForeignKey("works.id", ondelete="CASCADE"), nullable=False, index=True)
    evidence_document_url = Column(String(2000), nullable=True)  # 证据文档存储URL
    summary_text = Column(Text, nullable=True)  # 证明摘要内容
    status = Column(
        Enum("pending", "completed", "reviewed", name="innocence_proof_status"),
        nullable=False,
        default="pending",
    )  # 证明状态：待处理/已完成/已审核
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # 关系 - 引用对应的工作
    work = relationship("Work", backref="innocence_proofs")

    __table_args__ = (
        Index("idx_innocence_work_id", "work_id"),
        Index("idx_innocence_status", "status"),
        Index("idx_innocence_created", "created_at"),
    )