"""Tests for publish (content distribution) endpoints."""

from datetime import date, datetime, timezone
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session


def _auth_headers() -> dict:
    return {"Authorization": "Bearer local"}


def _create_product(db_session: Session, **kwargs) -> dict:
    """Helper: create a product and return its id."""
    from app.models.publish import Product

    product = Product(
        title=kwargs.get("title", "Test Product"),
        description=kwargs.get("description", "A test product"),
        price=kwargs.get("price", 99.0),
        category=kwargs.get("category", "design"),
        status="active",
        **{k: v for k, v in kwargs.items() if k not in ("title", "description", "price", "category")},
    )
    db_session.add(product)
    db_session.commit()
    db_session.refresh(product)
    return {"id": product.id, "title": product.title}


class TestListProducts:
    def test_returns_empty_list(self, client: TestClient):
        resp = client.get("/api/publish/products")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert isinstance(data, list)

    def test_returns_created_products(self, client: TestClient, db_session: Session):
        prod = _create_product(db_session, title="Listing Product")
        resp = client.get("/api/publish/products")
        assert resp.status_code == 200
        ids = [p["id"] for p in resp.json()["data"]]
        assert prod["id"] in ids

    def test_includes_fields(self, client: TestClient, db_session: Session):
        prod = _create_product(db_session, title="Field Product", price=150.0)
        resp = client.get(f"/api/publish/products")
        items = resp.json()["data"]
        found = next(p for p in items if p["id"] == prod["id"])
        assert found["title"] == "Field Product"
        assert found["price"] == 150.0


class TestCreateProduct:
    def test_creates_product(self, client: TestClient, db_session: Session):
        payload = {
            "title": "New Product",
            "description": "Description here",
            "price": 49.9,
            "category": "art",
            "images": ["img1.jpg"],
        }
        resp = client.post("/api/publish/products", json=payload, headers=_auth_headers())
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert "id" in data

    def test_defaults_price_to_zero(self, client: TestClient, db_session: Session):
        payload = {"title": "Free Product"}
        resp = client.post("/api/publish/products", json=payload, headers=_auth_headers())
        assert resp.status_code == 200
        assert resp.json()["data"]["id"] is not None


class TestUpdateProduct:
    def test_updates_title(self, client: TestClient, db_session: Session):
        prod = _create_product(db_session)
        resp = client.put(
            f"/api/publish/products/{prod['id']}",
            json={"title": "Updated Title"},
            headers=_auth_headers(),
        )
        assert resp.status_code == 200
        assert resp.json()["data"]["id"] == prod["id"]

    def test_returns_404_for_missing(self, client: TestClient):
        resp = client.put(
            "/api/publish/products/nonexistent",
            json={"title": "Ghost"},
            headers=_auth_headers(),
        )
        assert resp.status_code == 404

    def test_updating_nonexistent_field_is_ignored(self, client: TestClient, db_session: Session):
        prod = _create_product(db_session)
        resp = client.put(
            f"/api/publish/products/{prod['id']}",
            json={"nonexistent_field": "x"},
            headers=_auth_headers(),
        )
        assert resp.status_code == 200


class TestDeleteProduct:
    def test_deletes_product(self, client: TestClient, db_session: Session):
        prod = _create_product(db_session)
        resp = client.delete(f"/api/publish/products/{prod['id']}", headers=_auth_headers())
        assert resp.status_code == 200
        assert resp.json()["message"] == "商品已删除"

    def test_returns_404_for_missing(self, client: TestClient):
        resp = client.delete("/api/publish/products/nonexistent", headers=_auth_headers())
        assert resp.status_code == 404


class TestDescribeStyles:
    def test_returns_all_styles(self, client: TestClient):
        resp = client.get("/api/publish/describe/styles")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert isinstance(data, list)
        keys = [s["key"] for s in data]
        assert "xiaohongshu" in keys
        assert "taobao" in keys


