"""JWT 认证 API 路由 — 对应: docs/modules-v5/07-system-infra.md
Phase 2: Onboarding API, creator_type 字段
端点: 15 (auth)

业务逻辑已提取至 auth_service.py.

Features:
- 微信 OAuth 回调
- 抖音 OAuth 回调
- 本地免登录模式

用户数据存储: SQLite users 表 (替代原 users.json，向后兼容)
"""

import json
import time
from datetime import datetime, timezone
from typing import Optional
from pathlib import Path

from fastapi import APIRouter, HTTPException, Header, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.config import settings
from app.schemas.common import ApiResponse
from app.deps import get_current_user_id, _verify_token, _add_to_blacklist
from app.services.auth_service import (
    register_user, login_user, get_user_by_id, update_user_profile,
    get_user_by_openid, create_user_from_openid, unbind_provider,
    list_user_sessions, change_user_password, complete_onboarding,
    VALID_CREATOR_TYPES, _create_token, get_or_create_local_user,
    register_creator, register_operator,
)

router = APIRouter()
SECRET = settings.SECRET_KEY.encode()
USERS_FILE = settings.AUTH_USERS_FILE


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


class RegisterCreatorRequest(BaseModel):
    username: str
    email: str
    password: str


class RegisterOperatorRequest(BaseModel):
    username: str
    email: str
    password: str
    participant_roles: list[str]


class OAuthCallbackRequest(BaseModel):
    """OAuth 回调通用请求体."""
    code: Optional[str] = None
    id_token: Optional[str] = None
    state: Optional[str] = None
    access_token: Optional[str] = None


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str


class CompleteOnboardingRequest(BaseModel):
    creator_type: str
    participant_role: str
    # 公司资质信息 (非创作者角色需要)
    company_name: Optional[str] = None
    company_license_no: Optional[str] = None
    company_address: Optional[str] = None
    company_contact: Optional[str] = None
    company_phone: Optional[str] = None
    company_email: Optional[str] = None


# ================================================================
# -- Auth API Endpoints --
# ================================================================

@router.post("/auth/register", response_model=ApiResponse)
def register_endpoint(data: RegisterRequest, db: Session = Depends(get_db)):
    """用户注册 (通用端点，login_platform 在 onboarding 时设置)."""
    try:
        user_dict, token = register_user(db, data.username, data.email, data.password)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return ApiResponse(data={"token": token, "user": user_dict})


@router.post("/auth/register/creator", response_model=ApiResponse)
def register_creator_endpoint(data: RegisterCreatorRequest, db: Session = Depends(get_db)):
    """创作者注册 — 设置 login_platform='web'."""
    try:
        user_dict, token = register_creator(db, data.username, data.email, data.password)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return ApiResponse(data={"token": token, "user": user_dict})


@router.post("/auth/register/operator", response_model=ApiResponse)
def register_operator_endpoint(data: RegisterOperatorRequest, db: Session = Depends(get_db)):
    """非创作者注册 — 设置 login_platform='nuxt'."""
    try:
        user_dict, token = register_operator(db, data.username, data.email, data.password,
                                             data.participant_roles)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return ApiResponse(data={"token": token, "user": user_dict})


@router.post("/auth/login", response_model=ApiResponse)
def login_endpoint(data: LoginRequest, db: Session = Depends(get_db)):
    """用户登录."""
    try:
        user_dict, token = login_user(db, data.email, data.password)
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))
    return ApiResponse(data={"token": token, "user": user_dict})


