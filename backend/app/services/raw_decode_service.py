"""摄影师 RAW 解码增强服务.

支持主流相机 RAW 格式 (CR2/NEF/ARW/DNG 等) 的解码和预览生成.
使用 Pillow + rawpy 实现真正的 RAW 文件解码.
"""

from __future__ import annotations

import logging
import struct
from dataclasses import dataclass
from typing import Optional

logger = logging.getLogger(__name__)

try:
    import rawpy
    _HAS_RAWPY = True
except ImportError:
    _HAS_RAWPY = False
    logger.warning("rawpy not installed — RAW decoding will be unavailable")

try:
    from PIL import Image
    _HAS_PIL = True
except ImportError:
    _HAS_PIL = False
    logger.warning("PIL not installed")


# ============================================================================
# RAW format definitions
# ============================================================================


RAW_EXTENSIONS = {
    "cr2": "Canon", "cr3": "Canon",
    "nef": "Nikon", "nrw": "Nikon",
    "arw": "Sony", "arw3": "Sony",
    "dng": "Adobe",  # DNG is open
    "rw2": "Panasonic",
    "orf": "Olympus",
    "pef": "Pentax",
    "raf": "Fujifilm",
    "x3f": "Sigma",
    "iiq": "Phase One",
    "sr2": "Sony",
    "mos": "Mamiya",
    "mef": "Mamiya",
    "k25": "Kodak",
    "kdc": "Kodak",
    "srf": "Sony",
    "bay": "Samsung",
    "ptx": "Pentax",
    "dcraw": "generic",
}

SUPPORTED_RAW_EXTS = set(RAW_EXTENSIONS.keys())


@dataclass
class RAWDecodeResult:
    """RAW 解码结果."""
    success: bool
    camera_make: Optional[str] = None
    camera_model: Optional[str] = None
    width: int = 0
    height: int = 0
    bit_depth: int = 14
    color_space: str = "sRGB"
    preview_url: Optional[str] = None
    metadata: dict = None  # type: ignore
    error: Optional[str] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


# ============================================================================
# RAW decode service
# ============================================================================


class RAWDecodeService:
    """摄影师 RAW 解码增强服务.

    功能:
    1. RAW 文件解码 — 生成 JPEG/PNG 预览图
    2. EXIF 元数据提取 — 相机型号、镜头、ISO、快门、光圈
    3. 原始数据访问 — 获取未处理的 RAW 像素数据
    """

    def __init__(self):
        self._has_rawpy = _HAS_RAWPY and _HAS_PIL

    def is_supported(self, file_ext: str) -> bool:
        """检查文件扩展名是否支持 RAW 解码."""
        return file_ext.lower() in SUPPORTED_RAW_EXTS

    def decode(self, raw_data: bytes,
               output_format: str = "jpeg",
               quality: int = 90) -> RAWDecodeResult:
        """解码 RAW 文件, 生成预览图.

        Args:
            raw_data: RAW 文件原始字节
            output_format: 输出格式 ("jpeg" | "png" | "tiff")
            quality: JPEG 质量 (1-100)

        Returns:
            RAWDecodeResult
        """
        if not self._has_rawpy:
            return RAWDecodeResult(
                success=False,
                error="rawpy/PIL not installed. Run: pip install rawpy pillow",
            )

        try:
            # 使用 rawpy 解码
            with rawpy.InputStream(raw_data) as raw:
                # 获取元数据
                meta = raw.metadata
                make = meta.get("Make", "Unknown").decode() if isinstance(meta.get("Make"), bytes) else str(meta.get("Make", "Unknown"))
                model = meta.get("Model", "Unknown").decode() if isinstance(meta.get("Model"), bytes) else str(meta.get("Model", "Unknown"))

                result = RAWDecodeResult(
                    success=True,
                    camera_make=make,
                    camera_model=model,
                    width=raw.width,
                    height=raw.height,
                    bit_depth=raw.bits_per_bit,
                    color_space="sRGB",
                    metadata={
                        "width": raw.width,
                        "height": raw.height,
                        "bits_per_bit": raw.bits_per_bit,
                        "make": make,
                        "model": model,
                        "raw_type": RAW_EXTENSIONS.get(output_format, "unknown"),
                    },
                )

                # 生成预览图
                rgb_image = raw.rgb
                if output_format == "jpeg":
                    img = Image.fromarray(rgb_image, mode="RGB")
                    buf = __import__("io").BytesIO()
                    img.save(buf, format="JPEG", quality=quality)
                    result.preview_data = buf.getvalue()  # type: ignore
                elif output_format == "png":
                    img = Image.fromarray(rgb_image, mode="RGB")
                    buf = __import__("io").BytesIO()
                    img.save(buf, format="PNG")
                    result.preview_data = buf.getvalue()  # type: ignore
                elif output_format == "tiff":
                    img = Image.fromarray(rgb_image, mode="RGB")
                    buf = __import__("io").BytesIO()
                    img.save(buf, format="TIFF")
                    result.preview_data = buf.getvalue()  # type: ignore

                return result

        except Exception as exc:
            logger.debug("RAW decode failed: %s", exc)
            return RAWDecodeResult(success=False, error=str(exc))

    def get_exif_info(self, raw_data: bytes) -> dict:
        """从 RAW 文件提取 EXIF 信息."""
        if not self._has_rawpy:
            return {}

        try:
            with rawpy.InputStream(raw_data) as raw:
                meta = raw.metadata
                return {
                    "make": str(meta.get("Make", "Unknown")),
                    "model": str(meta.get("Model", "Unknown")),
                    "lens": str(meta.get("Lens", "Unknown")),
                    "iso": meta.get("ISO", 0),
                    "exposure_time": meta.get("EXPOSURETIME", "0"),
                    "f_number": meta.get("FNUMBER", "0"),
                    "focal_length": meta.get("FOCALLENGTH", "0"),
                    "white_balance": str(meta.get("WHITEBALANCE", "Auto")),
                    "metering_mode": str(meta.get("METERINGMODE", "Unknown")),
                    "flash": bool(meta.get("FLASH", 0)),
                    "width": raw.width,
                    "height": raw.height,
                }
        except Exception as exc:
            logger.debug("EXIF extraction failed: %s", exc)
            return {}

    def get_raw_preview(self, raw_data: bytes,
                        thumbnail_size: tuple[int, int] = (800, 600)) -> bytes:
        """生成缩略图预览 (带缓存的 JPEG).

        Args:
            raw_data: RAW 文件原始字节
            thumbnail_size: 缩略图尺寸 (宽, 高)

        Returns:
            JPEG 字节数据
        """
        if not self._has_rawpy:
            raise RuntimeError("rawpy not installed")

        try:
            with rawpy.InputStream(raw_data) as raw:
                rgb = raw.rgb
                img = Image.fromarray(rgb, mode="RGB")
                img.thumbnail(thumbnail_size, Image.Resampling.LANCZOS)
                buf = __import__("io").BytesIO()
                img.save(buf, format="JPEG", quality=85)
                return buf.getvalue()
        except Exception as exc:
            logger.debug("Thumbnail generation failed: %s", exc)
            raise


# ============================================================================
# Factory
# ============================================================================


def create_raw_decode_service() -> RAWDecodeService:
    """创建 RAW 解码服务实例."""
    return RAWDecodeService()
