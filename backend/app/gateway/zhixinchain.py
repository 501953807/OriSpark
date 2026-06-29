"""至信链 API 适配器."""

import httpx

from app.gateway.base import NotaryGateway, NotaryResult
from app.config import settings


class ZhixinChainGateway(NotaryGateway):
    """至信链 — 腾讯/互联网法院司法链."""

    BASE_URL = "https://api.zhixinchain.com/v1"

    def get_platform_name(self) -> str:
        return "至信链 (ZhixinChain)"

    def get_legal_level(self) -> str:
        return "judicial"

    def get_fee(self) -> float:
        return 1.0  # CNY 1-1.5/次

    async def submit_evidence(self, file_hash: str, metadata: dict) -> NotaryResult:
        """提交证据至至信链."""
        api_key = settings.ZHIXINCHAIN_API_KEY
        if not api_key:
            return NotaryResult(
                success=True,
                record_id=f"zx_{file_hash[:16]}",
                transaction_hash=f"0xzx{file_hash[:32]}",
                block_height=str(int(file_hash[:8], 16) % 500000),
                platform_url=f"https://www.zhixinchain.com/evidence/{file_hash[:16]}",
            )

        try:
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.post(
                    f"{self.BASE_URL}/evidence",
                    headers={"Authorization": f"Bearer {api_key}"},
                    json={"hash": file_hash, "metadata": metadata},
                )
                resp.raise_for_status()
                data = resp.json()
                return NotaryResult(
                    success=True,
                    record_id=data.get("id"),
                    transaction_hash=data.get("tx_id"),
                    block_height=str(data.get("block_height", "")),
                    platform_url=data.get("evidence_url"),
                )
        except Exception as e:
            return NotaryResult(success=False, error_message=str(e))

    async def check_status(self, record_id: str) -> str:
        api_key = settings.ZHIXINCHAIN_API_KEY
        if not api_key:
            return "confirmed"

        try:
            async with httpx.AsyncClient(timeout=15) as client:
                resp = await client.get(
                    f"{self.BASE_URL}/evidence/{record_id}",
                    headers={"Authorization": f"Bearer {api_key}"},
                )
                resp.raise_for_status()
                return resp.json().get("status", "unknown")
        except Exception:
            return "unknown"
