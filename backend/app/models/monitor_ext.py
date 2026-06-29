"""侵权监测扩展数据模型 (P2.3).

表:
- LocalFingerprint: 本地视觉指纹存储
- BrandWatch: 品牌监测注册
- DomainWatch: 域名监测注册
- WhitelistSuggestion: 白名单自动建议
"""

from datetime import datetime

from sqlalchemy import (
    Column, String, Text, DateTime, Boolean, ForeignKey, Index, Float, Integer, JSON,
)
from sqlalchemy.orm import relationship

from app.database import Base
from app.models.work import generate_uuid


class LocalFingerprint(Base):
    """本地视觉指纹表 — 存储 dHash/pHash/wHash 等感知哈希."""
    __tablename__ = "local_fingerprints"

    id = Column(String(32), primary_key=True, default=generate_uuid)
    work_id = Column(String(32), ForeignKey("works.id", ondelete="CASCADE"), nullable=False)
    hash_type = Column(String(20), nullable=False)  # dhash/phash/whash/average_hash
    hash_value = Column(String(256), nullable=False)  # 哈希字符串 (hex)
    hash_size = Column(Integer, default=16)  # 哈希尺寸 e.g. 16x16
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("idx_fp_work_id", "work_id"),
        Index("idx_fp_hash_type", "hash_type"),
        Index("idx_fp_work_type", "work_id", "hash_type", unique=True),
    )


class BrandWatch(Base):
    """品牌监测表 — 注册需要监测的品牌."""
    __tablename__ = "brand_watches"

    id = Column(String(32), primary_key=True, default=generate_uuid)
    brand_name = Column(String(200), nullable=False)
    brand_logo_path = Column(String(2000), nullable=True)  # Logo 文件路径 (用于模板匹配)
    keywords = Column(JSON, nullable=True)  # 关联关键词列表
    platforms = Column(JSON, nullable=True)  # 监测平台列表 ["taobao","jd","pinduoduo","amazon"]
    is_active = Column(Boolean, default=True)
    last_scan_at = Column(DateTime, nullable=True)
    total_matches = Column(Integer, default=0)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    scans = relationship("BrandScanResult", back_populates="brand", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_brand_active", "is_active"),
    )


class BrandScanResult(Base):
    """品牌扫描结果表."""
    __tablename__ = "brand_scan_results"

    id = Column(String(32), primary_key=True, default=generate_uuid)
    brand_id = Column(String(32), ForeignKey("brand_watches.id", ondelete="CASCADE"), nullable=False)
    platform = Column(String(50), nullable=False)
    item_url = Column(String(2000), nullable=False)
    item_title = Column(String(500), nullable=True)
    similarity = Column(Float, default=0.0)  # 0-100
    thumbnail_url = Column(String(2000), nullable=True)
    found_at = Column(DateTime, default=datetime.utcnow)
    status = Column(String(20), default="pending_review")  # pending_review/infringing/ignored
    notes = Column(Text, nullable=True)

    brand = relationship("BrandWatch", back_populates="scans")

    __table_args__ = (
        Index("idx_brand_scan_brand", "brand_id"),
        Index("idx_brand_scan_status", "status"),
    )


class DomainWatch(Base):
    """域名监测表 — 注册需要监测的域名."""
    __tablename__ = "domain_watches"

    id = Column(String(32), primary_key=True, default=generate_uuid)
    domain = Column(String(500), nullable=False)
    target_brand = Column(String(200), nullable=True)  # 关联品牌名
    watch_type = Column(String(20), default="whois")  # whois/typo/phishing
    is_active = Column(Boolean, default=True)
    last_checked_at = Column(DateTime, nullable=True)
    registrar = Column(String(200), nullable=True)
    creation_date = Column(DateTime, nullable=True)
    expiry_date = Column(DateTime, nullable=True)
    status_notes = Column(Text, nullable=True)  # WHOIS 状态备注
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index("idx_domain_active", "is_active"),
        Index("idx_domain_watch_domain", "domain"),
    )


class WhitelistSuggestion(Base):
    """白名单自动建议表 — 基于用户行为模式学习."""
    __tablename__ = "whitelist_suggestions"

    id = Column(String(32), primary_key=True, default=generate_uuid)
    pattern_url = Column(String(2000), nullable=False)  # URL 或域名模式
    pattern_type = Column(String(20), default="domain")  # domain/url/regex
    occurrence_count = Column(Integer, default=1)
    last_seen_at = Column(DateTime, default=datetime.utcnow)
    suggested_at = Column(DateTime, default=datetime.utcnow)
    status = Column(String(20), default="suggested")  # suggested/accepted/declined
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("idx_whitelist_status", "status"),
    )
