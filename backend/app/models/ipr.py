"""IP 登记数据模型 (仅指引，不做法律判断)."""

from datetime import datetime

from sqlalchemy import (
    Column, String, Text, DateTime, Date, Boolean, ForeignKey, Index, Float, Integer, JSON,
)
from sqlalchemy.orm import relationship

from app.database import Base
from app.models.work import generate_uuid


class IPRegistration(Base):
    """IP 登记记录 (增强 v2)."""
    __tablename__ = "ip_registrations"

    id = Column(String(32), primary_key=True, default=generate_uuid)
    work_id = Column(String(32), ForeignKey("works.id", ondelete="SET NULL"), nullable=True)
    ip_type = Column(String(20), nullable=False)  # copyright/trademark/design_patent/utility_patent
    jurisdiction = Column(String(10), nullable=False, default="cn")  # cn/us/eu/jp/kr/wipo
    application_no = Column(String(100), nullable=True)
    registration_no = Column(String(100), nullable=True)  # 注册号
    filing_date = Column(Date, nullable=True)
    registration_date = Column(Date, nullable=True)  # 注册日
    expiration_date = Column(Date, nullable=True)  # 到期日
    next_action_date = Column(Date, nullable=True)  # 下一个关键日期(续展/年费)
    next_action_type = Column(String(30), nullable=True)  # renewal/annuity/declaration_of_use
    status = Column(String(30), default="draft")  # draft/filed/under_review/registered/rejected/expired
    category_info = Column(JSON, nullable=True)  # 商标类别信息
    official_fee = Column(Float, default=0.0)  # 官费
    total_cost = Column(Float, default=0.0)  # 总费用(含官费+代理费+其他)
    agent_name = Column(String(200), nullable=True)  # 代理机构
    agent_fee = Column(Float, default=0.0)  # 代理费
    application_package_path = Column(String(2000), nullable=True)  # 导出的申请材料包路径(ZIP)
    application_form_path = Column(String(2000), nullable=True)  # PDF申请表路径
    official_url = Column(String(2000), nullable=True)  # 官方平台提交链接
    certificate_path = Column(String(2000), nullable=True)  # 证书扫描件路径
    reminder_date = Column(DateTime, nullable=True)
    notes = Column(Text, nullable=True)
    lawyer_consulted = Column(String(3), nullable=True)  # v3 UPL合规: A(已咨询律师)/B(自行承担风险)/C(暂不提交)
    disclaimer_accepted_at = Column(DateTime, nullable=True)  # v3: 首次进入IP登记模块时的免责声明接受时间
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    work = relationship("Work", foreign_keys=[work_id])

    __table_args__ = (
        Index("idx_ipr_work", "work_id"),
        Index("idx_ipr_type", "ip_type"),
        Index("idx_ipr_status", "status"),
        Index("idx_ipr_jurisdiction", "jurisdiction"),
        Index("idx_ipr_expiration", "expiration_date"),
        Index("idx_ipr_next_action", "next_action_date"),
        Index("idx_ipr_reminder", "reminder_date"),
    )


class TrademarkClass(Base):
    """商标类别."""
    __tablename__ = "trademark_classes"

    id = Column(String(32), primary_key=True, default=generate_uuid)
    registration_id = Column(String(32), ForeignKey("ip_registrations.id", ondelete="CASCADE"), nullable=False)
    class_no = Column(Integer, nullable=False)
    class_desc = Column(String(500), nullable=True)
    status = Column(String(20), default="planned")  # planned/filed/registered

    __table_args__ = (
        Index("idx_tm_class_reg", "registration_id"),
    )


class CopyrightRegistration(Base):
    """版权登记."""
    __tablename__ = "copyright_registrations"

    id = Column(String(32), primary_key=True, default=generate_uuid)
    work_id = Column(String(32), ForeignKey("works.id", ondelete="SET NULL"), nullable=True)
    registration_number = Column(String(100), nullable=True)
    application_date = Column(Date, nullable=True)
    registration_date = Column(Date, nullable=True)
    status = Column(String(30), default="draft")
    certificate_path = Column(String(2000), nullable=True)
    registration_url = Column(String(2000), nullable=True)  # 官方平台链接
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index("idx_copyright_work", "work_id"),
    )


class TrademarkRegistration(Base):
    """商标注册."""
    __tablename__ = "trademark_registrations"

    id = Column(String(32), primary_key=True, default=generate_uuid)
    name = Column(String(500), nullable=False)
    logo_work_id = Column(String(32), ForeignKey("works.id", ondelete="SET NULL"), nullable=True)
    categories = Column(JSON, nullable=True)  # 申请类别列表
    application_number = Column(String(100), nullable=True)
    application_date = Column(Date, nullable=True)
    registration_number = Column(String(100), nullable=True)
    status = Column(String(30), default="draft")
    trademark_office = Column(String(100), default="cnipa")  # 商标局
    agent_name = Column(String(200), nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index("idx_tm_reg_name", "name"),
        Index("idx_tm_reg_status", "status"),
    )


class TrademarkMonitoring(Base):
    """商标监测."""
    __tablename__ = "trademark_monitoring"

    id = Column(String(32), primary_key=True, default=generate_uuid)
    trademark_id = Column(String(32), ForeignKey("trademark_registrations.id", ondelete="CASCADE"), nullable=False)
    monitored_name = Column(String(500), nullable=False)
    application_number = Column(String(100), nullable=True)
    applicant = Column(String(500), nullable=True)
    category = Column(String(50), nullable=True)
    publication_date = Column(Date, nullable=True)
    status = Column(String(30), default="monitoring")
    action_type = Column(String(50), nullable=True)  # opposition/invalidation/monitoring
    action_date = Column(Date, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("idx_tm_monitor_name", "monitored_name"),
    )


class ApplicationTemplate(Base):
    """申请表单模板."""
    __tablename__ = "application_templates"

    id = Column(String(32), primary_key=True, default=generate_uuid)
    ip_type = Column(String(20), nullable=False)  # copyright/trademark/design_patent/utility_patent
    jurisdiction = Column(String(10), nullable=False)  # cn/us/eu/jp/kr/wipo
    template_name = Column(String(200), nullable=False)
    template_version = Column(String(20), default="1.0")
    form_schema = Column(JSON, nullable=False)  # 表单字段定义
    field_mappings = Column(JSON, nullable=False)  # 字段映射: 官方字段 -> 数据来源
    validation_rules = Column(JSON, nullable=True)  # 校验规则
    fee_schedule = Column(JSON, nullable=True)  # 费用表
    required_documents = Column(JSON, nullable=True)  # 所需材料清单
    official_submission_url = Column(String(2000), nullable=True)
    official_guide_url = Column(String(2000), nullable=True)
    estimated_duration = Column(String(50), nullable=True)
    legal_basis = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index("idx_at_type_jur", "ip_type", "jurisdiction"),
    )


class NiceClassification(Base):
    """尼斯分类数据库."""
    __tablename__ = "nice_classification"

    id = Column(String(32), primary_key=True, default=generate_uuid)
    class_no = Column(Integer, nullable=False, unique=True)
    class_name_zh = Column(String(200), nullable=False)
    class_name_en = Column(String(200), nullable=True)
    goods_services = Column(JSON, nullable=True)  # 规范商品/服务项目列表
    is_creative_relevant = Column(Boolean, default=False)
    common_for_creators = Column(JSON, nullable=True)  # 创作者常用子项
    updated_year = Column(Integer, default=2026)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("idx_nice_class_no", "class_no"),
        Index("idx_nice_creative", "is_creative_relevant"),
    )
