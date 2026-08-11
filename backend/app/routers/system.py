"""系统基础设施 API 路由 — 对应: docs/modules-v5/07-system-infra.md
Phase 0: 免责声明管理, Phase 2: Onboarding API
端点: 54 (system)
"""
import logging
import json
import os
import secrets
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, Header
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.common import ApiResponse
from app.deps import get_current_user_id, require_auth
from app.services.system_service import (
    SystemService,
    SystemSettingsUpdate, DictionaryItemCreate, DictionaryItemUpdate,
    WechatTemplateMessage, PluginRegister, PluginUpdate,
    DesignVariantInput, DisclaimerAcceptanceInput,
    record_api_call, _check_password_strength,
)
from app.utils.system_helpers import (
    get_dict_values,
    get_dict_values_rich,
    push_notification,
)

router = APIRouter()


# ─── 端点实现 ───────────────────────────────────────────────────

# ---- 系统设置 ----

@router.get("/system/settings", response_model=ApiResponse[dict], dependencies=[Depends(require_auth)])
def get_settings(db: Session = Depends(get_db)):
    """获取所有系统设置."""
    svc = SystemService(db)
    return svc.get_settings()


@router.patch("/system/settings", response_model=ApiResponse, dependencies=[Depends(require_auth)])
def update_settings(settings: SystemSettingsUpdate, db: Session = Depends(get_db)):
    """更新系统设置."""
    svc = SystemService(db)
    return svc.update_settings(settings)


# ---- 数据备份 ----

@router.post("/system/backup", response_model=ApiResponse, dependencies=[Depends(require_auth)])
def create_backup(
    include_files: bool = True,
    encrypted: bool = False,
    incremental: bool = False,
    db: Session = Depends(get_db),
):
    """创建数据备份 (支持加密和增量)."""
    svc = SystemService(db)
    return svc.create_backup(include_files, encrypted, incremental)


@router.post("/system/backup/schedule", response_model=ApiResponse, dependencies=[Depends(require_auth)])
def create_scheduled_backup(
    cron_expr: str = Query(default="0 2 * * *", description="Cron 表达式"),
    include_files: bool = True,
    encrypted: bool = True,
    db: Session = Depends(get_db),
):
    """创建定时备份任务 (调度配置)."""
    svc = SystemService(db)
    return svc.create_scheduled_backup(cron_expr, include_files, encrypted)


@router.get("/system/backup/schedule", response_model=ApiResponse, dependencies=[Depends(require_auth)])
def get_backup_schedule(db: Session = Depends(get_db)):
    """获取定时备份配置."""
    svc = SystemService(db)
    return svc.get_backup_schedule()


@router.get("/system/backups", response_model=ApiResponse, dependencies=[Depends(require_auth)])
def list_backups(db: Session = Depends(get_db)):
    """获取备份列表."""
    svc = SystemService(db)
    return svc.list_backups()


@router.post("/system/restore", response_model=ApiResponse, dependencies=[Depends(require_auth)])
def restore_backup(backup_id: str, db: Session = Depends(get_db)):
    """从备份恢复."""
    svc = SystemService(db)
    return svc.restore_backup(backup_id)


@router.delete("/system/backups/{backup_id}", response_model=ApiResponse, dependencies=[Depends(require_auth)])
def delete_backup(backup_id: str, db: Session = Depends(get_db)):
    """删除备份记录."""
    svc = SystemService(db)
    return svc.delete_backup(backup_id)


# ---- 审计日志 ----

