"""v6.0 平台路由中间件 — X-Platform 请求头验证.

在请求上附加 platform 信息 (web/nuxt), 供路由层做角色过滤.
不做权限拦截 (由 Depends(require_creator/require_operator) 负责),
仅做平台归属标记.
"""

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response


class PlatformMiddleware(BaseHTTPMiddleware):
    """将 X-Platform 请求头暴露为 request.state.platform."""

    async def dispatch(self, request: Request, call_next) -> Response:
        platform = request.headers.get("x-platform", "")
        if platform in ("web", "nuxt", "miniprogram"):
            request.state.platform = platform
        else:
            # 未指定时根据 Token 中的 user 信息推断
            auth = request.headers.get("authorization", "")
            if auth.startswith("Bearer "):
                from app.deps import _verify_token
                user_id = _verify_token(auth[7:])
                if user_id:
                    from app.database import SessionLocal
                    from app.models.system import User
                    db = SessionLocal()
                    try:
                        user = db.query(User).filter(User.id == user_id).first()
                        if user:
                            request.state.platform = user.login_platform or "web"
                        else:
                            request.state.platform = "web"
                    finally:
                        db.close()
                else:
                    request.state.platform = "public"
            else:
                request.state.platform = "public"
        return await call_next(request)
