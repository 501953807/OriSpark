"""对象存储集成服务 — MinIO / AWS S3 / 阿里云 OSS.

实现统一的对象存储抽象层, 支持 MinIO (私有) 和 AWS S3 / 阿里云 OSS (云存储).
双写模式: 所有写操作同时写入两个存储, 读操作优先从 S3 读取.
"""

from __future__ import annotations

import io
import logging
import mimetypes
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import BinaryIO, Optional
from urllib.parse import quote

logger = logging.getLogger(__name__)


# ============================================================================
# Domain types
# ============================================================================


@dataclass
class StorageResult:
    """存储操作结果."""
    success: bool
    url: Optional[str] = None
    key: Optional[str] = None
    size: int = 0
    content_type: str = "application/octet-stream"
    etag: Optional[str] = None
    error: Optional[str] = None
    stored_at: Optional[datetime] = None


@dataclass
class StorageConfig:
    """对象存储配置."""
    provider: str              # "minio" | "s3" | "oss" | "cos"
    endpoint: str
    bucket: str
    region: str = "us-east-1"
    access_key: str = ""
    secret_key: str = ""
    public_url: str = ""       # CDN / 公开访问 URL 前缀
    use_ssl: bool = True
    force_path_style: bool = False


# ============================================================================
# Storage Gateway ABC
# ============================================================================


class StorageGateway(ABC):
    """对象存储网关基类."""

    provider: str = ""

    def __init__(self, config: StorageConfig):
        self.config = config

    @abstractmethod
    async def put_object(self, key: str, data: bytes,
                         content_type: str = "application/octet-stream") -> StorageResult:
        """上传对象."""
        ...

    @abstractmethod
    async def get_object(self, key: str) -> tuple[bytes, str]:
        """获取对象, 返回 (data, content_type)."""
        ...

    @abstractmethod
    async def delete_object(self, key: str) -> bool:
        """删除对象."""
        ...

    @abstractmethod
    async def list_objects(self, prefix: str = "", max_keys: int = 1000) -> list[str]:
        """列出对象."""
        ...

    @abstractmethod
    async def generate_presigned_url(self, key: str, expires_in: int = 3600) -> str:
        """生成预签名 URL."""
        ...

    def object_url(self, key: str) -> str:
        """获取对象的公开访问 URL."""
        encoded_key = quote(key, safe="")
        if self.config.public_url:
            return f"{self.config.public_url}/{encoded_key}"
        return f"{self.config.endpoint}/{self.config.bucket}/{encoded_key}"


# -- MinIO ------------------------------------------------------------------


class MinIOGateway(StorageGateway):
    """MinIO 对象存储网关.

    MinIO 兼容 AWS S3 API, 使用相同的 boto3 客户端.
    """

    provider = "minio"

    def __init__(self, config: StorageConfig):
        super().__init__(config)
        self._client = None

    def _get_client(self):
        """延迟初始化 boto3 client."""
        if self._client is None:
            try:
                import boto3
                from botocore.config import Config
                self._client = boto3.client(
                    "s3",
                    endpoint_url=self.config.endpoint,
                    aws_access_key_id=self.config.access_key,
                    aws_secret_access_key=self.config.secret_key,
                    config=Config(signature_version="s3v4"),
                    use_ssl=self.config.use_ssl,
                    region_name=self.config.region,
                )
            except ImportError:
                raise RuntimeError("boto3 not installed: pip install boto3")
        return self._client

    async def put_object(self, key: str, data: bytes,
                         content_type: str = "application/octet-stream") -> StorageResult:
        client = self._get_client()
        extra_args = {"ContentType": content_type}
        try:
            client.put_object(
                Bucket=self.config.bucket,
                Key=key,
                Body=data,
                ContentType=content_type,
                **extra_args,
            )
            return StorageResult(
                success=True,
                key=key,
                size=len(data),
                content_type=content_type,
                url=self.object_url(key),
                stored_at=datetime.now(timezone.utc),
            )
        except Exception as exc:
            logger.error("MinIO 上传失败: %s", exc)
            return StorageResult(success=False, error=str(exc))

    async def get_object(self, key: str) -> tuple[bytes, str]:
        client = self._get_client()
        resp = client.get_object(Bucket=self.config.bucket, Key=key)
        return resp["Body"].read(), resp.get("ContentType", "application/octet-stream")

    async def delete_object(self, key: str) -> bool:
        client = self._get_client()
        client.delete_object(Bucket=self.config.bucket, Key=key)
        return True

    async def list_objects(self, prefix: str = "", max_keys: int = 1000) -> list[str]:
        client = self._get_client()
        resp = client.list_objects_v2(
            Bucket=self.config.bucket,
            Prefix=prefix,
            MaxKeys=max_keys,
        )
        return [obj["Key"] for obj in resp.get("Contents", [])]

    async def generate_presigned_url(self, key: str, expires_in: int = 3600) -> str:
        client = self._get_client()
        return client.generate_presigned_url(
            "get_object",
            Params={"Bucket": self.config.bucket, "Key": key},
            ExpiresIn=expires_in,
        )


