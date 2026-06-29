"""侵权监测数据模型."""

from datetime import datetime

from sqlalchemy import (
    Column, String, Text, DateTime, Boolean, ForeignKey, Index, Float, Integer, JSON,
)
from sqlalchemy.orm import relationship

from app.database import Base
from app.models.work import generate_uuid


class MonitorTask(Base):
    """监测任务表."""
    __tablename__ = "monitor_tasks"

    id = Column(String(32), primary_key=True, default=generate_uuid)
    work_id = Column(String(32), ForeignKey("works.id", ondelete="CASCADE"), nullable=False)
    search_type = Column(String(20), nullable=False, default="image")  # image/text/code
    platform = Column(String(50), nullable=False)  # baidu/google/copyscape/github
    interval = Column(String(20), default="manual")  # manual/daily/weekly/monthly
    last_run = Column(DateTime, nullable=True)
    next_run = Column(DateTime, nullable=True)
    status = Column(String(20), default="active")  # active/paused/completed
    quota_used_today = Column(Integer, default=0)
    priority_score = Column(Float, default=0.0)  # P1.3.7: 扫描优先级评分 (0-100)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    results = relationship("MonitorResult", back_populates="task", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_monitor_task_work", "work_id"),
        Index("idx_monitor_task_status", "status"),
        Index("idx_monitor_work_platform", "work_id", "platform"),
    )


class MonitorResult(Base):
    """监测结果表."""
    __tablename__ = "monitor_results"

    id = Column(String(32), primary_key=True, default=generate_uuid)
    task_id = Column(String(32), ForeignKey("monitor_tasks.id", ondelete="CASCADE"), nullable=False)
    matched_url = Column(String(2000), nullable=False)
    matched_title = Column(String(500), nullable=True)
    similarity = Column(Float, default=0.0)  # 相似度 0-100
    matched_thumbnail_url = Column(String(2000), nullable=True)
    screenshot_path = Column(String(2000), nullable=True)
    found_at = Column(DateTime, default=datetime.utcnow)
    status = Column(String(20), default="pending_review")
    # pending_review/infringing/ignored/whitelisted
    action_taken = Column(String(50), nullable=True)
    # generate_complaint/export_evidence/mark_handled
    ignore_reason = Column(Text, nullable=True)  # 误报忽略原因
    notes = Column(Text, nullable=True)
    is_mock = Column(Integer, default=0)  # 1 = mock data, 0 = real
    match_type = Column(String(50), nullable=True)  # image/audio/text/video_fingerprint/text_similarity
    confidence = Column(Float, default=0.0)  # 0-100 confidence score for the match
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    task = relationship("MonitorTask", back_populates="results")

    __table_args__ = (
        Index("idx_result_task", "task_id"),
        Index("idx_result_status", "status"),
        Index("idx_result_similarity", "similarity"),
        Index("idx_result_match_type", "match_type"),
    )


class EvidencePackage(Base):
    """维权证据包."""
    __tablename__ = "evidence_packages"

    id = Column(String(32), primary_key=True, default=generate_uuid)
    work_id = Column(String(32), ForeignKey("works.id", ondelete="CASCADE"), nullable=False)
    related_result_ids = Column(JSON, nullable=True)  # 关联的监测结果 ID 列表
    package_path = Column(String(2000), nullable=False)  # ZIP 文件路径
    package_type = Column(String(50), default="complaint")  # complaint/lawyer_letter/evidence
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("idx_evidence_work", "work_id"),
    )


class ScanSchedule(Base):
    """扫描计划表."""
    __tablename__ = "scan_schedules"

    id = Column(String(32), primary_key=True, default=generate_uuid)
    name = Column(String(200), nullable=False)
    is_enabled = Column(Boolean, default=True)
    scan_type = Column(String(20), nullable=False)  # image/text/code
    scan_scope = Column(String(20), default="all")  # all/project/tag
    scope_value = Column(String(500), nullable=True)  # 项目ID或标签名
    cron_expression = Column(String(100), nullable=False)
    last_run_at = Column(DateTime, nullable=True)
    next_run_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index("idx_scan_schedule_enabled", "is_enabled"),
    )
