"""P3.5.2: 简易 API 速率限制中间件.

使用内存字典实现滑动窗口速率限制，适合单机部署。
生产环境建议替换为 Redis 实现。
"""

import time
import re
from collections import defaultdict

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse


class RateLimitMiddleware(BaseHTTPMiddleware):
    """基于 IP 的请求速率限制（滑动窗口）."""

    _test_disable: bool = False

    def __init__(self, app, max_requests: int = 200, window_seconds: int = 60, enabled: bool = True):
        super().__init__(app)
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.enabled = enabled
        self._store: dict[str, list[float]] = defaultdict(list)

    async def dispatch(self, request: Request, call_next):
        # P3.6.11: 记录 API 调用统计
        try:
            from app.routers.system import record_api_call
            record_api_call(request.url.path)
        except Exception:
            pass

        # Skip rate limiting if disabled (e.g., during tests)
        if not self.enabled or RateLimitMiddleware._test_disable:
            return await call_next(request)

        # 不限制静态文件、健康检查和 MCP
        path = request.url.path
        if path.startswith("/api/files") or path == "/api/health" or path.startswith("/api/mcp"):
            return await call_next(request)

        client_ip = request.client.host if request.client else "unknown"
        now = time.time()
        window_start = now - self.window_seconds

        # 清理过期记录
        self._store[client_ip] = [t for t in self._store[client_ip] if t > window_start]

        if len(self._store[client_ip]) >= self.max_requests:
            return JSONResponse(
                status_code=429,
                content={"detail": "请求过于频繁，请稍后重试", "retry_after": self.window_seconds},
            )

        self._store[client_ip].append(now)
        return await call_next(request)
