"""多市场扩展数据模型."""

import uuid
from datetime import date, datetime
from sqlalchemy import Column, String, DateTime, Float, Boolean, Text, Date, ForeignKey, JSON
from app.database import Base


class MarketInfo(Base):
    """目标市场信息表 — 四市场对比数据."""

    __tablename__ = "market_infos"

    id = Column(String(32), primary_key=True, default=lambda: uuid.uuid4().hex)
    market_code = Column(String(20), nullable=False, unique=True)  # "cn", "us", "eu", "jp"
    name_zh = Column(String(100), nullable=False)
    name_en = Column(String(100), nullable=False)
    total_creators = Column(Float, nullable=True)  # 创作者总数（万人）
    revenue_median_yuan = Column(Float, nullable=True)  # 年收入中位数
    avg_rpm_yuan = Column(Float, nullable=True)  # 千次展示 RPM
    growth_rate_yoy = Column(Float, nullable=True)  # 年同比增长率
    is_open_to_foreign_creators = Column(Boolean, default=True)
    copyright_protection_level = Column(String(20), default="berne")  # berne / us_registration_required
    language_barrier = Column(String(20), default="high")  # low / medium / high
    created_at = Column(DateTime, default=datetime.utcnow)


class ExpansionPlan(Base):
    """创作者出海规划记录."""

    __tablename__ = "expansion_plans"

    id = Column(String(32), primary_key=True, default=lambda: uuid.uuid4().hex)
    user_id = Column(String(32), nullable=False, index=True)
    current_markets = Column(JSON, nullable=True)  # ["cn"]
    target_markets = Column(JSON, nullable=True)  # ["us", "eu"]
    phase = Column(String(20), nullable=False)  # "validation", "expansion", "diversified"
    start_date = Column(Date, nullable=True)
    expected_revenue_increase_percent = Column(Float, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class TaxGuide(Base):
    """跨境税务指南配置表."""

    __tablename__ = "tax_guides"

    id = Column(String(32), primary_key=True, default=lambda: uuid.uuid4().hex)
    source_market = Column(String(20), nullable=False)
    target_market = Column(String(20), nullable=False)
    withholding_tax_rate = Column(Float, nullable=True)  # 预扣税率
    tax_treaty_reduction = Column(Float, nullable=True)  # 税收协定降低后的税率
    recommended_entity = Column(String(100), nullable=True)  # 推荐实体类型
    required_forms = Column(JSON, nullable=True)  # ["W-8BEN"]
    description_zh = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
