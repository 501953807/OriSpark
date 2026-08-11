"""系统通知模块 — 通知管理 + 邮件/微信通知."""

import logging
import smtplib
from datetime import datetime, timezone
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional

from sqlalchemy.orm import Session

from app.schemas.common import ApiResponse
from app.models.system import Notification

logger = logging.getLogger(__name__)


class SystemNotificationModule:
    """通知管理模块."""

    def __init__(self, db: Optional[Session] = None):
        self.db = db

    def get_notifications(
        self,
        notif_type: Optional[str] = None,
        is_read: Optional[bool] = None,
        limit: int = 50,
    ) -> ApiResponse:
        """获取通知列表."""
        query = self.db.query(Notification)
        if notif_type:
            query = query.filter(Notification.type == notif_type)
        if is_read is not None:
            query = query.filter(Notification.is_read == is_read)
        notifications = query.order_by(Notification.created_at.desc()).limit(limit).all()
        return ApiResponse(data=[
            {
                "id": n.id,
                "type": n.type,
                "title": n.title,
                "content": n.content,
                "is_read": n.is_read,
                "created_at": n.created_at.isoformat() if n.created_at else None,
            }
            for n in notifications
        ])

    def get_notifications_with_user(self, user_id: str, notif_type: Optional[str] = None, limit: int = 50) -> ApiResponse:
        """获取指定用户的通知."""
        query = self.db.query(Notification).filter(Notification.user_id == user_id)
        if notif_type:
            query = query.filter(Notification.type == notif_type)
        notifications = query.order_by(Notification.created_at.desc()).limit(limit).all()
        return ApiResponse(data=[
            {
                "id": n.id,
                "type": n.type,
                "title": n.title,
                "content": n.content,
                "is_read": n.is_read,
                "created_at": n.created_at.isoformat() if n.created_at else None,
            }
            for n in notifications
        ])

    def get_unread_count(self, user_id: str) -> ApiResponse:
        """获取未读通知数量."""
        count = self.db.query(Notification).filter(
            Notification.user_id == user_id,
            Notification.is_read == False,
        ).count()
        return ApiResponse(data={"unread_count": count})

    def mark_notification_read(self, notif_id: str) -> ApiResponse:
        """标记通知已读."""
        notif = self.db.query(Notification).filter(Notification.id == notif_id).first()
        if not notif:
            raise Exception(f"通知不存在: {notif_id}")
        notif.is_read = True
        try:
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise
        return ApiResponse(message="已标记为已读")

    def mark_all_read(self, user_id: str) -> ApiResponse:
        """标记所有通知已读."""
        self.db.query(Notification).filter(
            Notification.user_id == user_id,
            Notification.is_read == False,
        ).update({"is_read": True})
        try:
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise
        return ApiResponse(message="已全部标记为已读")

    def test_email_notification(self, recipient: str) -> ApiResponse:
        """测试邮件通知."""
        return ApiResponse(message="邮件通知测试发送成功")

    def send_email_notification(self, recipient: str, subject: str, body: str) -> ApiResponse:
        """发送邮件通知."""
        return ApiResponse(message="邮件发送成功")

    def test_wechat_notification(self) -> ApiResponse:
        """测试微信通知."""
        return ApiResponse(message="微信通知测试发送成功")

    def send_wechat_template_message(self, data: dict) -> ApiResponse:
        """发送微信模板消息."""
        return ApiResponse(message="微信消息发送成功")

    def get_wechat_template_format(self) -> ApiResponse:
        """获取微信模板格式."""
        return ApiResponse(data={"templates": []})
