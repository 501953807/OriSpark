"""v6.0: FactoryOrder 工厂订单全流程测试."""

import pytest
from fastapi.testclient import TestClient
from datetime import date

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


def _create_partner(db_session, name: str, user_id: str | None = None) -> str:
    from app.models.supply import Partner
    partner = Partner(
        name=name,
        company_name=name,
        type="manufacturer",
        status="active",
        contact_person=user_id,
    )
    db_session.add(partner)
    db_session.flush()
    return partner.id


def _create_factory_order(db_session, operator_id: str, factory_id: str | None = None, **kwargs) -> str:
    from app.models.factory_order import FactoryOrder
    order = FactoryOrder(
        order_number=kwargs.get("order_number", f"FO-TEST-{kwargs.get('id', '1')}"),
        operator_id=operator_id,
        factory_id=factory_id,
        product_name=kwargs.get("product_name", "测试产品"),
        product_category=kwargs.get("product_category", "apparel"),
        quantity=kwargs.get("quantity", 10),
        unit_price=kwargs.get("unit_price", 50.0),
        total_amount=kwargs.get("total_amount", 500.0),
        status=kwargs.get("status", "draft"),
    )
    db_session.add(order)
    db_session.flush()
    return order.id


CURRENT_USER_ID = "current_user"


