"""AuditLog 兼容层 - 供 routers 使用.

从 app.models.system 导入实际模型，提供静态 log() 方法.
"""

from app.models.system import AuditLog as _AuditLogModel


class AuditLog:
    """兼容类: 提供静态 log() 方法记录审计日志."""

    @staticmethod
    def log(db, action: str, detail: str = "", user_id: str = "") -> None:
        """记录审计日志."""
        try:
            log = _AuditLogModel(
                action=action,
                detail=detail,
                user_id=user_id,
            )
            db.add(log)
            db.commit()
        except Exception:
            pass  # 审计日志失败不阻断业务

    @staticmethod
    def query(db, limit: int = 100, offset: int = 0, **filters):
        """查询审计日志 (兼容旧接口)."""
        from sqlalchemy import and_, ilike
        query = db.query(_AuditLogModel)
        if filters.get("action"):
            query = query.filter(_AuditLogModel.action.ilike(f"%{filters['action']}%"))
        if filters.get("module"):
            query = query.filter(_AuditLogModel.module == filters["module"])
        if filters.get("user_id"):
            query = query.filter(_AuditLogModel.user_id == filters["user_id"])
        return query.order_by(_AuditLogModel.created_at.desc()).offset(offset).limit(limit).all()
