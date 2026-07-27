"""Craftsman Router HTTP-level integration tests — covers CRUD for products, factories, RFQs, materials, transactions, batches."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

import pytest


_BASE = "/api/craftsman"


class TestCraftProducts:
    """CRUD for /craftsman/products"""

    def test_list_empty(self, client):
        resp = client.get(f"{_BASE}/products")
        assert resp.status_code == 200
        assert resp.json()["data"] == []

    def test_create_product(self, client):
        resp = client.post(f"{_BASE}/products", json={
            "material": "ceramic",
            "dimensions": "10x10cm",
            "craft_type": "pottery",
            "moq": 5,
            "unit_price": 50.0,
            "production_time_days": 7,
        })
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert "id" in data

    def test_get_product(self, client):
        # Create first to get an ID
        create_resp = client.post(f"{_BASE}/products", json={
            "material": "wood", "craft_type": "carving",
        })
        product_id = create_resp.json()["data"]["id"]
        resp = client.get(f"{_BASE}/products/{product_id}")
        assert resp.status_code == 200
        assert resp.json()["data"]["material"] == "wood"

    def test_update_product(self, client):
        create_resp = client.post(f"{_BASE}/products", json={
            "material": "clay", "craft_type": "sculpture",
        })
        product_id = create_resp.json()["data"]["id"]
        resp = client.patch(f"{_BASE}/products/{product_id}", json={"material": "porcelain"})
        assert resp.status_code == 200
        assert resp.json()["data"]["material"] == "porcelain"

    def test_delete_product(self, client):
        create_resp = client.post(f"{_BASE}/products", json={
            "material": "glass", "craft_type": "blown",
        })
        product_id = create_resp.json()["data"]["id"]
        resp = client.delete(f"{_BASE}/products/{product_id}")
        assert resp.status_code == 200
        # Verify deleted
        resp = client.get(f"{_BASE}/products/{product_id}")
        assert resp.status_code == 404


class TestFactories:
    """CRUD for /craftsman/factories"""

    def test_list_empty(self, client):
        resp = client.get(f"{_BASE}/factories")
        assert resp.status_code == 200
        assert resp.json()["data"] == []

    def test_create_factory(self, client):
        resp = client.post(f"{_BASE}/factories", json={
            "name": "Test Factory",
            "location": "Beijing",
            "rating": 4.5,
            "capabilities": ["printing", "embossing"],
        })
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert "id" in data

    def test_update_factory(self, client):
        create_resp = client.post(f"{_BASE}/factories", json={"name": "Old Name"})
        factory_id = create_resp.json()["data"]["id"]
        resp = client.patch(f"{_BASE}/factories/{factory_id}", json={"name": "New Name"})
        assert resp.status_code == 200
        assert resp.json()["data"]["name"] == "New Name"

    def test_delete_factory(self, client):
        create_resp = client.post(f"{_BASE}/factories", json={"name": "To Delete"})
        factory_id = create_resp.json()["data"]["id"]
        resp = client.delete(f"{_BASE}/factories/{factory_id}")
        assert resp.status_code == 200


class TestRFQs:
    """CRUD for /craftsman/rfqs"""

    def test_list_empty(self, client):
        resp = client.get(f"{_BASE}/rfqs")
        assert resp.status_code == 200

    def test_create_rfq(self, client):
        resp = client.post(f"{_BASE}/rfqs", json={
            "title": "Need 100 ceramic mugs",
            "quantity_needed": 100,
            "target_price": 15.0,
        })
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert "id" in data

    def test_update_rfq_status(self, client):
        create_resp = client.post(f"{_BASE}/rfqs", json={"title": "Test RFQ"})
        rfq_id = create_resp.json()["data"]["id"]
        resp = client.patch(f"{_BASE}/rfqs/{rfq_id}", json={"status": "closed"})
        assert resp.status_code == 200
        assert resp.json()["data"]["status"] == "closed"

    def test_delete_rfq(self, client):
        create_resp = client.post(f"{_BASE}/rfqs", json={"title": "Delete Me"})
        rfq_id = create_resp.json()["data"]["id"]
        resp = client.delete(f"{_BASE}/rfqs/{rfq_id}")
        assert resp.status_code == 200


class TestPhysicalProducts:
    """CRUD for /craftsman/physical-products"""

    def test_list_empty(self, client):
        resp = client.get(f"{_BASE}/physical-products")
        assert resp.status_code == 200

    def test_create_physical_product(self, client):
        resp = client.post(f"{_BASE}/physical-products", json={
            "title": "Handmade Ceramic Mug",
            "category": "kitchenware",
            "price": 29.9,
            "stock_quantity": 100,
        })
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert "id" in data

    def test_update_physical_product(self, client):
        create_resp = client.post(f"{_BASE}/physical-products", json={
            "title": "Old Title", "price": 10.0,
        })
        pid = create_resp.json()["data"]["id"]
        resp = client.patch(f"{_BASE}/physical-products/{pid}", json={"title": "New Title", "price": 20.0})
        assert resp.status_code == 200

    def test_delete_physical_product(self, client):
        create_resp = client.post(f"{_BASE}/physical-products", json={
            "title": "To Delete", "price": 5.0,
        })
        pid = create_resp.json()["data"]["id"]
        resp = client.delete(f"{_BASE}/physical-products/{pid}")
        assert resp.status_code == 200


class TestMaterialInventory:
    """CRUD for /craftsman/materials"""

    def test_list_empty(self, client):
        resp = client.get(f"{_BASE}/materials")
        assert resp.status_code == 200

    def test_create_material(self, client):
        resp = client.post(f"{_BASE}/materials", json={
            "material_name": "Clay",
            "material_category": "ceramic",
            "unit": "kg",
            "quantity_on_hand": 50.0,
        })
        assert resp.status_code == 200

    def test_update_material(self, client):
        create_resp = client.post(f"{_BASE}/materials", json={
            "material_name": "Wood", "unit": "piece", "quantity_on_hand": 100,
        })
        mid = create_resp.json()["data"]["id"]
        resp = client.patch(f"{_BASE}/materials/{mid}", json={"quantity_on_hand": 80.0})
        assert resp.status_code == 200

    def test_delete_material(self, client):
        create_resp = client.post(f"{_BASE}/materials", json={
            "material_name": "Delete Me", "unit": "sheet", "quantity_on_hand": 10,
        })
        mid = create_resp.json()["data"]["id"]
        resp = client.delete(f"{_BASE}/materials/{mid}")
        assert resp.status_code == 200


class TestMaterialTransactions:
    """POST /craftsman/material-transactions and GET /craftsman/material-transactions"""

    def test_create_purchase_transaction(self, client):
        # First create a material
        mat_resp = client.post(f"{_BASE}/materials", json={
            "material_name": "Paint", "unit": "L", "quantity_on_hand": 10,
        })
        mat_id = mat_resp.json()["data"]["id"]
        resp = client.post(f"{_BASE}/material-transactions", json={
            "material_id": mat_id,
            "transaction_type": "purchase",
            "quantity": 5.0,
        })
        assert resp.status_code == 200

    def test_list_transactions(self, client):
        resp = client.get(f"{_BASE}/material-transactions")
        assert resp.status_code == 200
        assert isinstance(resp.json()["data"], list)


class TestProductionBatches:
    """CRUD for /craftsman/production-batches"""

    def test_list_empty(self, client):
        resp = client.get(f"{_BASE}/production-batches")
        assert resp.status_code == 200

    def test_create_batch(self, client):
        resp = client.post(f"{_BASE}/production-batches", json={
            "title": "Batch #1 - Ceramic Mugs",
            "planned_quantity": 500,
        })
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert "id" in data

    def test_update_batch_status(self, client):
        create_resp = client.post(f"{_BASE}/production-batches", json={
            "title": "Test Batch", "planned_quantity": 100,
        })
        bid = create_resp.json()["data"]["id"]
        resp = client.patch(f"{_BASE}/production-batches/{bid}", json={"status": "in_production"})
        assert resp.status_code == 200
        assert resp.json()["data"]["status"] == "in_production"

    def test_delete_batch(self, client):
        create_resp = client.post(f"{_BASE}/production-batches", json={
            "title": "Delete Me", "planned_quantity": 10,
        })
        bid = create_resp.json()["data"]["id"]
        resp = client.delete(f"{_BASE}/production-batches/{bid}")
        assert resp.status_code == 200
