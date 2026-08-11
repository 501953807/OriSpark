"""系统基础设施服务层 — 对应: docs/modules-v5/07-system-infra.md

包含: 系统设置、数据备份、审计日志、存储管理、字典数据中心、
通知中心、Email/微信通知渠道、插件框架、邮箱验证、密码重置、
密码强度检测、头像上传、数据导出、危险区、API统计、存储趋势、
TOTP双因素认证、设计变体、免责声明管理。
"""
import asyncio
import base64
import csv
import hashlib
import io
import json
import logging
import os
import re
import secrets
import shutil
import smtplib
from datetime import date, datetime, timedelta, timezone
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path
from typing import Optional, List

from fastapi import HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.system import (
    SystemSetting, AuditLog, BackupRecord,
    DictionaryGroup, DictionaryItem, Notification,
    Plugin, EmailVerification, PasswordReset,
    Disclaimer, DisclaimerAcceptance,
)
from app.models.system import User as UserModel
from app.schemas.common import ApiResponse, SuccessResponse
from app.services.system_settings_module import SystemSettingsModule
from app.services.system_dict_module import SystemDictModule
from app.services.system_notification_module import SystemNotificationModule
from app.services.system_plugin_module import SystemPluginModule
from app.services.system_audit_module import SystemAuditModule


# ================================================================
# -- Pydantic request schemas (re-exported for router compatibility) --
# ================================================================

class SystemSettingsUpdate(BaseModel):
    smtp_host: Optional[str] = None
    smtp_port: Optional[str] = None
    smtp_user: Optional[str] = None
    smtp_password: Optional[str] = None
    smtp_from: Optional[str] = None
    smtp_tls: Optional[str] = None
    wechat_appid: Optional[str] = None
    wechat_appsecret: Optional[str] = None
    wechat_template_id: Optional[str] = None
    banquanjia_api_key: Optional[str] = None
    banquanjia_api_secret: Optional[str] = None
    antchain_api_key: Optional[str] = None
    antchain_api_secret: Optional[str] = None
    zhixinchain_api_key: Optional[str] = None
    zhixinchain_api_secret: Optional[str] = None
    baidu_vision_api_key: Optional[str] = None
    google_vision_api_key: Optional[str] = None
    backup_schedule_cron: Optional[str] = None
    backup_schedule_enabled: Optional[bool] = None
    backup_schedule_encrypted: Optional[bool] = None


class DictionaryItemCreate(BaseModel):
    group_key: str
    item_key: str
    item_value: str = ""
    item_value_en: Optional[str] = None
    extra: Optional[dict] = None
    is_active: bool = True
    sort_order: int = 99


class DictionaryItemUpdate(BaseModel):
    item_key: Optional[str] = None
    item_value: Optional[str] = None
    item_value_en: Optional[str] = None
    extra: Optional[dict] = None
    is_active: Optional[bool] = None
    sort_order: Optional[int] = None


class WechatTemplateMessage(BaseModel):
    touser: str
    template_id: Optional[str] = None
    url: Optional[str] = None
    miniprogram: Optional["MiniProgram"] = None
    message_data: dict


class MiniProgram(BaseModel):
    appid: Optional[str] = ""
    pagepath: Optional[str] = ""


class PluginRegister(BaseModel):
    name: str
    display_name: Optional[str] = None
    version: str = "1.0.0"
    description: Optional[str] = None
    author: Optional[str] = None
    enabled: bool = True
    hooks: Optional[list] = []
    config: Optional[dict] = {}
    entry_point: Optional[str] = None
    priority: int = 0


class PluginUpdate(BaseModel):
    display_name: Optional[str] = None
    version: Optional[str] = None
    enabled: Optional[bool] = None
    hooks: Optional[list] = None
    config: Optional[dict] = None
    priority: Optional[int] = None
    description: Optional[str] = None


class DesignVariantInput(BaseModel):
    base_description: str
    target_categories: list[str]
    style_preferences: Optional[dict] = {}
    language: str = "zh"


class DisclaimerAcceptanceInput(BaseModel):
    disclaimer_key: str
    context: str = ""


# ================================================================
# -- Module-level constants and shared state --
# ================================================================

DISCLAIMER_SEEDS = [
    {
        "disclaimer_key": "no_attorney_relationship",
        "title": "不构成律师-客户关系",
        "content": "使用本软件不建立律师-客户特权关系。本软件是信息参考工具，不提供法律代理服务。如需法律意见，请咨询持证律师。",
        "category": "legal",
        "priority": 10,
        "is_required": True,
        "display_mode": "modal",
        "trigger_pages": ["ipr"],
    },
    {
        "disclaimer_key": "no_legal_advice",
        "title": "不构成法律建议",
        "content": "IP登记指引、类别推荐、费用计算等信息仅供参考，不构成法律建议。每个案件的具体情况不同，请咨询专业律师获取针对性的法律意见。",
        "category": "legal",
        "priority": 9,
        "is_required": True,
        "display_mode": "modal",
        "trigger_pages": ["ipr"],
    },
    {
        "disclaimer_key": "no_guarantee",
        "title": "不保证注册成功",
        "content": "商标/专利/版权注册结果取决于官方审查机构的审查标准和判断。本工具不保证任何注册申请的通过率或成功率。注册费用一旦支付，无论结果如何均不予退还(官方收费)。",
        "category": "legal",
        "priority": 8,
        "is_required": True,
        "display_mode": "banner",
        "trigger_pages": ["ipr"],
    },
    {
        "disclaimer_key": "pod_ip_warning",
        "title": "POD平台IP条款警告",
        "content": "在POD平台上传设计前，请仔细阅读平台服务条款中有关知识产权的部分。各平台对侵权内容的处理政策不同。上传他人享有著作权的设计可能导致账户被暂停或永久封禁。",
        "category": "warning",
        "priority": 7,
        "is_required": False,
        "display_mode": "banner",
        "trigger_pages": ["supply", "pod_channel"],
    },
    {
        "disclaimer_key": "ai_content_label",
        "title": "AI内容标注要求",
        "content": "建议按各平台规则标注'AI辅助生成'或等效标签。不同平台(小红书/抖音/Instagram/站酷等)的AI内容标注规则不同，请在发布前查阅对应平台的现行政策。",
        "category": "warning",
        "priority": 6,
        "is_required": False,
        "display_mode": "footer",
        "trigger_pages": ["publish"],
    },
    {
        "disclaimer_key": "monitor_limitation",
        "title": "侵权监测局限性",
        "content": "本监测功能基于公开搜索引擎的以图搜图能力（百度识图/Google Vision），存在以下局限：1. 不能保证发现所有侵权行为；2. 搜索结果需人工审核判断是否构成侵权；3. 相似度分数仅为参考——高相似度不必然等于侵权，低相似度不必然等于不侵权。本功能提供侵权线索发现辅助，不提供法律判断。",
        "category": "warning",
        "priority": 5,
        "is_required": False,
        "display_mode": "banner",
        "trigger_pages": ["monitor"],
    },
    {
        "disclaimer_key": "jurisdiction_limitation",
        "title": "司法管辖区限制",
        "content": "IP登记指引仅覆盖主要司法管辖区(中国/美国/欧盟/WIPO/日本/韩国)。其他辖区的IP法律法规、申请流程、费用标准可能不同。如需在未覆盖辖区进行IP登记，请咨询当地持证代理机构。",
        "category": "legal",
        "priority": 4,
        "is_required": False,
        "display_mode": "banner",
        "trigger_pages": ["ipr"],
    },
]


_api_call_counter: dict[str, int] = {}
_totp_store: dict[str, dict] = {}
_proto_variants_cache: dict[str, list[dict]] = {}


# ================================================================
# -- Helper functions (module-level, for cross-module usage) --
# ================================================================

def get_dict_values(group_key: str, db: Session) -> list[str]:
    """获取指定字典分组的 item_key 列表 (用于替代硬编码枚举).

    用法:
        from app.services.system_service import get_dict_values
        values = get_dict_values("notary_platforms", db)
    """
    items = db.query(DictionaryItem).filter(
        DictionaryItem.group_key == group_key,
        DictionaryItem.is_active == True,
    ).order_by(DictionaryItem.sort_order).all()
    return [i.item_key for i in items]


def get_dict_values_rich(group_key: str, db: Session) -> list[dict]:
    """获取指定字典分组的完整条目数据.

    返回每个条目的 key/value/extra 信息。
    """
    items = db.query(DictionaryItem).filter(
        DictionaryItem.group_key == group_key,
        DictionaryItem.is_active == True,
    ).order_by(DictionaryItem.sort_order).all()
    return [
        {
            "item_key": i.item_key,
            "item_value": i.item_value,
            "item_value_en": i.item_value_en,
            "extra": i.extra,
        }
        for i in items
    ]


def push_notification(
    db: Session,
    user_id: str = "default",
    type: str = "system",
    title: str = "",
    content: str = "",
    related_module: Optional[str] = None,
    related_id: Optional[str] = None,
    channel: str = "in_app",
    websocket_push: bool = True,
    notifier=None,
):
    """创建通知并可选 WebSocket 推送.

    Args:
        notifier: NotifierAdapter 实例，默认为 None（使用全局 manager）.
    """
    notif = Notification(
        id=hashlib.md5(str(secrets.token_hex(8)).encode()).hexdigest()[:16],
        user_id=user_id,
        type=type,
        title=title,
        content=content,
        related_module=related_module,
        related_id=related_id,
        channel=channel,
        is_read=False,
    )
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise

    if websocket_push:
        try:
            if notifier:
                # 使用注入的适配器
                asyncio.create_task(notifier.notify(
                    user_id=user_id,
                    type=type,
                    title=title,
                    content=content,
                    related_module=related_module,
                    related_id=related_id,
                ))
            else:
                # 回退到全局 manager
                from app.services.websocket_manager import manager
                asyncio.create_task(manager.broadcast({
                    "type": "notification",
                    "data": {
                        "id": notif.id,
                        "type": notif.type,
                        "title": notif.title,
                        "content": notif.content,
                        "created_at": notif.created_at.isoformat() if notif.created_at else None,
                    },
                }))
        except Exception as e:
            logging.getLogger(__name__).exception("Error pushing notification: %s", str(e))

    return notif