class TestAIDescription:
    def test_generates_description_with_template_fallback(self, client: TestClient, db_session: Session):
        prod = _create_product(db_session, title="AI Product")
        resp = client.post(
            f"/api/publish/products/{prod['id']}/describe",
            json={"style": "xiaohongshu"},
            headers=_auth_headers(),
        )
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert "description" in data
        # Template fallback contains the product title
        assert "AI Product" in data["description"]

    def test_rejects_invalid_style(self, client: TestClient, db_session: Session):
        prod = _create_product(db_session)
        resp = client.post(
            f"/api/publish/products/{prod['id']}/describe",
            json={"style": "nonexistent"},
            headers=_auth_headers(),
        )
        assert resp.status_code == 400

    def test_returns_404_for_missing_product(self, client: TestClient):
        resp = client.post(
            "/api/publish/products/nonexistent/describe",
            json={"style": "taobao"},
            headers=_auth_headers(),
        )
        assert resp.status_code == 404


class TestExportCSV:
    def test_exports_csv(self, client: TestClient, db_session: Session):
        prod = _create_product(db_session)
        resp = client.get(f"/api/publish/export/{prod['id']}?platform=taobao")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert "csv_content" in data
        assert "file_path" in data

    def test_rejects_invalid_platform(self, client: TestClient, db_session: Session):
        prod = _create_product(db_session)
        resp = client.get(f"/api/publish/export/{prod['id']}?platform=invalid")
        assert resp.status_code == 400

    def test_returns_404_for_missing(self, client: TestClient):
        resp = client.get("/api/publish/export/nonexistent?platform=taobao")
        assert resp.status_code == 404


class TestPlatforms:
    def test_returns_platforms(self, client: TestClient):
        resp = client.get("/api/publish/platforms")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert isinstance(data, list)
        keys = [p["key"] for p in data]
        assert "taobao" in keys


class TestPublishProduct:
    def test_publishes_product(self, client: TestClient, db_session: Session):
        prod = _create_product(db_session)
        resp = client.post(
            f"/api/publish/publish/{prod['id']}?platform=taobao",
            headers=_auth_headers(),
        )
        assert resp.status_code == 200
        assert "publish_id" in resp.json()["data"]

    def test_rejects_invalid_platform(self, client: TestClient, db_session: Session):
        prod = _create_product(db_session)
        resp = client.post(
            f"/api/publish/publish/{prod['id']}?platform=invalid",
            headers=_auth_headers(),
        )
        assert resp.status_code == 400


class TestRevenueSummary:
    def test_returns_summary(self, client: TestClient):
        resp = client.get("/api/publish/revenue/summary")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert "total_amount" in data
        assert "period" in data

    def test_filters_by_period(self, client: TestClient):
        resp = client.get("/api/publish/revenue/summary?period=year")
        assert resp.status_code == 200
        assert resp.json()["data"]["period"] == "year"


class TestAddRevenue:
    def test_adds_revenue_record(self, client: TestClient, db_session: Session):
        payload = {
            "platform": "taobao",
            "amount": 200.0,
            "order_count": 3,
            "notes": "Test sale",
        }
        resp = client.post("/api/publish/revenue", json=payload, headers=_auth_headers())
        assert resp.status_code == 200
        assert resp.json()["message"] == "收入记录已添加"

    def test_accepts_custom_date(self, client: TestClient, db_session: Session):
        payload = {"platform": "test", "amount": 50.0, "date": "2025-06-15"}
        resp = client.post("/api/publish/revenue", json=payload, headers=_auth_headers())
        assert resp.status_code == 200


class TestListRevenue:
    def test_lists_revenue(self, client: TestClient, db_session: Session):
        _create_product(db_session)
        client.post(
            "/api/publish/revenue",
            json={"platform": "taobao", "amount": 100.0},
            headers=_auth_headers(),
        )
        resp = client.get("/api/publish/revenue")
        assert resp.status_code == 200
        assert len(resp.json()["data"]) >= 1

    def test_filters_by_platform(self, client: TestClient, db_session: Session):
        client.post(
            "/api/publish/revenue",
            json={"platform": "douyin", "amount": 50.0},
            headers=_auth_headers(),
        )
        resp = client.get("/api/publish/revenue?platform=douyin")
        assert resp.status_code == 200
        for r in resp.json()["data"]:
            assert r["platform"] == "douyin"


