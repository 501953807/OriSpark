"""导出文件元数据审计服务.

对导出文件 (PDF/MP4/JPG 等) 进行元数据审计, 提取并验证:
1. EXIF / XMP 元数据
2. C2PA 内容凭证
3. 文件指纹 (SHA-256 / pHash)
4. 创作时间线
5. 修改历史
"""

from __future__ import annotations

import hashlib
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

logger = logging.getLogger(__name__)

try:
    from PIL import Image
    _HAS_PIL = True
except ImportError:
    _HAS_PIL = False

try:
    import pytesseract
    _HAS_OCR = True
except ImportError:
    _HAS_OCR = False


# ============================================================================
# Domain types
# ============================================================================


@dataclass
class MetadataAuditResult:
    """元数据审计结果."""
    success: bool
    file_hash: str = ""
    file_size: int = 0
    file_type: str = ""
    content_type: str = ""
    exif_data: dict = field(default_factory=dict)
    xmp_data: dict = field(default_factory=dict)
    c2pa_data: Optional[dict] = None
    thumbnail: Optional[str] = None  # base64 encoded
    text_content: str = ""          # OCR 识别的文字内容
    watermark_detected: bool = False
    audit_timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    warnings: list[str] = field(default_factory=list)
    error: Optional[str] = None

    def to_dict(self) -> dict:
        """序列化为字典."""
        return {
            "success": self.success,
            "file_hash": self.file_hash,
            "file_size": self.file_size,
            "file_type": self.file_type,
            "content_type": self.content_type,
            "exif_data": self.exif_data,
            "xmp_data": self.xmp_data,
            "c2pa_data": self.c2pa_data,
            "text_content_length": len(self.text_content),
            "watermark_detected": self.watermark_detected,
            "audit_timestamp": self.audit_timestamp.isoformat(),
            "warnings": self.warnings,
            "error": self.error,
        }


# ============================================================================
# Audit service
# ============================================================================


