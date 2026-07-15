import enum
import uuid
from datetime import datetime

from sqlalchemy import Column, String, DateTime, Float, ForeignKey, Enum as SAEnum, Text, Integer, JSON
from app.database import Base


class IPEvaluationStage(enum.StrEnum):
    ASSESSMENT = "assessment"
    CONCEPT = "concept"
    PROTOTYPE = "prototype"
    SUPPLY_LOCK = "supply_lock"
    MASS_PRODUCTION = "mass_production"
    LAUNCH_REVIEW = "launch_review"


class IPAsset(Base):
    """IP资产表 — 跟踪IP商业化全生命周期."""
    __tablename__ = "ip_assets"

    id = Column(String(32), primary_key=True, default=lambda: uuid.uuid4().hex)
    work_id = Column(String(32), ForeignKey("works.id"), nullable=False, index=True)
    ip_name = Column(String(200), nullable=False)
    originality_score = Column(Float, nullable=True)  # 原创性 0-100
    market_demand_score = Column(Float, nullable=True)  # 市场需求 0-100
    competition_density = Column(Float, nullable=True)  # 竞争密度 0-100
    monetization_potential = Column(Float, nullable=True)  # 变现潜力 0-100
    overall_score = Column(Float, nullable=True)  # 综合评分
    current_stage = Column(SAEnum(IPEvaluationStage), default=IPEvaluationStage.ASSESSMENT)
    derivative_products = Column(JSON, nullable=True)  # 衍生品列表
    pod_platforms = Column(JSON, nullable=True)  # POD平台集成配置
    mgr_floor_price = Column(Float, nullable=True)  # MGR保底金
    brand_premium_estimate = Column(Float, nullable=True)  # 品牌溢价预估(%)
    trademark_classes = Column(JSON, nullable=True)  # 推荐商标类别
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