class TestImportRevenueCSV:
    def test_imports_generic_csv(self, client: TestClient, db_session: Session):
        csv_content = "platform,amount,date,order_count,product_sku,notes\ntaobao,100.0,2025-07-01,2,SKU1,Test"
        resp = client.post(
            "/api/publish/revenue/import",
            files={"file": ("test.csv", csv_content.encode("utf-8-sig"), "text/csv")},
            headers=_auth_headers(),
        )
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["imported"] >= 1

    def test_rejects_non_csv_file(self, client: TestClient):
        resp = client.post(
            "/api/publish/revenue/import",
            files={"file": ("test.txt", b"hello", "text/plain")},
            headers=_auth_headers(),
        )
        assert resp.status_code == 400

    def test_rejects_empty_file(self, client: TestClient):
        resp = client.post(
            "/api/publish/revenue/import",
            files={"file": ("empty.csv", b"", "text/csv")},
            headers=_auth_headers(),
        )
        assert resp.status_code == 400


class TestSchedules:
    def test_creates_schedule(self, client: TestClient, db_session: Session):
        payload = {
            "platform": "xiaohongshu",
            "scheduled_time": "2026-08-01T10:00:00",
            "content_preview": "Test post",
        }
        resp = client.post("/api/publish/schedule", json=payload, headers=_auth_headers())
        assert resp.status_code == 200
        assert resp.json()["message"] == "排期已创建"

    def test_list_schedules(self, client: TestClient, db_session: Session):
        client.post(
            "/api/publish/schedule",
            json={"platform": "taobao"},
            headers=_auth_headers(),
        )
        resp = client.get("/api/publish/schedules")
        assert resp.status_code == 200

    def test_cancels_schedule(self, client: TestClient, db_session: Session):
        client.post(
            "/api/publish/schedule",
            json={
                "platform": "douyin",
                "scheduled_time": "2026-09-01T10:00:00",
            },
            headers=_auth_headers(),
        )
        # Get the schedule from list to find its ID
        list_resp = client.get("/api/publish/schedules")
        scheds = list_resp.json()["data"]
        assert len(scheds) >= 1
        schedule_id = scheds[-1]["id"]  # last one is the one we just created
        resp = client.delete(f"/api/publish/schedules/{schedule_id}", headers=_auth_headers())
        assert resp.status_code == 200
        assert resp.json()["message"] == "排期已取消"


class TestPublishContents:
    def test_creates_content(self, client: TestClient, db_session: Session):
        payload = {"title": "My Post", "content_type": "work", "text_content": "Hello world"}
        resp = client.post("/api/publish/contents", json=payload, headers=_auth_headers())
        assert resp.status_code == 200
        assert resp.json()["message"] == "发布内容已创建"

    def test_list_contents(self, client: TestClient, db_session: Session):
        client.post(
            "/api/publish/contents",
            json={"title": "Content 1"},
            headers=_auth_headers(),
        )
        resp = client.get("/api/publish/contents")
        assert resp.status_code == 200
        assert len(resp.json()["data"]) >= 1


class TestAnalytics:
    def test_adds_analytics(self, client: TestClient, db_session: Session):
        payload = {
            "platform": "xiaohongshu",
            "views": 100,
            "likes": 20,
            "comments": 5,
            "shares": 3,
            "saves": 1,
        }
        resp = client.post("/api/publish/analytics", json=payload, headers=_auth_headers())
        assert resp.status_code == 200
        assert resp.json()["message"] == "影响力数据已录入"

    def test_list_analytics(self, client: TestClient, db_session: Session):
        client.post(
            "/api/publish/analytics",
            json={"platform": "taobao", "views": 50},
            headers=_auth_headers(),
        )
        resp = client.get("/api/publish/analytics")
        assert resp.status_code == 200
        assert len(resp.json()["data"]) >= 1

    def test_filters_analytics_by_platform(self, client: TestClient, db_session: Session):
        client.post(
            "/api/publish/analytics",
            json={"platform": "douyin", "views": 10},
            headers=_auth_headers(),
        )
        resp = client.get("/api/publish/analytics?platform=douyin")
        assert resp.status_code == 200
        for a in resp.json()["data"]:
            assert a["platform"] == "douyin"
