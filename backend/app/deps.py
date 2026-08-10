"""Reusable dependencies for FastAPI routes.

Central place for shared auth, db, and error-handling dependencies.
"""

from typing import Optional, Dict, Any
import time as _time
import json as _json
import hmac as _hmac
import hashlib
import base64
from pathlib import Path

from fastapi import Depends, Header, HTTPException, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.database import get_db
from app.config import settings
from app.models.system import User as UserModel

# Local JWT secret
_SECRET = settings.SECRET_KEY.encode()

# P3.5.5: Token 黑名单 (内存字典，重启后失效 — 生产环境改用 Redis)
_token_blacklist: Dict[str, float] = {}

# Optional Redis client for production
_redis_client: Optional[Any] = None


def _init_redis():
    """尝试初始化 Redis 客户端，失败则设为 None."""
    global _redis_client
    try:
        import redis
        r = redis.from_url(settings.REDIS_URL, socket_connect_timeout=2)
        r.ping()
        _redis_client = r
        print(f"Redis token blacklist initialized: {settings.REDIS_URL}")
    except Exception:
        _redis_client = None  # Fallback to memory


# Initialize Redis on import
_init_redis()


def _add_to_blacklist(token: str, expires: float = None) -> None:
    """将 token 加入黑名单。若设置了 expires，使用 Redis TTL."""
    if _redis_client:
        # Use Redis with TTL (30 days same as token expiry)
        ttl = int(expires - _time.time()) if expires and expires > _time.time() else 86400 * 30
        _redis_client.setex(token, ttl, "1")
    else:
        _token_blacklist[token] = _time.time()


def _is_blacklisted(token: str) -> bool:
    """检查 token 是否在黑名单中."""
    if _redis_client:
        return _redis_client.exists(token) == 1
    return token in _token_blacklist


def _cleanup_blacklist() -> None:
    """清理过期的黑名单项。Redis 会自动处理 TTL，内存版需要手动清理."""
    if not _redis_client:
        now = _time.time()
        expired = [t for t, ts in _token_blacklist.items() if now - ts > 86400 * 30]
        for t in expired:
            del _token_blacklist[t]


def _deb64(data: str) -> str:
    import base64
    padding = 4 - len(data) % 4
    if padding != 4:
        data += "=" * padding
    return base64.urlsafe_b64decode(data).decode()


def _sign(data: str) -> str:
    """Generate a secure HMAC-SHA256 signature (full 64-char hex digest)."""
    return _hmac.new(_SECRET, data.encode(), hashlib.sha256).hexdigest()


def _verify_token(token: str) -> Optional[str]:
    """验证 token 并返回 user_id.

    P3.5.5: 检查 token 是否在黑名单中。
    Moved here to break circular import (was in auth.py).
    """
    # Clean up expired blacklist entries first
    _cleanup_blacklist()

    # Check if token is blacklisted using unified method
    if _is_blacklisted(token):
        return None

    try:
        parts = token.split(".")
        if len(parts) != 3:
            return None
        header_b64, payload_b64, signature = parts

        # Validate signature length (64 hex chars for full HMAC-SHA256)
        if len(signature) != 64:
            return None

        expected_sig = _sign(f"{header_b64}.{payload_b64}")
        if not _hmac.compare_digest(signature, expected_sig):
            return None
        payload = _json.loads(_deb64(payload_b64))
        now = _time.time()
        if payload.get("exp", 0) < now:
            return None
        return payload.get("sub")
    except Exception:
        return None


# Optional: HTTP Bearer token extractor (allows Depends(security_scheme))
security_scheme = HTTPBearer(auto_error=False)


def get_current_user_id(
    authorization: Optional[str] = Header(None, alias="Authorization"),
) -> str:
    """Extract and verify the current user ID from the Authorization header.

    Returns:
        The verified user_id string.

    Raises:
        HTTPException(401): If no valid authentication header is provided.

    Usage:
        @router.get("/protected", response_model=ApiResponse)
        def protected_endpoint(
            user_id: str = Depends(get_current_user_id),
            db: Session = Depends(get_db),
        ):
            ...
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="缺少认证凭证")

    token = authorization.replace("Bearer ", "")
    user_id = _verify_token(token)
    if not user_id:
        raise HTTPException(status_code=401, detail="认证令牌无效或已过期")

    return user_id


def require_auth(
    authorization: Optional[str] = Header(None, alias="Authorization"),
) -> str:
    """Require authentication. Returns user_id.

    Requires a valid HMAC-signed token. Raises 401 if authentication is missing or invalid.

    Args:
        authorization: Authorization header with Bearer token

    Returns:
        The authenticated user_id

    Raises:
        HTTPException(401): If authentication fails
    """
    return get_current_user_id(authorization)


def is_admin(user_id: str) -> bool:
    """Check if user has admin privileges.

    In production this would check user roles in database.
    For development, admin users can be configured via ADMIN_IDS env var.

    Args:
        user_id: The user ID to check

    Returns:
        True if user is admin, False otherwise
    """
    import os
    admin_ids = os.environ.get("ADMIN_IDS", "").split(",")
    if not admin_ids or admin_ids == ['']:
        return False
    return user_id.strip() in [a.strip() for a in admin_ids if a.strip()]


def get_current_user(
    authorization: Optional[str] = Header(None, alias="Authorization"),
    db: Session = Depends(get_db),
) -> Optional[UserModel]:
    """Return the authenticated UserModel for authorized requests only.

    Note: This function uses get_current_user_id which raises HTTPException(401) on invalid auth.
    For demo purposes where unauthenticated access is allowed, call get_current_user_id directly.

    Args:
        authorization: Authorization header with Bearer token
        db: Database session

    Returns:
        The authenticated UserModel, or None if not found in database

    Raises:
        HTTPException(401): If authentication is missing or invalid
    """
    user_id = get_current_user_id(authorization)
    return db.query(UserModel).filter(UserModel.id == user_id).first()


# ================================================================
# -- v6.0 平台角色依赖 --
# ================================================================

def require_creator(
    authorization: Optional[str] = Header(None, alias="Authorization"),
    db: Session = Depends(get_db),
) -> UserModel:
    """要求创作者角色登录. 非创作者返回 403."""
    user = get_current_user(authorization, db)
    if not user:
        raise HTTPException(status_code=401, detail="认证失败")
    if not user.creator_type:
        raise HTTPException(status_code=403, detail="需要创作者账号")
    return user


def require_operator(
    authorization: Optional[str] = Header(None, alias="Authorization"),
    db: Session = Depends(get_db),
) -> UserModel:
    """要求非创作者角色登录. 创作者返回 403."""
    user = get_current_user(authorization, db)
    if not user:
        raise HTTPException(status_code=401, detail="认证失败")
    roles = user.participant_roles or []
    if not roles or roles == ["creator"]:
        raise HTTPException(status_code=403, detail="需要运营者账号")
    return user
