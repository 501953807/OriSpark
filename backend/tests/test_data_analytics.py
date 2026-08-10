"""v6.0: 数据看板 API 测试."""

import pytest
from fastapi.testclient import TestClient

from app.deps import _sign


def _create_token(user_id: str) -> str:
    import time, json, base64
    header = {"alg": "HS256", "typ": "JWT"}
    payload = {"sub": user_id, "iat": int(time.time()), "exp": int(time.time()) + 3600}
    h = base64.urlsafe_b64encode(json.dumps(header).encode()).rstrip(b"=").decode()
    p = base64.urlsafe_b64encode(json.dumps(payload).encode()).rstrip(b"=").decode()
    sig = _sign(f"{h}.{p}")
    return f"{h}.{p}.{sig}"


def _create_user(db_session, user_id: str, email: str, **kwargs):
    from app.models.system import User
    user = User(
        id=user_id,
        username=kwargs.get("username", "用户"),
        email=email,
        password_hash="$2b$12$LZmMhq3X.example",
        login_platform=kwargs.get("login_platform", "web"),
        creator_type=kwargs.get("creator_type"),
        participant_roles=kwargs.get("participant_roles", []),
    )
    db_session.add(user)
    db_session.flush()
    return user


def _create_work(db_session, creator_id: str, title: str = "测试作品") -> str:
    from app.models.work import Work
    work = Work(
        title=title, description="测试", creator_id=creator_id,
        file_path="/tmp/test.jpg", file_name="test.jpg",
        file_size=1024, file_type="image", file_extension="jpg",
    )
    db_session.add(work)
    db_session.flush()
    return work.id


def _create_contract(db_session, work_id: str, amount: float = 1000.0) -> str:
    from app.models.contract import ContractInstance
    contract = ContractInstance(
        work_id=work_id,
        title="测试合约",
        total_amount=amount,
        currency="CNY",
        status="active",
        split_rules_json='[{"party": "creator", "percent": 70}, {"party": "operator", "percent": 30}]',
    )
    db_session.add(contract)
    db_session.flush()
    return contract.id


CURRENT_USER_ID = "current_user"


class TestPlatformStats:
    def test_returns_stats(self, client: TestClient, db_session):
        """返回平台统计数据."""
        _create_user(db_session, CURRENT_USER_ID, "op@test.com",
                     login_platform="nuxt", participant_roles=["operator"])
        db_session.commit()
        token = _create_token(CURRENT_USER_ID)
        headers = {"Authorization": f"Bearer {token}"}
        resp = client.get("/api/operator/data/platform-stats", headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "total_creators" in data
        assert "total_works" in data
        assert "active_contracts" in data
        assert "monthly_transaction_volume" in data


class TestCreatorRanking:
    def test_rank_by_works(self, client: TestClient, db_session):
        """按作品数排行."""
        _create_user(db_session, CURRENT_USER_ID, "op@test.com",
                     login_platform="nuxt", participant_roles=["operator"])
        creator1 = _create_user(db_session, "c1@test.com", "c1@test.com",
                                creator_type="illustrator", login_platform="web")
        creator2 = _create_user(db_session, "c2@test.com", "c2@test.com",
                                creator_type="photographer", login_platform="web")
        _create_work(db_session, creator1.id, title="作品1")
        _create_work(db_session, creator1.id, title="作品2")
        _create_work(db_session, creator2.id, title="作品3")
        db_session.commit()
        token = _create_token(CURRENT_USER_ID)
        headers = {"Authorization": f"Bearer {token}"}
        resp = client.get("/api/operator/data/creator-ranking?sort_by=works", headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        if data:
            assert data[0]["work_count"] >= data[-1]["work_count"]

    def test_rank_by_scr(self, client: TestClient, db_session):
        """按SCR信誉排行."""
        from app.models.scr_reputation import SCRScore
        _create_user(db_session, CURRENT_USER_ID, "op@test.com",
                     login_platform="nuxt", participant_roles=["operator"])
        creator = _create_user(db_session, "c3@test.com", "c3@test.com",
                               creator_type="musician", login_platform="web")
        scr = SCRScore(user_id=creator.id, overall_score=85.0, rating_level="gold")
        db_session.add(scr)
        db_session.commit()
        token = _create_token(CURRENT_USER_ID)
        headers = {"Authorization": f"Bearer {token}"}
        resp = client.get("/api/operator/data/creator-ranking?sort_by=scr", headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)


class TestCategoryTrends:
    def test_returns_trends(self, client: TestClient, db_session):
        """返回品类趋势."""
        _create_user(db_session, CURRENT_USER_ID, "op@test.com",
                     login_platform="nuxt", participant_roles=["operator"])
        creator = _create_user(db_session, "c4@test.com", "c4@test.com",
                               creator_type="illustrator", login_platform="web")
        _create_work(db_session, creator.id)
        db_session.commit()
        token = _create_token(CURRENT_USER_ID)
        headers = {"Authorization": f"Bearer {token}"}
        resp = client.get("/api/operator/data/category-trends", headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)

    def test_quarterly_period(self, client: TestClient, db_session):
        """季度统计."""
        _create_user(db_session, CURRENT_USER_ID, "op@test.com",
                     login_platform="nuxt", participant_roles=["operator"])
        db_session.commit()
        token = _create_token(CURRENT_USER_ID)
        headers = {"Authorization": f"Bearer {token}"}
        resp = client.get("/api/operator/data/category-trends?period=quarterly", headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        assert all(d.get("period") == "quarterly" for d in data)


class TestIndustryReport:
    def test_returns_report(self, client: TestClient, db_session):
        """返回行业报告."""
        _create_user(db_session, CURRENT_USER_ID, "op@test.com",
                     login_platform="nuxt", participant_roles=["operator"])
        db_session.commit()
        token = _create_token(CURRENT_USER_ID)
        headers = {"Authorization": f"Bearer {token}"}
        resp = client.get("/api/operator/data/industry-report", headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "report_month" in data
        assert "total_creators" in data
        assert "transaction_volume" in data
        assert "summary" in data

    def test_specific_month(self, client: TestClient, db_session):
        """指定月份报告."""
        _create_user(db_session, CURRENT_USER_ID, "op@test.com",
                     login_platform="nuxt", participant_roles=["operator"])
        db_session.commit()
        token = _create_token(CURRENT_USER_ID)
        headers = {"Authorization": f"Bearer {token}"}
        resp = client.get("/api/operator/data/industry-report?month=2026-07", headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["report_month"] == "2026-07"
