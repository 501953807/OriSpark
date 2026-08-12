"""Phase 0: 作品公开可运营状态测试 (work_operation_public).

测试范围:
- 默认值: 新作品 work_operation_public = False
- 切换状态: PATCH /api/creator/works/{id}/operation-public
- 权限: 非所有者返回 403
- 运营者发现: GET /api/operator/works/available 只返回公开作品
- 持久化: 状态变更后重新查询保持正确
"""

import hashlib
import pytest
from app.deps import _sign

# 固定 mock 用户 ID，与 fixture 中预创建的用户 ID 保持一致
MOCK_CREATOR_UID = hashlib.md5(b"mock_creator@test.com").hexdigest()[:16]
MOCK_OPERATOR_UID = hashlib.md5(b"mock_operator@test.com").hexdigest()[:16]


def _create_token(user_id: str) -> str:
    """创建 JWT token 供测试使用."""
    import time, json, base64
    header = {"alg": "HS256", "typ": "JWT"}
    payload = {"sub": user_id, "iat": int(time.time()), "exp": int(time.time()) + 3600}
    h = base64.urlsafe_b64encode(json.dumps(header).encode()).rstrip(b"=").decode()
    p = base64.urlsafe_b64encode(json.dumps(payload).encode()).rstrip(b"=").decode()
    sig = _sign(f"{h}.{p}")
    return f"{h}.{p}.{sig}"


def _create_creator_user(db_session, email: str = "creator@test.com", username: str = "创作者") -> str:
    """在 DB 中直接创建创作者用户并返回 user_id."""
    from app.models.system import User
    from app.services.auth_service import _hash_password
    user_id = hashlib.md5(email.encode()).hexdigest()[:16]
    user = User(
        id=user_id,
        username=username,
        email=email,
        password_hash=_hash_password("testpass123"),
        role="user",
        status="active",
        login_platform="web",
        creator_type="illustrator",
    )
    db_session.add(user)
    db_session.flush()
    return user_id


def _create_operator_user(db_session, email: str = "operator@test.com") -> str:
    """在 DB 中直接创建运营者用户并返回 user_id."""
    from app.models.system import User
    from app.services.auth_service import _hash_password
    user_id = hashlib.md5(email.encode()).hexdigest()[:16]
    user = User(
        id=user_id,
        username="运营者",
        email=email,
        password_hash=_hash_password("testpass123"),
        role="user",
        status="active",
        login_platform="nuxt",
        participant_roles=["operator"],
    )
    db_session.add(user)
    db_session.flush()
    return user_id


def _create_work(db_session, work_id: str, creator_id: str | None = None,
                 work_operation_public: bool = False) -> str:
    """在 DB 中直接创建作品并返回 work_id."""
    from app.models.work import Work
    work = Work(
        id=work_id,
        title="测试作品",
        description="Phase 0 测试作品",
        creator_id=creator_id or MOCK_CREATOR_UID,
        file_path="/tmp/test.jpg",
        file_name="test.jpg",
        file_size=1024,
        file_type="image",
        file_extension="jpg",
        status="active",
        work_operation_public=work_operation_public,
    )
    db_session.add(work)
    db_session.flush()
    return work_id


@pytest.fixture(autouse=True)
def _mock_role_deps(client, db_session):
    """Pre-create mock users in DB and override role dependencies.

    Depends on 'client' fixture so this runs AFTER client sets up its overrides,
    ensuring our role mocks take precedence.
    """
    from app.main import app
    from app.deps import require_creator, require_operator
    from app.models.system import User
    from app.services.auth_service import _hash_password

    # Pre-create mock users in DB so FK constraints pass
    for uid, username, email, creator_type, participant_roles, platform in [
        (MOCK_CREATOR_UID, "mock_creator", "mock_creator@test.com", "illustrator", None, "web"),
        (MOCK_OPERATOR_UID, "mock_operator", "mock_operator@test.com", None, ["operator"], "nuxt"),
    ]:
        user = db_session.query(User).filter(User.id == uid).first()
        if not user:
            user = User(
                id=uid,
                username=username,
                email=email,
                password_hash=_hash_password("testpass123"),
                role="user",
                status="active",
                login_platform=platform,
                creator_type=creator_type,
                participant_roles=participant_roles,
            )
            db_session.add(user)
    db_session.flush()

    def mock_require_creator(authorization=None, db=None):
        return db_session.query(User).filter(User.id == MOCK_CREATOR_UID).first()

    def mock_require_operator(authorization=None, db=None):
        return db_session.query(User).filter(User.id == MOCK_OPERATOR_UID).first()

    app.dependency_overrides[require_creator] = mock_require_creator
    app.dependency_overrides[require_operator] = mock_require_operator
    try:
        yield
    finally:
        if require_creator in app.dependency_overrides:
            del app.dependency_overrides[require_creator]
        if require_operator in app.dependency_overrides:
            del app.dependency_overrides[require_operator]


