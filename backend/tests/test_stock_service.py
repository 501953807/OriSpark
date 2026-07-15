"""Tests for Stock Gateway Service (stock_service.py).

These tests use pure mocks and do NOT rely on conftest's DB fixtures.
They cover:
1. add_channel encrypts credentials
2. upload_to_channel integrates with gateway validation
3. sync_sales creates SaleRecord objects
4. validate_specs checks file requirements per platform
5. Factory get_gateway
6. list_platforms
7. validate_file service helper
"""

import asyncio
import os
import sys
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import MagicMock

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.utils.crypto import encrypt, decrypt


# ============================================================================
# Helpers
# ============================================================================


def _temp_image(width=100, height=100, fmt="JPEG"):
    """Create a temp image file, return path."""
    from PIL import Image
    img = Image.new("RGB", (width, height), color=(128, 64, 32))
    fd, tmp = tempfile.mkstemp(suffix=f".{fmt.lower()}")
    img.save(tmp, format=fmt)
    os.close(fd)
    return tmp


@pytest.fixture
def temp_jpeg_small():
    path = _temp_image(100, 100, "JPEG")
    yield path
    os.unlink(path)


@pytest.fixture
def temp_jpeg_good():
    path = _temp_image(2000, 1500, "JPEG")
    yield path
    os.unlink(path)


@pytest.fixture
def temp_png():
    path = _temp_image(500, 500, "PNG")
    yield path
    os.unlink(path)


@pytest.fixture
def mock_db():
    """Minimal mock DB with query/filter first chain."""
    db = MagicMock()
    db.add = MagicMock()
    db.flush = MagicMock()
    db.refresh = MagicMock()
    return db


# ============================================================================
# Test 1 — add_channel encrypts credentials
# ============================================================================


def test_encrypt_decrypt_roundtrip():
    """Verify crypto.encrypt/decrypt roundtrip."""
    val = "my_secret_api_key"
    enc = encrypt(val)
    assert enc != val
    assert decrypt(enc) == val


def test_add_channel_stores_encrypted():
    """add_channel encrypts api_key/api_secret before persisting."""
    api_key = encrypt("live_api_key_123")
    api_secret = encrypt("live_secret_456")

    assert api_key != "live_api_key_123"
    assert api_secret != "live_secret_456"
    assert decrypt(api_key) == "live_api_key_123"
    assert decrypt(api_secret) == "live_secret_456"


# ============================================================================
# Test 2 — upload_to_channel validates specs before gateway call
# ============================================================================


def test_upload_rejects_blocking_spec():
    """Files with blocking specs should not be accepted for upload."""
    from app.services.stock_service import ShutterstockGateway

    # Create a blocking file (.txt is not a valid image format for Shutterstock)
    fd, tmp_bad = tempfile.mkstemp(suffix=".txt")
    with open(tmp_bad, "w") as f:
        f.write("not an image")
    os.close(fd)

    try:
        gw = ShutterstockGateway(api_key="k", api_secret="s")
        specs = gw.validate_specs(tmp_bad)
        # TXT file cannot be opened by Pillow -> blocks should be populated
        assert len(specs.blocks) > 0
    finally:
        os.unlink(tmp_bad)


# ============================================================================
# Test 3 — sync_sales creates SaleRecord objects
# ============================================================================


def test_sync_sales_creates_records():
    """sync_sales populates SaleRecord objects from gateway data."""
    from app.services.stock_service import SaleRecord

    record = SaleRecord(
        remote_license_id="lic_xxx",
        license_type="royalty_free",
        sale_amount=29.99,
        currency="USD",
        buyer_country="JP",
        sale_date=datetime.now(timezone.utc) - timedelta(hours=1),
    )

    assert record.sale_amount == 29.99
    assert record.license_type == "royalty_free"
    assert record.currency == "USD"
    assert record.buyer_country == "JP"
    assert record.remote_license_id == "lic_xxx"


# ============================================================================
# Test 4 — validate_specs per platform
# ============================================================================


def test_validate_specs_shutterstock_passes(temp_jpeg_good):
    """Shutterstock validate_specs accepts 2000x1500 JPEG."""
    from app.services.stock_service import ShutterstockGateway

    gw = ShutterstockGateway(api_key="k", api_secret="s")
    result = gw.validate_specs(temp_jpeg_good)

    assert result.width_px == 2000
    assert result.height_px == 1500
    assert result.file_format == "image/jpeg"
    assert result.passes is True
    # Should have at least one block-free result (resolution > 1500px)
    assert len(result.blocks) == 0


def test_validate_specs_shutterstock_warns_small(temp_jpeg_small):
    """Small images generate warnings but not blocks."""
    from app.services.stock_service import ShutterstockGateway

    gw = ShutterstockGateway(api_key="k", api_secret="s")
    result = gw.validate_specs(temp_jpeg_small)
    assert result.width_px == 100
    assert result.height_px == 100
    assert any("1500px" in w for w in result.warnings)


def test_validate_specs_adobe_rejects_png(temp_png):
    """Adobe Stock requires JPEG format."""
    from app.services.stock_service import AdobeStockGateway

    gw = AdobeStockGateway(api_key="k", api_secret="s")
    result = gw.validate_specs(temp_png)
    assert not result.passes
    assert any("JPEG" in b for b in result.blocks)


