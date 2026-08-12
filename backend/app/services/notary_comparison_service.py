"""存证平台对比服务 — 自动发现 Gateway 子类，提供平台信息."""

import importlib
import inspect
import logging
from typing import Optional

from app.gateway.base import NotaryGateway
from app.gateway.antchain import AntChainGateway
from app.gateway.zhixinchain import ZhixinChainGateway
from app.gateway.banquanjia import BanquanjiaGateway
from app.schemas.notary import NotaryPlatformInfo, PlatformFeeItem

logger = logging.getLogger(__name__)

_PLATFORM_CONFIG: dict = {
    "banquanjia": {
        "description": "国家版权局 DCI 体系，法律效力最高",
        "website": "https://www.banquanjia.com",
    },
    "antchain": {
        "description": "支付宝蚂蚁区块链存证，商用级",
        "website": "https://antchain.antgroup.com",
    },
    "zhixinchain": {
        "description": "腾讯/互联网法院司法链，司法级",
        "website": "https://zhixinchain.com",
    },
    "polygon": {
        "description": "Polygon 公链存证，智能合约级",
        "website": "https://polygon.technology",
    },
}


class NotaryComparisonService:
    """存证平台对比服务 — 自动发现并管理 NotaryGateway 实现."""

    def __init__(self) -> None:
        self._gateways: dict[str, NotaryGateway] = {}
        self._discover_gateways()

    def _discover_gateways(self) -> None:
        self._gateways["banquanjia"] = BanquanjiaGateway()
        self._gateways["antchain"] = AntChainGateway()
        self._gateways["zhixinchain"] = ZhixinChainGateway()

    @property
    def platforms(self) -> dict[str, NotaryPlatformInfo]:
        result: dict[str, NotaryPlatformInfo] = {}
        for key, gw in self._gateways.items():
            cfg = _PLATFORM_CONFIG.get(key, {})
            result[key] = NotaryPlatformInfo(
                key=key,
                name=gw.get_platform_name(),
                description=cfg.get("description", ""),
                fee_per_record=gw.get_fee(),
                legal_level=gw.get_legal_level(),
                website=cfg.get("website", ""),
            )
        return result

    def get_platforms(self) -> list[NotaryPlatformInfo]:
        return list(self.platforms.values())

    def get_platform(self, key: str) -> Optional[NotaryPlatformInfo]:
        return self.platforms.get(key)

    def has_platform(self, key: str) -> bool:
        return key in self._gateways

    def compare(
        self,
        work_count: int,
        work_type: str = "image",
        budget: float = 50.0,
        legal_level: str = "commercial",
        priority: str = "cost",
    ) -> tuple[list[PlatformFeeItem], str, list[str]]:
        from app.routers.notary import _PLATFORM_PROFILES, _WORK_TYPE_SCORES, _score_platform

        platforms: list[PlatformFeeItem] = []
        best_key: Optional[str] = None
        best_score = -1

        for key, info in self.platforms.items():
            profile = _PLATFORM_PROFILES.get(key, {"pros": [], "cons": [], "priority": []})
            total_fee = info.fee_per_record * work_count
            score, reasons = _score_platform(
                key, info, work_type, budget, legal_level, work_count, priority,
            )
            platforms.append(PlatformFeeItem(
                key=key,
                name=info.name,
                fee_per_record=info.fee_per_record,
                legal_level=info.legal_level,
                estimated_total=round(total_fee, 2),
                pros=profile["pros"],
                cons=profile["cons"],
            ))
            if score > best_score:
                best_score = score
                best_key = key

        platforms.sort(key=lambda p: p.estimated_total)

        if best_key is None:
            return platforms, "", []

        _, best_reasons = _score_platform(
            best_key, self.platforms[best_key], work_type, budget, legal_level, work_count, priority,
        )
        return platforms, best_key, best_reasons
