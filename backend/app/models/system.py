"""系统管理数据模型.

表:
- system_settings: 系统设置 (key-value)
- audit_logs: 审计日志 (90天自动清理)
- backup_records: 备份记录
- dictionary_groups: 字典分组
- dictionary_items: 字典条目
- users: 用户账号中心
- user_login_history: 登录历史
- notifications: 通知消息
- plugins: 插件注册表 (P2.7.8)
- email_verifications: 邮箱验证码 (P2.7.11)
- password_resets: 密码重置令牌 (P2.7.12)
"""

from datetime import datetime

from sqlalchemy import Column, String, Text, DateTime, Boolean, Integer, BigInteger, Index, JSON, ForeignKey, Float
from sqlalchemy.orm import relationship

from app.database import Base
from app.models.work import generate_uuid


class SystemSetting(Base):
    """系统设置表 (key-value)."""
    __tablename__ = "system_settings"

    key = Column(String(200), primary_key=True)
    value = Column(Text, nullable=True)
    category = Column(String(50), default="general")
    description = Column(Text, nullable=True)
    is_public = Column(Boolean, default=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class AuditLog(Base):
    """审计日志 (90天自动清理)."""
    __tablename__ = "audit_logs"

    id = Column(String(32), primary_key=True, default=generate_uuid)
    user_id = Column(String(32), nullable=True, index=True)
    action = Column(String(200), nullable=False)
    detail = Column(Text, nullable=True)
    module = Column(String(50), nullable=True)
    ip = Column(String(50), nullable=True)
    user_agent = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("idx_audit_logs_created", "created_at"),
        Index("idx_audit_logs_action", "action"),
        Index("idx_audit_logs_user", "user_id"),
    )


class BackupRecord(Base):
    """备份记录."""
    __tablename__ = "backup_records"

    id = Column(String(32), primary_key=True, default=generate_uuid)
    path = Column(String(2000), nullable=False)
    size = Column(BigInteger, default=0)  # bytes
    type = Column(String(20), default="manual")  # manual/auto/scheduled
    includes_files = Column(Boolean, default=True)
    incremental = Column(Boolean, default=False)
    encrypted = Column(Boolean, default=False)
    schedule_cron = Column(String(100), nullable=True)  # cron expression
    status = Column(String(20), default="completed")  # completed/failed/in_progress
    restored_from = Column(String(2000), nullable=True)  # 从哪个备份恢复
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("idx_backup_created", "created_at"),
    )


# -- 统一字典数据中心 --

class DictionaryGroup(Base):
    """字典分组."""
    __tablename__ = "dictionary_groups"

    id = Column(String(32), primary_key=True, default=generate_uuid)
    group_key = Column(String(100), unique=True, nullable=False, index=True)
    group_name = Column(String(200), nullable=False)
    module = Column(String(50), nullable=False, index=True)
    description = Column(Text, nullable=True)
    is_extensible = Column(Boolean, default=False)
    sort_order = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    items = relationship("DictionaryItem", back_populates="group", cascade="all, delete-orphan")


class DictionaryItem(Base):
    """字典条目."""
    __tablename__ = "dictionary_items"

    id = Column(String(32), primary_key=True, default=generate_uuid)
    group_key = Column(String(100), ForeignKey("dictionary_groups.group_key", ondelete="CASCADE"), nullable=False, index=True)
    item_key = Column(String(100), nullable=False)
    item_value = Column(String(200), nullable=False)
    item_value_en = Column(String(200), nullable=True)
    extra = Column(JSON, nullable=True)  # {icon, color, description, parent_key, ...}
    is_active = Column(Boolean, default=True)
    sort_order = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index("idx_dict_items_group", "group_key", "item_key"),
    )

    group = relationship("DictionaryGroup", back_populates="items")


# -- 用户账号中心 --

class User(Base):
    """用户账号表 (替代原 users.json)."""
    __tablename__ = "users"

    id = Column(String(32), primary_key=True, default=generate_uuid)

    # 本地账号
    username = Column(String(100), nullable=False, default="创作者")
    email = Column(String(200), unique=True, nullable=True)
    email_verified = Column(Boolean, default=False)
    password_hash = Column(String(256), nullable=True)

    # Google
    google_id = Column(String(200), unique=True, nullable=True)
    google_email = Column(String(200), nullable=True)
    google_name = Column(String(200), nullable=True)
    google_picture = Column(Text, nullable=True)

    # 微信
    wechat_openid = Column(String(200), nullable=True)
    wechat_unionid = Column(String(200), nullable=True)
    wechat_nickname = Column(String(200), nullable=True)
    wechat_avatar = Column(Text, nullable=True)

    # 抖音
    douyin_openid = Column(String(200), nullable=True)
    douyin_unionid = Column(String(200), nullable=True)
    douyin_nickname = Column(String(200), nullable=True)
    douyin_avatar = Column(Text, nullable=True)

    # 联系方式
    phone = Column(String(50), nullable=True)
    phone_verified = Column(Boolean, default=False)

    # 头像 URL (通用)
    avatar_url = Column(Text, nullable=True)

    # 通知偏好
    notification_prefs = Column(JSON, default=dict)

    # 账号状态
    role = Column(String(20), default="user")  # user/admin/local
    status = Column(String(20), default="active")  # active/inactive/banned

    # v3 创作者类型 (Onboarding Step1 选择)
    creator_type = Column(String(20), nullable=True)  # illustrator/photographer/video_creator/crafter/musician/writer

    # 登录信息
    last_login_at = Column(DateTime, nullable=True)
    last_login_provider = Column(String(20), nullable=True)  # google/wechat/douyin/email/local
    login_count = Column(Integer, default=0)

    # P2.7.13: Password strength tracking
    password_strength_score = Column(Integer, nullable=True)  # 0-100
    password_updated_at = Column(DateTime, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index("idx_users_email", "email"),
        Index("idx_users_google_id", "google_id"),
    )


