"""审计日志中间件."""

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from app.database import SessionLocal
from app.models.system import AuditLog


class AuditMiddleware(BaseHTTPMiddleware):
    """记录审计日志 (非 GET 请求)."""

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)

        # 仅记录写操作
        if request.method not in ("GET", "HEAD", "OPTIONS"):
            try:
                db = SessionLocal()
                log = AuditLog(
                    action=f"{request.method} {request.url.path}",
                    detail=str(response.status_code),
                    ip=request.client.host if request.client else None,
                )
                db.add(log)
                db.commit()
                db.close()
            except Exception:
                pass  # 审计日志失败不阻断请求

        return response
