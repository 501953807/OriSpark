import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

import pytest
from datetime import datetime, timedelta, timezone

from app.models.publish import RevenueRecord


@pytest.fixture(autouse=True)
def _cleanup_revenue(db_session):
    yield
    try:
        from sqlalchemy import text
        db_session.execute(text("DELETE FROM revenue_records"))
        db_session.flush()
        db_session.rollback()
    except Exception:
        db_session.rollback()


def test_export_csv(client, db_session):
    now = datetime.now(timezone.utc)
    for i in range(3):
        rec = RevenueRecord(
            user_id="current_user",
            income_category="subscription",
            amount=100.0 * (i + 1),
            platform="patreon",
            source_description=f"Monthly subscription {i+1}",
            created_at=now - timedelta(days=i * 30),
        )
        db_session.add(rec)
    db_session.flush()

    resp = client.get("/api/revenue/records/export?format=csv")
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "text/csv; charset=utf-8"
    assert "attachment" in resp.headers["content-disposition"]
    lines = resp.text.strip().split("\n")
    assert len(lines) >= 4  # header + 3 records
    assert "date" in lines[0]
    assert "category" in lines[0]


def test_export_json(client, db_session):
    now = datetime.now(timezone.utc)
    rec = RevenueRecord(
        user_id="current_user",
        income_category="ecommerce",
        amount=500.0,
        platform="shopify",
        source_description="Product sale",
        created_at=now,
    )
    db_session.add(rec)
    db_session.flush()

    resp = client.get("/api/revenue/records/export?format=json")
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert len(data["data"]) == 1
    assert data["data"][0]["category"] == "ecommerce"
    assert data["data"][0]["amount"] == 500.0


def test_export_csv_with_date_filter(client, db_session):
    now = datetime.now(timezone.utc)
    old_date = (now - timedelta(days=60)).strftime("%Y-%m-%dT%H:%M:%S%z")
    new_date = now.strftime("%Y-%m-%dT%H:%M:%S%z")
    for i in range(6):
        rec = RevenueRecord(
            user_id="current_user",
            income_category="ad_revenue",
            amount=50.0,
            created_at=now - timedelta(days=i * 10),
        )
        db_session.add(rec)
    db_session.flush()

    resp = client.get(f"/api/revenue/records/export?format=csv&start_date={old_date}&end_date={new_date}")
    assert resp.status_code == 200
    lines = resp.text.strip().split("\n")
    assert len(lines) >= 6  # header + 6 records


def test_export_csv_empty(client):
    resp = client.get("/api/revenue/records/export?format=csv")
    assert resp.status_code == 200
    lines = resp.text.strip().split("\n")
    assert len(lines) == 1  # only header
    assert "date" in lines[0]


def test_export_json_empty(client):
    resp = client.get("/api/revenue/records/export?format=json")
    assert resp.status_code == 200
    data = resp.json()
    assert data["data"] == []
    assert data["success"] is True


def test_export_invalid_format(client):
    resp = client.get("/api/revenue/records/export?format=xml")
    assert resp.status_code == 422
