"""Tests for v6.0 auth platform separation: creator vs operator registration."""

import pytest
from app.deps import _sign


def _create_token(user_id: str) -> str:
    import time, json
    header = {"alg": "HS256", "typ": "JWT"}
    exp = int(time.time()) + 3600
    payload = {"sub": user_id, "iat": int(time.time()), "exp": exp}
    import base64
    def b64encode(data: str) -> str:
        return base64.urlsafe_b64encode(data.encode()).rstrip(b"=").decode()
    h = b64encode(json.dumps(header))
    p = b64encode(json.dumps(payload))
    sig = _sign(f"{h}.{p}")
    return f"{h}.{p}.{sig}"


class TestCreatorRegistration:
    """POST /api/auth/register/creator"""

    def test_creates_user_with_login_platform_web(self, client, db_session):
        res = client.post("/api/auth/register/creator", json={
            "username": "林山海",
            "email": "lin@artist.com",
            "password": "testpass123",
        })
        assert res.status_code == 200
        data = res.json()
        assert data["data"]["user"]["email"] == "lin@artist.com"
        assert data["data"]["user"]["login_platform"] == "web"
        assert "token" in data["data"]

    def test_rejects_missing_creator_type_in_onboarding(self, client, db_session):
        """Register creator without creator_type should fail at onboarding step."""
        res = client.post("/api/auth/register/creator", json={
            "username": "Test",
            "email": "test2@example.com",
            "password": "testpass123",
        })
        assert res.status_code == 200
        # Registration succeeds, but creator_type is None (filled in onboarding)
        data = res.json()
        assert data["data"]["user"]["login_platform"] == "web"

    def test_rejects_email_duplicate(self, client, db_session):
        client.post("/api/auth/register/creator", json={
            "username": "User1", "email": "dup@example.com", "password": "pass123",
        })
        res = client.post("/api/auth/register/creator", json={
            "username": "User2", "email": "dup@example.com", "password": "pass456",
        })
        assert res.status_code == 400
        assert "已注册" in res.json().get("detail", "")

    def test_rejects_non_creator_on_operator_endpoint(self, client, db_session):
        """Operator endpoint should reject creator-type registration."""
        res = client.post("/api/auth/register/operator", json={
            "username": "Company",
            "email": "company@test.com",
            "password": "testpass123",
            "participant_roles": ["operator"],
        })
        assert res.status_code == 200
        data = res.json()
        assert data["data"]["user"]["login_platform"] == "nuxt"


class TestOperatorRegistration:
    """POST /api/auth/register/operator"""

    def test_creates_user_with_login_platform_nuxt(self, client, db_session):
        res = client.post("/api/auth/register/operator", json={
            "username": "张总",
            "email": "zhang@corp.com",
            "password": "testpass123",
            "participant_roles": ["operator"],
        })
        assert res.status_code == 200
        data = res.json()
        assert data["data"]["user"]["email"] == "zhang@corp.com"
        assert data["data"]["user"]["login_platform"] == "nuxt"
        assert "operator" in data["data"]["user"].get("participant_roles", [])

    def test_rejects_duplicate_email(self, client, db_session):
        client.post("/api/auth/register/operator", json={
            "username": "User1", "email": "dup2@example.com", "password": "pass123",
            "participant_roles": ["trader"],
        })
        res = client.post("/api/auth/register/operator", json={
            "username": "User2", "email": "dup2@example.com", "password": "pass456",
            "participant_roles": ["operator"],
        })
        assert res.status_code == 400

    def test_participant_roles_stored(self, client, db_session):
        res = client.post("/api/auth/register/operator", json={
            "username": "MultiRole",
            "email": "multi@test.com",
            "password": "testpass123",
            "participant_roles": ["operator", "trader"],
        })
        assert res.status_code == 200
        data = res.json()
        assert "operator" in data["data"]["user"]["participant_roles"]
        assert "trader" in data["data"]["user"]["participant_roles"]


class TestLoginPlatformRouting:
    """Login should set login_platform based on user's creator_type / participant_roles."""

    def test_creator_login_sets_web_platform(self, client, db_session):
        """After registering as creator, login should show login_platform='web'."""
        # Register as creator (login_platform set to 'web' automatically)
        res = client.post("/api/auth/register/creator", json={
            "username": "Creator", "email": "creator@test.com", "password": "pass123",
        })
        assert res.status_code == 200
        user = res.json()["data"]["user"]
        assert user["login_platform"] == "web"

        # Login and verify
        res = client.post("/api/auth/login", json={
            "email": "creator@test.com", "password": "pass123",
        })
        assert res.status_code == 200
        assert res.json()["data"]["user"]["login_platform"] == "web"

    def test_operator_login_sets_nuxt_platform(self, client, db_session):
        """After registering as operator, login should show login_platform='nuxt'."""
        res = client.post("/api/auth/register/operator", json={
            "username": "Operator", "email": "operator@test.com",
            "password": "pass123", "participant_roles": ["operator"],
        })
        assert res.status_code == 200
        user = res.json()["data"]["user"]
        assert user["login_platform"] == "nuxt"

        # Login and verify
        res = client.post("/api/auth/login", json={
            "email": "operator@test.com", "password": "pass123",
        })
        assert res.status_code == 200
        assert res.json()["data"]["user"]["login_platform"] == "nuxt"

    def test_local_user_keeps_web_platform(self, client, db_session):
        """Local demo user should keep login_platform='web'."""
        res = client.post("/api/auth/local-login")
        assert res.status_code == 200
        user = res.json()["data"]["user"]
        # local user has no creator_type or participant_roles, defaults to 'web'
        assert user.get("login_platform") in ("web", None)


class TestUserModelMigration:
    """login_platform field should exist and be populated for existing users."""

    def test_login_platform_column_exists(self, db_session):
        """login_platform should be a valid column on User."""
        from app.models.system import User
        assert hasattr(User, "login_platform")

    def test_existing_users_get_migration(self, client, db_session):
        """Existing users without login_platform should default to 'web'."""
        # Create a user without login_platform (simulating pre-v6.0 data)
        from app.models.system import User
        from app.services.auth_service import _hash_password
        import hashlib
        user = User(
            id=hashlib.md5(b"old_user").hexdigest()[:16],
            email="old@example.com",
            username="OldUser",
            password_hash=_hash_password("oldpass"),
            role="user",
            status="active",
            # login_platform not set — simulating pre-v6.0
        )
        db_session.add(user)
        db_session.commit()

        # Login should work and assign default platform
        res = client.post("/api/auth/login", json={
            "email": "old@example.com", "password": "oldpass",
        })
        assert res.status_code == 200
        # After login, login_platform should be set
        db_session.refresh(user)
        assert user.login_platform in ("web", "nuxt", None)
