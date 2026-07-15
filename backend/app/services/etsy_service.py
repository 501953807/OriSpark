"""Etsy Open API v3 Gateway + Business Service.

Handyman (v3b) — Etsy 店铺连接、商品发布、订单同步.
"""

import os
import time
from datetime import datetime, timedelta
from typing import Optional

import httpx

from app.utils.crypto import encrypt, decrypt
from app.models.etsy import EtsyListing, EtsyOrder, EtsyShop


# =============================================================================
# EtsyGateway — Low-level Open API v3 client
# =============================================================================


class EtsyGateway:
    """Etsy Open API v3 gateway."""

    BASE_URL = "https://openapi.etsy.com/v3"
    AUTH_URL = "https://www.etsy.com/oauth"

    RATE_LIMIT_REQS_PER_SEC = 5.0
    _last_request_time: float = 0.0

    def __init__(self, client_id: Optional[str] = None, client_secret: Optional[str] = None):
        self.client_id = client_id or os.environ.get("ETSY_CLIENT_ID", "")
        self.client_secret = client_secret or os.environ.get("ETSY_CLIENT_SECRET", "")

    @property
    def _is_configured(self) -> bool:
        return bool(self.client_id and self.client_secret)

    # ---------------------------------------------------------------
    # Internal helpers
    # ---------------------------------------------------------------

    async def _authenticate(self, access_token: str) -> httpx.AsyncClient:
        """Return an authenticated AsyncClient (caller must close)."""
        headers = {"Authorization": f"OAuth {access_token}"}
        return httpx.AsyncClient(base_url=self.BASE_URL, headers=headers, timeout=30)

    async def _request(
        self,
        method: str,
        endpoint: str,
        access_token: str,
        **kwargs,
    ) -> dict:
        """Rate-limit aware request to Etsy Open API v3."""
        # Enforce 5 req/sec per token
        elapsed = time.time() - self._last_request_time
        min_interval = 1.0 / self.RATE_LIMIT_REQS_PER_SEC
        if elapsed < min_interval:
            await httpx.AsyncClient().aclose()
            await asyncio_sleep(min_interval - elapsed)
        self._last_request_time = time.time()

        async with await self._authenticate(access_token) as client:
            url = f"{self.BASE_URL}/{endpoint.lstrip('/')}"
            resp = await client.request(method, url, **kwargs)
            resp.raise_for_status()
            return resp.json()

    async def create_listing(self, access_token, shop_id, product_data, images) -> str:
        """Create a listing via Etsy Open API v3."""
        if not self._is_configured:
            listing_id = f"etsy-mock-{hash(product_data.get('title', '')) & 0xFFFF:04x}"
            print(f"[Etsy] MOCK create_listing: {listing_id}")
            return listing_id

        endpoint = f"shops/{shop_id}/listings"
        body = {
            "title": product_data.get("title", ""),
            "description": product_data.get("description", ""),
            "price": str(product_data.get("price", "0.00")),
            "quantity": product_data.get("quantity", 1),
            "category_identifier": product_data.get("category_id"),
            "processing_min": product_data.get("processing_time_days", 1),
            "processing_max": product_data.get("processing_time_days", 1),
            "tax_required": False,
            "who_is_it_for": [],
            "is_private": False,
        }
        if product_data.get("tags"):
            body["tags"] = product_data.get("tags", [])[:13]
        if product_data.get("materials"):
            body["materials"] = product_data.get("materials", [])
        if product_data.get("variations"):
            body["options"] = [{"name": "Option1", "values": product_data.get("variations", ["Default"])}]
        if images:
            body["images"] = [{"local_path": img} for img in images[:12]]

        data = await self._request("POST", endpoint, access_token, json=body)
        return str(data.get("results", [{}])[0].get("listing_id", ""))

    async def update_listing(self, access_token, listing_id, product_data) -> dict:
        """Update an existing Etsy listing."""
        if not self._is_configured:
            print(f"[Etsy] MOCK update_listing: {listing_id}")
            return {"listing_id": listing_id, "status": "mock_updated"}

        data = await self._request(
            "PUT",
            f"listings/{listing_id}",
            access_token,
            json={
                "title": product_data.get("title"),
                "description": product_data.get("description"),
                "price": str(product_data.get("price", "0.00")),
                "quantity": product_data.get("quantity"),
                "tags": product_data.get("tags"),
                "materials": product_data.get("materials"),
                "who_is_it_for": product_data.get("who_is_it_for"),
                "is_private": product_data.get("is_private", False),
            },
        )
        return data

    async def get_listing(self, access_token, listing_id) -> dict:
        """Get a single listing detail."""
        if not self._is_configured:
            return {
                "listing_id": listing_id,
                "title": "Mock Listing",
                "state": "active",
                "price": "10.00",
                "quantity": 1,
            }

        data = await self._request(
            "GET",
            f"listings/{listing_id}",
            access_token,
        )
        return data

    async def delete_listing(self, access_token, listing_id) -> bool:
        """Delete (deactivate) a listing."""
        try:
            await self._request(
                "DELETE",
                f"listings/{listing_id}",
                access_token,
            )
            return True
        except Exception as e:
            print(f"[Etsy] delete_listing error: {e}")
            return False

    async def get_listings(self, access_token, shop_id, status="active") -> list:
        """Get all listings for a shop."""
        if not self._is_configured:
            return []

        data = await self._request(
            "GET",
            f"shops/{shop_id}/listings",
            access_token,
            params={"status": status, "limit": 25},
        )
        return data.get("results", [])

    async def get_orders(self, access_token, shop_id, filters=None) -> list:
        """Get orders for a shop."""
        if not self._is_configured:
            return []

        params = {"limit": 25}
        if filters:
            params.update(filters)

        data = await self._request(
            "GET",
            f"shops/{shop_id}/orders",
            access_token,
            params=params,
        )
        return data.get("results", [])

    async def get_inventory(self, access_token, listing_id) -> dict:
        """Get inventory quantity for a listing."""
        if not self._is_configured:
            return {"listing_id": listing_id, "quantity": 1}

        listing = await self.get_listing(access_token, listing_id)
        return {"listing_id": listing_id, "quantity": listing.get("quantity", 1)}

    async def update_inventory(self, access_token, listing_id, quantity) -> dict:
        """Update inventory quantity."""
        if not self._is_configured:
            return {"listing_id": listing_id, "quantity": quantity}

        listing = await self._request(
            "GET",
            f"listings/{listing_id}",
            access_token,
        )
        # PATCH via update_listing endpoint
        await self._request(
            "PUT",
            f"listings/{listing_id}",
            access_token,
            json={"quantity": quantity},
        )
        return {"listing_id": listing_id, "quantity": quantity}

    async def get_reviews(self, access_token, listing_id) -> list:
        """Get reviews for a listing."""
        if not self._is_configured:
            return []

        data = await self._request(
            "GET",
            f"listings/{listing_id}/reviews",
            access_token,
        )
        return data.get("results", [])

    async def publish_listing(self, access_token, listing_id) -> bool:
        """Set listing state to active."""
        if not self._is_configured:
            print(f"[Etsy] MOCK publish_listing: {listing_id}")
            return True

        await self._request(
            "PUT",
            f"listings/{listing_id}",
            access_token,
            json={"state": "active"},
        )
        return True

    async def sync_listing_data(self, access_token, listing_id) -> dict:
        """Fetch views/favorites/sales analytics for a listing."""
        if not self._is_configured:
            return {
                "listing_id": listing_id,
                "views": 0,
                "favorites": 0,
                "num_favorers": 0,
                "state": "active",
            }

        data = await self._request(
            "GET",
            f"listings/{listing_id}",
            access_token,
        )
        return {
            "listing_id": listing_id,
            "views": data.get("num_views", 0),
            "favorites": data.get("num_favorers", 0),
            "state": data.get("state", "active"),
        }