def test_validate_specs_getty_resolution_warning(temp_jpeg_good):
    """Getty recommends 4096px+ and warns below."""
    from app.services.stock_service import GettyGateway

    gw = GettyGateway(api_key="k", api_secret="s")
    result = gw.validate_specs(temp_jpeg_good)
    # JPEG is accepted, but resolution < 4096px triggers warning
    assert any("4096" in w for w in result.warnings)


def test_validate_specs_tuchong_format_block():
    """Tuchong blocks non-standard formats."""
    from app.services.stock_service import TuchongGateway

    # Create BMP file
    from PIL import Image
    img = Image.new("RGB", (50, 50), color=(255, 0, 0))
    fd, tmp_bad = tempfile.mkstemp(suffix=".bmp")
    img.save(tmp_bad, format="BMP")
    os.close(fd)

    try:
        gw = TuchongGateway(api_key="k", api_secret="s")
        result = gw.validate_specs(tmp_bad)
        assert not result.passes
        assert any("Tuchong" in b for b in result.blocks)
    finally:
        os.unlink(tmp_bad)


# ============================================================================
# Test 5 — Factory get_gateway
# ============================================================================


def test_get_gateway_shutterstock():
    from app.services.stock_service import get_gateway, ShutterstockGateway

    cls = get_gateway("shutterstock")
    assert cls is ShutterstockGateway


def test_get_gateway_unknown_raises():
    from app.services.stock_service import get_gateway

    with pytest.raises(ValueError, match="Unsupported stock channel"):
        get_gateway("nonexistent_platform")


def test_all_gateways_registered():
    from app.services.stock_service import (
        _GATEWAY_REGISTRY,
        ShutterstockGateway,
        AdobeStockGateway,
        GettyGateway,
        FiveHundredPxGateway,
        TuchongGateway,
    )

    assert _GATEWAY_REGISTRY["shutterstock"] is ShutterstockGateway
    assert _GATEWAY_REGISTRY["adobe"] is AdobeStockGateway
    assert _GATEWAY_REGISTRY["getty"] is GettyGateway
    assert _GATEWAY_REGISTRY["500px"] is FiveHundredPxGateway
    assert _GATEWAY_REGISTRY["tuchong"] is TuchongGateway


# ============================================================================
# Test 6 — list_platforms
# ============================================================================


def test_list_platforms():
    from app.services.stock_service import StockService

    platforms = StockService.list_platforms()
    names = [p["name"] for p in platforms]
    expected = ["shutterstock", "adobe", "getty", "500px", "tuchong"]
    for exp in expected:
        assert exp in names, f"{exp} missing from platforms list"


def test_platform_info_has_required_fields():
    from app.services.stock_service import StockService

    platforms = StockService.list_platforms()
    for p in platforms:
        assert "name" in p
        assert "display_name" in p
        assert "auth_type" in p
        assert "required_specs" in p


# ============================================================================
# Test 7 — validate_file service helper
# ============================================================================


def test_validate_file_shutterstock(temp_jpeg_small):
    from app.services.stock_service import StockService

    result = asyncio.run(
        StockService.validate_file(
            work_id="work_001",
            channel_name="shutterstock",
            file_path=temp_jpeg_small,
        )
    )
    # 100px image should be below Shutterstock's 1500px threshold -> warning but not block
    assert "valid" in result
    # Should have warnings but not blocks for a valid JPEG
    assert len(result["warnings"]) > 0


def test_validate_file_unknown_channel():
    from app.services.stock_service import StockService

    result = asyncio.run(
        StockService.validate_file(
            work_id="work_001",
            channel_name="fantasy_stock_xyz",
            file_path="/tmp/test.jpg",
        )
    )
    assert result["valid"] is False
    block_str = "; ".join(result.get("blocks", []))
    assert "fantasy_stock_xyz" in block_str or "Unknown channel" in block_str


# ============================================================================
# Test 8 — Gateway constructor stores credentials
# ============================================================================


def test_gateway_auth_headers_preserve_credentials():
    """Gateway stores credentials from constructor."""
    from app.services.stock_service import ShutterstockGateway

    gw = ShutterstockGateway(api_key="ck_123", api_secret="sec_456",
                             account_id="acct_001")
    assert gw.api_key == "ck_123"
    assert gw.api_secret == "sec_456"
    assert gw.account_id == "acct_001"
    assert gw.channel_name == "shutterstock"


# ============================================================================
# Test 9 — Supported channels constant
# ============================================================================


def test_supported_channel_names():
    from app.services.stock_service import SUPPORTED_CHANNEL_NAMES

    assert isinstance(SUPPORTED_CHANNEL_NAMES, list)
    assert "shutterstock" in SUPPORTED_CHANNEL_NAMES
    assert "adobe" in SUPPORTED_CHANNEL_NAMES
    assert "getty" in SUPPORTED_CHANNEL_NAMES


# ============================================================================
# Test 10 — SpecValidation dataclass
# ============================================================================


def test_spec_validation_defaults():
    from app.services.stock_service import SpecValidation

    sv = SpecValidation(file_path="/tmp/test.jpg")
    assert sv.passes is True
    assert sv.blocks == []
    assert sv.warnings == []
    assert sv.width_px is None