class TestCreateFactory:
    def test_operator_can_register_factory(self, client: TestClient, db_session):
        """运营者可以注册工厂."""
        _create_user(db_session, CURRENT_USER_ID, "op@test.com",
                     login_platform="nuxt", participant_roles=["operator"])
        db_session.commit()
        token = _create_token(CURRENT_USER_ID)
        headers = {"Authorization": f"Bearer {token}"}
        resp = client.post(
            "/api/operator/supply/factories", headers=headers,
            json={"name": "测试工厂", "location": "东莞", "phone": "1234567890",
                  "categories": ["clothing"], "product_categories": ["t_shirt"]},
        )
        assert resp.status_code == 200, f"Create factory failed: {resp.json()}"
        data = resp.json()
        assert data["name"] == "测试工厂"
        assert data["status"] == "active"

    def test_operator_can_list_factories(self, client: TestClient, db_session):
        """运营者可以查看工厂列表."""
        factory_id = _create_partner(db_session, "工厂A")
        _create_user(db_session, CURRENT_USER_ID, "op2@test.com",
                     login_platform="nuxt", participant_roles=["operator"])
        db_session.commit()
        token = _create_token(CURRENT_USER_ID)
        headers = {"Authorization": f"Bearer {token}"}
        resp = client.get("/api/operator/supply/factories", headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert any(f["id"] == factory_id for f in data)

    def test_get_factory_detail(self, client: TestClient, db_session):
        """运营者可以查看工厂详情."""
        factory_id = _create_partner(db_session, "工厂B", "test_contact")
        _create_user(db_session, CURRENT_USER_ID, "op3@test.com",
                     login_platform="nuxt", participant_roles=["operator"])
        db_session.commit()
        token = _create_token(CURRENT_USER_ID)
        headers = {"Authorization": f"Bearer {token}"}
        resp = client.get(f"/api/operator/supply/factories/{factory_id}", headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == factory_id
        assert data["name"] == "工厂B"

    def test_get_factory_not_found(self, client: TestClient, db_session):
        """不存在的工厂返回404."""
        _create_user(db_session, CURRENT_USER_ID, "op4@test.com",
                     login_platform="nuxt", participant_roles=["operator"])
        db_session.commit()
        token = _create_token(CURRENT_USER_ID)
        headers = {"Authorization": f"Bearer {token}"}
        resp = client.get("/api/operator/supply/factories/nonexistent-id", headers=headers)
        assert resp.status_code == 404


class TestCreateOrder:
    def test_operator_can_create_order(self, client: TestClient, db_session):
        """运营者可以创建生产订单."""
        factory_id = _create_partner(db_session, "工厂C")
        _create_user(db_session, CURRENT_USER_ID, "op5@test.com",
                     login_platform="nuxt", participant_roles=["operator"])
        db_session.commit()
        token = _create_token(CURRENT_USER_ID)
        headers = {"Authorization": f"Bearer {token}"}
        resp = client.post(
            "/api/operator/supply/orders", headers=headers,
            json={"factory_id": factory_id, "product_name": "T恤定制",
                  "product_category": "apparel", "quantity": 100, "unit_price": 25.0,
                  "expected_date": "2026-09-15"},
        )
        assert resp.status_code == 200, f"Create order failed: {resp.json()}"
        data = resp.json()
        assert data["status"] == "draft"
        assert data["total_amount"] == 2500.0
        assert "order_number" in data

    def test_create_order_without_factory(self, client: TestClient, db_session):
        """运营者可以不指定工厂创建订单."""
        _create_user(db_session, CURRENT_USER_ID, "op6@test.com",
                     login_platform="nuxt", participant_roles=["operator"])
        db_session.commit()
        token = _create_token(CURRENT_USER_ID)
        headers = {"Authorization": f"Bearer {token}"}
        resp = client.post(
            "/api/operator/supply/orders", headers=headers,
            json={"product_name": "测试产品", "quantity": 10},
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "draft"

    def test_list_orders(self, client: TestClient, db_session):
        """运营者可以查看自己的订单列表."""
        _create_user(db_session, CURRENT_USER_ID, "op7@test.com",
                     login_platform="nuxt", participant_roles=["operator"])
        db_session.commit()
        order_id = _create_factory_order(db_session, CURRENT_USER_ID, product_name="批量T恤", quantity=200)
        db_session.commit()
        token = _create_token(CURRENT_USER_ID)
        headers = {"Authorization": f"Bearer {token}"}
        resp = client.get("/api/operator/supply/orders", headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert any(o["id"] == order_id for o in data)

    def test_list_orders_with_status_filter(self, client: TestClient, db_session):
        """按状态筛选订单."""
        _create_user(db_session, CURRENT_USER_ID, "op8@test.com",
                     login_platform="nuxt", participant_roles=["operator"])
        db_session.commit()
        order_id = _create_factory_order(db_session, CURRENT_USER_ID, status="confirmed")
        _create_factory_order(db_session, CURRENT_USER_ID, order_number="FO-TEST-2", status="draft")
        db_session.commit()
        token = _create_token(CURRENT_USER_ID)
        headers = {"Authorization": f"Bearer {token}"}
        resp = client.get("/api/operator/supply/orders?status=confirmed", headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        assert all(o["status"] == "confirmed" for o in data)


class TestOrderLifecycle:
    def test_confirm_order(self, client: TestClient, db_session):
        """订单从draft状态可以确认."""
        _create_user(db_session, CURRENT_USER_ID, "op9@test.com",
                     login_platform="nuxt", participant_roles=["operator"])
        db_session.commit()
        order_id = _create_factory_order(db_session, CURRENT_USER_ID, status="draft")
        db_session.commit()
        token = _create_token(CURRENT_USER_ID)
        headers = {"Authorization": f"Bearer {token}"}
        resp = client.post(f"/api/operator/supply/orders/{order_id}/confirm", headers=headers)
        assert resp.status_code == 200
        assert resp.json()["status"] == "confirmed"

    def test_confirm_already_confirmed_returns_400(self, client: TestClient, db_session):
        """已确认的订单不能再次确认."""
        _create_user(db_session, CURRENT_USER_ID, "op10@test.com",
                     login_platform="nuxt", participant_roles=["operator"])
        db_session.commit()
        order_id = _create_factory_order(db_session, CURRENT_USER_ID, status="confirmed")
        db_session.commit()
        token = _create_token(CURRENT_USER_ID)
        headers = {"Authorization": f"Bearer {token}"}
        resp = client.post(f"/api/operator/supply/orders/{order_id}/confirm", headers=headers)
        assert resp.status_code == 400

    def test_start_production(self, client: TestClient, db_session):
        """确认后订单可以开始生产."""
        _create_user(db_session, CURRENT_USER_ID, "op11@test.com",
                     login_platform="nuxt", participant_roles=["operator"])
        db_session.commit()
        order_id = _create_factory_order(db_session, CURRENT_USER_ID, status="confirmed")
        db_session.commit()
        token = _create_token(CURRENT_USER_ID)
        headers = {"Authorization": f"Bearer {token}"}
        resp = client.post(f"/api/operator/supply/orders/{order_id}/start", headers=headers)
        assert resp.status_code == 200
        assert resp.json()["status"] == "in_production"

    def test_ship_order(self, client: TestClient, db_session):
        """生产中订单可以标记发货."""
        _create_user(db_session, CURRENT_USER_ID, "op12@test.com",
                     login_platform="nuxt", participant_roles=["operator"])
        db_session.commit()
        order_id = _create_factory_order(db_session, CURRENT_USER_ID, status="in_production")
        db_session.commit()
        token = _create_token(CURRENT_USER_ID)
        headers = {"Authorization": f"Bearer {token}"}
        resp = client.post(
            f"/api/operator/supply/orders/{order_id}/ship?shipping_method=顺丰快递&tracking_number=SF1234567890",
            headers=headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "shipped"
        assert data["tracking_number"] == "SF1234567890"
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "shipped"
        assert data["tracking_number"] == "SF1234567890"

    def test_inspect_pass(self, client: TestClient, db_session):
        """质检通过订单完成."""
        _create_user(db_session, CURRENT_USER_ID, "op13@test.com",
                     login_platform="nuxt", participant_roles=["operator"])
        db_session.commit()
        order_id = _create_factory_order(db_session, CURRENT_USER_ID, status="shipped")
        db_session.commit()
        token = _create_token(CURRENT_USER_ID)
        headers = {"Authorization": f"Bearer {token}"}
        resp = client.post(
            f"/api/operator/supply/orders/{order_id}/inspect", headers=headers,
            json={"passed": True, "notes": "质量良好"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "completed"
        assert data["quality_passed"] is True

    def test_inspect_fail(self, client: TestClient, db_session):
        """质检不通过订单保持质检状态."""
        _create_user(db_session, CURRENT_USER_ID, "op14@test.com",
                     login_platform="nuxt", participant_roles=["operator"])
        db_session.commit()
        order_id = _create_factory_order(db_session, CURRENT_USER_ID, status="in_production")
        db_session.commit()
        token = _create_token(CURRENT_USER_ID)
        headers = {"Authorization": f"Bearer {token}"}
        resp = client.post(
            f"/api/operator/supply/orders/{order_id}/inspect", headers=headers,
            json={"passed": False, "notes": "有瑕疵"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "quality_check"
        assert data["quality_passed"] is False

    def test_order_not_found(self, client: TestClient, db_session):
        """不存在的订单返回404."""
        _create_user(db_session, CURRENT_USER_ID, "op15@test.com",
                     login_platform="nuxt", participant_roles=["operator"])
        db_session.commit()
        token = _create_token(CURRENT_USER_ID)
        headers = {"Authorization": f"Bearer {token}"}
        headers = {"Authorization": f"Bearer {token}"}
        resp = client.post(
            "/api/operator/supply/orders/nonexistent/confirm", headers=headers,
        )
        assert resp.status_code == 404

    def test_inspect_wrong_status_returns_400(self, client: TestClient, db_session):
        """draft状态不能质检."""
        _create_user(db_session, CURRENT_USER_ID, "op16@test.com",
                     login_platform="nuxt", participant_roles=["operator"])
        db_session.commit()
        order_id = _create_factory_order(db_session, CURRENT_USER_ID, status="draft")
        db_session.commit()
        token = _create_token(CURRENT_USER_ID)
        headers = {"Authorization": f"Bearer {token}"}
        resp = client.post(
            f"/api/operator/supply/orders/{order_id}/inspect", headers=headers,
            json={"passed": True},
        )
        assert resp.status_code == 400


class TestPODConfig:
    def test_create_pod_config(self, client: TestClient, db_session):
        """运营者可以配置POD平台."""
        _create_user(db_session, CURRENT_USER_ID, "op17@test.com",
                     login_platform="nuxt", participant_roles=["operator"])
        db_session.commit()
        token = _create_token(CURRENT_USER_ID)
        headers = {"Authorization": f"Bearer {token}"}
        resp = client.post(
            "/api/operator/supply/pod/configs", headers=headers,
            json={"platform": "printful", "api_key": "test_key_123"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["platform"] == "printful"
        assert data["is_active"] is True

    def test_duplicate_pod_config_rejected(self, client: TestClient, db_session):
        """同一平台重复配置返回400."""
        _create_user(db_session, CURRENT_USER_ID, "op18@test.com",
                     login_platform="nuxt", participant_roles=["operator"])
        db_session.commit()
        token = _create_token(CURRENT_USER_ID)
        headers = {"Authorization": f"Bearer {token}"}
        client.post("/api/operator/supply/pod/configs", headers=headers,
                    json={"platform": "printful", "api_key": "test_key_123"})
        resp = client.post("/api/operator/supply/pod/configs", headers=headers,
                           json={"platform": "printful", "api_key": "test_key_456"})
        assert resp.status_code == 400

    def test_list_pod_configs(self, client: TestClient, db_session):
        """运营者可以查看POD配置列表."""
        _create_user(db_session, CURRENT_USER_ID, "op19@test.com",
                     login_platform="nuxt", participant_roles=["operator"])
        db_session.commit()
        token = _create_token(CURRENT_USER_ID)
        headers = {"Authorization": f"Bearer {token}"}
        client.post("/api/operator/supply/pod/configs", headers=headers,
                    json={"platform": "printful", "api_key": "key1"})
        resp = client.get("/api/operator/supply/pod/configs", headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        assert data[0]["platform"] == "printful"
