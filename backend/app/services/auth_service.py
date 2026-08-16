"""认证服务层 — 从 auth.py 提取的业务逻辑."""

import hashlib
import hmac
import json
import time
from datetime import datetime, timezone, date
from typing import Optional
from pathlib import Path

from sqlalchemy.orm import Session

from app.models.system import User, UserLoginHistory, SystemSetting

USERS_FILE = Path("data/config/users.json")


# ================================================================
# -- JWT Token 工具 --
# ================================================================

def _hash_password(password: str) -> str:
    """Hash password using bcrypt with cost factor 12."""
    import bcrypt
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')


def _verify_password(plain_password: str, hashed_password: str) -> tuple[bool, bool]:
    """Verify a password against its hash. Supports bcrypt and legacy SHA256.

    Returns:
        tuple: (is_password_correct, needs_password_upgrade)
    """
    if hashed_password.startswith('$2b$') or hashed_password.startswith('$2a$') or hashed_password.startswith('$2y$'):
        import bcrypt
        return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8')), False

    if len(hashed_password) == 32 and all(c in '0123456789abcdef' for c in hashed_password):
        expected = hashlib.sha256(plain_password.encode('utf-8')).hexdigest()[:16]
        return hmac.compare_digest(expected, hashed_password), True

    return False, False


def _create_token(user_id: str) -> str:
    """创建简单的 JWT-like token."""
    from app.config import settings
    import base64 as _base64
    header = {"alg": "HS256", "typ": "JWT"}
    payload = {"sub": user_id, "iat": int(time.time()), "exp": int(time.time()) + 86400 * 30}
    secret = settings.SECRET_KEY.encode()
    header_b64 = _base64.urlsafe_b64encode(json.dumps(header).encode()).decode().rstrip("=")
    payload_b64 = _base64.urlsafe_b64encode(json.dumps(payload).encode()).decode().rstrip("=")
    signature = hmac.new(secret, f"{header_b64}.{payload_b64}".encode(), hashlib.sha256).hexdigest()
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
        USERS_FILE.rename(USERS_FILE.with_suffix(".json.bak"))


def _user_to_dict(user: User) -> dict:
    """用户对象转字典."""
    roles = user.participant_roles or []
    role_name_map = {
        "creator": "创作者",
        "operator": "运营方",
        "legal_rep": "法务代表",
        "tax_agent": "税务代理",
        "logistics": "物流方",
        "insurer": "保险方",
        "trader": "采购方",
        "payment_provider": "支付托管方",
        "platform": "平台方",
    }
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "role": "管理员" if user.role == "admin" else ("本地用户" if user.role == "local" else "注册用户"),
        "participant_roles": roles,
        "participant_role_names": [role_name_map.get(r, r) for r in roles],
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
        "creator_type": user.creator_type,
        "company_name": user.company_name,
        "company_license_no": user.company_license_no,
        "qualification_verified": user.qualification_verified,
        "login_platform": user.login_platform,
    }


# ================================================================
# -- 核心业务函数 --
# ================================================================


