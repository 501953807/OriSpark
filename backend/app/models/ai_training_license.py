import enum
import uuid
from datetime import datetime

from sqlalchemy import Column, String, DateTime, Boolean, Integer, ForeignKey, Enum as SAEnum, Text
from app.database import Base


class CCProtocol(enum.StrEnum):
    CC0 = "CC0"
    CC_BY = "CC-BY"
    CC_BY_NC = "CC-BY-NC"
    CC_BY_SA = "CC-BY-SA"
    CC_BY_NC_SA = "CC-BY-NC-SA"
    CC_BY_NC_ND = "CC-BY-NC-ND"


class AITrainingLicense(Base):
    """AI训练数据授权配置表."""
    __tablename__ = "ai_training_licenses"

    id = Column(String(32), primary_key=True, default=lambda: uuid.uuid4().hex)
    work_id = Column(String(32), ForeignKey("works.id"), nullable=False, index=True)
    cc_protocol = Column(SAEnum(CCProtocol), nullable=False, default=CCProtocol.CC0)
    enabled = Column(Boolean, default=False)  # 是否允许AI训练使用
    price_per_use_cents = Column(Integer, default=5)  # $0.05 = 5 cents
    exclude_ai_training_clause = Column(Text, nullable=True)  # AI排除条款文本
    total_uses = Column(Integer, default=0)  # 累计被使用次数
    total_revenue_cents = Column(Integer, default=0)  # 累计收入（美分）
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
