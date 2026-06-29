"""Reusable dependencies for FastAPI routes.

Central place for shared auth, db, and error-handling dependencies.
"""

from typing import Optional

from fastapi import Depends, Header, HTTPException, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.database import get_db
from app.config import settings
from app.models.system import User as UserModel

# Local JWT secret
_SECRET = settings.SECRET_KEY.encode()

# P3.5.5: Token 黑名单 (内存字典，重启后失效 — 生产环境改用 Redis)
_token_blacklist: dict[str, float] = {}


def _deb64(data: str) -> str:
    import base64
    padding = 4 - len(data) % 4
    if padding != 4:
        data += "=" * padding
    return base64.urlsafe_b64decode(data).decode()


def _sign(data: str) -> str:
    import hashlib
    import hmac as _hmac
    return _hmac.new(_SECRET, data.encode(), hashlib.sha256).hexdigest()[:32]


def _verify_token(token: str) -> Optional[str]:
    """验证 token 并返回 user_id.

    P3.5.5: 检查 token 是否在黑名单中。
    Moved here to break circular import (was in auth.py).
    """
    if token in _token_blacklist:
        return None

    import time as _time
    now = _time.time()
    expired = [t for t, ts in _token_blacklist.items() if now - ts > 86400 * 30]
    for t in expired:
        del _token_blacklist[t]

    try:
        parts = token.split(".")
        if len(parts) != 3:
            return None
        header_b64, payload_b64, signature = parts
        expected_sig = _sign(f"{header_b64}.{payload_b64}")
        if not _hmac.compare_digest(signature, expected_sig):
            return None
        import json as _json
        payload = _json.loads(_deb64(payload_b64))
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
        The verified user_id string, or falls back to "local" for
        unauthenticated / demo mode (matching existing app behavior).

    Usage:
        @router.get("/protected", response_model=ApiResponse)
        def protected_endpoint(
            user_id: str = Depends(get_current_user_id),
            db: Session = Depends(get_db),
        ):
            ...
    """
    if not authorization or not authorization.startswith("Bearer "):
        return "local"

    token = authorization.replace("Bearer ", "")
    user_id = _verify_token(token)
    if not user_id:
        return "local"

    return user_id


def get_current_user(
    authorization: Optional[str] = Header(None, alias="Authorization"),
    db: Session = Depends(get_db),
) -> Optional[UserModel]:
    """Return the authenticated UserModel, or None for unauthenticated/demos."""
    user_id = get_current_user_id(authorization)
    if user_id == "local":
        return None
    return db.query(UserModel).filter(UserModel.id == user_id).first()


def require_auth(
    authorization: Optional[str] = Header(None, alias="Authorization"),
) -> str:
    """Require authentication. Returns user_id.

    Accepts a valid HMAC-signed token, OR falls back to "local" for
    development/demo mode (matching get_current_user_id behavior).
    """
    user_id = get_current_user_id(authorization)
    return user_id
