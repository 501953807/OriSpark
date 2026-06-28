"""RFC 3161 时间戳服务."""

import hashlib
import os
from pathlib import Path
from typing import Optional

from app.gateway.digicert_tsa import TimestampGateway, MockTSAGateway
from app.gateway.digicert_tsa import TimestampToken


class TimestampService:
    """时间戳服务 — 封装 TSA 网关调用."""

    def __init__(self, gateway: Optional[TimestampGateway] = None):
        self.gateway = gateway or MockTSAGateway()

    async def timestamp_file(self, file_path: str) -> Optional[TimestampToken]:
        """为文件获取时间戳."""
        if not os.path.exists(file_path):
            return None

        h = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                h.update(chunk)
        data_hash = h.hexdigest()

        return await self.gateway.request_timestamp(data_hash)

    async def timestamp_hash(self, data_hash: str) -> Optional[TimestampToken]:
        """为已有哈希获取时间戳."""
        return await self.gateway.request_timestamp(data_hash)

    async def save_timestamp(self, token: TimestampToken, work_id: str) -> str:
        """保存时间戳令牌到文件.

        Returns:
            保存的文件路径
        """
        ts_dir = Path("data/timestamps")
        ts_dir.mkdir(parents=True, exist_ok=True)
        ts_path = ts_dir / f"{work_id}.tsr"
        with open(ts_path, "wb") as f:
            f.write(token.token_bytes)
        return str(ts_path)
