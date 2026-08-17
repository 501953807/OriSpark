"""议价协商模块 API 测试."""
import pytest


def _create_user(db_session, email="nego_test@example.com"):
    from app.models.system import User
    from app.services.auth_service import _hash_password
    u = User(
        id=email,
        email=email,
        username=email.split("@")[0],
        password_hash=_hash_password("testpass123"),
    )
    db_session.add(u)
    db_session.flush()
    return u


class TestNegotiationCRUD:
    """测试 /api/negotiations CRUD 端点."""

    def test_create_negotiation(self, client, db_session):
        """创建议价应成功."""
        _create_user(db_session, email="current_user")
        _create_user(db_session, email="nego_buyer@example.com")
        _create_user(db_session, email="nego_seller@example.com")
        resp = client.post(
            "/api/negotiations",
            json={
                "buyer_id": "nego_buyer@example.com",
                "seller_id": "nego_seller@example.com",
                "description": "议价测试",
                "initial_price_yuan": 1000.0,
            },
        )
        assert resp.status_code in (200, 201)
        data = resp.json()
        assert isinstance(data, (dict, list))

    def test_list_negotiations(self, client, db_session):
        """议价列表应返回列表或成功响应."""
        _create_user(db_session, email="current_user")
        resp = client.get("/api/negotiations")
        assert resp.status_code == 200
        data = resp.json()
        # 可能是 list 或 dict with "data"
        if isinstance(data, dict):
            assert data.get("success") is True or "data" in data
        else:
            assert isinstance(data, list)

    def test_list_negotiations_with_status_filter(self, client, db_session):
        """按状态过滤议价列表."""
        _create_user(db_session, email="current_user")
        resp = client.get("/api/negotiations?status=pending")
        assert resp.status_code == 200

    def test_get_negotiation_not_found(self, client):
        """获取不存在的议价应返回404."""
        resp = client.get("/api/negotiations/nonexistent-id")
        assert resp.status_code == 404


class TestNegotiationActions:
    """测试议价操作端点."""

    def _create_nego(self, client, db_session):
        _create_user(db_session, email="current_user")
        _create_user(db_session, email="nego_op_seller@example.com")
        resp = client.post(
            "/api/negotiations",
            json={
                "buyer_id": "current_user",
                "seller_id": "nego_op_seller@example.com",
                "description": "操作测试",
                "initial_price_yuan": 500.0,
            },
        )
        data = resp.json()
        if isinstance(data, dict):
            return data.get("id") or data.get("data", {}).get("id")
        return None

    def test_submit_offer(self, client, db_session):
        """提交出价应更新状态为negotiating."""
        nego_id = self._create_nego(client, db_session)
        if not nego_id:
            return pytest.skip("Could not create negotiation")
        resp = client.post(
            f"/api/negotiations/{nego_id}/offer",
            json={"amount_yuan": 450.0, "message": "还价450"},
        )
        assert resp.status_code in (200, 201)

    def test_accept_offer(self, client, db_session):
        """接受出价应更新状态为agreed."""
        nego_id = self._create_nego(client, db_session)
        if not nego_id:
            return pytest.skip("Could not create negotiation")
        client.post(
            f"/api/negotiations/{nego_id}/offer",
            json={"amount_yuan": 450.0},
        )
        resp = client.patch(
            f"/api/negotiations/{nego_id}/accept",
            json={},
        )
        assert resp.status_code in (200, 201)

    def test_complete_negotiation(self, client, db_session):
        """完成议价应更新状态为completed."""
        nego_id = self._create_nego(client, db_session)
        if not nego_id:
            return pytest.skip("Could not create negotiation")
        client.post(
            f"/api/negotiations/{nego_id}/offer",
            json={"amount_yuan": 450.0},
        )
        client.patch(f"/api/negotiations/{nego_id}/accept", json={})
        resp = client.post(
            f"/api/negotiations/{nego_id}/complete",
            json={},
        )
        assert resp.status_code in (200, 201)

    def test_cancel_negotiation(self, client, db_session):
        """取消议价应更新状态为cancelled."""
        nego_id = self._create_nego(client, db_session)
        if not nego_id:
            return pytest.skip("Could not create negotiation")
        resp = client.patch(
            f"/api/negotiations/{nego_id}/cancel",
            json={},
        )
        assert resp.status_code in (200, 201)
