"""系统审计模块 — 审计日志和 API 统计."""

import logging
from typing import Optional

from sqlalchemy.orm import Session
from sqlalchemy import func

from app.schemas.common import ApiResponse
from app.models.system import AuditLog

logger = logging.getLogger(__name__)


class SystemAuditModule:
    """审计日志模块."""

    def __init__(self, db: Optional[Session] = None):
        self.db = db

    def get_audit_logs(
        self,
        page: int = 1,
        page_size: int = 50,
        action: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> ApiResponse:
        """获取审计日志."""
        query = self.db.query(AuditLog)
        if action:
            query = query.filter(AuditLog.action.like(f"%{action}%"))
        if user_id:
            query = query.filter(AuditLog.user_id == user_id)
        total = query.count()
        logs = query.order_by(AuditLog.created_at.desc()).offset(
            (page - 1) * page_size
        ).limit(page_size).all()
        return ApiResponse(data={
            "items": [
                {
                    "id": l.id,
                    "user_id": l.user_id,
                    "action": l.action,
                    "module": l.module,
                    "detail": l.detail,
                    "created_at": l.created_at.isoformat() if l.created_at else None,
                }
                for l in logs
            ],
            "total": total,
            "page": page,
            "page_size": page_size,
        })

    def record_api_call(self, path: str) -> None:
        """记录 API 调用."""
        pass  # 由中间件处理