@router.get("/system/audit-logs", response_model=ApiResponse, dependencies=[Depends(require_auth)])
def get_audit_logs(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    action: Optional[str] = None,
    module: Optional[str] = None,
    user_id: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """获取审计日志."""
    svc = SystemService(db)
    return svc.get_audit_logs(page, page_size, action, module, user_id)


# ---- 存储管理 ----

@router.get("/system/storage", response_model=ApiResponse, dependencies=[Depends(require_auth)])
def get_storage_info(db: Session = Depends(get_db)):
    """获取存储空间信息."""
    svc = SystemService(db)
    return svc.get_storage_info()


# ---- 健康监控 ----

@router.get("/system/health/dashboard", response_model=ApiResponse)
def get_health_dashboard(db: Session = Depends(get_db)):
    """系统健康仪表盘: CPU/内存/磁盘/服务状态."""
    svc = SystemService(db)
    return svc.get_health_dashboard()


@router.get("/system/health/services", response_model=ApiResponse)
def get_service_status(db: Session = Depends(get_db)):
    """获取各服务状态."""
    svc = SystemService(db)
    return svc.get_service_status()


# ---- 字典数据中心 ----

@router.get("/system/dict/groups", response_model=ApiResponse)
def get_dict_groups(
    module: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """获取所有字典分组."""
    svc = SystemService(db)
    return svc.get_dict_groups(module)


@router.get("/system/dict/groups/{group_key}", response_model=ApiResponse)
def get_dict_group_items(
    group_key: str,
    db: Session = Depends(get_db),
):
    """获取指定分组的所有条目."""
    svc = SystemService(db)
    return svc.get_dict_group_items(group_key)


@router.get("/system/dict/items", response_model=ApiResponse)
def get_dict_items_bulk(
    keys: Optional[str] = Query(None, description="逗号分隔的 group_key 列表"),
    db: Session = Depends(get_db),
):
    """批量获取多个字典分组的条目."""
    svc = SystemService(db)
    return svc.get_dict_items_bulk(keys)


@router.get("/system/dict/export", response_model=ApiResponse)
def export_dict(db: Session = Depends(get_db)):
    """导出完整字典数据 (JSON)."""
    svc = SystemService(db)
    return svc.export_dict()


@router.post("/system/dict/items", response_model=ApiResponse, dependencies=[Depends(require_auth)])
def create_dict_item(
    item: DictionaryItemCreate,
    db: Session = Depends(get_db),
):
    """添加自定义字典条目 (仅可扩展分组)."""
    svc = SystemService(db)
    return svc.create_dict_item(item)


@router.patch("/system/dict/items/{item_id}", response_model=ApiResponse, dependencies=[Depends(require_auth)])
def update_dict_item(
    item_id: str,
    updates: DictionaryItemUpdate,
    db: Session = Depends(get_db),
):
    """更新字典条目."""
    svc = SystemService(db)
    return svc.update_dict_item(item_id, updates)


@router.delete("/system/dict/items/{item_id}", response_model=ApiResponse, dependencies=[Depends(require_auth)])
def delete_dict_item(
    item_id: str,
    db: Session = Depends(get_db),
):
    """删除自定义字典条目."""
    svc = SystemService(db)
    return svc.delete_dict_item(item_id)


# ---- 通知中心 ----

@router.get("/notifications", response_model=ApiResponse, dependencies=[Depends(require_auth)])
def get_notifications(
    type: Optional[str] = None,
    is_read: Optional[bool] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db),
):
    """获取通知列表."""
    user_id = get_current_user_id(authorization)
    svc = SystemService(db)
    return svc.get_notifications_with_user(user_id, type, is_read, page, page_size)


@router.get("/notifications/unread-count", response_model=ApiResponse, dependencies=[Depends(require_auth)])
def get_unread_count(
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db),
):
    """获取未读通知数."""
    user_id = get_current_user_id(authorization)
    svc = SystemService(db)
    return svc.get_unread_count(user_id)


@router.patch("/notifications/{notif_id}/read", response_model=ApiResponse, dependencies=[Depends(require_auth)])
def mark_notification_read(
    notif_id: str,
    db: Session = Depends(get_db),
):
    """标记通知为已读."""
    svc = SystemService(db)
    return svc.mark_notification_read(notif_id)


@router.post("/notifications/read-all", response_model=ApiResponse, dependencies=[Depends(require_auth)])
def mark_all_read(
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db),
):
    """全部标记为已读."""
    user_id = get_current_user_id(authorization)
    svc = SystemService(db)
    return svc.mark_all_read(user_id)


# ---- Email 通知 ----

@router.post("/system/notification/email/test", response_model=ApiResponse, dependencies=[Depends(require_auth)])
def test_email_notification(
    recipient: str = Query(..., description="测试接收邮箱"),
    db: Session = Depends(get_db),
):
    """测试邮件通知渠道."""
    svc = SystemService(db)
    return svc.test_email_notification(recipient)


@router.post("/system/notification/email/send", response_model=ApiResponse, dependencies=[Depends(require_auth)])
def send_email_notification(
    recipient: str = Query(...),
    subject: str = Query(...),
    body: str = Query(...),
    db: Session = Depends(get_db),
):
    """发送邮件通知."""
    svc = SystemService(db)
    return svc.send_email_notification(recipient, subject, body)


# ---- 微信通知 ----

@router.post("/system/notification/wechat/test", response_model=ApiResponse, dependencies=[Depends(require_auth)])
def test_wechat_notification(db: Session = Depends(get_db)):
    """测试微信模板消息通知渠道."""
    svc = SystemService(db)
    return svc.test_wechat_notification()


@router.post("/system/notification/wechat/send", response_model=ApiResponse, dependencies=[Depends(require_auth)])
def send_wechat_template_message(
    data: WechatTemplateMessage,
    db: Session = Depends(get_db),
):
    """发送微信模板消息."""
    svc = SystemService(db)
    return svc.send_wechat_template_message(data)