def get_or_create_local_user(db: Session) -> tuple[dict, str]:
    """获取或创建本地演示用户，用于开发/演示模式免登录."""
    _migrate_json_users(db)

    local_user = db.query(User).filter(User.id == "local").first()
    if local_user:
        local_user.last_login_at = datetime.now(timezone.utc)
        local_user.last_login_provider = "local"
        local_user.login_count = (local_user.login_count or 0) + 1
        db.add(UserLoginHistory(
            id=hashlib.md5(f"login_local_{time.time()}".encode()).hexdigest()[:16],
            user_id="local",
            provider="local",
            success=True,
        ))
        try:
            db.commit()
        except Exception:
            db.rollback()
            raise
        # 重新查询以确保获取最新数据
        db.refresh(local_user)
        token = _create_token("local")
        return _user_to_dict(local_user), token

    user = User(
        id="local",
        username="创作者",
        email="local@oristudio",
        password_hash=_hash_password("local"),
        role="local",
        status="active",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    token = _create_token("local")
    return _user_to_dict(user), token


def register_user(db: Session, username: str, email: str, password: str) -> tuple[dict, str]:
    """用户注册. Returns: (user_dict, token)."""
    _migrate_json_users(db)

    existing = db.query(User).filter(User.email == email).first()
    if existing:
        raise ValueError("该邮箱已注册")

    user_id = hashlib.md5(email.encode()).hexdigest()[:16]
    user = User(
        id=user_id,
        username=username,
        email=email,
        password_hash=_hash_password(password),
        role="user",
        status="active",
    )
    db.add(user)
    db.add(UserLoginHistory(
        id=hashlib.md5(f"reg_{user_id}_{time.time()}".encode()).hexdigest()[:16],
        user_id=user_id,
        provider="email",
    ))

    try:
        db.commit()
    except Exception:
        db.rollback()
        raise

    token = _create_token(user_id)
    return _user_to_dict(user), token


def register_creator(db: Session, username: str, email: str, password: str) -> tuple[dict, str]:
    """创作者注册 — 设置 login_platform='web'."""
    _migrate_json_users(db)

    existing = db.query(User).filter(User.email == email).first()
    if existing:
        raise ValueError("该邮箱已注册")

    user_id = hashlib.md5(email.encode()).hexdigest()[:16]
    user = User(
        id=user_id,
        username=username,
        email=email,
        password_hash=_hash_password(password),
        role="user",
        status="active",
        login_platform="web",
    )
    db.add(user)
    db.add(UserLoginHistory(
        id=hashlib.md5(f"reg_{user_id}_{time.time()}".encode()).hexdigest()[:16],
        user_id=user_id,
        provider="email",
    ))

    try:
        db.commit()
    except Exception:
        db.rollback()
        raise

    token = _create_token(user_id)
    return _user_to_dict(user), token


def register_operator(db: Session, username: str, email: str, password: str,
                      participant_roles: list[str]) -> tuple[dict, str]:
    """非创作者注册 — 设置 login_platform='nuxt'."""
    _migrate_json_users(db)

    existing = db.query(User).filter(User.email == email).first()
    if existing:
        raise ValueError("该邮箱已注册")

    user_id = hashlib.md5(email.encode()).hexdigest()[:16]
    user = User(
        id=user_id,
        username=username,
        email=email,
        password_hash=_hash_password(password),
        role="user",
        status="active",
        login_platform="nuxt",
        participant_roles=participant_roles,
    )
    db.add(user)
    db.add(UserLoginHistory(
        id=hashlib.md5(f"reg_{user_id}_{time.time()}".encode()).hexdigest()[:16],
        user_id=user_id,
        provider="email",
    ))

    try:
        db.commit()
    except Exception:
        db.rollback()
        raise

    token = _create_token(user_id)
    return _user_to_dict(user), token


def login_user(db: Session, email: str, password: str) -> tuple[dict, str]:
    """用户登录. Returns: (user_dict, token)."""
    _migrate_json_users(db)

    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise ValueError("邮箱或密码错误")

    is_valid, needs_upgrade = _verify_password(password, user.password_hash)
    if not is_valid:
        raise ValueError("邮箱或密码错误")

    if needs_upgrade:
        user.password_hash = _hash_password(password)

    user.last_login_at = datetime.now(timezone.utc)
    user.last_login_provider = "email"
    user.login_count = (user.login_count or 0) + 1

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
    return _user_to_dict(user), token


def get_user_by_id(db: Session, user_id: str) -> Optional[User]:
    """按 ID 查询用户."""
    return db.query(User).filter(User.id == user_id).first()


def update_user_profile(db: Session, user_id: str, updates: dict) -> dict:
    """更新用户资料. Returns: updated user dict."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise ValueError("用户不存在")

    updatable = ["username", "avatar_url", "phone"]
    for field in updatable:
        if field in updates and updates[field] is not None:
            setattr(user, field, updates[field])

    try:
        db.commit()
    except Exception:
        db.rollback()
        raise
    return _user_to_dict(user)


def get_user_by_openid(db: Session, openid: str) -> Optional[User]:
    """按 openid 查询微信用户."""
    return db.query(User).filter(User.id == openid).first()


def create_user_from_openid(openid: str, db: Session) -> User:
    """创建微信用户."""
    username = f"wx_{openid[:8]}"
    user = User(
        id=openid,
        username=username,
        email=f"{username}@wechat.local",
        is_active=True,
        wechat_openid=openid,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def unbind_provider(db: Session, user_id: str, provider: str) -> bool:
    """解绑第三方账号. Returns: True if successful."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise ValueError("用户不存在")

    if provider == "google":
        user.google_id = None; user.google_email = None
        user.google_name = None; user.google_picture = None
    elif provider == "wechat":
        user.wechat_openid = None; user.wechat_unionid = None
        user.wechat_nickname = None; user.wechat_avatar = None
    elif provider == "douyin":
        user.douyin_openid = None; user.douyin_unionid = None
        user.douyin_nickname = None; user.douyin_avatar = None
    else:
        raise ValueError(f"不支持的认证提供方: {provider}")

    try:
        db.commit()
    except Exception:
        db.rollback()
        raise
    return True


def list_user_sessions(db: Session, user_id: str, limit: int = 10) -> list:
    """列出用户会话."""
    sessions = db.query(UserLoginHistory).filter(
        UserLoginHistory.user_id == user_id,
        UserLoginHistory.success == True,
    ).order_by(UserLoginHistory.timestamp.desc()).limit(limit).all()

    return [
        {"provider": s.provider, "timestamp": s.created_at.isoformat() if s.created_at else None}
        for s in sessions
    ]


def change_user_password(db: Session, user_id: str, current_password: str, new_password: str) -> bool:
    """修改密码. Returns: True if successful."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise ValueError("用户不存在")

    is_valid, _ = _verify_password(current_password, user.password_hash)
    if not is_valid:
        raise ValueError("当前密码不正确")

    user.password_hash = _hash_password(new_password)

    try:
        db.commit()
    except Exception:
        db.rollback()
        raise
    return True


def complete_onboarding(
    db: Session,
    user_id: str,
    creator_type: str,
    participant_role: str,
    company_name: Optional[str] = None,
    company_license_no: Optional[str] = None,
    company_address: Optional[str] = None,
    company_contact: Optional[str] = None,
    company_phone: Optional[str] = None,
    company_email: Optional[str] = None,
) -> dict:
    """完成 Onboarding 向导. Returns: result dict."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise ValueError("用户不存在")

    user.creator_type = creator_type
    user.participant_roles = [participant_role]

    # v6.0: 根据角色设置登录平台
    if participant_role == "creator" or (creator_type and not participant_roles):
        user.login_platform = "web"
    elif participant_role != "creator" or participant_roles:
        user.login_platform = "nuxt"

    # 保存公司资质信息 (非创作者角色)
    if participant_role != 'creator':
        user.company_name = company_name
        user.company_license_no = company_license_no
        user.company_address = company_address
        user.company_contact = company_contact
        user.company_phone = company_phone
        user.company_email = company_email

    setting = db.query(SystemSetting).filter(SystemSetting.key == "onboarding_completed").first()
    if setting:
        setting.value = "true"
    else:
        db.add(SystemSetting(key="onboarding_completed", value="true",
                             category="user", description="用户是否已完成 Onboarding 向导"))

    default_platforms = CREATOR_DEFAULT_PLATFORMS.get(creator_type, [])
    platform_setting = db.query(SystemSetting).filter(SystemSetting.key == "default_publish_platforms").first()
    if platform_setting:
        platform_setting.value = ",".join(default_platforms)
    else:
        db.add(SystemSetting(key="default_publish_platforms", value=",".join(default_platforms),
                             category="user", description="用户默认分发平台列表"))

    try:
        db.commit()
    except Exception:
        db.rollback()
        raise

    return {"creator_type": creator_type, "participant_role": participant_role,
            "onboarding_completed": True, "default_platforms": default_platforms}


def create_user_from_wechat_openid(db: Session, openid: str) -> User:
    """创建微信用户 (别名，兼容)."""
    return create_user_from_openid(openid, db)


# 默认创作者平台映射
CREATOR_DEFAULT_PLATFORMS = {
    "illustrator": ["xiaohongshu", "zcool", "bilibili"],
    "photographer": ["xiaohongshu", "instagram", "weibo"],
    "video_creator": ["bilibili", "douyin", "youtube"],
    "crafter": ["xiaohongshu", "etsy", "instagram"],
    "musician": ["bilibili", "douyin", "spotify"],
    "writer": ["wechat", "xiaohongshu", "qidian"],
}

# 有效的创作者类型
VALID_CREATOR_TYPES = tuple(CREATOR_DEFAULT_PLATFORMS.keys())
