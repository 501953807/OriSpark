"""Tests for auth module — password change and profile update."""

import pytest
from app.deps import _sign


def _create_token(user_id: str) -> str:
    import time, json
    header = {"alg": "HS256", "typ": "JWT"}
    exp = int(time.time()) + 3600  # 1 hour expiry
    payload = {"sub": user_id, "iat": int(time.time()), "exp": exp}
    import base64

    def b64encode(data: str) -> str:
        return base64.urlsafe_b64encode(data.encode()).rstrip(b"=").decode()

    h = b64encode(json.dumps(header))
    p = b64encode(json.dumps(payload))
    sig = _sign(f"{h}.{p}")
    return f"{h}.{p}.{sig}"


def _create_user(db_session, email="test@example.com", password="testpass123"):
    from app.models.system import User
    from app.routers.auth import _hash_password
    u = User(
        id=email,
        email=email,
        username=email.split("@")[0],
        password_hash=_hash_password(password),
    )
    db_session.add(u)
    db_session.flush()
    return u


class TestChangePassword:
    """Tests for POST /auth/change-password endpoint."""

    def test_requires_login(self, client):
        """Unauthenticated request should return 401."""
        res = client.post("/api/auth/change-password", json={
            "current_password": "old",
            "new_password": "new",
        })
        assert res.status_code == 401

    def test_wrong_current_password(self, client, db_session):
        """Changing with wrong current password should return 400."""
        _create_user(db_session, email="pw@test.com", password="correct123")
        token = _create_token("pw@test.com")

        res = client.post(
            "/api/auth/change-password",
            json={"current_password": "wrong", "new_password": "newpass123"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert res.status_code == 400
        assert "当前密码不正确" in res.json()["detail"]

    def test_success_updates_password(self, client, db_session):
        """Correct current password should update successfully."""
        _create_user(db_session, email="ok@test.com", password="oldpass123")
        token = _create_token("ok@test.com")

        res = client.post(
            "/api/auth/change-password",
            json={"current_password": "oldpass123", "new_password": "newpass456"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert res.status_code == 200
        data = res.json()
        assert data["message"] == "密码已修改"

    def test_missing_fields(self, client):
        """Missing fields should return 422 validation error."""
        res = client.post("/api/auth/change-password", json={"current_password": "old"})
        assert res.status_code == 422
