"""JWT 认证 API 路由 — 对应: docs/modules-v5/07-system-infra.md
Phase 2: Onboarding API, creator_type 字段
端点: 15 (auth)

Features:
- 微信 OAuth 回调
- 抖音 OAuth 回调
- 本地免登录模式

用户数据存储: SQLite users 表 (替代原 users.json，向后兼容)
"""

import json
import hashlib
import hmac
import time
from datetime import datetime, timedelta, timezone
from typing import Optional
from pathlib import Path
import bcrypt

from fastapi import APIRouter, HTTPException, Header, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.system import User, UserLoginHistory
from app.config import settings
from app.schemas.common import ApiResponse
from app.deps import get_current_user_id, _verify_token, _sign, _add_to_blacklist

router = APIRouter()

# 本地 JWT secret
SECRET = settings.SECRET_KEY.encode()

# User storage file (backward compatible, auto-migrated on startup)
USERS_FILE = Path("data/config/users.json")


# ================================================================
# -- JWT Token 工具 --
# ================================================================

def _hash_password(password: str) -> str:
    """Hash password using bcrypt with cost factor 12."""
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')


def _verify_password(plain_password: str, hashed_password: str) -> tuple[bool, bool]:
    """Verify a password against its hash. Supports bcrypt hashes and falls back to SHA256 for legacy data.

    Returns:
        tuple: (is_password_correct, needs_password_upgrade)
               second flag is True if the stored hash uses weak SHA256 and should be upgraded
    """
    # First try bcrypt (new format: $2b$, $2a$, $2y$)
    if hashed_password.startswith('$2b$') or hashed_password.startswith('$2a$') or hashed_password.startswith('$2y$'):
        return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8')), False

    # Fallback: legacy SHA256 hash (first 16 chars of hex digest) - WEAK!
    if len(hashed_password) == 32 and all(c in '0123456789abcdef' for c in hashed_password):
        expected = hashlib.sha256(plain_password.encode('utf-8')).hexdigest()[:16]
        return hmac.compare_digest(expected, hashed_password), True

    return False, False


def _create_token(user_id: str) -> str:
    """创建简单的 JWT-like token."""
    header = {"alg": "HS256", "typ": "JWT"}
    payload = {
        "sub": user_id,
        "iat": int(time.time()),
        "exp": int(time.time()) + 86400 * 30,  # 30 天
    }
    import base64 as _base64
    header_b64 = _base64.urlsafe_b64encode(json.dumps(header).encode()).decode().rstrip("=")
    payload_b64 = _base64.urlsafe_b64encode(json.dumps(payload).encode()).decode().rstrip("=")
    signature = _sign(f"{header_b64}.{payload_b64}")
    return f"{header_b64}.{payload_b64}.{signature}"


def _migrate_json_users(db: Session):
    """从 users.json 迁移用户到 SQLite，保持向后兼容."""
    if not USERS_FILE.exists():
        return

    try:
        json_users = json.loads(USERS_FILE.read_text())
    except (json.JSONDecodeError, IOError):
        return

    migrated = 0
    for email, data in json_users.items():
        existing = db.query(User).filter(User.email == email).first()
        if existing:
            continue

        user = User(
            id=data.get("id", hashlib.md5(email.encode()).hexdigest()[:16]),
            username=data.get("username", "创作者"),
            email=email,
            password_hash=data.get("password_hash"),
            role="user",
            status="active",
            created_at=datetime.fromisoformat(data["created_at"]) if data.get("created_at") else datetime.now(timezone.utc),
        )
        db.add(user)
        migrated += 1

    if migrated > 0:
        try:
            db.commit()
        except Exception:
            db.rollback()
            raise
        # 迁移后重命名旧文件备份
        USERS_FILE.rename(USERS_FILE.with_suffix(".json.bak"))


def _get_user_from_db(user_id: str, db: Session) -> Optional[User]:
    """从数据库获取用户."""
    return db.query(User).filter(User.id == user_id).first()


