"""RFC 3161 时间戳网关 — DigiCert TSA 服务适配器."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional


@dataclass
class TimestampToken:
    """RFC 3161 时间戳令牌."""
    token_bytes: bytes  # DER 编码的时间戳令牌
    hash_algorithm: str = "sha256"
    policy: str = "1.2.840.113549.3.2"  # TS Policy OID
    accuracy_seconds: int = 10


class TimestampGateway(ABC):
    """时间戳网关基类."""

    @abstractmethod
    async def request_timestamp(self, data_hash: str) -> Optional[TimestampToken]:
        """请求时间戳令牌.

        Args:
            data_hash: 要加时间戳的数据的 hex 编码 SHA-256 哈希

        Returns:
            TimestampToken 或 None (失败)
        """
        ...


class DigiCertTSAGateway(TimestampGateway):
    """DigiCert 时间戳服务网关.

    TSA Endpoint: http://timestamp.digicert.com
    """

    TSA_URL = "http://timestamp.digicert.com"

    async def request_timestamp(self, data_hash: str) -> Optional[TimestampToken]:
        """v1: 模拟实现.

        实际实现需要:
        1. 构建 RFC 3161 TST Request (DER 编码)
        2. POST 到 TSA URL
        3. 解析 TST Response (DER 编码)
        4. 返回 TimestampToken
        """
        import hashlib
        return TimestampToken(
            token_bytes=hashlib.sha256(data_hash.encode()).digest(),
            hash_algorithm="sha256",
        )


class MockTSAGateway(TimestampGateway):
    """模拟网关 — 用于开发和测试."""

    async def request_timestamp(self, data_hash: str) -> Optional[TimestampToken]:
        import datetime
        import hashlib
        nonce_hash = hashlib.sha256(str(datetime.datetime.utcnow()).encode()).hexdigest()
        return TimestampToken(
            token_bytes=f"mock-tsa:{data_hash[:16]}:{nonce_hash}".encode(),
            hash_algorithm="sha256",
        )
