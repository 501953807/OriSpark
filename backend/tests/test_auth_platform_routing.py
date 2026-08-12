"""Phase 0: 认证平台路由测试 — 创作者 vs 运营者注册/登录行为."""

import pytest
from app.deps import _sign


def _create_token(user_id: str) -> str:
    """创建 JWT token 供测试使用."""
    import time, json, base64
    header = {"alg": "HS256", "typ": "JWT"}
    payload = {"sub": user_id, "iat": int(time.time()), "exp": int(time.time()) + 3600}
    h = base64.urlsafe_b64encode(json.dumps(header).encode()).rstrip(b"=").decode()
    p = base64.urlsafe_b64encode(json.dumps(payload).encode()).rstrip(b"=").decode()
    sig = _sign(f"{h}.{p}")
    return f"{h}.{p}.{sig}"


class TestCreatorRegistration:
    """POST /api/auth/register/creator — 创作者注册行为."""

    def test_creator_register_sets_web_platform(self, client, db_session):
        """创作者注册后 login_platform='web'."""
        res = client.post("/api/auth/register/creator", json={
            "username": "林山海",
            "email": "lin_shanhai@test.com",
            "password": "testpass123",
        })
        assert res.status_code == 200
        data = res.json()
        assert data["data"]["user"]["login_platform"] == "web"
        assert data["data"]["user"]["email"] == "lin_shanhai@test.com"
        assert "token" in data["data"]

    def test_duplicate_email_creator_rejected(self, client, db_session):
        """重复邮箱注册返回 400."""
        client.post("/api/auth/register/creator", json={
            "username": "创作者A",
            "email": "dup_creator@test.com",
            "password": "testpass123",
        })
        res = client.post("/api/auth/register/creator", json={
            "username": "创作者B",
            "email": "dup_creator@test.com",
            "password": "testpass456",
        })
        assert res.status_code == 400
        detail = res.json().get("detail", "")
        assert "已注册" in detail or "duplicate" in detail.lower()


class TestOperatorRegistration:
    """POST /api/auth/register/operator — 运营者注册行为."""

    def test_operator_register_sets_nuxt_platform(self, client, db_session):
        """运营者注册后 login_platform='nuxt'."""
        res = client.post("/api/auth/register/operator", json={
            "username": "张总",
            "email": "zhang_zong@test.com",
            "password": "testpass123",
            "participant_roles": ["operator"],
        })
        assert res.status_code == 200
        data = res.json()
        assert data["data"]["user"]["login_platform"] == "nuxt"
        assert data["data"]["user"]["email"] == "zhang_zong@test.com"
        assert "operator" in data["data"]["user"].get("participant_roles", [])
        assert "token" in data["data"]

    def test_operator_missing_roles_still_succeeds(self, client, db_session):
        """operator 注册无 participant_roles 也成功（roles 可选）."""
        res = client.post("/api/auth/register/operator", json={
            "username": "李总",
            "email": "li_zong_no_roles@test.com",
            "password": "testpass123",
        })
        assert res.status_code == 200
        data = res.json()
        assert data["data"]["user"]["login_platform"] == "nuxt"
        assert data["data"]["user"]["email"] == "li_zong_no_roles@test.com"
        assert "token" in data["data"]


class TestLoginPlatformRouting:
    """登录后的 platform 路由行为."""

    def test_creator_login_returns_web_platform(self, client, db_session):
        """创作者登录后 login_platform='web'."""
        # 注册
        client.post("/api/auth/register/creator", json={
            "username": "登录创作者",
            "email": "login_creator@test.com",
            "password": "testpass123",
        })
        # 登录
        res = client.post("/api/auth/login", json={
            "email": "login_creator@test.com",
            "password": "testpass123",
        })
        assert res.status_code == 200
        assert res.json()["data"]["user"]["login_platform"] == "web"

    def test_operator_login_returns_nuxt_platform(self, client, db_session):
        """运营者登录后 login_platform='nuxt'."""
        # 注册
        client.post("/api/auth/register/operator", json={
            "username": "登录运营者",
            "email": "login_operator@test.com",
            "password": "testpass123",
            "participant_roles": ["operator"],
        })
        # 登录
        res = client.post("/api/auth/login", json={
            "email": "login_operator@test.com",
            "password": "testpass123",
        })
        assert res.status_code == 200
        assert res.json()["data"]["user"]["login_platform"] == "nuxt"

    def test_local_login_default_platform(self, client, db_session):
        """本地登录用户 login_platform 为 'web' 或 None."""
        res = client.post("/api/auth/local-login")
        assert res.status_code == 200
        user = res.json()["data"]["user"]
        assert user.get("login_platform") in ("web", None)