class TestWorkDefaultOperationPublic:
    """新作品 work_operation_public 默认值测试."""

    def test_work_default_operation_public_false(self, db_session):
        """新作品 work_operation_public 默认为 False."""
        work_id = _create_work(db_session, "test_work_001")

        from app.models.work import Work
        work = db_session.query(Work).filter(Work.id == work_id).first()
        assert work is not None
        assert work.work_operation_public is False


class TestToggleOperationPublic:
    """切换作品公开可运营状态测试."""

    def test_toggle_operation_public_to_true(self, client, db_session):
        """创作者可将作品切换到公开可运营状态."""
        work_id = _create_work(db_session, "toggle_work_001", MOCK_CREATOR_UID,
                               work_operation_public=False)
        res = client.patch(
            f"/api/creator/works/{work_id}/operation-public",
            headers={"Authorization": "Bearer test-token"},
        )
        assert res.status_code == 200, f"响应: {res.json()}"
        data = res.json()
        assert data.get("work_operation_public") is True

    def test_toggle_operation_public_to_false(self, client, db_session):
        """创作者可将公开作品切换回不公开状态."""
        work_id = _create_work(db_session, "toggle_back_work_001", MOCK_CREATOR_UID,
                               work_operation_public=True)

        res = client.patch(
            f"/api/creator/works/{work_id}/operation-public",
            headers={"Authorization": "Bearer test-token"},
        )
        assert res.status_code == 200
        data = res.json()
        assert data.get("work_operation_public") is False


class TestNonOwnerCannotToggle:
    """非所有者尝试切换操作应返回 403."""

    def test_non_owner_cannot_toggle_service(self, db_session):
        """Service 层验证非所有者无法切换作品公开状态."""
        from app.models.work import Work
        from app.services.work_operation_service import WorkOperationService

        # 创建由不同 creator 拥有的作品
        other_creator_id = _create_creator_user(db_session, email="other_owner@test.com")
        work_id = _create_work(db_session, "nonowner_service_work", other_creator_id,
                               work_operation_public=False)

        # 尝试用 mock creator 切换 → 应抛出 ValueError
        with pytest.raises(ValueError, match="只有创作者可以操作"):
            WorkOperationService.toggle_operation_public(
                db_session, work_id, MOCK_CREATOR_UID
            )


class TestListOperationPublicWorks:
    """运营者端点只返回 work_operation_public=True 的作品."""

    def test_list_operation_public_works(self, client, db_session):
        """运营者端点只返回公开可运营的作品."""
        creator_id = MOCK_CREATOR_UID
        work_public_id = _create_work(db_session, "list_op_public_001", creator_id,
                                      work_operation_public=True)
        work_private_id = _create_work(db_session, "list_op_private_001", creator_id,
                                       work_operation_public=False)

        res = client.get(
            "/api/operator/works/available?page=1&limit=20",
            headers={"Authorization": "Bearer test-token"},
        )
        assert res.status_code == 200
        data = res.json()
        work_ids = [item["id"] for item in data["items"]]
        assert work_public_id in work_ids
        assert work_private_id not in work_ids


class TestOperationPublicPersists:
    """作品公开状态在操作后持久化."""

    def test_work_operation_public_persists(self, db_session):
        """切换后重新查询确认状态保持."""
        work_id = _create_work(db_session, "persist_work_001", MOCK_CREATOR_UID,
                               work_operation_public=False)

        from app.models.work import Work
        from app.services.work_operation_service import WorkOperationService

        WorkOperationService.toggle_operation_public(db_session, work_id, MOCK_CREATOR_UID)

        work = db_session.query(Work).filter(Work.id == work_id).first()
        assert work.work_operation_public is True

        WorkOperationService.toggle_operation_public(db_session, work_id, MOCK_CREATOR_UID)

        work = db_session.query(Work).filter(Work.id == work_id).first()
        assert work.work_operation_public is False
