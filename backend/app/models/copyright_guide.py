"""版权登记指南数据模型."""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Float, Boolean, Text, Integer, JSON
from app.database import Base


class CopyrightRegistration(Base):
    __tablename__ = "cr_guide_registrations"
    """版权登记记录."""

    __tablename__ = "copyright_registrations"

    id = Column(String(32), primary_key=True, default=lambda: uuid.uuid4().hex)
    user_id = Column(String(32), nullable=False, index=True)
    work_id = Column(String(32), nullable=True, index=True)
    title = Column(String(500), nullable=False)
    work_type = Column(String(50), nullable=False)  # "art", "photo", "illustration", "music", "writing"
    registration_type = Column(String(50), default="domestic")  # "domestic", "bernis_convention"
    status = Column(String(20), default="draft")  # draft / submitted / approved / rejected
    application_number = Column(String(100), nullable=True)
    registration_date = Column(DateTime, nullable=True)
    certificate_url = Column(String(500), nullable=True)
    fee_yuan = Column(Float, default=0)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class RegistrationGuide(Base):
    """版权登记指南 — 按作品类型提供步骤."""

    __tablename__ = "registration_guides"

    id = Column(String(32), primary_key=True, default=lambda: uuid.uuid4().hex)
    work_type = Column(String(50), nullable=False, unique=True)
    title_zh = Column(String(200), nullable=False)
    steps = Column(JSON, nullable=False)  # [{"step": 1, "title": "...", "description": "...", "required_files": [...]}]
    estimated_days = Column(Integer, default=30)
    estimated_fee_yuan = Column(Float, default=200)
    is_active = Column(Boolean, default=True)
