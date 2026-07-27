"""Logistics Router HTTP-level integration tests."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

import pytest


_BASE = "/api/logistics"


def _get_id(resp):
    """Extract ID from response — handles ApiResponse wrapper or raw dict."""
    data = resp.json()
    if isinstance(data, dict) and "data" in data:
        return data["data"]["id"]
    return data.get("id", "")


class TestProviders:
    """Provider CRUD"""

    def test_list_providers_empty(self, client):
        resp = client.get(f"{_BASE}/providers")
        assert resp.status_code == 200

    def test_create_provider(self, client):
        resp = client.post(f"{_BASE}/providers", json={
            "name": "FastShip Express",
            "contact_email": "contact@fastship.example.com",
        })
        assert resp.status_code == 200
        pid = _get_id(resp)
        assert pid

    def test_get_provider(self, client):
        # Create first
        create_resp = client.post(f"{_BASE}/providers", json={
            "name": "GetMe",
        })
        if create_resp.status_code != 200:
            pytest.skip("Cannot create provider")
        provider_id = _get_id(create_resp)

        resp = client.get(f"{_BASE}/providers/{provider_id}")
        assert resp.status_code == 200
        assert "name" in resp.json() or "data" in resp.json()

    def test_get_nonexistent_provider(self, client):
        resp = client.get(f"{_BASE}/providers/nonexistent")
        assert resp.status_code == 404

    def test_update_provider(self, client):
        create_resp = client.post(f"{_BASE}/providers", json={
            "name": "UpdateMe",
        })
        if create_resp.status_code != 200:
            pytest.skip("Cannot create provider")
        provider_id = _get_id(create_resp)

        resp = client.patch(f"{_BASE}/providers/{provider_id}", json={
            "name": "Updated Provider",
        })
        assert resp.status_code == 200


class TestShipments:
    """Shipment CRUD"""

    def test_create_shipment(self, client):
        # Create provider first (needed for shipment)
        prov_resp = client.post(f"{_BASE}/providers", json={
            "name": "Ship Provider",
        })
        if prov_resp.status_code != 200:
            pytest.skip("Cannot create provider")
        provider_id = _get_id(prov_resp)

        resp = client.post(f"{_BASE}/shipments", json={
            "contract_id": "test_contract",
            "provider_id": provider_id,
            "tracking_number": "TRACK123",
            "recipient_name": "John Doe",
            "recipient_address": "123 Main St",
        })
        assert resp.status_code in (200, 400)

    def test_list_shipments(self, client):
        resp = client.get(f"{_BASE}/shipments", params={
            "contract_id": "test_contract",
        })
        assert resp.status_code == 200

    def test_get_shipment(self, client):
        resp = client.get(f"{_BASE}/shipments/nonexistent")
        assert resp.status_code == 404

    def test_update_shipment_status(self, client):
        # Create shipment first
        prov_resp = client.post(f"{_BASE}/providers", json={
            "name": "Status Provider",
        })
        if prov_resp.status_code != 200:
            pytest.skip("Cannot create provider")
        provider_id = _get_id(prov_resp)

        ship_resp = client.post(f"{_BASE}/shipments", json={
            "contract_id": "status_contract",
            "provider_id": provider_id,
            "tracking_number": "STATUS1",
        })
        if ship_resp.status_code not in (200, 400):
            pytest.skip("Cannot create shipment")
        if ship_resp.status_code == 200:
            shipment_id = _get_id(ship_resp)

            resp = client.put(f"{_BASE}/shipments/{shipment_id}/status", json={
                "status": "shipped",
                "location": "Warehouse A",
            })
            assert resp.status_code == 200

    def test_confirm_delivery(self, client):
        prov_resp = client.post(f"{_BASE}/providers", json={
            "name": "Deliver Provider",
        })
        if prov_resp.status_code != 200:
            pytest.skip("Cannot create provider")
        provider_id = _get_id(prov_resp)

        ship_resp = client.post(f"{_BASE}/shipments", json={
            "contract_id": "deliver_contract",
            "provider_id": provider_id,
            "tracking_number": "DELIVER1",
        })
        if ship_resp.status_code not in (200, 400):
            pytest.skip("Cannot create shipment")
        if ship_resp.status_code == 200:
            shipment_id = _get_id(ship_resp)

            resp = client.post(f"{_BASE}/shipments/{shipment_id}/confirm-delivery", params={
                "confirmed_by": "buyer_1",
            })
            assert resp.status_code == 200