# -- AWS S3 -----------------------------------------------------------------


class S3Gateway(StorageGateway):
    """AWS S3 对象存储网关."""

    provider = "s3"

    def __init__(self, config: StorageConfig):
        super().__init__(config)
        self._client = None

    def _get_client(self):
        if self._client is None:
            try:
                import boto3
                self._client = boto3.client(
                    "s3",
                    region_name=self.config.region,
                    aws_access_key_id=self.config.access_key,
                    aws_secret_access_key=self.config.secret_key,
                )
            except ImportError:
                raise RuntimeError("boto3 not installed: pip install boto3")
        return self._client

    async def put_object(self, key: str, data: bytes,
                         content_type: str = "application/octet-stream") -> StorageResult:
        client = self._get_client()
        try:
            client.put_object(
                Bucket=self.config.bucket,
                Key=key,
                Body=data,
                ContentType=content_type,
            )
            return StorageResult(
                success=True, key=key, size=len(data),
                content_type=content_type,
                url=self.object_url(key),
                stored_at=datetime.now(timezone.utc),
            )
        except Exception as exc:
            return StorageResult(success=False, error=str(exc))

    async def get_object(self, key: str) -> tuple[bytes, str]:
        client = self._get_client()
        resp = client.get_object(Bucket=self.config.bucket, Key=key)
        return resp["Body"].read(), resp.get("ContentType", "application/octet-stream")

    async def delete_object(self, key: str) -> bool:
        client = self._get_client()
        client.delete_object(Bucket=self.config.bucket, Key=key)
        return True

    async def list_objects(self, prefix: str = "", max_keys: int = 1000) -> list[str]:
        client = self._get_client()
        resp = client.list_objects_v2(Bucket=self.config.bucket, Prefix=prefix, MaxKeys=max_keys)
        return [obj["Key"] for obj in resp.get("Contents", [])]

    async def generate_presigned_url(self, key: str, expires_in: int = 3600) -> str:
        client = self._get_client()
        return client.generate_presigned_url(
            "get_object",
            Params={"Bucket": self.config.bucket, "Key": key},
            ExpiresIn=expires_in,
        )


# -- 阿里云 OSS -------------------------------------------------------------


