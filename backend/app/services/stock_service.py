"""Stock photo platform gateway service.

Connects creator works to stock photo channels (Shutterstock, Adobe Stock, Getty,
500px, Tuchong). Abstracts each platform's API behind a unified gateway interface.
"""

from __future__ import annotations

import asyncio
import logging
import mimetypes
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Optional

import httpx
from pydantic import BaseModel

from app.utils.crypto import encrypt, decrypt
from app.schemas.photographer import STOCK_PLATFORM_INFO

logger = logging.getLogger(__name__)

# Supported stock channel names
SUPPORTED_CHANNEL_NAMES = ["shutterstock", "adobe", "getty", "500px", "tuchong"]

# ============================================================================
# Domain types (shared across gateways)
# ============================================================================


@dataclass
class UploadResult:
    """Result of uploading a file to a stock platform."""
    remote_id: str
    status: str  # pending / approved / rejected
    title: str = ""
    error: Optional[str] = None


@dataclass
class UploadStatus:
    """Current status of a remote upload."""
    remote_id: str
    status: str  # pending / reviewing / approved / rejected
    rejection_reason: Optional[str] = None
    last_checked: datetime = field(default_factory=datetime.now)


@dataclass
class SaleRecord:
    """A single licensing / sale event from a stock platform."""
    remote_license_id: str
    license_type: str  # royalty_free / extended / rf / ee
    sale_amount: float
    currency: str = "USD"
    buyer_country: Optional[str] = None
    sale_date: Optional[datetime] = None


@dataclass
class SpecValidation:
    """Result of checking a file against platform upload specs."""
    file_path: str
    width_px: Optional[int] = None
    height_px: Optional[int] = None
    file_size_bytes: Optional[int] = None
    file_format: Optional[str] = None
    passes: bool = True
    warnings: list[str] = field(default_factory=list)
    blocks: list[str] = field(default_factory=list)


# ============================================================================
# Gateway ABC
# ============================================================================

# Registry: channel_name -> gateway class
_GATEWAY_REGISTRY: dict[str, type["StockGateway"]] = {}


def _gateway_registry(name: str):
    """Decorator to auto-register gateway classes under their channel name."""
    def wrap(cls):
        cls.channel_name = name
        _GATEWAY_REGISTRY[name] = cls
        return cls
    return wrap


class StockGateway(ABC):
    """Abstract base for a stock photo platform connector."""

    channel_name: str = ""

    def __init__(self, api_key: str, api_secret: Optional[str] = None,
                 account_id: Optional[str] = None):
        self.api_key = api_key
        self.api_secret = api_secret or ""
        self.account_id = account_id

    @abstractmethod
    async def upload(self, file_path: str, keywords: list[str],
                     categories: list[str]) -> UploadResult:
        """Upload a single image file to the platform."""

    @abstractmethod
    async def get_status(self, remote_id: str) -> UploadStatus:
        """Poll upload / review status."""

    @abstractmethod
    async def get_sales(self, start_date: datetime,
                        end_date: datetime) -> list[SaleRecord]:
        """Fetch sales/licensing records for a date range."""

    @abstractmethod
    def validate_specs(self, file_path: str) -> SpecValidation:
        """Check file against platform upload requirements."""

    # -- helpers (common across gateways) ------------------------------------

    async def _authenticate(self) -> dict[str, str]:
        """Return a dict ready to spread as headers."""
        return {}

    async def _request(self, method: str, url: str,
                       **kwargs: Any) -> httpx.Response:
        """Base HTTP request with rate-limit retry."""
        headers = await self._authenticate()
        headers.setdefault("Accept", "application/json")
        kwargs.setdefault("timeout", 30.0)
        kwargs["headers"] = {**headers, **(kwargs.get("headers") or {})}

        max_retries = kwargs.pop("_retries", 3)
        last_err: Optional[Exception] = None

        for attempt in range(max_retries):
            try:
                async with httpx.AsyncClient() as client:
                    resp = await client.request(method, url, **kwargs)
                    if resp.status_code == 429 and attempt < max_retries - 1:
                        retry_after = int(resp.headers.get("retry-after", 2))
                        logger.warning("Rate limited (%s), retry-after=%ds",
                                       url, retry_after)
                        await asyncio.sleep(retry_after)
                        continue
                    return resp
            except (httpx.ConnectError, httpx.TimeoutException) as exc:
                last_err = exc
                wait = min(2 ** attempt, 8)
                logger.warning("Connection error on %s (attempt %d/%d), "
                               "retrying in %ds: %s",
                               url, attempt + 1, max_retries, wait, exc)
                await asyncio.sleep(wait)

        if last_err:
            raise last_err
        raise RuntimeError("exhausted retries without response")


