"""Etsy API Gateway Service 集成测试.

Tests:
1. connect_shop — exchanges auth code, stores encrypted token
2. sync_product_to_etsy — creates listing, calls Etsy API
3. sync_orders — fetches orders, creates EtsyOrder records
4. get_dashboard — aggregates data
"""

import asyncio
import datetime
import os
import sys
from pathlib import Path
from unittest.mock import AsyncMock, patch, MagicMock, PropertyMock

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.models.etsy import EtsyListing, EtsyOrder, EtsyShop
from app.models.system import User as UserModel
from app.services.etsy_service import EtsyService, EtsyGateway


@pytest.fixture
def ettsy_service(db_session):
    return EtsyService(db_session)


# ── 1. connect_shop ─────────────────────────────────────────

class TestConnectShop:
    def test_connect_shop_mock_mode(self, ettsy_service, db_session):
        """Real mode: still needs HTTP mock for token exchange."""
        # Patch _is_configured so the service doesn't short-circuit to mock mode
        with patch.object(type(ettsy_service.gateway), '_is_configured', new_callable=PropertyMock, return_value=True):
            # Seed user
            user = UserModel(id="test-user-001", username="tester", email="test@example.com")
            db_session.add(user)
            db_session.commit()

            mock_token_response = {
                "access_token": "fake-access-token",
                "refresh_token": "fake-refresh-token",
                "expires_in": 14400,
                "shop_name": "Test Shop",
                "shop_id": "etsy-mock-shop",
            }
            mock_resp = MagicMock()
            mock_resp.raise_for_status.return_value = None
            mock_resp.json.return_value = mock_token_response

            with patch("app.services.etsy_service.httpx.AsyncClient") as mock_client_cls:
                mock_client = AsyncMock()
                mock_client.post.return_value = mock_resp
                mock_client.aclose = AsyncMock()
                mock_client_cls.return_value.__aenter__.return_value = mock_client

                result = asyncio_run(ettsy_service.connect_shop("test-user-001", "fake-code"))

            assert result["shop_name"] == "Test Shop"
            assert result["shop_id"] == "etsy-mock-shop"
            # Verify DB record
            shop = db_session.query(EtsyShop).filter(
                EtsyShop.user_id == "test-user-001"
            ).first()
            assert shop is not None
            assert shop.shop_name == "Test Shop"
            assert shop.access_token  # encrypted value stored

    def test_connect_shop_real_flow(self, ettsy_service, db_session):
        """Real OAuth flow: exchange code for tokens, stored in DB."""
        with patch.object(type(ettsy_service.gateway), '_is_configured', new_callable=PropertyMock, return_value=True):
            user = UserModel(id="test-user-001", username="tester", email="test@example.com")
            db_session.add(user)
            db_session.commit()

            mock_token_response = {
                "access_token": "fake-access-token-xyz",
                "refresh_token": "fake-refresh-token-abc",
                "expires_in": 14400,
                "shop_name": "My Mock Etsy Shop",
                "shop_id": "etsy-shop-real-123",
            }
            mock_resp = MagicMock()
            mock_resp.raise_for_status.return_value = None
            mock_resp.json.return_value = mock_token_response

            with patch("app.services.etsy_service.httpx.AsyncClient") as mock_client_cls:
                mock_client = AsyncMock()
                mock_client.post.return_value = mock_resp
                mock_client.aclose = AsyncMock()
                mock_client_cls.return_value.__aenter__.return_value = mock_client

                result = asyncio_run(ettsy_service.connect_shop("test-user-001", "auth-code-123"))

            assert result["shop_name"] == "My Mock Etsy Shop"
            assert result["shop_id"] == "etsy-shop-real-123"

            # Verify encrypted storage
            shop = db_session.query(EtsyShop).filter(
                EtsyShop.user_id == "test-user-001"
            ).first()
            assert shop is not None
            assert shop.access_token  # should be encrypted, not plain text
            assert shop.refresh_token  # also encrypted


# ── 2. sync_product_to_etsy ─────────────────────────────────