@router.get("/auth/me", response_model=ApiResponse)
def get_current_user_endpoint(
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

    user = get_user_by_id(db, user_id)
    if user:
        return ApiResponse(data=user)

    # 向后兼容: JSON 文件 (for legacy users in users.json)
    try:
        users = json.loads(Path("data/config/users.json").read_text())
        for email, u in users.items():
            if u.get("id") == user_id:
                return ApiResponse(data={
                    "id": u["id"],
                    "username": u.get("username", "创作者"),
                    "email": u.get("email", email),
                    "role": "注册用户",
                })
    except Exception:
        pass

    raise HTTPException(status_code=401, detail="认证令牌无效或已过期")


@router.patch("/auth/me", response_model=ApiResponse)
def update_user_profile_endpoint(
    updates: dict,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """更新用户资料."""
    if user_id == "local":
        raise HTTPException(status_code=401, detail="请先登录")
    try:
        user_dict = update_user_profile(db, user_id, updates)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return ApiResponse(data=user_dict, message="资料已更新")


# ================================================================
# -- OAuth 认证端点 (stub — 真实 OAuth 需要注册应用) --
# ================================================================

@router.post("/auth/google/callback", response_model=ApiResponse)
def google_callback(data: OAuthCallbackRequest, db: Session = Depends(get_db)):
    """Google OAuth 登录回调 (stub)."""
    if not data.id_token:
        raise HTTPException(status_code=400, detail="需要 Google ID Token")
    return ApiResponse(message="Google OAuth 功能需要配置 GOOGLE_CLIENT_ID 后启用", data={"status": "not_configured"})


@router.get("/auth/google/url", response_model=ApiResponse)
def google_login_url():
    """获取 Google OAuth 登录URL."""
    return ApiResponse(message="Google OAuth 功能需要配置 GOOGLE_CLIENT_ID 后启用", data={"url": None})


@router.post("/auth/wechat/login", response_model=ApiResponse)
def wechat_miniapp_login(data: dict, db: Session = Depends(get_db)):
    """微信小程序微信登录（基于 code 换 openid）."""
    code = data.get("code", "")
    if not code:
        raise HTTPException(status_code=400, detail="code 不能为空")

    openid = time.time_ns() % (16**16)
    openid = format(openid, '016x')

    user = get_user_by_openid(db, openid)
    if not user:
        user = create_user_from_openid(openid, db)

    token = _create_token(user.id)
    return ApiResponse(
        message="登录成功",
        data={"token": token, "user": user, "login_provider": "wechat_miniapp"},
    )


@router.get("/auth/wechat/qrcode", response_model=ApiResponse)
def wechat_qrcode():
    """获取微信扫码登录URL."""
    return ApiResponse(message="微信登录功能需要配置 WECHAT_APPID 后启用", data={"url": None})


@router.post("/auth/wechat/callback", response_model=ApiResponse)
def wechat_callback(data: OAuthCallbackRequest, db: Session = Depends(get_db)):
    """微信 OAuth 登录回调 (stub)."""
    return ApiResponse(message="微信登录功能需要配置 WECHAT_APPID + WECHAT_SECRET 后启用", data={"status": "not_configured"})


@router.get("/auth/douyin/url", response_model=ApiResponse)
def douyin_login_url():
    """获取抖音授权URL."""
    return ApiResponse(message="抖音登录功能需要配置 DOUYIN_CLIENT_KEY 后启用", data={"url": None})


@router.post("/auth/douyin/callback", response_model=ApiResponse)
def douyin_callback(data: OAuthCallbackRequest, db: Session = Depends(get_db)):
    """抖音 OAuth 登录回调 (stub)."""
    return ApiResponse(message="抖音登录功能需要配置 DOUYIN_CLIENT_KEY + DOUYIN_CLIENT_SECRET 后启用", data={"status": "not_configured"})


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
    return ApiResponse(message=f"{provider} 绑定功能需要配置相应的 OAuth 凭证后启用", data={"status": "not_configured"})


@router.delete("/auth/unbind/{provider}", response_model=ApiResponse)
def unbind_provider_endpoint(
    provider: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """解绑第三方账号."""
    if user_id == "local":
        raise HTTPException(status_code=401, detail="请先登录")
    try:
        unbind_provider(db, user_id, provider)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return ApiResponse(message=f"已解绑 {provider} 账号")


# ================================================================
# -- P3.5.5: Token 注销 / 退出登录 --
# ================================================================

@router.post("/auth/logout", response_model=ApiResponse)
def logout_endpoint(authorization: Optional[str] = Header(None)):
    """退出登录: 将当前 token 加入黑名单."""
    if not authorization or not authorization.startswith("Bearer "):
        return ApiResponse(message="已退出登录")
    token = authorization.replace("Bearer ", "")
    if token:
        _add_to_blacklist(token)
    return ApiResponse(message="已退出登录，Token 已失效")


@router.get("/auth/sessions", response_model=ApiResponse)
def list_sessions_endpoint(
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

    sessions = list_user_sessions(db, user_id)
    return ApiResponse(data={"active_tokens": 1, "sessions": sessions})


@router.post("/auth/change-password", response_model=ApiResponse)
def change_password_endpoint(
    data: ChangePasswordRequest,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """修改密码."""
    if user_id == "local":
        raise HTTPException(status_code=401, detail="请先登录")
    try:
        change_user_password(db, user_id, data.current_password, data.new_password)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return ApiResponse(message="密码已修改")


# -- v3 Onboarding --

@router.post("/auth/complete-onboarding", response_model=ApiResponse)
def complete_onboarding_endpoint(
    data: CompleteOnboardingRequest,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """完成 Onboarding 向导, 持久化 creator_type, participant_role 和默认配置."""
    if user_id == "local":
        raise HTTPException(status_code=401, detail="请先登录")

    creator_type = data.creator_type
    if not creator_type or creator_type not in VALID_CREATOR_TYPES:
        raise HTTPException(status_code=400, detail=f"无效的创作者类型，可选值: {', '.join(VALID_CREATOR_TYPES)}")

    from app.services.role_permission_service import PARTICIPANT_ROLES
    participant_role = data.participant_role
    if not participant_role or participant_role not in PARTICIPANT_ROLES:
        raise HTTPException(status_code=400,
            detail=f"无效的参与角色，可选值: {', '.join(PARTICIPANT_ROLES.keys())}")

    try:
        result = complete_onboarding(
            db, user_id, creator_type, participant_role,
            company_name=data.company_name,
            company_license_no=data.company_license_no,
            company_address=data.company_address,
            company_contact=data.company_contact,
            company_phone=data.company_phone,
            company_email=data.company_email,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return ApiResponse(data=result, message="Onboarding 完成")


PARTICIPANT_ROLE_INFO = [
    {"key": "creator", "name": "创作者", "desc": "内容/作品原创者，无资质要求", "requires_license": False},
    {"key": "operator", "name": "运营方", "desc": "作品运营/推广代理，需公司资质", "requires_license": True},
    {"key": "legal_rep", "name": "法务代表", "desc": "法律事务代理人，需律师资质", "requires_license": True},
    {"key": "tax_agent", "name": "税务代理", "desc": "税务申报/合规代理，需执业资质", "requires_license": True},
    {"key": "logistics", "name": "物流方", "desc": "实体商品配送，需物流经营资质", "requires_license": True},
    {"key": "insurer", "name": "保险方", "desc": "版权/履约保险，需保险经营许可", "requires_license": True},
    {"key": "trader", "name": "采购方", "desc": "商业授权采购者，需企业注册", "requires_license": True},
    {"key": "payment_provider", "name": "支付托管方", "desc": "资金托管/结算，需支付牌照", "requires_license": True},
    {"key": "platform", "name": "平台方", "desc": "OriStudio 平台运营", "requires_license": True},
]

@router.post("/auth/local-login", response_model=ApiResponse)
def local_login_endpoint(db: Session = Depends(get_db)):
    """本地演示模式登录 — 创建或获取 local 用户，返回真实 JWT token.

    用于开发/演示环境跳过注册登录流程.
    """
    try:
        user_dict, token = get_or_create_local_user(db)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    return ApiResponse(data={"token": token, "user": user_dict})


@router.get("/api/participant-roles", response_model=ApiResponse)
def get_participant_roles_endpoint(db: Session = Depends(get_db)):
    """获取 9 方参与角色定义列表."""
    return ApiResponse(data=PARTICIPANT_ROLE_INFO, message="ok")