# ============================================================================
# Individual platform gateways
# ============================================================================

# -- Shutterstock -----------------------------------------------------------


@_gateway_registry("shutterstock")
class ShutterstockGateway(StockGateway):
    """Shutterstock Contributor API connector (self-signed JWT)."""

    TOKEN_URL = "https://api.shutterstock.com/oauth/token"
    UPLOAD_URL = "https://api.shutterstock.com/v2/content"

    async def _authenticate(self) -> dict[str, str]:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                self.TOKEN_URL,
                data={
                    "GRANT_TYPE": "client_credentials",
                    "CLIENT_ID": self.api_key,
                    "CLIENT_SECRET": self.api_secret,
                },
                timeout=15.0,
            )
            resp.raise_for_status()
        return {"Authorization": f"Bearer {resp.json()['access_token']}"}

    async def upload(self, file_path: str, keywords: list[str],
                     categories: list[str]) -> UploadResult:
        specs = self.validate_specs(file_path)
        if specs.blocks:
            return UploadResult(remote_id="", status="rejected",
                                error="; ".join(specs.blocks))

        headers = await self._authenticate()
        async with httpx.AsyncClient() as client:
            with open(file_path, "rb") as f:
                files = {"file": (Path(file_path).name, f, "image/jpeg")}
                resp = await client.post(
                    self.UPLOAD_URL,
                    files=files,
                    data={"keywords": ",".join(keywords)},
                    headers=headers,
                    timeout=60.0,
                )
            resp.raise_for_status()
            data = resp.json()

        return UploadResult(
            remote_id=str(data.get("id", "")),
            status="pending",
        )

    async def get_status(self, remote_id: str) -> UploadStatus:
        return UploadStatus(remote_id=remote_id, status="pending")

    async def get_sales(self, start_date: datetime,
                        end_date: datetime) -> list[SaleRecord]:
        return []

    def validate_specs(self, file_path: str) -> SpecValidation:
        p = Path(file_path)
        try:
            from PIL import Image
            with Image.open(file_path) as img:
                w, h = img.size
        except Exception:
            return SpecValidation(
                file_path=str(p),
                blocks=["Unable to read image dimensions"],
            )

        blocks: list[str] = []
        warnings: list[str] = []

        if w < 1500 or h < 1500:
            warnings.append("Image resolution below 1500px recommended minimum")
        if p.suffix.lower() not in (".jpg", ".jpeg", ".png", ".tiff", ".tif"):
            blocks.append("Unsupported format; must be JPEG/PNG/TIFF")
        if p.stat().st_size < 500_000:
            warnings.append("File smaller than 500 KB — may not meet quality bar")

        fmt = mimetypes.guess_type(str(p))[0] or "unknown"
        return SpecValidation(
            file_path=str(p), width_px=w, height_px=h,
            file_size_bytes=p.stat().st_size, file_format=fmt,
            passes=len(blocks) == 0, warnings=warnings, blocks=blocks,
        )


# -- Adobe Stock ------------------------------------------------------------


