"""C2PA manifest 二进制嵌入服务.

支持将 C2PA manifest 直接嵌入 PNG/JPEG 文件的二进制内容中。
失败时 fallback 到卫星文件模式。
"""

import io
import json
import struct
from pathlib import Path
from typing import Optional


# ==============================================================================
# PNG embedding
# ==============================================================================

def embed_into_png(file_path: str, manifest_bytes: bytes, output_path: Optional[str] = None) -> Optional[str]:
    """将 C2PA manifest 嵌入 PNG 文件.

    PNG 结构: [IHDR][...]...[IDAT...][c2pa chunk][IEND]
    在 IDAT 之后、IEND 之前插入自定义 chunk。

    Args:
        file_path: 源 PNG 文件路径
        manifest_bytes: C2PA manifest 的原始字节
        output_path: 输出路径 (默认覆盖原文件)

    Returns:
        输出文件路径，失败返回 None
    """
    try:
        with open(file_path, "rb") as f:
            data = f.read()

        result = _embed_c2pa_chunk_into_png(data, manifest_bytes)
        if not result:
            return None

        out = output_path or file_path
        with open(out, "wb") as f:
            f.write(result)
        return out

    except Exception:
        return None


def extract_from_png(file_path: str) -> Optional[bytes]:
    """从 PNG 文件中提取 C2PA chunk 数据."""
    try:
        with open(file_path, "rb") as f:
            data = f.read()
        return _extract_c2pa_from_png(data)
    except Exception:
        return None


def _embed_c2pa_chunk_into_png(data: bytes, manifest_bytes: bytes) -> Optional[bytes]:
    """在 PNG 数据中嵌入 c2pa chunk."""
    # Validate PNG signature
    png_sig = b"\x89PNG\r\n\x1a\n"
    if not data.startswith(png_sig):
        return None

    # Find IEND chunk
    iend_pos = data.rfind(b"IEND")
    if iend_pos < len(png_sig):
        return None

    # Build c2pa chunk
    chunk_type = b"c2pa"
    # Chunk length must be <= 0x7FFFFFFF
    if len(manifest_bytes) > 0x7FFFFFFF:
        return None

    chunk_length = struct.pack(">I", len(manifest_bytes))
    chunk_crc = _crc32(chunk_type + manifest_bytes)
    chunk = chunk_length + chunk_type + manifest_bytes + chunk_crc

    # Insert before IEND
    return data[:iend_pos] + chunk + data[iend_pos:]


def _extract_c2pa_from_png(data: bytes) -> Optional[bytes]:
    """从 PNG 中提取 c2pa chunk 数据."""
    pos = len(b"\x89PNG\r\n\x1a\n")
    while pos < len(data) - 8:
        length = struct.unpack(">I", data[pos:pos + 4])[0]
        chunk_type = data[pos + 4:pos + 8]
        chunk_data = data[pos + 8:pos + 8 + length]
        pos += 12 + length

        if chunk_type == b"IEND":
            break
        if chunk_type == b"c2pa":
            return chunk_data
    return None


# ==============================================================================
# JPEG embedding (APP13 / XMP)
# ==============================================================================

def embed_into_jpeg(file_path: str, xmp_data: bytes, output_path: Optional[str] = None) -> Optional[str]:
    """将 XMP 数据嵌入 JPEG 文件的 APP13 segment.

    Args:
        file_path: 源 JPEG 文件路径
        xmp_data: XMP XML 字节数据
        output_path: 输出路径

    Returns:
        输出文件路径，失败返回 None
    """
    try:
        with open(file_path, "rb") as f:
            data = f.read()

        result = _embed_xmp_into_jpeg(data, xmp_data)
        if not result:
            return None

        out = output_path or file_path
        with open(out, "wb") as f:
            f.write(result)
        return out

    except Exception:
        return None


def extract_from_jpeg(file_path: str) -> Optional[bytes]:
    """从 JPEG 文件中提取 APP13/XMP 数据."""
    try:
        with open(file_path, "rb") as f:
            data = f.read()
        return _extract_xmp_from_jpeg(data)
    except Exception:
        return None


def _embed_xmp_into_jpeg(data: bytes, xmp_data: bytes) -> Optional[bytes]:
    """在 JPEG 数据中嵌入 XMP 到 APP13 segment."""
    soi = b"\xff\xd8"
    eoi = b"\xff\xd9"

    if not data.startswith(soi):
        return None

    # Find existing APP13 segment
    pos = 2  # skip SOI
    while pos < len(data) - 4:
        marker = data[pos:pos + 2]
        if marker == soi or marker == eoi:
            pos += 2
            continue
        if len(marker) < 2 or marker[0] != 0xFF:
            break

        segment_type = marker[1]
        if segment_type == 0xDA:  # SOS — stop here
            break

        seg_len = struct.unpack(">H", data[pos + 2:pos + 4])[0]
        seg_end = pos + 4 + seg_len - 2

        # Check if this is APP13 (Adobe)
        if segment_type == 0xED:
            # Replace existing APP13
            header = data[pos:pos + 2] + struct.pack(">H", len(xmp_data) + 2)
            return data[:pos] + header + xmp_data + data[seg_end:]

        pos = seg_end

    # No APP13 found — insert after APP0 (JFIF) or APP1 (EXIF)
    pos = 2
    insert_pos = len(data) - 2  # before EOI by default
    while pos < len(data) - 4:
        marker = data[pos:pos + 2]
        if len(marker) < 2 or marker[0] != 0xFF:
            break
        segment_type = marker[1]
        if segment_type == 0xDA:  # SOS
            break
        if segment_type in (0xE0, 0xE1):  # APP0 (JFIF), APP1 (EXIF)
            seg_len = struct.unpack(">H", data[pos + 2:pos + 4])[0]
            next_pos = pos + 4 + seg_len - 2
            if next_pos < insert_pos:
                insert_pos = next_pos
        else:
            seg_len = struct.unpack(">H", data[pos + 2:pos + 4])[0]
            pos += 4 + seg_len - 2
            continue
        pos += 4

    segment_header = b"\xff\xed" + struct.pack(">H", len(xmp_data) + 2)
    return data[:insert_pos] + segment_header + xmp_data + data[insert_pos:]


def _extract_xmp_from_jpeg(data: bytes) -> Optional[bytes]:
    """从 JPEG 中提取 APP13/XMP 数据."""
    pos = 2
    while pos < len(data) - 4:
        marker = data[pos:pos + 2]
        if len(marker) < 2 or marker[0] != 0xFF:
            break
        segment_type = marker[1]
        if segment_type == 0xDA:  # SOS
            break
        if segment_type == 0xED:  # APP13
            seg_len = struct.unpack(">H", data[pos + 2:pos + 4])[0]
            return data[pos + 4:pos + 4 + seg_len - 2]
        seg_len = struct.unpack(">H", data[pos + 2:pos + 4])[0]
        pos += 4 + seg_len - 2
    return None


# ==============================================================================
# CRC32 calculation
# ==============================================================================

def _crc32(data: bytes) -> bytes:
    """Calculate CRC32 matching PNG spec (same as zlib.crc32 but no dependency)."""
    import binascii
    return struct.pack(">I", binascii.crc32(data) & 0xFFFFFFFF)
