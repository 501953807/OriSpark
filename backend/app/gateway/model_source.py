"""模型/LoRA 来源查询网关 — 对接 Civitai/HuggingFace."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional


@dataclass
class ModelSourceInfo:
    """模型来源信息."""
    model_name: str
    source: str  # "civitai" / "huggingface" / "unknown"
    author: str = ""
    license_type: str = "unknown"  # "public" / "restricted" / "commercial_allowed" / "unknown"
    allows_commercial: bool = False
    requires_attribution: bool = False
    model_url: str = ""
    risk_level: str = "unknown"  # "safe" / "caution" / "risk"


class ModelSourceGateway(ABC):
    """模型来源查询网关基类."""

    @abstractmethod
    async def query(self, model_name: str, source: str = "civitai") -> Optional[ModelSourceInfo]:
        """查询模型来源信息."""
        ...


class CivitaiModelSourceGateway(ModelSourceGateway):
    """Civitai 模型查询适配器 (v1: 模拟).

    实际实现需要调用 Civitai API:
    GET https://civitainer.com/api/v1/models?name={model_name}
    """

    async def query(self, model_name: str, source: str = "civitai") -> Optional[ModelSourceInfo]:
        # v1 模拟: 已知风险模型
        _RISK_MODELS = ["photorealism", "realisticVision"]
        if model_name.lower() in _RISK_MODELS:
            return ModelSourceInfo(
                model_name=model_name, source="civitai",
                license_type="restricted", allows_commercial=False,
                requires_attribution=True, risk_level="caution",
            )
        return ModelSourceInfo(
            model_name=model_name, source="civitai",
            license_type="public", allows_commercial=True,
            requires_attribution=False, risk_level="safe",
        )


class MockModelSourceGateway(ModelSourceGateway):
    """模拟网关 — 用于开发和测试."""

    async def query(self, model_name: str, source: str = "civitai") -> Optional[ModelSourceInfo]:
        return ModelSourceInfo(
            model_name=model_name, source=source,
            license_type="public", allows_commercial=True,
            requires_attribution=False, risk_level="safe",
        )