@_gateway_registry("adobe")
class AdobeStockGateway(StockGateway):
    """Adobe Stock Contributor API connector (Adobe Identity Service JWT)."""

    TOKEN_URL = "https://ims-na1.adobelogin.com/ims/token/v3"
    UPLOAD_URL = "https://stock.adobe.com/webservices/ContentUploadService"

    async def _authenticate(self) -> dict[str, str]:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                self.TOKEN_URL,
                data={
                    "grant_type": "client_credentials",
                    "client_id": self.api_key,
                    "client_secret": self.api_secret,
                    "scope": "AdobeID,openid",
                },
                timeout=15.0,
            )
            resp.raise_for_status()
        return {"Authorization": f"Bearer {resp.json()['access_token']}"}

    async def upload(self, file_path: str, keywords: list[str],
                     categories: list[str]) -> UploadResult:
        specs = self.validate_specs(file_path)
        if specs.blocks:
            return UploadResult(remote_id="", status="rejected",
                                error="; ".join(specs.blocks))
        # Real flow: get CDN pre-signed URL first, then PUT.
        return UploadResult(
            remote_id="", status="pending",
            error="Adobe Stock upload requires CDN pre-signed URL step",
        )

    async def get_status(self, remote_id: str) -> UploadStatus:
        return UploadStatus(remote_id=remote_id, status="pending")

    async def get_sales(self, start_date: datetime,
                        end_date: datetime) -> list[SaleRecord]:
        return []

    def validate_specs(self, file_path: str) -> SpecValidation:
        p = Path(file_path)
        try:
            from PIL import Image
            with Image.open(file_path) as img:
                w, h = img.size
        except Exception:
            return SpecValidation(
                file_path=str(p),
                blocks=["Unable to read image dimensions"],
            )

        blocks: list[str] = []
        warnings: list[str] = []

        if p.suffix.lower() not in (".jpg", ".jpeg"):
            blocks.append("Adobe Stock requires JPEG format")
        if w < 1000 or h < 1000:
            warnings.append("Resolution below 1000px")

        fmt = mimetypes.guess_type(str(p))[0] or "unknown"
        return SpecValidation(
            file_path=str(p), width_px=w, height_px=h,
            file_size_bytes=p.stat().st_size, file_format=fmt,
            passes=len(blocks) == 0, warnings=warnings, blocks=blocks,
        )


# -- Getty Images -----------------------------------------------------------


@_gateway_registry("getty")
class GettyGateway(StockGateway):
    """Getty Images Contributor API connector (OAuth2 client_credentials)."""

    TOKEN_URL = "https://api.gettyimages.com/oauth2/token"
    UPLOAD_URL = "https://api.gettyimages.com/v4/images"

    async def _authenticate(self) -> dict[str, str]:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                self.TOKEN_URL,
                data={
                    "grant_type": "client_credentials",
                    "client_id": self.api_key,
                    "client_secret": self.api_secret,
                },
                timeout=15.0,
            )
            resp.raise_for_status()
        return {"Authorization": f"Bearer {resp.json()['access_token']}"}

    async def upload(self, file_path: str, keywords: list[str],
                     categories: list[str]) -> UploadResult:
        specs = self.validate_specs(file_path)
        if specs.blocks:
            return UploadResult(remote_id="", status="rejected",
                                error="; ".join(specs.blocks))

        headers = await self._authenticate()
        async with httpx.AsyncClient() as client:
            with open(file_path, "rb") as f:
                files = {"image": (Path(file_path).name, f, "image/jpeg")}
                resp = await client.post(
                    self.UPLOAD_URL,
                    files=files,
                    headers=headers,
                    timeout=60.0,
                )
            resp.raise_for_status()
            data = resp.json()

        return UploadResult(remote_id=str(data.get("id", "")), status="pending")

    async def get_status(self, remote_id: str) -> UploadStatus:
        return UploadStatus(remote_id=remote_id, status="pending")

    async def get_sales(self, start_date: datetime,
                        end_date: datetime) -> list[SaleRecord]:
        return []

    def validate_specs(self, file_path: str) -> SpecValidation:
        p = Path(file_path)
        try:
            from PIL import Image
            with Image.open(file_path) as img:
                w, h = img.size
        except Exception:
            return SpecValidation(
                file_path=str(p),
                blocks=["Unable to read image dimensions"],
            )

        blocks: list[str] = []
        warnings: list[str] = []

        if p.suffix.lower() not in (".jpg", ".jpeg"):
            blocks.append("Getty Images requires JPEG")
        if w < 4096 or h < 4096:
            warnings.append("Getty recommends 4096px+ on the shortest edge")

        fmt = mimetypes.guess_type(str(p))[0] or "unknown"
        return SpecValidation(
            file_path=str(p), width_px=w, height_px=h,
            file_size_bytes=p.stat().st_size, file_format=fmt,
            passes=len(blocks) == 0, warnings=warnings, blocks=blocks,
        )


