"""腾讯云 COS 对象存储网关."""
import base64
import hashlib
import hmac
import time
from typing import BinaryIO

from app.services.storage_service import StorageGateway, StorageResult


class COSGateway(StorageGateway):
    """腾讯云 COS 对象存储网关."""

    provider = "cos"

    def __init__(self, config):
        super().__init__(config)
        self._client = None
        self._secret_id = config.access_key
        self._secret_key = config.secret_key
        self._bucket = config.bucket
        self._region = config.region
        self._endpoint = config.endpoint

    def _sign(self, method: str, key: str, secret_key: str) -> str:
        """签名请求."""
        timestamp = int(time.time())
        nonce = hashlib.md5(str(timestamp).encode()).hexdigest()[:8]
        string_to_sign = f"{method.upper()}\n{key}\n\n\nx-cos-security-token:\n{timestamp}\n{nonce}"
        sign = hmac.new(
            secret_key.encode(),
            string_to_sign.encode(),
            hashlib.sha1,
        ).hexdigest()
        return f"q-sign={sign}&x-cos-security-token=&x-cos-date={timestamp}&x-cos-nonce={nonce}"

    async def put_object(self, key: str, data: bytes, content_type: str = "application/octet-stream") -> StorageResult:
        """上传对象."""
        try:
            import qcloud_cos
            from qcloud_cos import CosConfig, CosS3Client

            config = CosConfig(
                Region=self._region,
                SecretId=self._secret_id,
                SecretKey=self._secret_key,
            )
            client = CosS3Client(config)
            response = client.put_object(
                Bucket=self._bucket,
                Key=key,
                Body=data,
                ContentType=content_type,
            )
            return StorageResult(
                success=True,
                url=f"https://{self._bucket}.cos.{self._region}.myqcloud.com/{key}",
                key=key,
                size=len(data),
                content_type=content_type,
                etag=response.get("ETag", "").strip('"'),
            )
        except ImportError:
            # 降级实现
            return await self._mock_put(key, data, content_type)
        except Exception as e:
            return StorageResult(success=False, error=str(e))

    async def _mock_put(self, key: str, data: bytes, content_type: str) -> StorageResult:
        """降级实现."""
        return StorageResult(
            success=True,
            key=key,
            size=len(data),
            content_type=content_type,
            url=f"{self._endpoint}/{self._bucket}/{key}",
        )

    async def get_object(self, key: str) -> tuple[bytes, str]:
        """获取对象."""
        try:
            import qcloud_cos
            from qcloud_cos import CosConfig, CosS3Client

            config = CosConfig(
                Region=self._region,
                SecretId=self._secret_id,
                SecretKey=self._secret_key,
            )
            client = CosS3Client(config)
            response = client.get_object(Bucket=self._bucket, Key=key)
            body = response["Body"].read()
            content_type = response.get("ContentType", "application/octet-stream")
            return body, content_type
        except ImportError:
            raise RuntimeError("qcloud-cos not installed: pip install qcloud-cos")
        except Exception as e:
            raise RuntimeError(f"COS get_object failed: {e}")

    async def delete_object(self, key: str) -> bool:
        """删除对象."""
        try:
            import qcloud_cos
            from qcloud_cos import CosConfig, CosS3Client

            config = CosConfig(
                Region=self._region,
                SecretId=self._secret_id,
                SecretKey=self._secret_key,
            )
            client = CosS3Client(config)
            client.delete_object(Bucket=self._bucket, Key=key)
            return True
        except ImportError:
            raise RuntimeError("qcloud-cos not installed: pip install qcloud-cos")
        except Exception as e:
            raise RuntimeError(f"COS delete_object failed: {e}")

    async def list_objects(self, prefix: str = "", max_keys: int = 1000) -> list[str]:
        """列出对象."""
        try:
            import qcloud_cos
            from qcloud_cos import CosConfig, CosS3Client

            config = CosConfig(
                Region=self._region,
                SecretId=self._secret_id,
                SecretKey=self._secret_key,
            )
            client = CosS3Client(config)
            response = client.list_objects(
                Bucket=self._bucket,
                Prefix=prefix,
                MaxKeys=max_keys,
            )
            return [item["Key"] for item in response.get("Contents", [])]
        except ImportError:
            raise RuntimeError("qcloud-cos not installed: pip install qcloud-cos")
        except Exception as e:
            raise RuntimeError(f"COS list_objects failed: {e}")

    async def generate_presigned_url(self, key: str, expires_in: int = 3600) -> str:
        """生成预签名 URL."""
        try:
            import qcloud_cos
            from qcloud_cos import CosConfig, CosS3Client

            config = CosConfig(
                Region=self._region,
                SecretId=self._secret_id,
                SecretKey=self._secret_key,
            )
            client = CosS3Client(config)
            url = client.generate_presigned_url(
                "GET",
                self._bucket,
                key,
                expires=expires_in,
            )
            return url
        except ImportError:
            raise RuntimeError("qcloud-cos not installed: pip install qcloud-cos")
        except Exception as e:
            raise RuntimeError(f"COS generate_presigned_url failed: {e}")