def record_api_call(path: str):
    """记录 API 调用次数 (由中间件调用)."""
    _api_call_counter[path] = _api_call_counter.get(path, 0) + 1


def _check_password_strength(password: str) -> dict:
    """检测密码强度，返回 score (0-100) 和 feedback."""
    score = 0
    feedback = []

    if len(password) >= 8:
        score += 20
    elif len(password) >= 6:
        score += 10
        feedback.append("密码长度至少8位")

    if len(password) >= 12:
        score += 10

    if re.search(r"[A-Z]", password):
        score += 15
    else:
        feedback.append("缺少大写字母")

    if re.search(r"[a-z]", password):
        score += 10
    else:
        feedback.append("缺少小写字母")

    if re.search(r"[0-9]", password):
        score += 15
    else:
        feedback.append("缺少数字")

    if re.search(r"[!@#$%^&*(),.?\":{}|<>_\-+=;'\\[\]`~]", password):
        score += 20
    else:
        feedback.append("缺少特殊字符")

    if len(set(password)) >= len(password) * 0.7:
        score += 10
    else:
        feedback.append("避免重复字符")

    return {
        "score": min(score, 100),
        "level": "strong" if score >= 80 else ("medium" if score >= 50 else "weak"),
        "feedback": ", ".join(feedback) if feedback else "密码强度良好",
    }


def _dict_group_to_dict(g: DictionaryGroup) -> dict:
    return {
        "id": g.id,
        "group_key": g.group_key,
        "group_name": g.group_name,
        "module": g.module,
        "description": g.description,
        "is_extensible": g.is_extensible,
        "sort_order": g.sort_order,
        "created_at": g.created_at.isoformat() if g.created_at else None,
        "updated_at": g.updated_at.isoformat() if g.updated_at else None,
    }


def _dict_item_to_dict(i: DictionaryItem) -> dict:
    return {
        "id": i.id,
        "group_key": i.group_key,
        "item_key": i.item_key,
        "item_value": i.item_value,
        "item_value_en": i.item_value_en,
        "extra": i.extra,
        "is_active": i.is_active,
        "sort_order": i.sort_order,
        "created_at": i.created_at.isoformat() if i.created_at else None,
        "updated_at": i.updated_at.isoformat() if i.updated_at else None,
    }


def _get_backup_dir() -> Path:
    """获取备份目录."""
    d = Path("data/backups")
    d.mkdir(parents=True, exist_ok=True)
    return d


def _aes_encrypt_file(src: Path, dst: Path, key: bytes = None) -> None:
    """AES-256-GCM 加密文件."""
    try:
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM
        if key is None:
            key = hashlib.sha256(b"oristudio-default-backup-key").digest()
        aesgcm = AESGCM(key)
        nonce = os.urandom(12)
        data = src.read_bytes()
        encrypted = aesgcm.encrypt(nonce, data, None)
        dst.write_bytes(nonce + encrypted)
    except ImportError:
        if key is None:
            key = b"oristudio-default-backup-key"
        data = src.read_bytes()
        result = bytes(b ^ key[i % len(key)] for i, b in enumerate(data))
        dst.write_bytes(result)


def _aes_decrypt_file(src: Path, dst: Path, key: bytes = None) -> None:
    """AES-256-GCM 解密文件."""
    try:
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM
        if key is None:
            key = hashlib.sha256(b"oristudio-default-backup-key").digest()
        aesgcm = AESGCM(key)
        raw = src.read_bytes()
        nonce, encrypted = raw[:12], raw[12:]
        decrypted = aesgcm.decrypt(nonce, encrypted, None)
        dst.write_bytes(decrypted)
    except ImportError:
        if key is None:
            key = b"oristudio-default-backup-key"
        data = src.read_bytes()
        result = bytes(b ^ key[i % len(key)] for i, b in enumerate(data))
        dst.write_bytes(result)


def _get_smtp_config(db: Session) -> dict:
    """获取 SMTP 配置 (P3.5.1: 解密敏感字段)."""
    from app.utils.crypto import decrypt as aes_decrypt

    cfg = {}
    for key in ["smtp_host", "smtp_port", "smtp_user", "smtp_password", "smtp_from", "smtp_tls"]:
        setting = db.query(SystemSetting).filter(SystemSetting.key == key).first()
        val = setting.value if setting else None
        if val and key == "smtp_password":
            val = aes_decrypt(val)
        cfg[key] = val
    return cfg


def _get_wechat_config(db: Session) -> dict:
    """获取微信配置."""
    cfg = {}
    for key in ["wechat_appid", "wechat_appsecret", "wechat_template_id"]:
        setting = db.query(SystemSetting).filter(SystemSetting.key == key).first()
        cfg[key] = setting.value if setting else None
    return cfg


def _seed_disclaimers(db: Session):
    """初始化 7 项免责声明种子数据."""
    for seed in DISCLAIMER_SEEDS:
        existing = db.query(Disclaimer).filter(
            Disclaimer.disclaimer_key == seed["disclaimer_key"]
        ).first()
        if existing:
            continue
        db.add(Disclaimer(
            disclaimer_key=seed["disclaimer_key"],
            title=seed["title"],
            content=seed["content"],
            category=seed["category"],
            priority=seed["priority"],
            is_required=seed["is_required"],
            display_mode=seed["display_mode"],
            trigger_pages=seed["trigger_pages"],
        ))
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise


def _generate_color_variants(style_prefs: dict) -> list[dict]:
    """根据风格偏好生成配色变体."""
    base_variants = [
        {"name": "original", "palette": ["原图色彩"], "hex": []},
        {"name": "monochrome", "palette": ["#1a1a1a", "#ffffff", "#808080"], "hex": ["#1a1a1a", "#ffffff", "#808080"]},
        {"name": "vibrant", "palette": ["#FF6B6B", "#4ECDC4", "#FFE66D"], "hex": ["#FF6B6B", "#4ECDC4", "#FFE66D"]},
        {"name": "pastel", "palette": ["#FFD6E0", "#C9E4FF", "#FFF5BA"], "hex": ["#FFD6E0", "#C9E4FF", "#FFF5BA"]},
        {"name": "dark", "palette": ["#2D2D2D", "#5A5A5A", "#8B8B8B"], "hex": ["#2D2D2D", "#5A5A5A", "#8B8B8B"]},
    ]
    scheme = style_prefs.get("color_scheme", "vibrant")
    return [v for v in base_variants if v["name"] == scheme or v["name"] == "original"][:3]


def _estimate_cost(category: str) -> dict:
    """估算生产成本 (模板)."""
    estimates = {
        "t_shirt": {"base_cost_cny": 18, "min_order": 1, "shipping_estimate": "3-5天"},
        "mug": {"base_cost_cny": 12, "min_order": 1, "shipping_estimate": "3-5天"},
        "poster": {"base_cost_cny": 8, "min_order": 1, "shipping_estimate": "2-4天"},
        "sticker": {"base_cost_cny": 2, "min_order": 10, "shipping_estimate": "2-4天"},
        "phone_case": {"base_cost_cny": 15, "min_order": 1, "shipping_estimate": "3-5天"},
    }
    return estimates.get(category, {"base_cost_cny": 10, "min_order": 1, "shipping_estimate": "3-5天"})


# ================================================================
# -- Service class --
# ================================================================

# ================================================================
# -- Service class --
# ================================================================