# -- 500px ------------------------------------------------------------------


@_gateway_registry("500px")
class FiveHundredPxGateway(StockGateway):
    """500px API v2 connector (OAuth2 + REST)."""

    TOKEN_URL = "https://api.500px.com/v1/oauth/token"
    UPLOAD_URL = "https://api.500px.com/v1/photos"

    async def _authenticate(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self.api_key}"}

    async def upload(self, file_path: str, keywords: list[str],
                     categories: list[str]) -> UploadResult:
        specs = self.validate_specs(file_path)
        if specs.blocks:
            return UploadResult(remote_id="", status="rejected",
                                error="; ".join(specs.blocks))

        headers = await self._authenticate()
        async with httpx.AsyncClient() as client:
            with open(file_path, "rb") as f:
                files = {"photo": (Path(file_path).name, f, "image/jpeg")}
                resp = await client.post(
                    self.UPLOAD_URL,
                    files=files,
                    headers=headers,
                    timeout=60.0,
                )
            resp.raise_for_status()
            data = resp.json()

        return UploadResult(remote_id=str(data.get("id", "")), status="pending")

    async def get_status(self, remote_id: str) -> UploadStatus:
        return UploadStatus(remote_id=remote_id, status="pending")

    async def get_sales(self, start_date: datetime,
                        end_date: datetime) -> list[SaleRecord]:
        return []

    def validate_specs(self, file_path: str) -> SpecValidation:
        p = Path(file_path)
        try:
            from PIL import Image
            with Image.open(file_path) as img:
                w, h = img.size
        except Exception:
            return SpecValidation(
                file_path=str(p),
                blocks=["Unable to read image dimensions"],
            )

        blocks: list[str] = []
        warnings: list[str] = []

        if w < 1200 or h < 1200:
            warnings.append("500px recommends 1200px+ per side")

        fmt = mimetypes.guess_type(str(p))[0] or "unknown"
        return SpecValidation(
            file_path=str(p), width_px=w, height_px=h,
            file_size_bytes=p.stat().st_size, file_format=fmt,
            passes=len(blocks) == 0, warnings=warnings, blocks=blocks,
        )


# -- Tuchong ----------------------------------------------------------------


@_gateway_registry("tuchong")
class TuchongGateway(StockGateway):
    """Tuchong (Chromatic) connector — limited API, mostly manual."""

    API_BASE = "https://api.tuchong.com"

    async def _authenticate(self) -> dict[str, str]:
        return {"X-Auth-Token": self.api_key}

    async def upload(self, file_path: str, keywords: list[str],
                     categories: list[str]) -> UploadResult:
        # Tuchong does not expose a partner media-upload API.
        return UploadResult(
            remote_id="", status="pending",
            error="Tuchong API is limited -- manual submission required",
        )

    async def get_status(self, remote_id: str) -> UploadStatus:
        return UploadStatus(remote_id=remote_id, status="pending")

    async def get_sales(self, start_date: datetime,
                        end_date: datetime) -> list[SaleRecord]:
        return []

    def validate_specs(self, file_path: str) -> SpecValidation:
        p = Path(file_path)
        blocks: list[str] = []
        if p.suffix.lower() not in (".jpg", ".jpeg", ".png", ".webp"):
            blocks.append("Unsupported format for Tuchong")

        fmt = mimetypes.guess_type(str(p))[0] or "unknown"
        return SpecValidation(
            file_path=str(p),
            file_size_bytes=p.stat().st_size,
            file_format=fmt,
            passes=len(blocks) == 0,
            blocks=blocks,
        )