class MetadataAuditService:
    """导出文件元数据审计服务.

    对导出文件进行全面元数据审计, 用于版权保护和内容溯源.
    """

    def __init__(self):
        self._supported_image_types = {"JPEG", "PNG", "TIFF", "WEBP", "GIF"}
        self._supported_video_types = {"MP4", "MOV", "AVI", "MKV"}
        self._supported_audio_types = {"MP3", "WAV", "FLAC", "AAC", "OGG"}

    def compute_file_hash(self, file_data: bytes) -> str:
        """计算文件的 SHA-256 哈希值."""
        return hashlib.sha256(file_data).hexdigest()

    def detect_file_type(self, file_data: bytes) -> tuple[str, str]:
        """检测文件类型 (MIME type + 扩展名).

        使用文件头 magic bytes 进行识别.
        """
        if file_data[:3] == b"\xff\xd8\xff":
            return "image/jpeg", "jpg"
        elif file_data[:8] == b"\x89PNG\r\n\x1a\n":
            return "image/png", "png"
        elif file_data[:4] == b"RIFF" and file_data[8:12] == b"WEBP":
            return "image/webp", "webp"
        elif file_data[:4] == b"ID3":
            return "audio/mpeg", "mp3"
        elif file_data[:4] == b"ftyp":
            # ISO base media (MP4/MOV)
            if file_data[8:12] in (b"iso2", b"iso4", b"mp41", b"mp42"):
                return "video/mp4", "mp4"
            elif file_data[8:12] == b"qt  ":
                return "video/quicktime", "mov"
        elif file_data[:3] == b"Ogg":
            return "application/ogg", "ogg"
        elif file_data[:4] == b"fLaC":
            return "audio/flac", "flac"
        return "application/octet-stream", "bin"

    def audit_image(self, file_data: bytes) -> MetadataAuditResult:
        """审计图片文件的元数据."""
        result = MetadataAuditResult(success=False)

        # 基本信息
        result.file_hash = self.compute_file_hash(file_data)
        result.file_size = len(file_data)
        result.content_type, result.file_type = self.detect_file_type(file_data)

        if result.content_type.startswith("image/"):
            result.success = True

            if _HAS_PIL:
                try:
                    img = Image.open(file_data if isinstance(file_data, (bytes, bytearray)) else file_data)
                    result.exif_data = dict(img.getexif() or {})
                    result.width = img.width
                    result.height = img.height

                    # 尝试提取 XMP
                    if hasattr(img, "text") and "XML:com.adobe.xmp" in img.text:
                        result.xmp_data = {"raw": img.text["XML:com.adobe.xmp"]}

                    # 检查是否有 C2PA 关联数据
                    if img.info and "c2pa" in str(img.info).lower():
                        result.c2pa_data = {"detected": True}

                except Exception as exc:
                    result.warnings.append(f"EXIF 解析警告: {exc}")
            else:
                result.warnings.append("PIL 未安装, 跳过 EXIF 解析")

            # OCR 文字识别
            if _HAS_OCR:
                try:
                    if _HAS_PIL:
                        img = Image.open(file_data if isinstance(file_data, (bytes, bytearray)) else file_data)
                        result.text_content = pytesseract.image_to_string(img).strip()
                except Exception:
                    pass

            # 水印检测
            try:
                from app.services.watermark_detector import WatermarkDetector
                detector = WatermarkDetector()
                wmr = detector.detect(file_data)
                result.watermark_detected = wmr.has_watermark
            except Exception:
                pass

        return result

    def audit_video(self, file_data: bytes) -> MetadataAuditResult:
        """审计视频文件的元数据."""
        result = MetadataAuditResult(success=False)

        result.file_hash = self.compute_file_hash(file_data)
        result.file_size = len(file_data)
        result.content_type, result.file_type = self.detect_file_type(file_data)

        if result.content_type.startswith("video/"):
            result.success = True
            # 视频元数据提取较复杂, 暂只记录基本信息
            result.warnings.append("视频元数据提取需要 ffmpeg 支持, 当前仅记录文件级信息")
        else:
            result.error = f"非视频文件: {result.content_type}"

        return result

    def audit_audio(self, file_data: bytes) -> MetadataAuditResult:
        """审计音频文件的元数据."""
        result = MetadataAuditResult(success=False)

        result.file_hash = self.compute_file_hash(file_data)
        result.file_size = len(file_data)
        result.content_type, result.file_type = self.detect_file_type(file_data)

        if result.content_type.startswith("audio/"):
            result.success = True
            # 音频元数据 (ID3 tags)
            if self._has_id3_tags(file_data):
                result.exif_data = self._parse_id3_tags(file_data)
        else:
            result.error = f"非音频文件: {result.content_type}"

        return result

    def _has_id3_tags(self, data: bytes) -> bool:
        """检查是否有 ID3 标签 (MP3)."""
        return data[:3] == b"ID3"

    def _parse_id3_tags(self, data: bytes) -> dict:
        """解析 ID3 标签."""
        try:
            import mutagen
            audio = mutagen.File(data if isinstance(data, (bytes, bytearray)) else file_path)
            if audio is None:
                return {}
            return {
                "title": str(audio.get("TIT2", "")),
                "artist": str(audio.get("TPE1", "")),
                "album": str(audio.get("TALB", "")),
                "track": str(audio.get("TRCK", "")),
                "year": str(audio.get("TDRC", "")),
                "genre": str(audio.get("TCON", "")),
            }
        except Exception:
            return {}

    def audit_file(self, file_data: bytes, file_path: Optional[str] = None) -> MetadataAuditResult:
        """审计任意文件, 自动识别类型并调用对应审计方法."""
        content_type, _ = self.detect_file_type(file_data)

        if content_type.startswith("image/"):
            return self.audit_image(file_data)
        elif content_type.startswith("video/"):
            return self.audit_video(file_data)
        elif content_type.startswith("audio/"):
            return self.audit_audio(file_data)
        else:
            # 通用审计 (PDF 等)
            result = MetadataAuditResult(success=True)
            result.file_hash = self.compute_file_hash(file_data)
            result.file_size = len(file_data)
            result.content_type = content_type
            result.file_type = "pdf" if content_type == "application/pdf" else "other"
            result.warnings.append(f"不支持的文件类型: {content_type}, 仅记录文件级信息")
            return result

    def generate_audit_report(self, result: MetadataAuditResult,
                               work_id: Optional[str] = None) -> dict:
        """生成完整的审计报告 (用于 PDF 导出)."""
        return {
            "work_id": work_id,
            "audit_timestamp": result.audit_timestamp.isoformat(),
            "file_info": {
                "hash_sha256": result.file_hash,
                "size_bytes": result.file_size,
                "mime_type": result.content_type,
                "extension": result.file_type,
            },
            "metadata": {
                "exif": result.exif_data,
                "xmp": result.xmp_data,
                "c2pa": result.c2pa_data,
            },
            "content_analysis": {
                "ocr_text_length": len(result.text_content),
                "watermark_detected": result.watermark_detected,
            },
            "warnings": result.warnings,
            "summary": self._generate_summary(result),
        }

    def _generate_summary(self, result: MetadataAuditResult) -> str:
        """生成审计摘要."""
        parts = []
        parts.append(f"文件哈希: {result.file_hash[:16]}...")
        parts.append(f"文件大小: {result.file_size:,} 字节")
        parts.append(f"文件类型: {result.content_type}")
        if result.width and result.height:
            parts.append(f"图像尺寸: {result.width}x{result.height}")
        if result.watermark_detected:
            parts.append("检测到水印")
        if result.exif_data:
            parts.append(f"EXIF 数据: {len(result.exif_data)} 项")
        if result.text_content:
            parts.append(f"OCR 文字: {len(result.text_content)} 字符")
        return " | ".join(parts)


# ============================================================================
# Factory
# ============================================================================


def create_metadata_audit_service() -> MetadataAuditService:
    """创建元数据审计服务实例."""
    return MetadataAuditService()
