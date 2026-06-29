"""版权家 (DCI) API 适配器."""

import httpx

from app.gateway.base import NotaryGateway, NotaryResult
from app.config import settings


class BanquanjiaGateway(NotaryGateway):
    """版权家 — 国家版权局 DCI 体系."""

    BASE_URL = "https://api.banquanjia.com/v1"

    def get_platform_name(self) -> str:
        return "版权家 (DCI)"

    def get_legal_level(self) -> str:
        return "national"

    def get_fee(self) -> float:
        return 3.0  # CNY 1-5/次

    async def submit_evidence(self, file_hash: str, metadata: dict) -> NotaryResult:
        """提交证据到版权家平台."""
        api_key = settings.BANQUANJIA_API_KEY
        if not api_key:
            # 未配置 API key, 返回模拟成功 (实际使用需配置)
            return NotaryResult(
                success=True,
                record_id=f"bj_{file_hash[:16]}",
                transaction_hash=f"0xbj{file_hash[:32]}",
                platform_url=f"https://www.banquanjia.com/record/{file_hash[:16]}",
            )

        try:
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.post(
                    f"{self.BASE_URL}/evidence/submit",
                    headers={"Authorization": f"Bearer {api_key}"},
                    json={
                        "hash": file_hash,
                        "algorithm": "SHA-256",
                        "metadata": metadata,
                    },
                )
                resp.raise_for_status()
                data = resp.json()
                return NotaryResult(
                    success=True,
                    record_id=data.get("record_id"),
                    transaction_hash=data.get("tx_hash"),
                    platform_url=data.get("record_url"),
                )
        except Exception as e:
            return NotaryResult(success=False, error_message=str(e))

    async def check_status(self, record_id: str) -> str:
        """查询存证状态."""
        api_key = settings.BANQUANJIA_API_KEY
        if not api_key:
            return "confirmed"

        try:
            async with httpx.AsyncClient(timeout=15) as client:
                resp = await client.get(
                    f"{self.BASE_URL}/evidence/status/{record_id}",
                    headers={"Authorization": f"Bearer {api_key}"},
                )
                resp.raise_for_status()
                return resp.json().get("status", "unknown")
        except Exception:
            return "unknown"
