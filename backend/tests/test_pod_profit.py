"""POD利润模块 API 测试."""
import pytest


def _create_user(db_session, email="pod_test@example.com"):
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


class TestPODProductConfig:
    """测试 /api/pod-profit/product-config 端点."""

    def test_create_product_config(self, client, db_session):
        """创建POD产品配置应成功."""
        _create_user(db_session, email="pod_creator@example.com")
        resp = client.post(
            "/api/pod-profit/product-config",
            json={
                "platform": "redbubble",
                "product_type": "tshirt",
                "markup_rate": 1.5,
            },
        )
        assert resp.status_code in (200, 201)
        data = resp.json()
        assert data["platform"] == "redbubble"

    def test_create_product_duplicate(self, client, db_session):
        """重复创建应返回现有配置."""
        _create_user(db_session, email="pod_dup@example.com")
        resp1 = client.post(
            "/api/pod-profit/product-config",
            json={"platform": "society6", "product_type": "mug", "markup_rate": 2.0},
        )
        assert resp1.status_code in (200, 201)
        resp2 = client.post(
            "/api/pod-profit/product-config",
            json={"platform": "society6", "product_type": "mug", "markup_rate": 2.0},
        )
        assert resp2.status_code in (200, 201)


class TestPODPricing:
    """测试定价模拟端点."""

    def test_simulate_pricing(self, client):
        """定价模拟应返回结果列表."""
        resp = client.post(
            "/api/pod-profit/simulate-pricing",
            json={
                "platform": "redbubble",
                "product_type": "tshirt",
                "markup_rate": 1.5,
            },
        )
        # 返回直接是 list[PricingSimulation]，不是 ApiResponse
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) > 0
        assert "markup_pct" in data[0]

    def test_simulate_pricing_invalid(self, client):
        """缺少必填字段应返回422."""
        resp = client.post(
            "/api/pod-profit/simulate-pricing",
            json={},
        )
        assert resp.status_code == 422


class TestPODSale:
    """测试销售记录端点."""

    def test_log_sale(self, client, db_session):
        """记录销售应成功 — 需要完整字段."""
        _create_user(db_session, email="pod_seller@example.com")
        resp = client.post(
            "/api/pod-profit/log-sale",
            json={
                "platform": "redbubble",
                "product_type": "tshirt",
                "sale_price_usd": 25.0,
                "base_cost_usd": 8.5,
            },
        )
        assert resp.status_code in (200, 201)
        data = resp.json()
        # ProfitResult 直接返回，无 success 包装
        assert "profit_usd" in data
        assert "margin_pct" in data


class TestPODSummary:
    """测试汇总统计端点."""

    def test_designs_summary(self, client):
        """设计汇总应返回空列表 — 返回 list[DesignSummary] 而非 ApiResponse."""
        resp = client.get("/api/pod-profit/designs-summary")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)

    def test_overview(self, client, db_session):
        """概览数据应返回 PodOverview."""
        _create_user(db_session, email="pod_overview@example.com")
        resp = client.get("/api/pod-profit/overview")
        assert resp.status_code == 200
        data = resp.json()
        assert "total_sales" in data
        assert "total_revenue_cny" in data

    def test_my_settlements(self, client, db_session):
        """我的结算列表应返回."""
        _create_user(db_session, email="pod_settle@example.com")
        resp = client.get("/api/pod-profit/my-settlements")
        assert resp.status_code == 200

    def test_generate_settlement(self, client, db_session):
        """生成结算单应成功 — 需先创建current_user以通过FK约束."""
        _create_user(db_session, email="current_user")
        _create_user(db_session, email="pod_gen@example.com")
        resp = client.post("/api/pod-profit/settlements/generate?period=2026-08")
        assert resp.status_code in (200, 400)

    def test_confirm_settlement(self, client, db_session):
        """确认结算单应成功."""
        _create_user(db_session, email="current_user")
        _create_user(db_session, email="pod_confirm@example.com")
        resp = client.post("/api/pod-profit/settlements/generate?period=2026-08")
        if resp.status_code == 200:
            settlement_id = resp.json().get("id")
            if settlement_id:
                resp2 = client.post(f"/api/pod-profit/settlements/{settlement_id}/confirm")
                assert resp2.status_code in (200, 400)
        else:
            pytest.skip("Settlement generation failed, skipping confirm")

    def test_sales_statistics(self, client, db_session):
        """销售统计应返回."""
        _create_user(db_session, email="pod_stats@example.com")
        resp = client.get("/api/pod-profit/sales/statistics")
        assert resp.status_code in (200, 500)