# ================================================================
# -- 请求模型 --
# ================================================================

class LoginRequest(BaseModel):
    email: str
    password: str


class RegisterRequest(BaseModel):
    username: str
    email: str
    password: str


class AuthResponse(BaseModel):
    token: str
    user: dict


class OAuthCallbackRequest(BaseModel):
    """OAuth 回调通用请求体."""
    code: Optional[str] = None
    id_token: Optional[str] = None
    state: Optional[str] = None
    access_token: Optional[str] = None


def _user_to_dict(user: User) -> dict:
    """用户对象转字典."""
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "role": "管理员" if user.role == "admin" else ("本地用户" if user.role == "local" else "注册用户"),
        "avatar_url": user.avatar_url,
        "google_name": user.google_name,
        "google_picture": user.google_picture,
        "wechat_nickname": user.wechat_nickname,
        "wechat_avatar": user.wechat_avatar,
        "douyin_nickname": user.douyin_nickname,
        "douyin_avatar": user.douyin_avatar,
        "email_verified": user.email_verified,
        "status": user.status,
        "last_login_at": user.last_login_at.isoformat() if user.last_login_at else None,
        "last_login_provider": user.last_login_provider,
    }


# ================================================================
# -- Auth API Endpoints --
# ================================================================

@router.post("/auth/register", response_model=ApiResponse)
def register(data: RegisterRequest, db: Session = Depends(get_db)):
    """用户注册."""
    _migrate_json_users(db)

    existing = db.query(User).filter(User.email == data.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="该邮箱已注册")

    user = User(
        id=hashlib.md5(data.email.encode()).hexdigest()[:16],
        username=data.username,
        email=data.email,
        password_hash=_hash_password(data.password),
        role="user",
        status="active",
    )
    db.add(user)

    # 记录登录
    db.add(UserLoginHistory(
        id=hashlib.md5(f"reg_{user.id}_{time.time()}".encode()).hexdigest()[:16],
        user_id=user.id,
        provider="email",
    ))

    try:
        db.commit()
    except Exception:
        db.rollback()
        raise

    token = _create_token(user.id)
    return ApiResponse(data={
        "token": token,
        "user": _user_to_dict(user),
    })


@router.post("/auth/login", response_model=ApiResponse)
def login(data: LoginRequest, db: Session = Depends(get_db)):
    """用户登录."""
    _migrate_json_users(db)

    user = db.query(User).filter(User.email == data.email).first()

    if not user:
        raise HTTPException(status_code=401, detail="邮箱或密码错误")

    # Verify password and check if upgrade needed
    is_valid, needs_upgrade = _verify_password(data.password, user.password_hash)
    if not is_valid:
        raise HTTPException(status_code=401, detail="邮箱或密码错误")

    # Upgrade old SHA256 hash to bcrypt if needed
    if needs_upgrade:
        user.password_hash = _hash_password(data.password)

    # 更新登录信息
    user.last_login_at = datetime.now(timezone.utc)
    user.last_login_provider = "email"
    user.login_count = (user.login_count or 0) + 1

    # 记录登录历史
    db.add(UserLoginHistory(
        id=hashlib.md5(f"login_{user.id}_{time.time()}".encode()).hexdigest()[:16],
        user_id=user.id,
        provider="email",
        success=True,
    ))

    try:
        db.commit()
    except Exception:
        db.rollback()
        raise

    token = _create_token(user.id)
    return ApiResponse(data={
        "token": token,
        "user": _user_to_dict(user),
    })