class UserLoginHistory(Base):
    """登录历史记录."""
    __tablename__ = "user_login_history"

    id = Column(String(32), primary_key=True, default=generate_uuid)
    user_id = Column(String(32), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    provider = Column(String(20), nullable=False)  # google/wechat/douyin/email/local
    ip = Column(String(50), nullable=True)
    user_agent = Column(Text, nullable=True)
    success = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("idx_login_history_user", "user_id", "created_at"),
    )


# -- 通知中心 --

class Notification(Base):
    """通知消息."""
    __tablename__ = "notifications"

    id = Column(String(32), primary_key=True, default=generate_uuid)
    user_id = Column(String(32), nullable=False, index=True)
    type = Column(String(50), nullable=False)  # cert_ready/scan_result/reminder/renewal/order_update/...
    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=True)
    related_module = Column(String(50), nullable=True)  # notary/monitor/ipr/supply/system
    related_id = Column(String(32), nullable=True)  # 关联数据ID
    channel = Column(String(50), nullable=False)  # websocket/in_app/email/wechat_template
    is_read = Column(Boolean, default=False)
    is_sent = Column(Boolean, default=False)
    sent_at = Column(DateTime, nullable=True)
    read_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("idx_notif_user", "user_id", "is_read", "created_at"),
        Index("idx_notif_type", "type"),
    )


# -- P2.7.8: 插件框架 --

class Plugin(Base):
    """插件注册表."""
    __tablename__ = "plugins"

    id = Column(String(32), primary_key=True, default=generate_uuid)
    name = Column(String(100), nullable=False, index=True)
    display_name = Column(String(200), nullable=False)
    version = Column(String(20), default="1.0.0")
    description = Column(Text, nullable=True)
    author = Column(String(200), nullable=True)
    enabled = Column(Boolean, default=True)
    hooks = Column(JSON, nullable=True)  # ["on_startup", "on_product_create", ...]
    config = Column(JSON, default=dict)  # plugin-specific config
    entry_point = Column(String(500), nullable=True)  # Python module path
    priority = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index("idx_plugins_enabled", "enabled"),
    )


# -- P2.7.11: 邮箱验证 --

class EmailVerification(Base):
    """邮箱验证码."""
    __tablename__ = "email_verifications"

    id = Column(String(32), primary_key=True, default=generate_uuid)
    email = Column(String(200), nullable=False, index=True)
    code = Column(String(6), nullable=False)
    expires_at = Column(DateTime, nullable=False)
    verified = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)


# -- P2.7.12: 密码重置 --

class PasswordReset(Base):
    """密码重置令牌."""
    __tablename__ = "password_resets"

    id = Column(String(32), primary_key=True, default=generate_uuid)
    email = Column(String(200), nullable=False, index=True)
    token = Column(String(128), nullable=False, unique=True, index=True)
    expires_at = Column(DateTime, nullable=False)
    used = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)


# -- v3 免责声明管理 --

class Disclaimer(Base):
    """免责声明定义表 (7项核心声明 + 可扩展)."""
    __tablename__ = "disclaimers"

    id = Column(String(32), primary_key=True, default=generate_uuid)
    disclaimer_key = Column(String(100), nullable=False, unique=True, index=True)
    # no_attorney_relationship / no_legal_advice / no_guarantee /
    # pod_ip_warning / ai_content_label / monitor_limitation / jurisdiction_limitation
    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=False)
    category = Column(String(50), nullable=False)  # legal/ip/warning
    priority = Column(Integer, default=0)  # 展示优先级
    is_required = Column(Boolean, default=False)  # 是否必须确认
    is_active = Column(Boolean, default=True)
    display_mode = Column(String(20), default="banner")  # modal/banner/footer
    trigger_pages = Column(JSON, nullable=True)  # ["ipr", "monitor", "pod_channel"]
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    acceptances = relationship("DisclaimerAcceptance", back_populates="disclaimer", cascade="all, delete-orphan")


class DisclaimerAcceptance(Base):
    """免责声明接受记录."""
    __tablename__ = "disclaimer_acceptances"

    id = Column(String(32), primary_key=True, default=generate_uuid)
    user_id = Column(String(32), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    disclaimer_id = Column(String(32), ForeignKey("disclaimers.id", ondelete="CASCADE"), nullable=False)
    accepted_at = Column(DateTime, default=datetime.utcnow)
    accepted_version = Column(String(20), default="1.0")
    context = Column(String(100), nullable=True)  # trigger_page

    disclaimer = relationship("Disclaimer", back_populates="acceptances")

    __table_args__ = (
        Index("idx_da_user", "user_id", "disclaimer_id"),
    )
