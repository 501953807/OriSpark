"""回流水印检测服务 — 验证内容来源."""

import random
from dataclasses import dataclass
from typing import Optional


@dataclass
class WatermarkDetectionResult:
    """水印检测结果."""
    has_watermark: bool
    watermark_text: Optional[str] = None
    confidence: float = 0.0
    detected_at: str = "center"


class WatermarkDetector:
    """水印检测器 — 用于回流归因时验证内容来源.

    当前为 Mock 实现，实际应接入图像识别 API.
    """

    def __init__(self, preset_watermarks: Optional[list[str]] = None):
        self.preset_watermarks = preset_watermarks or ["OriStudio", "© OriStudio"]

    def detect(self, image_data: bytes, watermark_text: Optional[str] = None) -> WatermarkDetectionResult:
        """检测图片中是否存在指定水印."""
        text_to_check = watermark_text or (self.preset_watermarks[0] if self.preset_watermarks else "")
        has_match = len(text_to_check) > 0 and random.random() > 0.5

        return WatermarkDetectionResult(
            has_watermark=has_match,
            watermark_text=text_to_check if has_match else None,
            confidence=0.85 if has_match else 0.0,
            detected_at="corner",
        )

    def verify_work_source(self, work_id: str, platform_content_url: str) -> dict:
        """验证作品来源 — 通过水印匹配确认内容是否来自本平台分发."""
        return {
            "matched": True,
            "confidence": 0.92,
            "source_platform": "weixin",
        }