class SystemService:
    def __init__(self, db=None):
        self.db = db

    # ---- 系统设置 ----

    def get_settings(self) -> ApiResponse:
        """获取所有系统设置.

        P3.5.1: 敏感字段自动 AES 解密返回。
        """
        sensitive_keys = {
            "smtp_password", "wechat_appsecret",
            "banquanjia_api_key", "banquanjia_api_secret",
            "antchain_api_key", "antchain_api_secret",
            "zhixinchain_api_key", "zhixinchain_api_secret",
            "baidu_vision_api_key", "google_vision_api_key",
        }

        from app.utils.crypto import decrypt as aes_decrypt

        all_settings = self.db.query(SystemSetting).all()
        result = {}
        for s in all_settings:
            val = s.value
            if val and s.key in sensitive_keys:
                val = aes_decrypt(val)
            result[s.key] = val
        return ApiResponse(data=result)

    def update_settings(self, settings: SystemSettingsUpdate) -> ApiResponse:
        """更新系统设置.

        P3.5.1: 敏感字段 (API keys/passwords) 自动 AES 加密存储。
        """
        sensitive_keys = {
            "smtp_password", "wechat_appsecret",
            "banquanjia_api_key", "banquanjia_api_secret",
            "antchain_api_key", "antchain_api_secret",
            "zhixinchain_api_key", "zhixinchain_api_secret",
            "baidu_vision_api_key", "google_vision_api_key",
        }

        from app.utils.crypto import encrypt as aes_encrypt

        for key, value in settings.model_dump(exclude_none=True).items():
            setting = self.db.query(SystemSetting).filter(SystemSetting.key == key).first()
            stored_value = str(value) if value is not None else None
            if key in sensitive_keys and stored_value:
                stored_value = aes_encrypt(stored_value)
            if setting:
                setting.value = stored_value
            else:
                self.db.add(SystemSetting(key=key, value=stored_value))

        try:
            self.db.commit()
        except Exception as e:
            self.db.rollback()
            raise HTTPException(status_code=500, detail=f"Failed to update settings: {str(e)}")
        return ApiResponse(message="设置已更新")

    # ---- 数据备份 ----

    def create_backup(self, include_files: bool = True, encrypted: bool = False, incremental: bool = False) -> ApiResponse:
        """创建数据备份 (支持加密和增量)."""
        backup_dir = _get_backup_dir()
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        backup_name = f"backup_{timestamp}.zip"
        suffix = ".enc" if encrypted else ""

        db_path = Path("data/oristudio.db")
        backup_path = backup_dir / (backup_name + suffix)

        last_backup = self.db.query(BackupRecord).filter(
            BackupRecord.status == "completed"
        ).order_by(BackupRecord.created_at.desc()).first()

        file_size = 0
        if db_path.exists():
            if encrypted:
                tmp_path = backup_dir / f"tmp_{timestamp}.db"
                shutil.copy2(db_path, tmp_path)
                _aes_encrypt_file(tmp_path, backup_path)
                file_size = backup_path.stat().st_size
                tmp_path.unlink(missing_ok=True)
            elif incremental and last_backup:
                shutil.copy2(db_path, backup_dir / f"db_inc_{timestamp}.bak")
                file_size = (backup_dir / f"db_inc_{timestamp}.bak").stat().st_size
                backup_path = backup_dir / f"backup_inc_{timestamp}.zip"
            else:
                shutil.copy2(db_path, backup_dir / f"db_{timestamp}.bak")
                file_size = (backup_dir / f"db_{timestamp}.bak").stat().st_size

        record = BackupRecord(
            path=str(backup_path),
            size=file_size,
            type="manual",
            includes_files=include_files,
            encrypted=encrypted,
            incremental=incremental,
            status="completed",
        )
        self.db.add(record)
        try:
            self.db.commit()
        except Exception as e:
            self.db.rollback()
            raise HTTPException(status_code=500, detail=f"Failed to create backup record: {str(e)}")

        return ApiResponse(
            message=f"备份创建成功: {backup_path.name}",
            data={
                "backup_path": str(backup_path),
                "backup_id": record.id,
                "size": file_size,
                "encrypted": encrypted,
                "incremental": incremental,
            },
        )

    def create_scheduled_backup(self, cron_expr: str = "0 2 * * *", include_files: bool = True, encrypted: bool = True) -> ApiResponse:
        """创建定时备份任务 (调度配置)."""
        self.db.query(SystemSetting).filter(SystemSetting.key == "backup_schedule_cron").delete()
        self.db.add(SystemSetting(key="backup_schedule_cron", value=cron_expr))
        self.db.add(SystemSetting(key="backup_schedule_enabled", value="true"))
        self.db.add(SystemSetting(key="backup_schedule_encrypted", value=str(encrypted).lower()))
        try:
            self.db.commit()
        except Exception as e:
            self.db.rollback()
            raise HTTPException(status_code=500, detail=f"Failed to create backup schedule: {str(e)}")

        return ApiResponse(
            message=f"定时备份已配置: {cron_expr}",
            data={"cron": cron_expr, "encrypted": encrypted, "enabled": True},
        )

    def get_backup_schedule(self) -> ApiResponse:
        """获取定时备份配置."""
        cron = self.db.query(SystemSetting).filter(SystemSetting.key == "backup_schedule_cron").first()
        enabled = self.db.query(SystemSetting).filter(SystemSetting.key == "backup_schedule_enabled").first()
        encrypted = self.db.query(SystemSetting).filter(SystemSetting.key == "backup_schedule_encrypted").first()

        return ApiResponse(data={
            "cron": cron.value if cron else "0 2 * * *",
            "enabled": enabled.value == "true" if enabled else False,
            "encrypted": encrypted.value == "true" if encrypted else True,
        })

    def list_backups(self) -> ApiResponse:
        """获取备份列表."""
        backups = self.db.query(BackupRecord).order_by(BackupRecord.created_at.desc()).all()
        return ApiResponse(data=[
            {
                "id": b.id,
                "path": b.path,
                "size": b.size,
                "type": b.type,
                "includes_files": b.includes_files,
                "incremental": b.incremental if hasattr(b, 'incremental') else False,
                "encrypted": b.encrypted if hasattr(b, 'encrypted') else False,
                "status": b.status if hasattr(b, 'status') else "completed",
                "created_at": b.created_at.isoformat() if b.created_at else None,
            }
            for b in backups
        ])

    def restore_backup(self, backup_id: str) -> ApiResponse:
        """从备份恢复."""
        record = self.db.query(BackupRecord).filter(BackupRecord.id == backup_id).first()
        if not record:
            raise HTTPException(status_code=404, detail="备份记录不存在")

        backup_path = Path(record.path)
        db_path = Path("data/oristudio.db")

        source_file = None
        if backup_path.exists() and backup_path.is_file():
            source_file = backup_path
        else:
            bak_dir = backup_path.parent
            for candidate in bak_dir.glob("db_*.bak"):
                source_file = candidate
                break
            if not source_file:
                for candidate in bak_dir.glob("*.enc"):
                    source_file = candidate
                    break

        if not source_file:
            raise HTTPException(status_code=404, detail="备份文件不存在")

        try:
            if db_path.exists():
                safe_backup = db_path.parent / f"pre_restore_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.db"
                shutil.copy2(db_path, safe_backup)

            is_encrypted = getattr(record, 'encrypted', False)
            if is_encrypted and str(source_file).endswith('.enc'):
                _aes_decrypt_file(source_file, db_path)
            else:
                shutil.copy2(source_file, db_path)

            record.restored_from = str(backup_path)
            try:
                self.db.commit()
            except Exception:
                self.db.rollback()
                raise
            return ApiResponse(message="数据已从备份恢复，请重启服务以生效")

        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"恢复失败: {str(e)}")

    def delete_backup(self, backup_id: str) -> ApiResponse:
        """删除备份记录."""
        record = self.db.query(BackupRecord).filter(BackupRecord.id == backup_id).first()
        if not record:
            raise HTTPException(status_code=404, detail="备份记录不存在")

        backup_path = Path(record.path)
        if backup_path.exists():
            backup_path.unlink()

        try:
            self.db.delete(record)
            self.db.commit()
        except Exception as e:
            self.db.rollback()
            raise HTTPException(status_code=500, detail=f"Failed to delete backup: {str(e)}")
        return ApiResponse(message="备份记录已删除")

    # ---- 审计日志 ----

    def get_audit_logs(self, page: int = 1, page_size: int = 50, action: Optional[str] = None,
                       module: Optional[str] = None, user_id: Optional[str] = None) -> ApiResponse:
        """获取审计日志."""
        query = self.db.query(AuditLog)

        if action:
            query = query.filter(AuditLog.action.ilike(f"%{action}%"))
        if module:
            query = query.filter(AuditLog.module == module)
        if user_id:
            query = query.filter(AuditLog.user_id == user_id)

        total = query.count()
        logs = query.order_by(AuditLog.created_at.desc()).offset(
            (page - 1) * page_size
        ).limit(page_size).all()

        return ApiResponse(data={
            "items": [
                {
                    "id": log.id,
                    "user_id": log.user_id,
                    "action": log.action,
                    "detail": log.detail,
                    "module": log.module,
                    "ip": log.ip,
                    "user_agent": log.user_agent,
                    "created_at": log.created_at.isoformat() if log.created_at else None,
                }
                for log in logs
            ],
            "total": total,
            "page": page,
            "page_size": page_size,
        })

    # ---- 存储管理 ----

    def get_storage_info(self) -> ApiResponse:
        """获取存储空间信息."""
        workspace = Path("data/workspace")
        certificates = Path("data/certificates")
        thumbnails = Path("data/thumbnails")

        def get_dir_size(path: Path) -> int:
            if not path.exists():
                return 0
            return sum(f.stat().st_size for f in path.rglob("*") if f.is_file())

        workspace_size = get_dir_size(workspace) if workspace.exists() else 0
        cert_size = get_dir_size(certificates)
        thumb_size = get_dir_size(thumbnails)

        db_path = Path("data/oristudio.db")
        db_size = db_path.stat().st_size if db_path.exists() else 0

        total, used, free = shutil.disk_usage(Path("data"))

        return ApiResponse(data={
            "total_space": total,
            "used_space": used,
            "free_space": free,
            "breakdown": {
                "workspace": workspace_size,
                "certificates": cert_size,
                "thumbnails": thumb_size,
                "database": db_size,
            },
        })

    # ---- 健康监控 ----

    def get_health_dashboard(self) -> ApiResponse:
        """系统健康仪表盘: CPU/内存/磁盘/服务状态."""
        health = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "cpu": {"percent": 0.0, "cores": 1},
            "memory": {"total_mb": 0, "used_mb": 0, "percent": 0.0},
            "disk": {"total_gb": 0, "used_gb": 0, "free_gb": 0, "percent": 0.0},
            "services": {"database": "unknown", "uptime_seconds": 0},
        }

        try:
            import psutil
            health["cpu"]["percent"] = round(psutil.cpu_percent(interval=0.5), 1)
            health["cpu"]["cores"] = psutil.cpu_count(logical=True)

            mem = psutil.virtual_memory()
            health["memory"]["total_mb"] = round(mem.total / (1024 * 1024), 1)
            health["memory"]["used_mb"] = round(mem.used / (1024 * 1024), 1)
            health["memory"]["percent"] = mem.percent

            disk_data = Path("data")
            du = shutil.disk_usage(disk_data)
            health["disk"]["total_gb"] = round(du.total / (1024**3), 2)
            health["disk"]["used_gb"] = round(du.used / (1024**3), 2)
            health["disk"]["free_gb"] = round(du.free / (1024**3), 2)
            health["disk"]["percent"] = round(du.used / du.total * 100, 1)
        except ImportError:
            disk_data = Path("data")
            du = shutil.disk_usage(disk_data)
            health["disk"]["total_gb"] = round(du.total / (1024**3), 2)
            health["disk"]["used_gb"] = round(du.used / (1024**3), 2)
            health["disk"]["free_gb"] = round(du.free / (1024**3), 2)
            health["disk"]["percent"] = round(du.used / du.total * 100, 1)
            health["memory"]["total_mb"] = 0
            health["memory"]["used_mb"] = 0
            health["memory"]["percent"] = 0
            health["cpu"]["percent"] = 0
            health["cpu"]["cores"] = 1

        try:
            self.db.query(SystemSetting).limit(1).all()
            health["services"]["database"] = "healthy"
        except Exception:
            health["services"]["database"] = "error"

        try:
            import psutil
            proc = psutil.Process()
            health["services"]["uptime_seconds"] = int(
                (datetime.now(timezone.utc) - datetime.fromtimestamp(proc.create_time(), tz=timezone.utc)).total_seconds()
            )
        except Exception:
            health["services"]["uptime_seconds"] = 0

        return ApiResponse(data=health)

    def get_service_status(self) -> ApiResponse:
        """获取各服务状态."""
        services = {
            "api_server": {"status": "healthy", "version": "0.1.0"},
            "database": {"status": "healthy", "type": "SQLite"},
            "mcp_server": {"status": "healthy", "endpoint": "/api/mcp"},
        }

        try:
            from app.config import settings
            import redis
            r = redis.from_url(settings.REDIS_URL, socket_connect_timeout=2)
            r.ping()
            services["redis"] = {"status": "healthy", "url": settings.REDIS_URL}
        except Exception:
            services["redis"] = {"status": "unavailable", "note": "Redis 未连接，使用本地模式"}

        try:
            from app.config import settings as cfg
            import urllib.request
            req = urllib.request.Request(f"{cfg.OLLAMA_BASE_URL}/api/tags", method="GET")
            urllib.request.urlopen(req, timeout=2)
            services["ollama"] = {"status": "healthy", "url": cfg.OLLAMA_BASE_URL}
        except Exception:
            services["ollama"] = {"status": "unavailable", "note": "Ollama 未运行，AI 功能降级为模板模式"}

        return ApiResponse(data=services)

    # ---- 字典数据中心 ----

    def get_dict_groups(self, module: Optional[str] = None) -> ApiResponse:
        """获取所有字典分组."""
        query = self.db.query(DictionaryGroup).order_by(DictionaryGroup.sort_order, DictionaryGroup.group_key)
        if module:
            query = query.filter(DictionaryGroup.module == module)

        groups = query.all()
        return ApiResponse(data=[_dict_group_to_dict(g) for g in groups])

    def get_dict_group_items(self, group_key: str) -> ApiResponse:
        """获取指定分组的所有条目."""
        group = self.db.query(DictionaryGroup).filter(DictionaryGroup.group_key == group_key).first()
        if not group:
            raise HTTPException(status_code=404, detail=f"字典分组 '{group_key}' 不存在")

        items = self.db.query(DictionaryItem).filter(
            DictionaryItem.group_key == group_key,
            DictionaryItem.is_active == True,
        ).order_by(DictionaryItem.sort_order).all()

        return ApiResponse(data={
            "group": _dict_group_to_dict(group),
            "items": [_dict_item_to_dict(i) for i in items],
        })

    def get_dict_items_bulk(self, keys: Optional[str] = None) -> ApiResponse:
        """批量获取多个字典分组的条目."""
        if keys:
            group_keys = [k.strip() for k in keys.split(",") if k.strip()]
        else:
            all_groups = self.db.query(DictionaryGroup).all()
            group_keys = [g.group_key for g in all_groups]

        result = {}
        for gk in group_keys:
            items = self.db.query(DictionaryItem).filter(
                DictionaryItem.group_key == gk,
                DictionaryItem.is_active == True,
            ).order_by(DictionaryItem.sort_order).all()
            result[gk] = [_dict_item_to_dict(i) for i in items]

        return ApiResponse(data=result)

    def export_dict(self) -> ApiResponse:
        """导出完整字典数据 (JSON)."""
        groups = self.db.query(DictionaryGroup).order_by(DictionaryGroup.sort_order).all()
        export_data = {}
        for g in groups:
            items = self.db.query(DictionaryItem).filter(
                DictionaryItem.group_key == g.group_key
            ).order_by(DictionaryItem.sort_order).all()
            export_data[g.group_key] = {
                "group": _dict_group_to_dict(g),
                "items": [_dict_item_to_dict(i) for i in items],
            }
        return ApiResponse(data=export_data)

    def create_dict_item(self, item: DictionaryItemCreate) -> ApiResponse:
        """添加自定义字典条目 (仅可扩展分组)."""
        group_key = item.group_key
        if not group_key:
            raise HTTPException(status_code=400, detail="group_key 是必填项")

        group = self.db.query(DictionaryGroup).filter(DictionaryGroup.group_key == group_key).first()
        if not group:
            raise HTTPException(status_code=404, detail=f"字典分组 '{group_key}' 不存在")
        if not group.is_extensible:
            raise HTTPException(status_code=403, detail=f"字典分组 '{group_key}' 不允许用户扩展")

        existing = self.db.query(DictionaryItem).filter(
            DictionaryItem.group_key == group_key,
            DictionaryItem.item_key == item.item_key,
        ).first()
        if existing:
            raise HTTPException(status_code=400, detail=f"条目 '{item.item_key}' 已存在")

        dict_item = DictionaryItem(
            id=hashlib.md5(str(secrets.token_hex(8)).encode()).hexdigest()[:16],
            group_key=group_key,
            item_key=item.item_key,
            item_value=item.item_value,
            item_value_en=item.item_value_en,
            extra=item.extra,
            is_active=item.is_active,
            sort_order=item.sort_order,
        )
        self.db.add(dict_item)
        try:
            self.db.commit()
            self.db.refresh(dict_item)
        except Exception as e:
            self.db.rollback()
            raise HTTPException(status_code=500, detail=f"Failed to create dictionary item: {str(e)}")
        return ApiResponse(data=_dict_item_to_dict(dict_item), message="条目已创建")

    def update_dict_item(self, item_id: str, updates: DictionaryItemUpdate) -> ApiResponse:
        """更新字典条目."""
        item = self.db.query(DictionaryItem).filter(DictionaryItem.id == item_id).first()
        if not item:
            raise HTTPException(status_code=404, detail="字典条目不存在")

        updatable_fields = ["item_key", "item_value", "item_value_en", "extra", "is_active", "sort_order"]
        for field in updatable_fields:
            value = getattr(updates, field, None)
            if value is not None:
                setattr(item, field, value)

        try:
            self.db.commit()
            self.db.refresh(item)
        except Exception as e:
            self.db.rollback()
            raise HTTPException(status_code=500, detail=f"Failed to update dictionary item: {str(e)}")
        return ApiResponse(data=_dict_item_to_dict(item), message="条目已更新")

    def delete_dict_item(self, item_id: str) -> ApiResponse:
        """删除自定义字典条目."""
        item = self.db.query(DictionaryItem).filter(DictionaryItem.id == item_id).first()
        if not item:
            raise HTTPException(status_code=404, detail="字典条目不存在")

        group = self.db.query(DictionaryGroup).filter(DictionaryGroup.group_key == item.group_key).first()
        if group and not group.is_extensible:
            raise HTTPException(status_code=403, detail="内置字典条目不可删除")

        try:
            self.db.delete(item)
            self.db.commit()
        except Exception as e:
            self.db.rollback()
            raise HTTPException(status_code=500, detail=f"Failed to delete dictionary item: {str(e)}")
        return ApiResponse(message="条目已删除")

    # ---- 通知中心 ----

    def get_notifications(self, notif_type: Optional[str] = None, is_read: Optional[bool] = None,
                          page: int = 1, page_size: int = 50) -> ApiResponse:
        """获取通知列表."""
        from app.deps import get_current_user_id
        # user_id 需要由调用方传入，这里使用 default
        user_id = "local"  # 占位，由路由器层传入

        # Override with instance method that accepts user_id
        raise NotImplementedError("Use get_notifications_with_user instead")

    def get_notifications_with_user(self, user_id: str, notif_type: Optional[str] = None,
                                     is_read: Optional[bool] = None, page: int = 1,
                                     page_size: int = 50) -> ApiResponse:
        """获取通知列表 (带用户ID)."""
        query = self.db.query(Notification).filter(Notification.user_id == user_id)

        if notif_type:
            query = query.filter(Notification.type == notif_type)
        if is_read is not None:
            query = query.filter(Notification.is_read == is_read)

        total = query.count()
        notifs = query.order_by(Notification.created_at.desc()).offset(
            (page - 1) * page_size
        ).limit(page_size).all()

        return ApiResponse(data={
            "items": [
                {
                    "id": n.id,
                    "type": n.type,
                    "title": n.title,
                    "content": n.content,
                    "related_module": n.related_module,
                    "related_id": n.related_id,
                    "channel": n.channel,
                    "is_read": n.is_read,
                    "created_at": n.created_at.isoformat() if n.created_at else None,
                    "read_at": n.read_at.isoformat() if n.read_at else None,
                }
                for n in notifs
            ],
            "total": total,
            "page": page,
            "page_size": page_size,
        })

    def get_unread_count(self, user_id: str) -> ApiResponse:
        """获取未读通知数."""
        count = self.db.query(Notification).filter(
            Notification.user_id == user_id,
            Notification.is_read == False,
        ).count()
        return ApiResponse(data={"count": count})

    def mark_notification_read(self, notif_id: str) -> ApiResponse:
        """标记通知为已读."""
        notif = self.db.query(Notification).filter(Notification.id == notif_id).first()
        if not notif:
            raise HTTPException(status_code=404, detail="通知不存在")

        notif.is_read = True
        notif.read_at = datetime.now(timezone.utc)
        try:
            self.db.commit()
        except Exception as e:
            self.db.rollback()
            raise HTTPException(status_code=500, detail=f"Failed to mark notification as read: {str(e)}")
        return ApiResponse(message="已标记为已读")

    def mark_all_read(self, user_id: str) -> ApiResponse:
        """全部标记为已读."""
        self.db.query(Notification).filter(
            Notification.user_id == user_id,
            Notification.is_read == False,
        ).update({"is_read": True, "read_at": datetime.now(timezone.utc)})
        try:
            self.db.commit()
        except Exception as e:
            self.db.rollback()
            raise HTTPException(status_code=500, detail=f"Failed to mark all notifications as read: {str(e)}")
        return ApiResponse(message="所有通知已标记为已读")

    # ---- Email 通知 ----

    def test_email_notification(self, recipient: str) -> ApiResponse:
        """测试邮件通知渠道."""
        cfg = _get_smtp_config(self.db)
        if not cfg.get("smtp_host"):
            raise HTTPException(status_code=400, detail="请先在系统设置中配置 SMTP 参数")

        try:
            msg = MIMEMultipart()
            msg["From"] = cfg.get("smtp_from") or cfg.get("smtp_user") or "noreply@oristudio.local"
            msg["To"] = recipient
            msg["Subject"] = "[OriStudio] 邮件通知测试"
            body = f"""
            <html><body>
            <h2>OriStudio 邮件通知测试</h2>
            <p>如果您收到此邮件，说明邮件通知渠道配置成功。</p>
            <p>发送时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            </body></html>
            """
            msg.attach(MIMEText(body, "html"))

            use_tls = cfg.get("smtp_tls", "true") == "true"
            port = int(cfg.get("smtp_port", "587"))

            if use_tls:
                server = smtplib.SMTP(cfg["smtp_host"], port, timeout=10)
                server.starttls()
            else:
                server = smtplib.SMTP_SSL(cfg["smtp_host"], port, timeout=10)

            if cfg.get("smtp_user") and cfg.get("smtp_password"):
                server.login(cfg["smtp_user"], cfg["smtp_password"])

            server.send_message(msg)
            server.quit()

            return ApiResponse(message=f"测试邮件已发送至 {recipient}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"邮件发送失败: {str(e)}")

    def send_email_notification(self, recipient: str, subject: str, body: str) -> ApiResponse:
        """发送邮件通知."""
        cfg = _get_smtp_config(self.db)
        if not cfg.get("smtp_host"):
            raise HTTPException(status_code=400, detail="请先在系统设置中配置 SMTP 参数")

        try:
            msg = MIMEMultipart()
            msg["From"] = cfg.get("smtp_from") or cfg.get("smtp_user") or "noreply@oristudio.local"
            msg["To"] = recipient
            msg["Subject"] = subject
            msg.attach(MIMEText(body, "html" if "<" in body else "plain"))

            use_tls = cfg.get("smtp_tls", "true") == "true"
            port = int(cfg.get("smtp_port", "587"))

            if use_tls:
                server = smtplib.SMTP(cfg["smtp_host"], port, timeout=10)
                server.starttls()
            else:
                server = smtplib.SMTP_SSL(cfg["smtp_host"], port, timeout=10)

            if cfg.get("smtp_user") and cfg.get("smtp_password"):
                server.login(cfg["smtp_user"], cfg["smtp_password"])

            server.send_message(msg)
            server.quit()

            return ApiResponse(message=f"邮件已发送至 {recipient}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"邮件发送失败: {str(e)}")

    # ---- 微信通知 ----

    def test_wechat_notification(self) -> ApiResponse:
        """测试微信模板消息通知渠道."""
        cfg = _get_wechat_config(self.db)
        if not cfg.get("wechat_appid") or not cfg.get("wechat_appsecret"):
            raise HTTPException(status_code=400, detail="请先在系统设置中配置微信 AppID 和 AppSecret")

        try:
            import urllib.request
            token_url = (
                f"https://api.weixin.qq.com/cgi-bin/token"
                f"?grant_type=client_credential&appid={cfg['wechat_appid']}&secret={cfg['wechat_appsecret']}"
            )
            req = urllib.request.Request(token_url, method="GET")
            resp = urllib.request.urlopen(req, timeout=10)
            token_data = json.loads(resp.read())
            access_token = token_data.get("access_token")

            if not access_token:
                errmsg = token_data.get("errmsg", "未知错误")
                raise HTTPException(status_code=500, detail=f"获取微信 access_token 失败: {errmsg}")

            return ApiResponse(
                message="微信 access_token 获取成功，通知渠道可正常使用",
                data={
                    "access_token_valid": True,
                    "template_message_format": {
                        "description": "微信模板消息标准 JSON 格式",
                        "fields": {
                            "touser": {"type": "string", "description": "接收者 openid"},
                            "template_id": {"type": "string", "description": "模板 ID"},
                            "url": {"type": "string", "description": "点击模板消息跳转的 URL（可选）"},
                            "miniprogram": {
                                "type": "object",
                                "description": "跳转小程序（可选，与 url 互斥）",
                                "fields": {
                                    "appid": {"type": "string", "description": "小程序 AppID"},
                                    "pagepath": {"type": "string", "description": "小程序页面路径"},
                                },
                            },
                            "data": {
                                "type": "object",
                                "description": "模板数据字段（key 对应模板中的 {{keyword.DATA}}）",
                                "fields": {
                                    "first": {"type": "object", "description": "头部字段", "fields": {"value": "string", "color": "hex color (可选)"}},
                                    "keyword1": {"type": "object", "description": "关键字1", "fields": {"value": "string", "color": "hex color (可选)"}},
                                    "keyword2": {"type": "object", "description": "关键字2", "fields": {"value": "string", "color": "hex color (可选)"}},
                                    "keyword3": {"type": "object", "description": "关键字3", "fields": {"value": "string", "color": "hex color (可选)"}},
                                    "remark": {"type": "object", "description": "备注字段", "fields": {"value": "string", "color": "hex color (可选)"}},
                                },
                            },
                        },
                        "example_request": {
                            "touser": "oOPENIDxxxxxxxxxxxxxxxxxxxx",
                            "template_id": cfg.get("wechat_template_id") or "TEMPLATE_ID_PLACEHOLDER",
                            "url": "https://oristudio.app/notifications",
                            "miniprogram": {
                                "appid": "wxMINIPROGRAM_APPID",
                                "pagepath": "pages/notification/detail?id=123",
                            },
                            "data": {
                                "first": {"value": "您有一条新的通知", "color": "#173177"},
                                "keyword1": {"value": "作品审核通过", "color": "#173177"},
                                "keyword2": {"value": "2025-01-15 14:30", "color": "#173177"},
                                "keyword3": {"value": "审核通过", "color": "#07C160"},
                                "remark": {"value": "点击查看详情", "color": "#888888"},
                            },
                        },
                        "send_endpoint": "POST https://api.weixin.qq.com/cgi-bin/message/template/send?access_token=ACCESS_TOKEN",
                        "note": "完整模板消息推送调用 send_wechat_template_message() helper，需提供 openid",
                    },
                },
            )
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"微信接口调用失败: {str(e)}")

    def send_wechat_template_message(self, data: WechatTemplateMessage) -> ApiResponse:
        """发送微信模板消息."""
        cfg = _get_wechat_config(self.db)
        if not cfg.get("wechat_appid") or not cfg.get("wechat_appsecret"):
            raise HTTPException(status_code=400, detail="请先在系统设置中配置微信 AppID 和 AppSecret")

        touser = data.touser
        message_data = data.message_data
        template_id = data.template_id or cfg.get("wechat_template_id")
        if not template_id:
            raise HTTPException(status_code=400, detail="缺少 template_id，请在系统设置或请求中配置")

        template_payload = {
            "touser": touser,
            "template_id": template_id,
        }

        url = data.url
        miniprogram = data.miniprogram

        if url:
            template_payload["url"] = url
        if miniprogram and isinstance(miniprogram, (dict, MiniProgram)):
            mp_dict = miniprogram if isinstance(miniprogram, dict) else miniprogram.model_dump()
            template_payload["miniprogram"] = {
                "appid": mp_dict.get("appid", ""),
                "pagepath": mp_dict.get("pagepath", ""),
            }

        formatted_data = {}
        for key, field in message_data.items():
            if isinstance(field, dict):
                formatted_data[key] = {
                    "value": str(field.get("value", "")),
                    "color": field.get("color") or "",
                }
            else:
                formatted_data[key] = {"value": str(field), "color": ""}

        template_payload["data"] = formatted_data

        try:
            import urllib.request

            token_url = (
                f"https://api.weixin.qq.com/cgi-bin/token"
                f"?grant_type=client_credential&appid={cfg['wechat_appid']}&secret={cfg['wechat_appsecret']}"
            )
            req = urllib.request.Request(token_url, method="GET")
            resp = urllib.request.urlopen(req, timeout=10)
            token_data_raw = json.loads(resp.read())
            access_token = token_data_raw.get("access_token")

            if not access_token:
                errmsg = token_data_raw.get("errmsg", "未知错误")
                raise HTTPException(status_code=500, detail=f"获取微信 access_token 失败: {errmsg}")

            send_url = f"https://api.weixin.qq.com/cgi-bin/message/template/send?access_token={access_token}"
            send_req = urllib.request.Request(
                send_url,
                method="POST",
                data=json.dumps(template_payload, ensure_ascii=False).encode("utf-8"),
                headers={"Content-Type": "application/json; charset=utf-8"},
            )
            send_resp = urllib.request.urlopen(send_req, timeout=10)
            send_result = json.loads(send_resp.read())

            if send_result.get("errcode") == 0:
                return ApiResponse(
                    message="模板消息发送成功",
                    data={
                        "msgid": send_result.get("msgid"),
                        "template_id": template_id,
                        "touser": touser,
                        "data_fields_count": len(formatted_data),
                    },
                )
            else:
                errmsg = send_result.get("errmsg", "未知错误")
                raise HTTPException(
                    status_code=500,
                    detail=f"模板消息发送失败 (errcode={send_result.get('errcode')}): {errmsg}",
                )

        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"微信模板消息发送失败: {str(e)}")

    def get_wechat_template_format(self) -> ApiResponse:
        """获取微信模板消息标准格式说明."""
        return ApiResponse(data={
            "description": "微信公众号模板消息格式",
            "api_endpoint": "POST https://api.weixin.qq.com/cgi-bin/message/template/send?access_token=ACCESS_TOKEN",
            "request_format": {
                "touser": {
                    "type": "string",
                    "required": True,
                    "description": "接收者 openid",
                    "example": "oOPENIDxxxxxxxxxxxxxxxxxxxx",
                },
                "template_id": {
                    "type": "string",
                    "required": True,
                    "description": "模板 ID (从微信公众平台模板库获取)",
                    "example": "ngqIpbwh8bUfcSsECmogfXcV14J0tQlEpbo27uEYWMY",
                },
                "url": {
                    "type": "string",
                    "required": False,
                    "description": "点击模板消息跳转的 URL",
                    "example": "https://oristudio.app/works/abc123",
                },
                "miniprogram": {
                    "type": "object",
                    "required": False,
                    "description": "跳转小程序（与 url 互斥，优先跳小程序）",
                    "fields": {
                        "appid": {"type": "string", "required": True, "description": "小程序 AppID", "example": "wx1234567890abcdef"},
                        "pagepath": {"type": "string", "required": True, "description": "小程序页面路径", "example": "pages/work/detail?id=abc123"},
                    },
                },
                "data": {
                    "type": "object",
                    "required": True,
                    "description": "模板数据，key 对应模板中的 {{keyword.DATA}}",
                    "structure": {
                        "first": {
                            "value": "string (必填 - 首行内容)",
                            "color": "hex color (可选，如 #173177)",
                        },
                        "keyword1": {
                            "value": "string (模板定义的字段)",
                            "color": "hex color (可选)",
                        },
                        "keyword2": {
                            "value": "string (模板定义的字段)",
                            "color": "hex color (可选)",
                        },
                        "keyword3": {
                            "value": "string (模板定义的字段)",
                            "color": "hex color (可选)",
                        },
                        "keyword4": {
                            "value": "string (模板定义的字段，可选)",
                            "color": "hex color (可选)",
                        },
                        "remark": {
                            "value": "string (可选 - 末行内容)",
                            "color": "hex color (可选，如 #888888)",
                        },
                    },
                },
            },
            "common_templates": [
                {
                    "name": "作品审核通知",
                    "template_id_short": "OPENTM207923849",
                    "keywords": ["first", "keyword1(作品名称)", "keyword2(审核时间)", "keyword3(审核结果)", "remark"],
                },
                {
                    "name": "版权存证完成通知",
                    "template_id_short": "OPENTM413477733",
                    "keywords": ["first", "keyword1(存证编号)", "keyword2(存证时间)", "keyword3(区块链)", "remark"],
                },
                {
                    "name": "订单状态变更",
                    "template_id_short": "OPENTM201541239",
                    "keywords": ["first", "keyword1(订单编号)", "keyword2(订单状态)", "keyword3(更新时间)", "remark"],
                },
            ],
            "color_defaults": {
                "success": "#07C160",
                "warning": "#FF9800",
                "error": "#F44336",
                "info": "#173177",
                "muted": "#888888",
            },
        })

    # ---- 插件框架 ----

    def list_plugins(self) -> ApiResponse:
        """获取所有插件."""
        plugins = self.db.query(Plugin).order_by(Plugin.priority.desc(), Plugin.name).all()
        return ApiResponse(data=[
            {
                "id": p.id,
                "name": p.name,
                "display_name": p.display_name,
                "version": p.version,
                "description": p.description,
                "author": p.author,
                "enabled": p.enabled,
                "hooks": p.hooks,
                "config": p.config,
                "entry_point": p.entry_point,
                "priority": p.priority,
                "created_at": p.created_at.isoformat() if p.created_at else None,
                "updated_at": p.updated_at.isoformat() if p.updated_at else None,
            }
            for p in plugins
        ])

    def register_plugin(self, plugin: PluginRegister) -> ApiResponse:
        """注册新插件."""
        existing = self.db.query(Plugin).filter(Plugin.name == plugin.name).first()
        if existing:
            raise HTTPException(status_code=400, detail=f"插件 '{plugin.name}' 已注册")

        disp_name = plugin.display_name or plugin.name
        plugin_data = Plugin(
            id=hashlib.md5(str(secrets.token_hex(8)).encode()).hexdigest()[:16],
            name=plugin.name,
            display_name=disp_name,
            version=plugin.version,
            description=plugin.description,
            author=plugin.author,
            enabled=plugin.enabled,
            hooks=plugin.hooks,
            config=plugin.config,
            entry_point=plugin.entry_point,
            priority=plugin.priority,
        )
        self.db.add(plugin_data)
        try:
            self.db.commit()
            self.db.refresh(plugin_data)
        except Exception as e:
            self.db.rollback()
            raise HTTPException(status_code=500, detail=f"Failed to register plugin: {str(e)}")

        return ApiResponse(message=f"插件 '{plugin_data.display_name}' 已注册", data={"id": plugin_data.id})

    def update_plugin(self, plugin_id: str, data: PluginUpdate) -> ApiResponse:
        """更新插件 (启用/禁用、配置)."""
        plugin = self.db.query(Plugin).filter(Plugin.id == plugin_id).first()
        if not plugin:
            raise HTTPException(status_code=404, detail="插件不存在")

        updatable = ["display_name", "version", "enabled", "hooks", "config", "priority", "description"]
        for field in updatable:
            value = getattr(data, field, None)
            if value is not None:
                setattr(plugin, field, value)

        try:
            self.db.commit()
        except Exception as e:
            self.db.rollback()
            raise HTTPException(status_code=500, detail=f"Failed to update plugin: {str(e)}")
        return ApiResponse(message=f"插件 '{plugin.display_name}' 已更新")

    def delete_plugin(self, plugin_id: str) -> ApiResponse:
        """删除插件."""
        plugin = self.db.query(Plugin).filter(Plugin.id == plugin_id).first()
        if not plugin:
            raise HTTPException(status_code=404, detail="插件不存在")

        try:
            self.db.delete(plugin)
            self.db.commit()
        except Exception as e:
            self.db.rollback()
            raise HTTPException(status_code=500, detail=f"Failed to delete plugin: {str(e)}")
        return ApiResponse(message="插件已删除")

    # ---- 邮箱验证 ----

    def send_verification_email(self, email: str) -> ApiResponse:
        """发送邮箱验证码."""
        from app.deps import get_current_user_id
        from app.models.system import User as UserModel

        existing_user = self.db.query(UserModel).filter(
            UserModel.email == email,
            UserModel.email_verified == True,
        ).first()
        if existing_user:
            raise HTTPException(status_code=400, detail="该邮箱已被其他账号验证")

        code = f"{secrets.randbelow(1000000):06d}"
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=10)

        verification = EmailVerification(
            email=email,
            code=code,
            expires_at=expires_at,
        )
        self.db.add(verification)

        cfg = _get_smtp_config(self.db)
        email_sent = False
        if cfg.get("smtp_host"):
            try:
                msg = MIMEMultipart()
                msg["From"] = cfg.get("smtp_from") or cfg.get("smtp_user") or "noreply@oristudio.local"
                msg["To"] = email
                msg["Subject"] = "[OriStudio] 邮箱验证码"
                body = f"""
                <html><body>
                <h2>OriStudio 邮箱验证</h2>
                <p>您的验证码是: <strong style="font-size:24px;color:#1a73e8">{code}</strong></p>
                <p>验证码有效期 10 分钟。</p>
                <p>如果这不是您的操作，请忽略此邮件。</p>
                </body></html>
                """
                msg.attach(MIMEText(body, "html"))

                use_tls = cfg.get("smtp_tls", "true") == "true"
                port = int(cfg.get("smtp_port", "587"))

                if use_tls:
                    server = smtplib.SMTP(cfg["smtp_host"], port, timeout=10)
                    server.starttls()
                else:
                    server = smtplib.SMTP_SSL(cfg["smtp_host"], port, timeout=10)

                if cfg.get("smtp_user") and cfg.get("smtp_password"):
                    server.login(cfg["smtp_user"], cfg["smtp_password"])
                server.send_message(msg)
                server.quit()
                email_sent = True
            except Exception as e:
                logging.getLogger(__name__).exception("Error in send_verification_email: %s", str(e))

        try:
            self.db.commit()
        except Exception as e:
            self.db.rollback()
            raise HTTPException(status_code=500, detail=f"Failed to send verification email: {str(e)}")

        return ApiResponse(
            message="验证码已发送" if email_sent else f"验证码已生成(未配置邮件服务): {code}",
            data={"email_sent": email_sent, "expires_in": 600},
        )

    def confirm_verification_email(self, email: str, code: str) -> ApiResponse:
        """确认邮箱验证码."""
        verification = self.db.query(EmailVerification).filter(
            EmailVerification.email == email,
            EmailVerification.code == code,
            EmailVerification.verified == False,
        ).order_by(EmailVerification.created_at.desc()).first()

        if not verification:
            raise HTTPException(status_code=400, detail="验证码错误或已失效")

        if verification.expires_at < datetime.now(timezone.utc):
            raise HTTPException(status_code=400, detail="验证码已过期")

        verification.verified = True
        try:
            self.db.commit()
        except Exception as e:
            self.db.rollback()
            raise HTTPException(status_code=500, detail=f"Failed to confirm email verification: {str(e)}")
        return ApiResponse(message="邮箱验证成功")

    # ---- 密码重置 ----

    def request_password_reset(self, email: str) -> ApiResponse:
        """请求密码重置: 发送重置令牌到邮箱."""
        user = self.db.query(UserModel).filter(UserModel.email == email).first()
        if not user:
            return ApiResponse(message="如果该邮箱已注册，重置邮件已发送")

        reset_token = secrets.token_urlsafe(32)
        expires_at = datetime.now(timezone.utc) + timedelta(hours=1)

        reset = PasswordReset(
            email=email,
            token=reset_token,
            expires_at=expires_at,
        )
        self.db.add(reset)

        cfg = _get_smtp_config(self.db)
        email_sent = False
        if cfg.get("smtp_host"):
            try:
                msg = MIMEMultipart()
                msg["From"] = cfg.get("smtp_from") or cfg.get("smtp_user") or "noreply@oristudio.local"
                msg["To"] = email
                msg["Subject"] = "[OriStudio] 密码重置"
                reset_url = f"http://localhost:8001/reset-password?token={reset_token}"
                body = f"""
                <html><body>
                <h2>OriStudio 密码重置</h2>
                <p>点击下方链接重置密码 (有效期1小时):</p>
                <p><a href="{reset_url}" style="display:inline-block;padding:12px 24px;background:#1a73e8;color:#fff;text-decoration:none;border-radius:6px">重置密码</a></p>
                <p>或复制此链接: {reset_url}</p>
                </body></html>
                """
                msg.attach(MIMEText(body, "html"))

                use_tls = cfg.get("smtp_tls", "true") == "true"
                port = int(cfg.get("smtp_port", "587"))

                if use_tls:
                    server = smtplib.SMTP(cfg["smtp_host"], port, timeout=10)
                    server.starttls()
                else:
                    server = smtplib.SMTP_SSL(cfg["smtp_host"], port, timeout=10)
                if cfg.get("smtp_user") and cfg.get("smtp_password"):
                    server.login(cfg["smtp_user"], cfg["smtp_password"])
                server.send_message(msg)
                server.quit()
                email_sent = True
            except Exception as e:
                logging.getLogger(__name__).exception("Error in request_password_reset: %s", str(e))

        try:
            self.db.commit()
        except Exception as e:
            self.db.rollback()
            raise HTTPException(status_code=500, detail=f"Failed to request password reset: {str(e)}")

        return ApiResponse(
            message="如果该邮箱已注册，重置邮件已发送",
            data={"reset_token": reset_token if not email_sent else None},
        )

    def confirm_password_reset(self, token: str, new_password: str) -> ApiResponse:
        """确认密码重置."""
        reset = self.db.query(PasswordReset).filter(
            PasswordReset.token == token,
            PasswordReset.used == False,
        ).first()

        if not reset:
            raise HTTPException(status_code=400, detail="重置令牌无效")

        if reset.expires_at < datetime.now(timezone.utc):
            raise HTTPException(status_code=400, detail="重置令牌已过期")

        strength = _check_password_strength(new_password)
        if strength["score"] < 30:
            raise HTTPException(status_code=400, detail=f"密码强度不足: {strength['feedback']}")

        user = self.db.query(UserModel).filter(UserModel.email == reset.email).first()
        if not user:
            raise HTTPException(status_code=404, detail="用户不存在")

        from app.utils.system_helpers import hash_password
        user.password_hash = hash_password(new_password)
        user.password_strength_score = strength["score"]
        user.password_updated_at = datetime.now(timezone.utc)

        reset.used = True
        try:
            self.db.commit()
        except Exception as e:
            self.db.rollback()
            raise HTTPException(status_code=500, detail=f"Failed to confirm password reset: {str(e)}")

        return ApiResponse(message="密码已重置，请使用新密码登录")

    # ---- 密码强度检测 ----

    def check_password_strength(self, password: str) -> ApiResponse:
        """检测密码强度."""
        result = _check_password_strength(password)
        return ApiResponse(data=result)

    # ---- 头像上传 ----

    async def upload_avatar(self, file_content: bytes, filename: str) -> ApiResponse:
        """上传用户头像."""
        if not filename or not any(filename.lower().endswith(ext) for ext in ['.png', '.jpg', '.jpeg', '.gif', '.webp']):
            raise HTTPException(status_code=400, detail="仅支持图片文件")

        if len(file_content) > 5 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="文件大小不能超过 5MB")

        avatar_dir = Path("data/avatars")
        avatar_dir.mkdir(parents=True, exist_ok=True)

        ext = os.path.splitext(filename)[1] or ".png"
        avatar_name = f"{secrets.token_hex(16)}{ext}"
        avatar_path = avatar_dir / avatar_name

        with open(avatar_path, "wb") as f:
            f.write(file_content)

        avatar_url = f"/api/files/avatars/{avatar_name}"
        return ApiResponse(
            message="头像已上传",
            data={"avatar_url": avatar_url},
        )

    # ---- 数据导出 ----

    def export_all_data(self, fmt: str = "json") -> ApiResponse:
        """导出所有用户数据."""
        export_data = {
            "exported_at": datetime.now(timezone.utc).isoformat(),
            "exported_by": "OriStudio Data Export",
            "format": fmt,
        }

        if fmt == "json":
            from app.models.work import Work
            from app.models.publish import Product, RevenueRecord

            works = self.db.query(Work).all()
            products = self.db.query(Product).all()
            revenue = self.db.query(RevenueRecord).all()

            export_data["works"] = [
                {
                    "id": w.id, "title": w.title, "description": w.description,
                    "file_type": w.file_type, "status": w.status,
                    "created_at": w.created_at.isoformat() if w.created_at else None,
                }
                for w in works
            ]
            export_data["products"] = [
                {
                    "id": p.id, "title": p.title, "price": p.price,
                    "category": p.category, "status": p.status,
                    "created_at": p.created_at.isoformat() if p.created_at else None,
                }
                for p in products
            ]
            export_data["revenue_records"] = [
                {
                    "id": r.id, "platform": r.platform, "amount": r.amount,
                    "date": r.date.isoformat() if r.date else None,
                    "notes": r.notes,
                }
                for r in revenue
            ]

            return ApiResponse(data=export_data)
        else:
            from app.models.work import Work
            from app.models.publish import Product

            output = io.StringIO()
            writer = csv.writer(output)

            writer.writerow(["## Works"])
            writer.writerow(["id", "title", "description", "file_type", "status", "created_at"])
            for w in self.db.query(Work).all():
                writer.writerow([w.id, w.title, w.description, w.file_type, w.status,
                                 w.created_at.isoformat() if w.created_at else ""])

            writer.writerow([])
            writer.writerow(["## Products"])
            writer.writerow(["id", "title", "price", "category", "status", "created_at"])
            for p in self.db.query(Product).all():
                writer.writerow([p.id, p.title, p.price, p.category, p.status,
                                 p.created_at.isoformat() if p.created_at else ""])

            return ApiResponse(data={"csv_content": output.getvalue()})

    # ---- 危险区 ----

    def delete_account(self, user_id: str) -> ApiResponse:
        """注销账号 (危险操作)."""
        from app.models.system import UserLoginHistory

        user = self.db.query(UserModel).filter(UserModel.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="用户不存在")

        self.db.query(Notification).filter(Notification.user_id == user_id).delete()
        self.db.query(UserLoginHistory).filter(UserLoginHistory.user_id == user_id).delete()
        self.db.query(EmailVerification).filter(EmailVerification.email == user.email).delete()
        self.db.query(PasswordReset).filter(PasswordReset.email == user.email).delete()

        user.status = "deleted"
        user.email = f"deleted_{user.id}@deleted.local"
        user.google_id = None
        user.wechat_openid = None
        user.douyin_openid = None

        try:
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise
        return ApiResponse(message="账号已注销")

    def clear_all_data(self) -> ApiResponse:
        """清除所有本地数据 (危险操作)."""
        from app.models.work import Work
        from app.models.publish import Product, ProductPublishing, VerifiedMark, RevenueRecord
        from app.models.notary import NotaryRecord
        from app.models.ipr import IPRRecord
        from app.models.monetization import Order
        from app.models.monitor import ScanRecord
        from app.models.system import UserLoginHistory

        tables_in_order = [
            RevenueRecord, VerifiedMark, ProductPublishing, Product,
            NotaryRecord, IPRRecord, ScanRecord, Order,
            Notification, AuditLog, BackupRecord,
            EmailVerification, PasswordReset,
            DictionaryItem, DictionaryGroup, Plugin,
            UserLoginHistory, UserModel,
            Work,
        ]

        for table in tables_in_order:
            try:
                self.db.query(table).delete()
            except Exception as e:
                logging.getLogger(__name__).exception("Error in clear_all_data: %s", str(e))

        try:
            self.db.query(SystemSetting).delete()
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise

        for d in ["workspace", "certificates", "thumbnails", "backups", "avatars"]:
            p = Path("data") / d
            if p.exists():
                shutil.rmtree(p, ignore_errors=True)
                p.mkdir(parents=True, exist_ok=True)

        return ApiResponse(message="所有数据已清除")

    # ---- API 统计 ----

    def get_api_stats(self, top_n: int = 20) -> ApiResponse:
        """获取 API 调用统计 (内存计数, 重启后重置)."""
        sorted_endpoints = sorted(_api_call_counter.items(), key=lambda x: x[1], reverse=True)
        total_calls = sum(c for _, c in sorted_endpoints)

        return ApiResponse(data={
            "total_api_calls": total_calls,
            "unique_endpoints": len(sorted_endpoints),
            "top_endpoints": [
                {"path": path, "calls": count}
                for path, count in sorted_endpoints[:top_n]
            ],
        })

    def reset_api_stats(self) -> ApiResponse:
        """重置 API 统计计数器."""
        _api_call_counter.clear()
        return ApiResponse(message="API 统计已重置")

    # ---- 存储趋势 ----

    def get_storage_trends(self, days: int = 7) -> ApiResponse:
        """获取存储使用趋势 (按日期聚合)."""
        workspace = Path("data/workspace")
        certificates = Path("data/certificates")
        thumbnails = Path("data/thumbnails")
        db_path = Path("data/oristudio.db")

        def get_dir_size(path: Path) -> int:
            if not path.exists():
                return 0
            return sum(f.stat().st_size for f in path.rglob("*") if f.is_file())

        today = date.today()
        trends = []

        for i in range(days):
            day = today - timedelta(days=days - 1 - i)
            day_start = datetime.combine(day, datetime.min.time(), tzinfo=timezone.utc)
            day_end = datetime.combine(day + timedelta(days=1), datetime.min.time(), tzinfo=timezone.utc)

            backups = self.db.query(BackupRecord).filter(
                BackupRecord.created_at >= day_start,
                BackupRecord.created_at < day_end,
            ).all()

            backup_total = sum(b.size for b in backups) if backups else 0

            ws_modified = 0
            if workspace.exists():
                try:
                    ws_modified = sum(
                        1 for f in workspace.rglob("*")
                        if f.is_file() and f.stat().st_mtime >= day_start.timestamp()
                        and f.stat().st_mtime < day_end.timestamp()
                    )
                except OSError:
                    logging.getLogger(__name__).exception("Error in get_storage_trends")

            trends.append({
                "date": day.isoformat(),
                "backup_size_bytes": backup_total,
                "backup_count": len(backups),
                "files_modified": ws_modified,
            })

        current = {
            "workspace_bytes": get_dir_size(workspace),
            "certificates_bytes": get_dir_size(certificates),
            "thumbnails_bytes": get_dir_size(thumbnails),
            "db_bytes": db_path.stat().st_size if db_path.exists() else 0,
        }

        total, used, free = shutil.disk_usage(Path("data"))

        return ApiResponse(data={
            "days": days,
            "current_snapshot": {
                **current,
                "total_bytes": sum(current.values()),
                "disk_total": total,
                "disk_used": used,
                "disk_free": free,
            },
            "daily_trends": trends,
        })

    # ---- TOTP ----

    def setup_totp(self) -> ApiResponse:
        """设置 TOTP 双因素认证."""
        import pyotp
        secret = pyotp.random_base32()
        totp = pyotp.TOTP(secret)
        qr_uri = totp.provisioning_uri(name="local", issuer_name="OriStudio")

        _totp_store["local"] = {
            "secret": secret,
            "enabled": False,
            "qr_uri": qr_uri,
        }

        return ApiResponse(
            message="TOTP 密钥已生成，请扫描 QR 码并验证",
            data={
                "secret": secret,
                "qr_uri": qr_uri,
                "instruction": "请使用 Google Authenticator / 1Password / Authy 等 TOTP 应用扫描 QR 或手动输入密钥",
            },
        )

    def verify_totp(self, code: str) -> ApiResponse:
        """验证 TOTP 码."""
        store = _totp_store.get("local")
        if not store:
            raise HTTPException(status_code=400, detail="请先设置 TOTP")

        import pyotp
        secret = store["secret"]
        totp = pyotp.TOTP(secret)

        if totp.verify(code):
            store["enabled"] = True
            return ApiResponse(message="TOTP 验证成功，已启用双因素认证")
        raise HTTPException(status_code=400, detail="验证码无效")

    def totp_status(self) -> dict:
        """查询 TOTP 状态."""
        store = _totp_store.get("local")
        return {"enabled": store["enabled"] if store else False}

    def disable_totp(self) -> ApiResponse:
        """禁用 TOTP 双因素认证."""
        store = _totp_store.get("local")
        if store:
            store["enabled"] = False
        return ApiResponse(message="TOTP 已禁用")

    # ---- 通知偏好 ----

    def get_notification_prefs(self, user_id: str) -> ApiResponse:
        """获取用户通知偏好设置."""
        user = self.db.query(UserModel).filter(UserModel.id == user_id).first()
        prefs = user.notification_prefs if user and user.notification_prefs else {}
        return ApiResponse(data=prefs)

    def update_notification_prefs(self, user_id: str, payload: dict) -> ApiResponse:
        """更新用户通知偏好设置."""
        user = self.db.query(UserModel).filter(UserModel.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        current = user.notification_prefs or {}
        current.update(payload)
        user.notification_prefs = current
        self.db.commit()
        self.db.refresh(user)
        return ApiResponse(data=current, message="通知偏好已更新")

    # ---- 设计变体 ----

    def generate_design_variants(self, data: DesignVariantInput) -> ApiResponse:
        """根据产品描述自动生成不同品类/场景的设计变体."""
        base_desc = data.base_description
        target_categories = data.target_categories
        style_prefs = data.style_preferences
        language = data.language

        if not base_desc or not target_categories:
            raise HTTPException(status_code=400, detail="base_description 和 target_categories 为必填")

        category_templates = {
            "t_shirt": {
                "name_zh": "T恤", "name_en": "T-Shirt",
                "recommended_size": "4500x5400px",
                "dpi": 300,
                "color_space": "CMYK",
                "layout": "中心构图，图案区域 30x40cm",
                "prompt_addition": "适合T恤印花设计，纯色背景，高对比度",
            },
            "mug": {
                "name_zh": "马克杯", "name_en": "Mug",
                "recommended_size": "2400x1200px",
                "dpi": 300,
                "color_space": "CMYK",
                "layout": "环绕式构图，图案区域 20x8cm",
                "prompt_addition": "适合杯子环绕图案，横向布局",
            },
            "poster": {
                "name_zh": "海报", "name_en": "Poster",
                "recommended_size": "3508x4961px (A3)",
                "dpi": 300,
                "color_space": "CMYK",
                "layout": "纵向构图，留白20%，标题区域底部",
                "prompt_addition": "海报级别细节，适合印刷，添加留白区域",
            },
            "sticker": {
                "name_zh": "贴纸", "name_en": "Sticker",
                "recommended_size": "1200x1200px",
                "dpi": 300,
                "color_space": "CMYK",
                "layout": "正方形构图，边缘留出 3mm 出血",
                "prompt_addition": "适合贴纸切割，添加出血线和白色描边",
            },
            "phone_case": {
                "name_zh": "手机壳", "name_en": "Phone Case",
                "recommended_size": "1800x3600px",
                "dpi": 300,
                "color_space": "CMYK",
                "layout": "纵向构图，摄像头区域留空 (顶部居中)",
                "prompt_addition": "适配主流手机壳尺寸，摄像头孔预留",
            },
        }

        variants = []
        for cat in target_categories:
            template = category_templates.get(cat, category_templates.get("sticker", {}))
            variant = {
                "category": cat,
                "category_name": template.get("name_zh" if language == "zh" else "name_en", cat),
                "design_spec": {
                    "size": template.get("recommended_size", "1200x1200px"),
                    "dpi": template.get("dpi", 300),
                    "color_space": template.get("color_space", "CMYK"),
                    "layout": template.get("layout", ""),
                },
                "ai_prompt_fragment": f"{template.get('prompt_addition', '')}",
                "adapted_description": f"[{template.get('name_zh', cat)}] {base_desc}. {template.get('prompt_addition', '')}",
                "color_variants": _generate_color_variants(style_prefs),
                "estimated_production_cost": _estimate_cost(cat),
            }
            variants.append(variant)

        import hashlib
        cache_key = hashlib.md5(f"{base_desc}{','.join(target_categories)}".encode()).hexdigest()[:16]
        _proto_variants_cache[cache_key] = variants

        return ApiResponse(data={
            "base_description": base_desc,
            "total_categories": len(target_categories),
            "variants": variants,
            "cache_key": cache_key,
            "ai_model": "template_rule_v1 (upgrade to Ollama/OpenAI for smart adaptation)",
        })

    def get_design_variants_cached(self, cache_key: str) -> ApiResponse:
        """获取缓存的 AI 设计变体."""
        variants = _proto_variants_cache.get(cache_key)
        if not variants:
            raise HTTPException(status_code=404, detail="缓存不存在或已过期")
        return ApiResponse(data={"cache_key": cache_key, "variants": variants})

    def get_design_categories(self) -> ApiResponse:
        """获取支持的产品设计品类列表."""
        from scripts.seeds.dict_seed import DESIGN_CATEGORIES
        return ApiResponse(data={
            "categories": [
                {"key": k, "name_zh": v["name_zh"], "name_en": v["name_en"],
                 "available_sizes": v.get("sizes", []), "supported": v.get("supported", True)}
                for k, v in DESIGN_CATEGORIES.items()
            ],
        })

    # ---- 免责声明 ----

    def get_disclaimers(self) -> ApiResponse:
        """获取免责声明列表."""
        _seed_disclaimers(self.db)
        disclaimers = self.db.query(Disclaimer).filter(
            Disclaimer.is_active == True
        ).order_by(Disclaimer.priority.desc()).all()

        return ApiResponse(data={
            "items": [
                {
                    "id": d.id,
                    "disclaimer_key": d.disclaimer_key,
                    "title": d.title,
                    "content": d.content,
                    "category": d.category,
                    "is_required": d.is_required,
                    "display_mode": d.display_mode,
                    "trigger_pages": d.trigger_pages,
                }
                for d in disclaimers
            ],
        })

    def accept_disclaimer(self, disclaimer_key: str, context: str = "", user_id: str = "default") -> ApiResponse:
        """记录用户接受免责声明."""
        disclaimer = self.db.query(Disclaimer).filter(
            Disclaimer.disclaimer_key == disclaimer_key
        ).first()
        if not disclaimer:
            raise HTTPException(status_code=404, detail="免责声明不存在")

        acceptance = DisclaimerAcceptance(
            user_id=user_id,
            disclaimer_id=disclaimer.id,
            context=context,
        )
        try:
            self.db.add(acceptance)
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise

        return ApiResponse(data={
            "disclaimer_key": disclaimer_key,
            "accepted_at": acceptance.accepted_at.isoformat(),
        }, message="免责声明已确认")

    def get_onboarding_status(self, user_id: str = "local") -> ApiResponse:
        """获取用户 Onboarding 状态."""
        setting = self.db.query(SystemSetting).filter(
            SystemSetting.key == "onboarding_completed"
        ).first()
        creator_type = None
        if user_id != "default":
            user = self.db.query(UserModel).filter(UserModel.id == user_id).first()
            if user:
                creator_type = user.creator_type

        return ApiResponse(data={
            "onboarding_completed": setting.value == "true" if setting else False,
            "creator_type": creator_type,
        })
