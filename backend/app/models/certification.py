import uuid
from datetime import datetime

from sqlalchemy import Column, String, DateTime, Boolean, Text, Integer, ForeignKey, JSON
from app.database import Base


class CertificationRecord(Base):
    """区块链存证记录表."""
    __tablename__ = "certification_records"

    id = Column(String(32), primary_key=True, default=lambda: uuid.uuid4().hex)
    work_id = Column(String(32), ForeignKey("works.id"), nullable=False, index=True)
    sha256_hash = Column(String(64), nullable=False)
    blockchain_tx_id = Column(String(128), nullable=True, index=True)  # 蚂蚁链交易ID
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    block_height = Column(Integer, nullable=True)
    is_court_admissible = Column(Boolean, default=True)
    certificate_url = Column(String(2000), nullable=True)  # 证书下载URL
    cost_saved_yuan = Column(Integer, default=0)  # 节省金额（对比传统公证）
    extra_metadata = Column(JSON, nullable=True)  # 额外元数据
    created_at = Column(DateTime, default=datetime.utcnow)
