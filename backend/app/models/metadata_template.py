"""元数据模板数据模型.

表:
- metadata_templates: 自定义元数据模板
- template_fields: 模板字段定义
"""

import uuid
from datetime import datetime

from sqlalchemy import (
    Column, String, Integer, Text, Boolean, DateTime,
    ForeignKey, Index, JSON,
)
from sqlalchemy.orm import relationship

from app.database import Base
from app.models.work import generate_uuid


class MetadataTemplate(Base):
    """自定义元数据模板."""
    __tablename__ = "metadata_templates"

    id = Column(String(32), primary_key=True, default=generate_uuid)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    fields = Column(JSON, nullable=True)  # [{"key":"title","label":"标题","type":"string","required":true}, ...]
    is_default = Column(Boolean, default=False)
    created_by = Column(String(32), ForeignKey("users.id", ondelete="CASCADE"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    fields_list = relationship(
        "TemplateField",
        back_populates="template",
        cascade="all, delete-orphan",
        order_by="TemplateField.sort_order",
    )

    __table_args__ = (
        Index("idx_mt_created", "created_at"),
    )


class TemplateField(Base):
    """模板字段定义."""
    __tablename__ = "template_fields"

    id = Column(String(32), primary_key=True, default=generate_uuid)
    template_id = Column(String(32), ForeignKey("metadata_templates.id", ondelete="CASCADE"), nullable=False)
    field_key = Column(String(100), nullable=False)
    label = Column(String(200), nullable=False)
    field_type = Column(String(20), nullable=False)  # string/number/date/boolean/text/choice
    required = Column(Boolean, default=False)
    default_value = Column(JSON, nullable=True)
    choices = Column(JSON, nullable=True)  # for choice type
    sort_order = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    template = relationship("MetadataTemplate", back_populates="fields_list")

    __table_args__ = (
        Index("idx_tf_template", "template_id"),
        Index("idx_tf_template_key", "template_id", "field_key"),
    )