@router.get("/system/notification/wechat/template-format", response_model=ApiResponse)
def get_wechat_template_format(db: Session = Depends(get_db)):
    """获取微信模板消息标准格式说明."""
    svc = SystemService(db)
    return svc.get_wechat_template_format()


# ---- 插件框架 ----

@router.get("/system/plugins", response_model=ApiResponse)
def list_plugins(db: Session = Depends(get_db)):
    """获取所有插件."""
    svc = SystemService(db)
    return svc.list_plugins()


@router.post("/system/plugins", response_model=ApiResponse, dependencies=[Depends(require_auth)])
def register_plugin(plugin: PluginRegister, db: Session = Depends(get_db)):
    """注册新插件."""
    svc = SystemService(db)
    return svc.register_plugin(plugin)


@router.patch("/system/plugins/{plugin_id}", response_model=ApiResponse, dependencies=[Depends(require_auth)])
def update_plugin(plugin_id: str, data: PluginUpdate, db: Session = Depends(get_db)):
    """更新插件 (启用/禁用、配置)."""
    svc = SystemService(db)
    return svc.update_plugin(plugin_id, data)


@router.delete("/system/plugins/{plugin_id}", response_model=ApiResponse, dependencies=[Depends(require_auth)])
def delete_plugin(plugin_id: str, db: Session = Depends(get_db)):
    """删除插件."""
    svc = SystemService(db)
    return svc.delete_plugin(plugin_id)


# ---- 邮箱验证 ----

@router.post("/system/email/verify/send", response_model=ApiResponse, dependencies=[Depends(require_auth)])
def send_verification_email(
    email: str = Query(...),
    db: Session = Depends(get_db),
):
    """发送邮箱验证码."""
    svc = SystemService(db)
    return svc.send_verification_email(email)


@router.post("/system/email/verify/confirm", response_model=ApiResponse, dependencies=[Depends(require_auth)])
def confirm_verification_email(
    email: str = Query(...),
    code: str = Query(...),
    db: Session = Depends(get_db),
):
    """确认邮箱验证码."""
    svc = SystemService(db)
    return svc.confirm_verification_email(email, code)


# ---- 密码重置 ----

@router.post("/system/password/reset/request", response_model=ApiResponse, dependencies=[Depends(require_auth)])
def request_password_reset(
    email: str = Query(...),
    db: Session = Depends(get_db),
):
    """请求密码重置: 发送重置令牌到邮箱."""
    svc = SystemService(db)
    return svc.request_password_reset(email)


@router.post("/system/password/reset/confirm", response_model=ApiResponse, dependencies=[Depends(require_auth)])
def confirm_password_reset(
    token: str = Query(...),
    new_password: str = Query(...),
    db: Session = Depends(get_db),
):
    """确认密码重置."""
    svc = SystemService(db)
    return svc.confirm_password_reset(token, new_password)


# ---- 密码强度检测 ----

@router.post("/system/password/check-strength", response_model=ApiResponse)
def check_password_strength(password: str = Query(...)):
    """检测密码强度."""
    svc = SystemService()
    return svc.check_password_strength(password)


# ---- 头像上传 ----

@router.post("/system/avatar/upload", response_model=ApiResponse, dependencies=[Depends(require_auth)])
async def upload_avatar(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """上传用户头像."""
    svc = SystemService(db)
    content = await file.read()
    return await svc.upload_avatar(content, file.filename or "")


# ---- 数据导出 ----

@router.get("/system/export/all", response_model=ApiResponse)
def export_all_data(
    format: str = Query(default="json", description="导出格式: json/csv"),
    db: Session = Depends(get_db),
):
    """导出所有用户数据."""
    svc = SystemService(db)
    return svc.export_all_data(format)


# ---- 危险区 ----

@router.post("/system/danger/delete-account", response_model=ApiResponse, dependencies=[Depends(require_auth)])
def delete_account(
    confirmation: str = Query(..., description="输入 'DELETE' 确认删除"),
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db),
):
    """注销账号 (危险操作)."""
    if confirmation != "DELETE":
        raise HTTPException(status_code=400, detail="请输入 'DELETE' 确认删除")

    user_id = get_current_user_id(authorization)
    if user_id == "local":
        raise HTTPException(status_code=401, detail="请先登录")

    svc = SystemService(db)
    return svc.delete_account(user_id)


@router.post("/system/danger/clear-data", response_model=ApiResponse, dependencies=[Depends(require_auth)])
def clear_all_data(
    confirmation: str = Query(..., description="输入 'CLEAR ALL' 确认清除所有数据"),
    db: Session = Depends(get_db),
):
    """清除所有本地数据 (危险操作)."""
    if confirmation != "CLEAR ALL":
        raise HTTPException(status_code=400, detail="请输入 'CLEAR ALL' 确认清除")

    svc = SystemService(db)
    return svc.clear_all_data()