@router.get("/auth/me", response_model=ApiResponse)
def get_current_user(
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db),
):
    """获取当前登录用户信息."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="缺少认证凭证")

    token = authorization.replace("Bearer ", "")
    user_id = _verify_token(token)
    if not user_id:
        raise HTTPException(status_code=401, detail="认证令牌无效或已过期")

    # 从数据库查找
    user = db.query(User).filter(User.id == user_id).first()
    if user:
        return ApiResponse(data=_user_to_dict(user))

    # 向后兼容: JSON 文件 (for legacy users in users.json)
    if USERS_FILE.exists():
        try:
            users = json.loads(USERS_FILE.read_text())
            for email, u in users.items():
                if u.get("id") == user_id:
                    return ApiResponse(data={
                        "id": u["id"],
                        "username": u.get("username", "创作者"),
                        "email": u.get("email", email),
                        "role": "注册用户",
                    })
        except (json.JSONDecodeError, IOError):
            pass

    raise HTTPException(status_code=401, detail="认证令牌无效或已过期")


@router.patch("/auth/me", response_model=ApiResponse)
def update_user_profile(
    updates: dict,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """更新用户资料."""
    if user_id == "local":
        raise HTTPException(status_code=401, detail="请先登录")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    updatable = ["username", "avatar_url", "phone"]
    for field in updatable:
        if field in updates and updates[field] is not None:
            setattr(user, field, updates[field])

    try:
        db.commit()
    except Exception:
        db.rollback()
        raise
    return ApiResponse(data=_user_to_dict(user), message="资料已更新")


# ================================================================
# -- OAuth 认证端点 (stub — 真实 OAuth 需要注册应用) --
# ================================================================

@router.post("/auth/google/callback", response_model=ApiResponse)
def google_callback(data: OAuthCallbackRequest, db: Session = Depends(get_db)):
    """Google OAuth 登录回调 (stub).

    完整实现需要:
    1. 使用 google-auth 库验证 id_token
    2. 提取 google_id, email, name, picture
    3. 查找或创建 User
    """
    if not data.id_token:
        raise HTTPException(status_code=400, detail="需要 Google ID Token")

    # Stub: 在真实部署中，此处验证 Google JWT 签名
    # from google.oauth2 import id_token
    # from google.auth.transport import requests
    # idinfo = id_token.verify_oauth2_token(data.id_token, requests.Request(), GOOGLE_CLIENT_ID)

    # Stub 返回
    return ApiResponse(
        message="Google OAuth 功能需要配置 GOOGLE_CLIENT_ID 后启用",
        data={"status": "not_configured"},
    )


@router.get("/auth/google/url", response_model=ApiResponse)
def google_login_url():
    """获取 Google OAuth 登录URL."""
    google_client_id = settings.__class__.model_fields.get("GOOGLE_CLIENT_ID")
    return ApiResponse(
        message="Google OAuth 功能需要配置 GOOGLE_CLIENT_ID 后启用",
        data={"url": None},
    )


@router.post("/auth/wechat/login", response_model=ApiResponse)
def wechat_miniapp_login(data: dict, db: Session = Depends(get_db)):
    """微信小程序微信登录（基于 code 换 openid）.

    Mini Program 流程:
    1. 前端调用 wx.login() 获取 code
    2. 发送 code 到此端点
    3. 后端用 code 换 openid/session_key
    4. 创建/查找用户，签发 JWT
    """
    code = data.get("code", "")
    if not code:
        raise HTTPException(status_code=400, detail="code 不能为空")

    # 模拟微信 openid 返回（生产环境需调用微信 API）
    import hashlib, time
    openid = hashlib.md5(f"miniapp_{code}_{int(time.time())}".encode()).hexdigest()[:16]

    user = _get_user_from_db(openid, db)
    if not user:
        user = User(
            id=openid,
            username=f"wx_{openid[:8]}",
            email=f"wx_{openid[:8]}@wechat.local",
            is_active=True,
            wechat_openid=openid,
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    token = _create_token(user.id)
    return ApiResponse(
        message="登录成功",
        data={
            "token": token,
            "user": _user_to_dict(user),
            "login_provider": "wechat_miniapp",
        },
    )


@router.get("/auth/wechat/qrcode", response_model=ApiResponse)
def wechat_qrcode():
    """获取微信扫码登录URL."""
    return ApiResponse(
        message="微信登录功能需要配置 WECHAT_APPID 后启用",
        data={"url": None},
    )


@router.post("/auth/wechat/callback", response_model=ApiResponse)
def wechat_callback(data: OAuthCallbackRequest, db: Session = Depends(get_db)):
    """微信 OAuth 登录回调 (stub).

    完整实现需要:
    1. 用 code 换 access_token (调用微信 /sns/oauth2/access_token)
    2. 用 access_token 获取用户信息 (/sns/userinfo)
    3. 查找或创建 User (按 unionid/openid)
    """
    return ApiResponse(
        message="微信登录功能需要配置 WECHAT_APPID + WECHAT_SECRET 后启用",
        data={"status": "not_configured"},
    )


@router.get("/auth/douyin/url", response_model=ApiResponse)
def douyin_login_url():
    """获取抖音授权URL."""
    return ApiResponse(
        message="抖音登录功能需要配置 DOUYIN_CLIENT_KEY 后启用",
        data={"url": None},
    )


@router.post("/auth/douyin/callback", response_model=ApiResponse)
def douyin_callback(data: OAuthCallbackRequest, db: Session = Depends(get_db)):
    """抖音 OAuth 登录回调 (stub).

    完整实现需要:
    1. 用 code 换 access_token (调用抖音 /oauth/access_token/)
    2. 获取用户信息 (/oauth/userinfo/)
    3. 查找或创建 User (按 open_id/union_id)
    """
    return ApiResponse(
        message="抖音登录功能需要配置 DOUYIN_CLIENT_KEY + DOUYIN_CLIENT_SECRET 后启用",
        data={"status": "not_configured"},
    )


# ================================================================
# -- 关联账号管理 --
# ================================================================

@router.post("/auth/bind/{provider}", response_model=ApiResponse)
def bind_provider(
    provider: str,
    data: OAuthCallbackRequest,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """绑定第三方账号到当前用户."""
    if user_id == "local":
        raise HTTPException(status_code=401, detail="请先登录")

    if provider not in ("google", "wechat", "douyin"):
        raise HTTPException(status_code=400, detail=f"不支持的认证提供方: {provider}")

    return ApiResponse(
        message=f"{provider} 绑定功能需要配置相应的 OAuth 凭证后启用",
        data={"status": "not_configured"},
    )


@router.delete("/auth/unbind/{provider}", response_model=ApiResponse)
def unbind_provider(
    provider: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """解绑第三方账号."""
    if user_id == "local":
        raise HTTPException(status_code=401, detail="请先登录")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    if provider == "google":
        user.google_id = None
        user.google_email = None
        user.google_name = None
        user.google_picture = None
    elif provider == "wechat":
        user.wechat_openid = None
        user.wechat_unionid = None
        user.wechat_nickname = None
        user.wechat_avatar = None
    elif provider == "douyin":
        user.douyin_openid = None
        user.douyin_unionid = None
        user.douyin_nickname = None
        user.douyin_avatar = None
    else:
        raise HTTPException(status_code=400, detail=f"不支持的认证提供方: {provider}")

    try:
        db.commit()
    except Exception:
        db.rollback()
        raise
    return ApiResponse(message=f"已解绑 {provider} 账号")


# ================================================================
# -- P3.5.5: Token 注销 / 退出登录 --
# ================================================================

@router.post("/auth/logout", response_model=ApiResponse)
def logout(
    authorization: Optional[str] = Header(None),
):
    """退出登录: 将当前 token 加入黑名单."""
    if not authorization or not authorization.startswith("Bearer "):
        return ApiResponse(message="已退出登录")

    token = authorization.replace("Bearer ", "")
    if token:
        _add_to_blacklist(token)

    return ApiResponse(message="已退出登录，Token 已失效")


@router.get("/auth/sessions", response_model=ApiResponse)
def list_sessions(
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db),
):
    """列出当前用户会话."""
    if not authorization or not authorization.startswith("Bearer "):
        return ApiResponse(data={"active_tokens": 0, "sessions": []})

    token = authorization.replace("Bearer ", "")
    user_id = _verify_token(token)
    if not user_id:
        return ApiResponse(data={"active_tokens": 0, "sessions": []})

    # 从登录历史获取
    sessions = db.query(UserLoginHistory).filter(
        UserLoginHistory.user_id == user_id,
        UserLoginHistory.success == True,
    ).order_by(UserLoginHistory.timestamp.desc()).limit(10).all()

    return ApiResponse(data={
        "active_tokens": 1,
        "sessions": [
            {
                "provider": s.provider,
                "timestamp": s.created_at.isoformat() if s.created_at else None,
            }
            for s in sessions
        ],
    })


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str


@router.post("/auth/change-password", response_model=ApiResponse)
def change_password(
    data: ChangePasswordRequest,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """修改密码."""
    if user_id == "local":
        raise HTTPException(status_code=401, detail="请先登录")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    is_valid, _ = _verify_password(data.current_password, user.password_hash)
    if not is_valid:
        raise HTTPException(status_code=400, detail="当前密码不正确")

    user.password_hash = _hash_password(data.new_password)

    try:
        db.commit()
    except Exception:
        db.rollback()
        raise

    return ApiResponse(message="密码已修改")


# -- v3 Onboarding --

class CompleteOnboardingRequest(BaseModel):
    creator_type: str


@router.post("/auth/complete-onboarding", response_model=ApiResponse)
def complete_onboarding(
    data: CompleteOnboardingRequest,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """完成 Onboarding 向导, 持久化 creator_type 和默认配置."""
    if user_id == "local":
        raise HTTPException(status_code=401, detail="请先登录")

    creator_type = data.creator_type
    VALID_CREATOR_TYPES = (
        "illustrator", "photographer", "video_creator",
        "crafter", "musician", "writer",
    )
    if not creator_type or creator_type not in VALID_CREATOR_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"无效的创作者类型，可选值: {', '.join(VALID_CREATOR_TYPES)}",
        )

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    user.creator_type = creator_type

    # 标记 Onboarding 完成
    setting = db.query(SystemSetting).filter(
        SystemSetting.key == "onboarding_completed"
    ).first()
    if setting:
        setting.value = "true"
    else:
        db.add(SystemSetting(
            key="onboarding_completed",
            value="true",
            category="user",
            description="用户是否已完成 Onboarding 向导",
        ))

    # 自动配置默认分发平台 (按创作者类型)
    default_platforms = CREATOR_DEFAULT_PLATFORMS.get(creator_type, [])
    platform_setting = db.query(SystemSetting).filter(
        SystemSetting.key == "default_publish_platforms"
    ).first()
    if platform_setting:
        platform_setting.value = ",".join(default_platforms)
    else:
        db.add(SystemSetting(
            key="default_publish_platforms",
            value=",".join(default_platforms),
            category="user",
            description="用户默认分发平台列表",
        ))

    try:
        db.commit()
    except Exception:
        db.rollback()
        raise

    return ApiResponse(data={
        "creator_type": creator_type,
        "onboarding_completed": True,
        "default_platforms": default_platforms,
    }, message="Onboarding 完成")


CREATOR_DEFAULT_PLATFORMS = {
    "illustrator": ["xiaohongshu", "zcool", "bilibili"],
    "photographer": ["xiaohongshu", "instagram", "weibo"],
    "video_creator": ["bilibili", "douyin", "youtube"],
    "crafter": ["xiaohongshu", "etsy", "instagram"],
    "musician": ["bilibili", "douyin", "spotify"],
    "writer": ["wechat", "xiaohongshu", "qidian"],
}