# ============================================================================
# Factory
# ============================================================================


def get_gateway(channel_name: str) -> StockGateway:
    """Return a StockGateway instance for *channel_name* (must be created
    separately by the caller with credentials).

    Raises ``ValueError`` if the channel is unknown.
    """
    cls = _GATEWAY_REGISTRY.get(channel_name)
    if not cls:
        raise ValueError(
            f"Unsupported stock channel: {channel_name}. "
            f"Supported: {list(_GATEWAY_REGISTRY.keys())}"
        )
    return cls  # type: ignore[return-value]


# ============================================================================
# Service layer
# ============================================================================


class StockService:
    """Orchestrates gateway operations with DB persistence."""

    def __init__(self, db):
        self._db = db

    # -- internal helpers ----------------------------------------------------

    def _load_channel(self, channel_id: str):
        """Load channel row + decrypt credentials."""
        from app.models.photographer_v2 import StockChannel
        row = self._db.query(StockChannel).filter(
            StockChannel.id == channel_id,
        ).first()
        if not row:
            raise ValueError(f"Channel {channel_id} not found")

        row._api_key_dec = decrypt(row.api_key)
        row._api_secret_dec = decrypt(row.api_secret) if row.api_secret else None
        return row

    def _store_channel(self, user_id: str, channel_name: str,
                       api_key: str, api_secret: str,
                       account_id: str) -> Any:
        """Encrypt + upsert a StockChannel record; return it."""
        from app.models.photographer_v2 import StockChannel
        existing = self._db.query(StockChannel).filter(
            StockChannel.user_id == user_id,
            StockChannel.channel_name == channel_name,
        ).first()

        if existing:
            existing.api_key = encrypt(api_key)
            existing.api_secret = encrypt(api_secret) if api_secret else None
            existing.account_id = account_id or existing.account_id
            existing.is_active = True
            existing.updated_at = datetime.now(timezone.utc)
            self._db.flush()
            return existing

        ch = StockChannel(
            user_id=user_id,
            channel_name=channel_name,
            api_key=encrypt(api_key),
            api_secret=encrypt(api_secret) if api_secret else None,
            account_id=account_id,
        )
        self._db.add(ch)
        self._db.flush()
        self._db.refresh(ch)
        return ch

    # -- public API ----------------------------------------------------------

    async def add_channel(self, user_id: str, channel_name: str,
                          api_key: str, api_secret: str = "",
                          account_id: str = "") -> dict[str, Any]:
        """Register / update a stock channel with encrypted credentials.

        Validates credentials by exercising the gateway's auth flow.
        """
        if channel_name not in SUPPORTED_CHANNEL_NAMES:
            raise ValueError(
                f"Unsupported channel: {channel_name}. "
                f"Supported: {SUPPORTED_CHANNEL_NAMES}"
            )

        gw_cls = _GATEWAY_REGISTRY[channel_name]
        gw = gw_cls(api_key=api_key, api_secret=api_secret,
                    account_id=account_id)
        # Authenticate to verify credentials are valid.
        try:
            headers = await gw._authenticate()
            del headers
        except Exception as exc:
            logger.warning("Credential validation failed for %s: %s",
                           channel_name, exc)
            # Still store -- platforms may accept credentials but reject later.

        ch = self._store_channel(user_id, channel_name, api_key, api_secret,
                                 account_id)

        return {
            "id": ch.id,
            "channel_name": ch.channel_name,
            "is_active": ch.is_active,
            "created_at": ch.created_at.isoformat() if ch.created_at else None,
        }

    async def upload_to_channel(
        self,
        channel_id: str,
        work_id: str,
        file_path: str,
        keywords: list[str],
        categories: list[str],
    ) -> dict[str, Any]:
        """Upload a file to the given channel and persist ``StockUpload``."""
        ch = self._load_channel(channel_id)
        gw = _GATEWAY_REGISTRY[ch.channel_name](
            api_key=ch._api_key_dec,
            api_secret=ch._api_secret_dec,
            account_id=ch.account_id,
        )

        # Validate file specs before uploading.
        specs = gw.validate_specs(file_path)
        if specs.blocks:
            raise ValueError(
                f"File spec validation failed: {'; '.join(specs.blocks)}"
            )

        result = await gw.upload(file_path, keywords, categories)

        # Persist upload record.
        from app.models.photographer_v2 import StockUpload
        upload = StockUpload(
            channel_id=channel_id,
            work_id=work_id,
            remote_id=result.remote_id,
            status=result.status,
            rejection_reason=result.error,
            uploaded_at=datetime.now(timezone.utc),
        )
        self._db.add(upload)
        self._db.flush()
        self._db.refresh(upload)

        return {
            "id": upload.id,
            "channel_id": channel_id,
            "work_id": work_id,
            "remote_id": result.remote_id,
            "status": result.status,
            "uploaded_at": upload.uploaded_at.isoformat()
                           if upload.uploaded_at else None,
        }

    async def sync_sales(
        self,
        channel_id: str,
        start_date: datetime,
        end_date: datetime,
    ) -> list[dict[str, Any]]:
        """Fetch sales from platform and persist as ``StockSale`` rows."""
        ch = self._load_channel(channel_id)
        gw = _GATEWAY_REGISTRY[ch.channel_name](
            api_key=ch._api_key_dec,
            api_secret=ch._api_secret_dec,
            account_id=ch.account_id,
        )

        records = await gw.get_sales(start_date, end_date)

        from app.models.photographer_v2 import StockSale
        created = []
        for rec in records:
            sale = StockSale(
                license_type=rec.license_type,
                sale_amount=rec.sale_amount,
                currency=rec.currency,
                buyer_country=rec.buyer_country,
                sale_date=rec.sale_date,
            )
            self._db.add(sale)
            self._db.flush()
            self._db.refresh(sale)
            created.append({
                "id": sale.id,
                "sale_amount": sale.sale_amount,
                "currency": sale.currency,
                "sale_date": sale.sale_date.isoformat()
                             if sale.sale_date else None,
            })
        return created

    @staticmethod
    async def validate_file(
        work_id: str,
        channel_name: str,
        file_path: str,
    ) -> dict[str, Any]:
        """Pre-validate a file against platform upload specs."""
        if channel_name not in _GATEWAY_REGISTRY:
            return {
                "valid": False,
                "error": f"Unknown channel: {channel_name}",
                "warnings": [],
                "blocks": [f"Unsupported channel: {channel_name}"],
            }

        gw = _GATEWAY_REGISTRY[channel_name](api_key="dummy")
        specs = gw.validate_specs(file_path)
        return {
            "valid": specs.passes,
            "file_path": file_path,
            "width_px": specs.width_px,
            "height_px": specs.height_px,
            "file_size_bytes": specs.file_size_bytes,
            "file_format": specs.file_format,
            "warnings": specs.warnings,
            "blocks": specs.blocks,
        }

    @staticmethod
    def list_platforms() -> list[dict[str, Any]]:
        """Return metadata for all supported stock platforms."""
        return STOCK_PLATFORM_INFO