# Lazy import for rate limiter
async def asyncio_sleep(seconds):
    """Non-blocking sleep for rate limiter."""
    import asyncio as _asyncio
    await _asyncio.sleep(seconds)


# =============================================================================
# EtsyService — High-level business logic
# =============================================================================


class EtsyService:
    """Etsy integration business service.

    Orchestrates OAuth connection, listing CRUD, order sync, and dashboard.
    """

    def __init__(self, db):
        self.db = db
        self.gateway = EtsyGateway()

    # ---------------------------------------------------------------
    # Shop connection
    # ---------------------------------------------------------------

    async def connect_shop(self, user_id, authorization_code) -> dict:
        """Exchange OAuth authorization code for access_token and store encrypted."""
        if not self.gateway._is_configured:
            return {
                "shop_id": "etsy-mock-shop",
                "shop_name": "Mock Etsy Shop",
                "status": "mock_connected",
                "message": "Etsy API not configured; using mock mode",
            }

        # Exchange code for tokens
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                f"{EtsyGateway.AUTH_URL}/token",
                data={
                    "grant_type": "authorization_code",
                    "code": authorization_code,
                    "client_id": self.gateway.client_id,
                    "client_secret": self.gateway.client_secret,
                    "redirect_uri": os.environ.get("ETSY_CALLBACK_URL", ""),
                },
            )
            resp.raise_for_status()
            token_data = resp.json()

        access_token = token_data.get("access_token", "")
        refresh_token = token_data.get("refresh_token")
        expires_in = token_data.get("expires_in", 14400)

        # Encrypt and store
        encrypted_access = encrypt(access_token)
        encrypted_refresh = encrypt(refresh_token) if refresh_token else None

        token_expires = datetime.utcnow() + timedelta(seconds=int(expires_in))

        # Upsert shop record
        shop = (
            self.db.query(EtsyShop)
            .filter(EtsyShop.user_id == user_id)
            .first()
        )

        if not shop:
            shop = EtsyShop(
                id=os.urandom(16).hex()[:32],
                user_id=user_id,
                shop_name=token_data.get("shop_name", "My Etsy Shop"),
                shop_id=token_data.get("shop_id", "etsy-shop-mock"),
                access_token=encrypted_access,
                refresh_token=encrypted_refresh,
                token_expires_at=token_expires,
                is_active=True,
            )
            self.db.add(shop)
        else:
            shop.access_token = encrypted_access
            shop.refresh_token = encrypted_refresh
            shop.token_expires_at = token_expires
            shop.shop_name = token_data.get("shop_name", shop.shop_name)
            shop.shop_id = token_data.get("shop_id", shop.shop_id)
            shop.is_active = True
            shop.updated_at = datetime.utcnow()

        self.db.commit()
        self.db.refresh(shop)

        return {
            "id": shop.id,
            "shop_name": shop.shop_name,
            "shop_id": shop.shop_id,
            "is_active": shop.is_active,
            "token_expires_at": shop.token_expires_at.isoformat() if shop.token_expires_at else None,
        }

    async def refresh_token(self, shop_id: str) -> bool:
        """Refresh an expired Etsy access token."""
        shop = (
            self.db.query(EtsyShop)
            .filter(EtsyShop.shop_id == shop_id)
            .first()
        )
        if not shop or not shop.refresh_token:
            return False

        decrypted_refresh = decrypt(shop.refresh_token)

        if not self.gateway._is_configured:
            return False

        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                f"{EtsyGateway.AUTH_URL}/token",
                data={
                    "grant_type": "refresh_token",
                    "refresh_token": decrypted_refresh,
                    "client_id": self.gateway.client_id,
                    "client_secret": self.gateway.client_secret,
                },
            )
            resp.raise_for_status()
            token_data = resp.json()

        shop.access_token = encrypt(token_data.get("access_token", ""))
        shop.refresh_token = encrypt(token_data.get("refresh_token", ""))
        shop.token_expires_at = datetime.utcnow() + timedelta(
            seconds=int(token_data.get("expires_in", 14400))
        )
        shop.updated_at = datetime.utcnow()
        self.db.commit()
        return True

    async def list_shops(self, user_id: str) -> list:
        """List all Etsy shops for a user."""
        shops = (
            self.db.query(EtsyShop)
            .filter(EtsyShop.user_id == user_id)
            .order_by(EtsyShop.created_at.desc())
            .all()
        )
        return [
            {
                "id": s.id,
                "shop_name": s.shop_name,
                "shop_id": s.shop_id,
                "is_active": s.is_active,
                "connected_at": s.created_at.isoformat() if s.created_at else None,
            }
            for s in shops
        ]

    # ---------------------------------------------------------------
    # Listings
    # ---------------------------------------------------------------

    async def sync_product_to_etsy(
        self,
        user_id: str,
        product_id: str,
        listing_data: dict,
    ) -> dict:
        """Create a local EtsyListing and push to Etsy API."""
        shop = (
            self.db.query(EtsyShop)
            .filter(
                EtsyShop.user_id == user_id,
                EtsyShop.is_active == True,
            )
            .first()
        )
        if not shop:
            return {"status": "error", "message": "No active Etsy shop connected"}

        access_token = decrypt(shop.access_token)
        title = listing_data.get("title", "Untitled")

        # Call Etsy API
        listing_id = await self.gateway.create_listing(
            access_token,
            shop.shop_id,
            listing_data,
            listing_data.get("images", []),
        )

        # Store locally
        now = datetime.utcnow()
        etl = EtsyListing(
            id=os.urandom(16).hex()[:32],
            user_id=user_id,
            product_id=product_id,
            etsy_listing_id=listing_id,
            etsy_shop_id=shop.shop_id,
            title=title,
            description=listing_data.get("description"),
            price=listing_data.get("price", 0),
            currency=listing_data.get("currency", "USD"),
            quantity=listing_data.get("quantity", 1),
            tags=listing_data.get("tags"),
            materials=listing_data.get("materials"),
            shipping_profile_id=listing_data.get("shipping_profile_id"),
            processing_time_days=listing_data.get("processing_time_days"),
            ships_from_country=listing_data.get("ships_from_country", "CN"),
            shipping_cost=listing_data.get("shipping_cost"),
            free_shipping=listing_data.get("free_shipping", False),
            variations=listing_data.get("variations"),
            status="draft",
            etsy_status="active",
            created_at=now,
            updated_at=now,
        )
        self.db.add(etl)
        self.db.commit()
        self.db.refresh(etl)

        return {
            "id": etl.id,
            "etsy_listing_id": etl.etsy_listing_id,
            "title": etl.title,
            "price": etl.price,
            "status": etl.status,
            "etsy_status": etl.etsy_status,
        }

    async def update_etsy_listing(self, user_id: str, listing_id: str, updates: dict) -> dict:
        """Update a local EtsyListing and sync to Etsy API."""
        etl = (
            self.db.query(EtsyListing)
            .filter(
                EtsyListing.id == listing_id,
                EtsyListing.user_id == user_id,
            )
            .first()
        )
        if not etl:
            return {"status": "error", "message": "Listing not found"}

        updatable = {
            "title", "description", "price", "quantity", "tags",
            "materials", "shipping_cost", "free_shipping", "variations",
            "status",
        }
        for key in updatable:
            if key in updates and updates[key] is not None:
                setattr(etl, key, updates[key])

        etl.updated_at = datetime.utcnow()

        # Also update on Etsy
        shop = (
            self.db.query(EtsyShop)
            .filter(
                EtsyShop.shop_id == etl.etsy_shop_id,
                EtsyShop.is_active == True,
            )
            .first()
        )
        if shop:
            access_token = decrypt(shop.access_token)
            await self.gateway.update_listing(
                access_token,
                etl.etsy_listing_id,
                {k: v for k, v in updates.items() if k in updatable},
            )

        self.db.commit()
        self.db.refresh(etl)
        return {"id": etl.id, "title": etl.title, "status": etl.status}

    async def delete_etsy_listing(self, user_id: str, listing_id: str) -> bool:
        """Soft-delete a listing locally."""
        etl = (
            self.db.query(EtsyListing)
            .filter(
                EtsyListing.id == listing_id,
                EtsyListing.user_id == user_id,
            )
            .first()
        )
        if not etl:
            return False
        etl.status = "inactive"
        etl.updated_at = datetime.utcnow()
        self.db.commit()
        return True

    async def publish_etsy_listing(self, user_id: str, listing_id: str) -> bool:
        """Publish (activate) a listing on Etsy."""
        etl = (
            self.db.query(EtsyListing)
            .filter(
                EtsyListing.id == listing_id,
                EtsyListing.user_id == user_id,
            )
            .first()
        )
        if not etl:
            return False

        shop = (
            self.db.query(EtsyShop)
            .filter(
                EtsyShop.shop_id == etl.etsy_shop_id,
                EtsyShop.is_active == True,
            )
            .first()
        )
        if not shop:
            return False

        access_token = decrypt(shop.access_token)
        success = await self.gateway.publish_listing(access_token, etl.etsy_listing_id)

        if success:
            etl.status = "active"
            etl.etsy_status = "active"
            etl.updated_at = datetime.utcnow()
            self.db.commit()

        return success

    async def sync_etsy_data(self, user_id: str, listing_id: str) -> dict:
        """Pull fresh analytics data from Etsy for a listing."""
        etl = (
            self.db.query(EtsyListing)
            .filter(
                EtsyListing.id == listing_id,
                EtsyListing.user_id == user_id,
            )
            .first()
        )
        if not etl:
            return {"status": "error", "message": "Listing not found"}

        shop = (
            self.db.query(EtsyShop)
            .filter(
                EtsyShop.shop_id == etl.etsy_shop_id,
                EtsyShop.is_active == True,
            )
            .first()
        )
        if not shop:
            return {"status": "error", "message": "No shop connected"}

        access_token = decrypt(shop.access_token)
        data = await self.gateway.sync_listing_data(
            access_token,
            etl.etsy_listing_id,
        )

        etl.views_count = data.get("views", etl.views_count)
        etl.favorites_count = data.get("favorites", etl.favorites_count)
        etl.updated_at = datetime.utcnow()
        self.db.commit()

        return data

    async def get_listings(self, user_id: str, status: Optional[str] = None) -> list:
        """List all Etsy listings for a user."""
        query = self.db.query(EtsyListing).filter(
            EtsyListing.user_id == user_id,
            EtsyListing.status != "inactive",
        )
        if status:
            query = query.filter(EtsyListing.status == status)

        listings = query.order_by(EtsyListing.updated_at.desc()).all()
        return [
            {
                "id": l.id,
                "title": l.title,
                "price": l.price,
                "currency": l.currency,
                "quantity": l.quantity,
                "status": l.status,
                "etsy_status": l.etsy_status,
                "etsy_listing_id": l.etsy_listing_id,
                "etsy_shop_id": l.etsy_shop_id,
                "views_count": l.views_count,
                "favorites_count": l.favorites_count,
                "sales_count": l.sales_count,
                "revenue": l.revenue,
                "tags": l.tags,
                "materials": l.materials,
                "free_shipping": l.free_shipping,
                "created_at": l.created_at.isoformat() if l.created_at else None,
                "updated_at": l.updated_at.isoformat() if l.updated_at else None,
            }
            for l in listings
        ]

    # ---------------------------------------------------------------
    # Orders
    # ---------------------------------------------------------------

    async def sync_orders(self, user_id: str, shop_id: Optional[str] = None) -> list:
        """Fetch Etsy orders and upsert into local database."""
        shop_query = self.db.query(EtsyShop).filter(
            EtsyShop.user_id == user_id,
            EtsyShop.is_active == True,
        )
        if shop_id:
            shop_query = shop_query.filter(EtsyShop.shop_id == shop_id)
        shops = shop_query.all()

        if not shops:
            return []

        all_orders = []
        for shop in shops:
            access_token = decrypt(shop.access_token)
            etsy_orders = await self.gateway.get_orders(access_token, shop.shop_id)

            for order_data in etsy_orders:
                etsy_order_id = str(order_data.get("order_id", ""))
                if not etsy_order_id:
                    continue

                existing = (
                    self.db.query(EtsyOrder)
                    .filter(EtsyOrder.etsy_order_id == etsy_order_id)
                    .first()
                )
                if existing:
                    # Update existing
                    if "state" in order_data:
                        existing.status = order_data["state"]
                    existing.updated_at = datetime.utcnow()
                else:
                    now = datetime.utcnow()
                    order_date = order_data.get("created_utc", None)
                    if order_date:
                        try:
                            order_date = datetime.fromisoformat(
                                order_date.replace("Z", "+00:00")
                            ).replace(tzinfo=None)
                        except Exception:
                            order_date = now

                    eo = EtsyOrder(
                        id=os.urandom(16).hex()[:32],
                        user_id=user_id,
                        listing_id=None,  # Will link after matching listing
                        etsy_order_id=etsy_order_id,
                        buyer_name=order_data.get("shipping_details", [{}])[0].get("name", ""),
                        buyer_country=order_data.get("shipping_details", [{}])[0].get("country", ""),
                        order_total=float(order_data.get("transactions", [{}])[0].get("amount", "0.00")),
                        shipping_cost=(
                            float(order_data.get("shipping_cost", {}).get("amount", "0")) / 100
                            if order_data.get("shipping_cost")
                            else None
                        ),
                        tax=(
                            float(order_data.get("tax", {}).get("amount", "0")) / 100
                            if order_data.get("tax")
                            else None
                        ),
                        order_date=order_date,
                        status=order_data.get("state", "paid"),
                        created_at=now,
                        updated_at=now,
                    )
                    self.db.add(eo)

                all_orders.append({
                    "etsy_order_id": etsy_order_id,
                    "status": existing.status if existing else "new",
                    "order_total": order_data.get("transactions", [{}])[0].get("amount", "0.00"),
                })

        self.db.commit()
        return all_orders

    async def get_orders(
        self,
        user_id: str,
        status: Optional[str] = None,
    ) -> list:
        """List Etsy orders for a user."""
        query = self.db.query(EtsyOrder).filter(
            EtsyOrder.user_id == user_id,
        )
        if status:
            query = query.filter(EtsyOrder.status == status)

        orders = query.order_by(EtsyOrder.order_date.desc()).all()
        return [
            {
                "id": o.id,
                "etsy_order_id": o.etsy_order_id,
                "buyer_name": o.buyer_name,
                "buyer_country": o.buyer_country,
                "order_total": o.order_total,
                "shipping_cost": o.shipping_cost,
                "tax": o.tax,
                "order_date": o.order_date.isoformat() if o.order_date else None,
                "shipping_deadline": o.shipping_deadline.isoformat() if o.shipping_deadline else None,
                "status": o.status,
                "tracking_number": o.tracking_number,
                "created_at": o.created_at.isoformat() if o.created_at else None,
            }
            for o in orders
        ]

    # ---------------------------------------------------------------
    # Dashboard
    # ---------------------------------------------------------------

    async def get_dashboard(self, user_id: str) -> dict:
        """Aggregate Etsy dashboard: sales, views, favorites, revenue trends."""
        listings = (
            self.db.query(EtsyListing)
            .filter(
                EtsyListing.user_id == user_id,
                EtsyListing.status != "inactive",
            )
            .all()
        )

        orders = (
            self.db.query(EtsyOrder)
            .filter(
                EtsyOrder.user_id == user_id,
                EtsyOrder.status.notin_(["cancelled"]),
            )
            .all()
        )

        # Totals
        total_sales = len(orders)
        total_views = sum(l.views_count for l in listings)
        total_favorites = sum(l.favorites_count for l in listings)
        total_revenue = round(
            sum(float(o.order_total) for o in orders), 2
        ) if orders else 0.0

        active_listings = sum(
            1 for l in listings if l.status == "active"
        )

        # Orders by status
        orders_by_status = {}
        for o in orders:
            orders_by_status[o.status] = orders_by_status.get(o.status, 0) + 1

        # Revenue by month (last 6 months)
        now = datetime.utcnow()
        revenue_by_month = []
        for i in range(6):
            m_start = now.replace(day=1) - timedelta(days=i * 31)
            m_end = m_start + timedelta(days=32)
            m_end = m_end.replace(day=1) - timedelta(days=1)

            month_rev = 0.0
            for o in orders:
                if o.order_date and m_start.date() <= o.order_date.date() <= m_end.date():
                    month_rev += float(o.order_total)

            revenue_by_month.append({
                "month": m_start.strftime("%Y-%m"),
                "revenue": round(month_rev, 2),
            })

        # Top listings by revenue
        top_listings = []
        listing_map = {l.id: l for l in listings}
        for o in orders:
            l = listing_map.get(o.listing_id)
            if l:
                l.revenue += float(o.order_total)

        sorted_listings = sorted(
            listings,
            key=lambda x: x.revenue,
            reverse=True,
        )[:10]

        for l in sorted_listings:
            top_listings.append({
                "id": l.id,
                "title": l.title,
                "price": l.price,
                "sales_count": l.sales_count,
                "revenue": round(l.revenue, 2),
            })

        return {
            "total_sales": total_sales,
            "total_views": total_views,
            "total_favorites": total_favorites,
            "total_revenue": total_revenue,
            "active_listings": active_listings,
            "revenue_by_month": revenue_by_month,
            "orders_by_status": orders_by_status,
            "top_listings": top_listings,
        }