# ---- API 统计 ----

@router.get("/system/stats/api", response_model=ApiResponse)
def get_api_stats(
    top_n: int = Query(default=20, ge=1, le=100),
):
    """获取 API 调用统计 (内存计数, 重启后重置)."""
    svc = SystemService()
    return svc.get_api_stats(top_n)


@router.get("/system/stats/api/reset", response_model=ApiResponse)
def reset_api_stats():
    """重置 API 统计计数器."""
    svc = SystemService()
    return svc.reset_api_stats()


# ---- 存储趋势 ----

@router.get("/system/stats/storage-trends", response_model=ApiResponse)
def get_storage_trends(
    days: int = Query(default=7, ge=1, le=90),
    db: Session = Depends(get_db),
):
    """获取存储使用趋势 (按日期聚合)."""
    svc = SystemService(db)
    return svc.get_storage_trends(days)


# ---- TOTP ----

@router.post("/auth/totp/setup", response_model=ApiResponse)
def setup_totp(authorization: Optional[str] = Header(None)):
    """设置 TOTP 双因素认证."""
    svc = SystemService()
    return svc.setup_totp()


@router.post("/auth/totp/verify", response_model=ApiResponse)
def verify_totp(
    code: str = Query(..., description="TOTP 6位验证码"),
    authorization: Optional[str] = Header(None),
):
    """验证 TOTP 码."""
    svc = SystemService()
    return svc.verify_totp(code)


@router.get("/auth/totp/status", response_model=ApiResponse)
def totp_status(authorization: Optional[str] = Header(None)):
    """查询 TOTP 状态."""
    svc = SystemService()
    return ApiResponse(data=svc.totp_status())


@router.post("/auth/totp/disable", response_model=ApiResponse, dependencies=[Depends(require_auth)])
def disable_totp(authorization: Optional[str] = Header(None)):
    """禁用 TOTP 双因素认证."""
    svc = SystemService()
    return svc.disable_totp()


# ---- 通知偏好 ----

@router.get("/system/notification/prefs", response_model=ApiResponse)
def get_notification_prefs(
    user_id: str = Depends(require_auth),
    db: Session = Depends(get_db),
):
    """获取用户通知偏好设置."""
    svc = SystemService(db)
    return svc.get_notification_prefs(user_id)


@router.post("/system/notification/prefs", response_model=ApiResponse, dependencies=[Depends(require_auth)])
def update_notification_prefs(
    payload: dict,
    user_id: str = Depends(require_auth),
    db: Session = Depends(get_db),
):
    """更新用户通知偏好设置."""
    svc = SystemService(db)
    return svc.update_notification_prefs(user_id, payload)


# ---- 设计变体 ----

@router.post("/system/design/variants", response_model=ApiResponse, dependencies=[Depends(require_auth)])
def generate_design_variants(data: DesignVariantInput, db: Session = Depends(get_db)):
    """根据产品描述自动生成不同品类/场景的设计变体."""
    svc = SystemService(db)
    return svc.generate_design_variants(data)


@router.get("/system/design/categories", response_model=ApiResponse)
def get_design_variants_cached(cache_key: str):
    """获取缓存的 AI 设计变体."""
    svc = SystemService()
    return svc.get_design_variants_cached(cache_key)


@router.get("/system/design/categories/list", response_model=ApiResponse)
def get_design_categories():
    """获取支持的产品设计品类列表."""
    svc = SystemService()
    return svc.get_design_categories()


# ---- 免责声明 ----

@router.get("/system/disclaimers", response_model=ApiResponse)
def get_disclaimers(db: Session = Depends(get_db)):
    """获取免责声明列表."""
    svc = SystemService(db)
    return svc.get_disclaimers()


@router.post("/system/disclaimers/accept", response_model=ApiResponse, dependencies=[Depends(require_auth)])
def accept_disclaimer(
    data: DisclaimerAcceptanceInput,
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db),
):
    """记录用户接受免责声明."""
    user_id = "default"
    uid = get_current_user_id(authorization)
    if uid != "local":
        user_id = uid

    svc = SystemService(db)
    return svc.accept_disclaimer(data.disclaimer_key, data.context, user_id)


@router.get("/system/onboarding-status", response_model=ApiResponse)
def get_onboarding_status(
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db),
):
    """获取用户 Onboarding 状态."""
    uid = get_current_user_id(authorization)
    user_id = "local" if uid == "local" else uid

    svc = SystemService(db)
    return svc.get_onboarding_status(user_id)