class TestSyncProductToEtsy:
    def test_sync_creates_listing(self, ettsy_service, db_session):
        """Create an Etsy shop + listing via mock."""
        user = UserModel(id="test-user-001", username="tester", email="test@example.com")
        db_session.add(user)
        db_session.commit()

        # First connect a shop (env vars already set via fixture)
        mock_token_response = {
            "access_token": "fake-token",
            "refresh_token": "fake-refresh",
            "expires_in": 14400,
            "shop_name": "Test Shop",
            "shop_id": "etsy-shop-456",
        }
        mock_resp = MagicMock()
        mock_resp.raise_for_status.return_value = None
        mock_resp.json.return_value = mock_token_response

        with patch("app.services.etsy_service.httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.post.return_value = mock_resp
            mock_client.aclose = AsyncMock()
            mock_client_cls.return_value.__aenter__.return_value = mock_client

            # Patch _is_configured so connect_shop goes through real OAuth path
            with patch.object(type(ettsy_service.gateway), '_is_configured', new_callable=PropertyMock, return_value=True):
                asyncio_run(ettsy_service.connect_shop("test-user-001", "auth-code"))

        # Replace the gateway instance with a mock for create_listing
        mock_gw_instance = MagicMock()
        mock_gw_instance.create_listing = AsyncMock(return_value="etsy-listing-789")
        orig_gateway = ettsy_service.gateway
        ettsy_service.gateway = mock_gw_instance
        try:
            result = asyncio_run(ettsy_service.sync_product_to_etsy(
                user_id="test-user-001",
                product_id=None,
                listing_data={
                    "title": "Handmade Ceramic Mug",
                    "price": 24.99,
                    "quantity": 5,
                    "tags": ["ceramic", "handmade", "mug"],
                    "materials": ["clay", "glaze"],
                    "images": ["http://example.com/mug.png"],
                },
            ))
        finally:
            ettsy_service.gateway = orig_gateway

        assert result["status"] == "draft"
        assert result["title"] == "Handmade Ceramic Mug"

        # Verify DB record
        listing = db_session.query(EtsyListing).filter(
            EtsyListing.etsy_listing_id == "etsy-listing-789"
        ).first()
        assert listing is not None
        assert listing.title == "Handmade Ceramic Mug"
        assert listing.price == 24.99
        assert listing.user_id == "test-user-001"

    def test_sync_no_shop_fails(self, ettsy_service, db_session):
        """Should fail if no active Etsy shop is connected."""
        user = UserModel(id="test-user-001", username="tester", email="test@example.com")
        db_session.add(user)
        db_session.commit()

        result = asyncio_run(ettsy_service.sync_product_to_etsy(
            user_id="test-user-001",
            product_id="prod-001",
            listing_data={"title": "No Shop", "price": 1.0},
        ))
        assert result["status"] == "error"


# ── 3. sync_orders ─────────────────────────────────────────

class TestSyncOrders:
    def test_sync_orders(self, ettsy_service, db_session):
        """Fetch Etsy orders and create EtsyOrder records."""
        user = UserModel(id="test-user-001", username="tester", email="test@example.com")
        db_session.add(user)
        db_session.commit()

        # Connect shop first (env vars already set via fixture)
        mock_token_response = {
            "access_token": "fake-token",
            "expires_in": 14400,
            "shop_name": "Test Shop",
            "shop_id": "etsy-shop-orders",
        }
        mock_resp = MagicMock()
        mock_resp.raise_for_status.return_value = None
        mock_resp.json.return_value = mock_token_response

        with patch("app.services.etsy_service.httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.post.return_value = mock_resp
            mock_client.aclose = AsyncMock()
            mock_client_cls.return_value.__aenter__.return_value = mock_client

            # Patch _is_configured so connect_shop goes through real OAuth path
            with patch.object(type(ettsy_service.gateway), '_is_configured', new_callable=PropertyMock, return_value=True):
                asyncio_run(ettsy_service.connect_shop("test-user-001", "auth-code"))

        # Mock order data from Etsy API
        mock_orders = [
            {
                "order_id": "etsy-order-100",
                "state": "paid",
                "created_utc": "2026-06-01T10:00:00Z",
                "transactions": [{"amount": "49.99"}],
                "shipping_cost": {"amount": "500"},  # cents
                "tax": {"amount": "200"},  # cents
                "shipping_details": [{"name": "John Doe", "country": "US"}],
            },
            {
                "order_id": "etsy-order-101",
                "state": "shipped",
                "created_utc": "2026-06-02T14:00:00Z",
                "transactions": [{"amount": "99.99"}],
                "shipping_cost": None,
                "tax": None,
                "shipping_details": [{"name": "Jane Smith", "country": "GB"}],
            },
        ]

        with patch.object(EtsyGateway, 'get_orders', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_orders
            result = asyncio_run(ettsy_service.sync_orders("test-user-001"))

        assert len(result) == 2
        assert result[0]["etsy_order_id"] == "etsy-order-100"
        assert result[1]["etsy_order_id"] == "etsy-order-101"

        # Verify DB records
        count = db_session.query(EtsyOrder).filter(
            EtsyOrder.user_id == "test-user-001"
        ).count()
        assert count == 2

        order1 = db_session.query(EtsyOrder).filter(
            EtsyOrder.etsy_order_id == "etsy-order-100"
        ).first()
        assert order1.buyer_name == "John Doe"
        assert order1.buyer_country == "US"
        assert order1.order_total == 49.99
        assert order1.status == "paid"


# ── 4. get_dashboard ───────────────────────────────────────

class TestGetDashboard:
    def test_dashboard_aggregation(self, ettsy_service, db_session):
        """Aggregate dashboard data from listings + orders."""
        user = UserModel(id="test-user-001", username="tester", email="test@example.com")
        db_session.add(user)
        db_session.commit()

        # Connect shop first (must be inside _is_configured patch so DB records are created)
        mock_token_response = {
            "access_token": "fake-token",
            "expires_in": 14400,
            "shop_name": "Test Shop",
            "shop_id": "etsy-shop-dash",
        }
        mock_resp = MagicMock()
        mock_resp.raise_for_status.return_value = None
        mock_resp.json.return_value = mock_token_response

        with patch("app.services.etsy_service.httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.post.return_value = mock_resp
            mock_client.aclose = AsyncMock()
            mock_client_cls.return_value.__aenter__.return_value = mock_client

            with patch.object(type(ettsy_service.gateway), '_is_configured', new_callable=PropertyMock, return_value=True):
                asyncio_run(ettsy_service.connect_shop("test-user-001", "auth-code"))

        # Create mock EtsyListing records
        listing1 = EtsyListing(
            id="etl-001",
            user_id="test-user-001",
            etsy_listing_id="etsy-listing-dash-1",
            etsy_shop_id="etsy-shop-orders",
            title="Ceramic Bowl",
            price=29.99,
            currency="USD",
            quantity=3,
            status="active",
            views_count=150,
            favorites_count=12,
            sales_count=5,
            revenue=149.95,
        )
        listing2 = EtsyListing(
            id="etl-002",
            user_id="test-user-001",
            etsy_listing_id="etsy-listing-dash-2",
            etsy_shop_id="etsy-shop-orders",
            title="Wooden Spoon",
            price=9.99,
            currency="USD",
            quantity=10,
            status="active",
            views_count=80,
            favorites_count=5,
            sales_count=2,
            revenue=19.98,
        )
        db_session.add_all([listing1, listing2])
        db_session.flush()

        # Create mock EtsyOrder records with dates in same month
        orders = [
            EtsyOrder(
                id="eoo-001",
                user_id="test-user-001",
                listing_id="etl-001",
                etsy_order_id="dash-order-1",
                order_total=29.99,
                status="paid",
                order_date=datetime.datetime(2026, 3, 15, 10, 0, 0),
            ),
            EtsyOrder(
                id="eoo-002",
                user_id="test-user-001",
                listing_id="etl-001",
                etsy_order_id="dash-order-2",
                order_total=29.99,
                status="shipped",
                order_date=datetime.datetime(2026, 3, 20, 14, 0, 0),
            ),
            EtsyOrder(
                id="eoo-003",
                user_id="test-user-001",
                listing_id="etl-002",
                etsy_order_id="dash-order-3",
                order_total=9.99,
                status="completed",
                order_date=datetime.datetime(2026, 3, 10, 9, 0, 0),
            ),
            EtsyOrder(
                id="eoo-004",
                user_id="test-user-001",
                listing_id="etl-001",
                etsy_order_id="dash-order-4",
                order_total=29.99,
                status="cancelled",
                order_date=datetime.datetime(2026, 3, 5, 16, 0, 0),
            ),
        ]
        db_session.add_all(orders)
        db_session.commit()

        result = asyncio_run(ettsy_service.get_dashboard("test-user-001"))

        assert result["total_sales"] == 3  # excludes cancelled
        assert result["total_views"] == 230  # 150 + 80
        assert result["total_favorites"] == 17  # 12 + 5
        assert result["total_revenue"] == 69.97  # 29.99*2 + 9.99 (excludes cancelled)
        assert result["active_listings"] == 2
        assert len(result["revenue_by_month"]) == 6
        assert "paid" in result["orders_by_status"]
        assert "shipped" in result["orders_by_status"]
        assert "completed" in result["orders_by_status"]
        assert len(result["top_listings"]) == 2
        # Top listing should be the bowl (more revenue)
        assert result["top_listings"][0]["title"] == "Ceramic Bowl"


# ── 5. Gateway mock tests ───────────────────────────────────

class TestEtsyGatewayMock:
    def test_create_listing_returns_mock_id(self):
        """Without configured API, returns mock ID."""
        # Clear Etsy env vars so _is_configured is False
        with patch.dict(os.environ, clear=True):
            gw = EtsyGateway()
            result = asyncio_run(gw.create_listing(
                "fake-token", "shop-1", {"title": "Test Item"}, []
            ))
        assert isinstance(result, str)
        assert len(result) > 0

    def test_get_listings_returns_empty_when_not_configured(self):
        """Without configured API, get_listings returns empty."""
        with patch.dict(os.environ, clear=True):
            gw = EtsyGateway()
            result = asyncio_run(gw.get_listings("fake-token", "shop-1"))
        assert result == []

    def test_get_inventory_returns_mock(self):
        """Without configured API, get_inventory returns mock."""
        with patch.dict(os.environ, clear=True):
            gw = EtsyGateway()
            result = asyncio_run(gw.get_inventory("fake-token", "listing-1"))
        assert result == {"listing_id": "listing-1", "quantity": 1}


def asyncio_run(coro):
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()