class OSSGateway(StorageGateway):
    """阿里云 OSS 对象存储网关.

    使用 oss2 库, 兼容阿里云 OSS API.
    """

    provider = "oss"

    def __init__(self, config: StorageConfig):
        super().__init__(config)
        self._client = None

    def _get_client(self):
        if self._client is None:
            try:
                import oss2
                auth = oss2.Auth(self.config.access_key, self.config.secret_key)
                endpoint = self.config.endpoint.replace("https://", "").replace("http://", "")
                self._client = oss2.Bucket(
                    auth,
                    f"https://{endpoint}",
                    self.config.bucket,
                )
            except ImportError:
                raise RuntimeError("oss2 not installed: pip install oss2")
        return self._client

    async def put_object(self, key: str, data: bytes,
                         content_type: str = "application/octet-stream") -> StorageResult:
        client = self._get_client()
        try:
            client.put_object(key, data, headers={"Content-Type": content_type})
            return StorageResult(
                success=True, key=key, size=len(data),
                content_type=content_type,
                url=self.object_url(key),
                stored_at=datetime.now(timezone.utc),
            )
        except Exception as exc:
            return StorageResult(success=False, error=str(exc))

    async def get_object(self, key: str) -> tuple[bytes, str]:
        client = self._get_client()
        result = client.get_object(key)
        return result.read(), result.headers.get("content-type", "application/octet-stream")

    async def delete_object(self, key: str) -> bool:
        client = self._get_client()
        client.delete_object(key)
        return True

    async def list_objects(self, prefix: str = "", max_keys: int = 1000) -> list[str]:
        client = self._get_client()
        marker = None
        keys = []
        while True:
            result = client.list_objects(prefix=prefix, marker=marker, max_keys=max_keys)
            keys.extend(obj.key for obj in result.object_list)
            if not result.is_truncated:
                break
            marker = result.next_marker
        return keys

    async def generate_presigned_url(self, key: str, expires_in: int = 3600) -> str:
        client = self._get_client()
        return client.sign_url("GET", key, expires_in)


# ============================================================================
# Factory
# ============================================================================


def create_storage_gateway(config: StorageConfig) -> StorageGateway:
    """根据配置创建存储网关."""
    if config.provider == "minio":
        return MinIOGateway(config)
    elif config.provider == "s3":
        return S3Gateway(config)
    elif config.provider == "oss":
        return OSSGateway(config)
    elif config.provider == "cos":
        from app.gateway.cos import COSGateway
        return COSGateway(config)
    else:
        raise ValueError(f"不支持的存储提供商: {config.provider}")


def get_storage_gateway(config: StorageConfig) -> StorageGateway:
    """获取存储网关 (兼容旧接口)."""
    return create_storage_gateway(config)


# ============================================================================
# Service layer
# ============================================================================


class StorageService:
    """对象存储综合服务层.

    支持双写模式: 所有写操作同时写入 minio 和 s3, 读操作优先从 s3 读取.
    适用于迁移过渡期.
    """

    def __init__(self, primary: StorageConfig, secondary: Optional[StorageConfig] = None):
        self._primary = create_storage_gateway(primary)
        self._secondary = create_storage_gateway(secondary) if secondary else None

    async def upload(self, key: str, data: bytes,
                     content_type: str = "application/octet-stream") -> StorageResult:
        """上传文件 (双写模式)."""
        # 主存储
        result = await self._primary.put_object(key, data, content_type)
        if not result.success:
            return result

        # 备用存储 (如果配置了)
        if self._secondary:
            await self._secondary.put_object(key, data, content_type)

        return result

    async def download(self, key: str) -> tuple[bytes, str]:
        """下载文件 (优先从主存储读取, 失败则从备用)."""
        try:
            return await self._primary.get_object(key)
        except Exception:
            if self._secondary:
                return await self._secondary.get_object(key)
            raise

    async def delete(self, key: str) -> bool:
        """删除文件 (双删)."""
        await self._primary.delete_object(key)
        if self._secondary:
            await self._secondary.delete_object(key)
        return True

    async def list(self, prefix: str = "", max_keys: int = 1000) -> list[str]:
        """列出文件."""
        return await self._primary.list_objects(prefix, max_keys)

    async def get_url(self, key: str, expires_in: int = 3600) -> str:
        """获取访问 URL (优先主存储的公开 URL)."""
        return self._primary.object_url(key)

    async def generate_presigned_url(self, key: str, expires_in: int = 3600) -> str:
        """生成预签名 URL."""
        return await self._primary.generate_presigned_url(key, expires_in)
