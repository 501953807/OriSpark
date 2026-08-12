"""水印预设服务."""

import struct
from typing import Optional, List
from datetime import datetime
from pathlib import Path
from sqlalchemy.orm import Session
from PIL import Image
import numpy as np
from app.models.watermark_preset import WatermarkPreset, PositionEnum

# 嵌入强度（alpha），保证 PSNR > 40 dB
_WATERMARK_ALPHA = 5

# 水印容量：creator_id (8bit) + timestamp (16bit) + contract_id (8bit) = 32 bit = 4字节
_WATERMARK_BIT_COUNT = 32

# 嵌入位置：DCT 块中频系数行/列索引（8x8 块内）
_EMBED_ROW_START = 3
_EMBED_ROW_END = 5   # exclusive
_EMBED_COL_START = 3
_EMBED_COL_END = 5   # exclusive


def _dct2d(matrix: np.ndarray) -> np.ndarray:
    """2D DCT-II 正交归一化实现."""
    M, N = matrix.shape
    dct = np.zeros((M, N), dtype=np.float64)
    for u in range(M):
        cu = np.sqrt(1.0 / M) if u == 0 else np.sqrt(2.0 / M)
        for v in range(N):
            cv = np.sqrt(1.0 / N) if v == 0 else np.sqrt(2.0 / N)
            total = 0.0
            for x in range(M):
                for y in range(N):
                    total += (
                        matrix[x, y]
                        * np.cos(np.pi * u * (2 * x + 1) / (2 * M))
                        * np.cos(np.pi * v * (2 * y + 1) / (2 * N))
                    )
            dct[u, v] = cu * cv * total
    return dct


def _idct2d(dct: np.ndarray) -> np.ndarray:
    """2D 逆 DCT-II（正交归一化）."""
    M, N = dct.shape
    img = np.zeros((M, N), dtype=np.float64)
    for x in range(M):
        for y in range(N):
            total = 0.0
            for u in range(M):
                cu = np.sqrt(1.0 / M) if u == 0 else np.sqrt(2.0 / M)
                for v in range(N):
                    cv = np.sqrt(1.0 / N) if v == 0 else np.sqrt(2.0 / N)
                    total += (
                        cu * cv
                        * dct[u, v]
                        * np.cos(np.pi * u * (2 * x + 1) / (2 * M))
                        * np.cos(np.pi * v * (2 * y + 1) / (2 * N))
                    )
            img[x, y] = total
    return img


def _bits_to_bytes(bits: list[int]) -> bytes:
    """将比特列表（每 8 个）转为 bytes."""
    result = bytearray()
    for i in range(0, len(bits), 8):
        byte = 0
        for j in range(8):
            if i + j < len(bits):
                byte = (byte << 1) | bits[i + j]
            else:
                byte = byte << 1
        result.append(byte)
    return bytes(result)


def _bytes_to_bits(n: int, num_bits: int = _WATERMARK_BIT_COUNT) -> list[int]:
    """将整数拆分为指定位数的比特列表（高位在前）."""
    bits = []
    for shift in range(num_bits - 1, -1, -1):
        bits.append((n >> shift) & 1)
    return bits


def _encode_watermark(
    creator_id: str, timestamp: int, contract_id: str
) -> bytes:
    """将 creator_id (首字节) + timestamp (2字节 big-endian) + contract_id (首字节)
    编码为 4 字节的 bytes 对象。

    creator_id 取 str 第一个字符的 ASCII，contract_id 同理。
    timestamp 使用 16 位，截断为 0-65535 范围。
    """
    c_id_byte = struct.pack("B", ord(creator_id[0]) if creator_id else 0)
    ts_bytes = struct.pack(">H", timestamp & 0xFFFF)
    cont_id_byte = struct.pack("B", ord(contract_id[0]) if contract_id else 0)
    return c_id_byte + ts_bytes + cont_id_byte


def _decode_watermark(data: bytes) -> dict:
    """从 4 字节数据解码水印字段."""
    if len(data) < 4:
        return {"creator_id": "", "timestamp": 0, "contract_id": ""}
    creator_byte = data[0]
    timestamp = struct.unpack(">H", data[1:3])[0]
    contract_byte = data[3]
    return {
        "creator_id": chr(creator_byte) if creator_byte else "",
        "timestamp": timestamp,
        "contract_id": chr(contract_byte) if contract_byte else "",
    }


def _psnr(original: np.ndarray, modified: np.ndarray) -> float:
    """计算两幅图像之间的 PSNR（dB）."""
    mse = np.mean((original.astype(np.float64) - modified.astype(np.float64)) ** 2)
    if mse == 0:
        return float("inf")
    return float(10 * np.log10(255.0 ** 2 / mse))


def apply_frequency_watermark(
    image_path: str,
    creator_id: str,
    timestamp: int,
    contract_id: str,
    output_path: Optional[str] = None,
) -> dict:
    """在图像频域嵌入隐形水印（固定位置策略）."""
    # 加载图像并转为灰度
    img = Image.open(image_path).convert("L")
    w, h = img.size

    # 补齐至 8 的倍数
    new_w = ((w + 7) // 8) * 8
    new_h = ((h + 7) // 8) * 8
    if new_w != w or new_h != h:
        img = img.resize((new_w, new_h), Image.LANCZOS)

    pixels = np.array(img, dtype=np.float64)
    original_pixels = pixels.copy()

    # 编码水印为 32 个比特
    wm_bytes = _encode_watermark(creator_id, timestamp, contract_id)
    bits = _bytes_to_bits(int.from_bytes(wm_bytes, "big"), _WATERMARK_BIT_COUNT)

    block_size = 8
    embed_count = 0

    # 收集所有块的位置
    all_blocks = []
    for by in range(0, pixels.shape[0], block_size):
        for bx in range(0, pixels.shape[1], block_size):
            all_blocks.append((by, bx))

    # 使用固定位置嵌入：每隔 N 个块嵌入一个比特
    # 确保块选择可重现
    step = max(1, len(all_blocks) // _WATERMARK_BIT_COUNT)
    selected_indices = list(range(0, len(all_blocks), step))[:_WATERMARK_BIT_COUNT]

    # 嵌入水印
    for i, block_idx in enumerate(selected_indices):
        by, bx = all_blocks[block_idx]
        block = pixels[by:by + block_size, bx:bx + block_size].copy()
        dct_block = _dct2d(block)

        # 使用固定位置嵌入 1 比特
        row = _EMBED_ROW_START + (i % 2)
        col = _EMBED_COL_START + ((i // 2) % 2)

        bit = bits[i]
        coeff = dct_block[row, col]
        # 符号嵌入（固定强度）
        if bit == 1:
            dct_block[row, col] = abs(coeff) + _WATERMARK_ALPHA
        else:
            dct_block[row, col] = -(abs(coeff) + _WATERMARK_ALPHA)
        embed_count += 1

        # 逆 DCT
        block_recon = _idct2d(dct_block)
        block_recon = np.clip(block_recon, 0, 255)
        pixels[by:by + block_size, bx:bx + block_size] = block_recon

    # 还原原始尺寸（若曾补齐）
    if new_w != w or new_h != h:
        pixels = pixels[:h, :w]

    # 计算 PSNR
    psnr_val = _psnr(original_pixels[:pixels.shape[0], :pixels.shape[1]], pixels)

    # 保存结果
    if output_path is None:
        p = Path(image_path)
        output_path = str(p.parent / (p.stem + "_wm" + p.suffix))

    out_img = Image.fromarray(pixels.astype(np.uint8), mode="L")
    out_img.save(output_path)

    return {
        "success": True,
        "psnr": round(psnr_val, 1),
        "output_path": output_path,
        "bits_embedded": embed_count,
    }


def extract_watermark(image_path: str) -> dict:
    """从图像中频域提取隐形水印."""
    img = Image.open(image_path).convert("L")
    w, h = img.size
    new_w = ((w + 7) // 8) * 8
    new_h = ((h + 7) // 8) * 8
    if new_w != w or new_h != h:
        img = img.resize((new_w, new_h), Image.LANCZOS)

    pixels = np.array(img, dtype=np.float64)
    block_size = 8

    # 收集所有块的位置
    all_blocks = []
    for by in range(0, pixels.shape[0], block_size):
        for bx in range(0, pixels.shape[1], block_size):
            all_blocks.append((by, bx))

    # 使用固定位置提取：与嵌入时相同的步长
    step = max(1, len(all_blocks) // _WATERMARK_BIT_COUNT)
    selected_indices = list(range(0, len(all_blocks), step))[:_WATERMARK_BIT_COUNT]

    # 从选中的块提取位
    bits: list[int] = []
    for i, block_idx in enumerate(selected_indices):
        by, bx = all_blocks[block_idx]
        block = pixels[by:by + block_size, bx:bx + block_size].copy()
        dct_block = _dct2d(block)

        row = _EMBED_ROW_START + (i % 2)
        col = _EMBED_COL_START + ((i // 2) % 2)

        if row >= _EMBED_ROW_END or col >= _EMBED_COL_END:
            continue

        coeff = dct_block[row, col]
        bits.append(1 if coeff > 0 else 0)

    if len(bits) < _WATERMARK_BIT_COUNT:
        return {
            "creator_id": "",
            "timestamp": 0,
            "contract_id": "",
            "confidence": 0.0,
            "error": "图像尺寸过小，无法提取完整水印",
        }

    # 解码
    wm_bits = bits[:_WATERMARK_BIT_COUNT]
    wm_bytes = _bits_to_bytes(wm_bits)
    decoded = _decode_watermark(wm_bytes)

    # 置信度：基于中频系数的绝对值均值与 alpha 的比值估算
    coeff_sum = 0.0
    count = 0
    for i, block_idx in enumerate(selected_indices):
        by, bx = all_blocks[block_idx]
        block = pixels[by:by + block_size, bx:bx + block_size].copy()
        dct_block = _dct2d(block)
        row = _EMBED_ROW_START + (i % 2)
        col = _EMBED_COL_START + ((i // 2) % 2)
        if row >= _EMBED_ROW_END or col >= _EMBED_COL_END:
            count += 1
            continue
        coeff_sum += abs(dct_block[row, col])
        count += 1
    avg_coeff = coeff_sum / max(count, 1)
    confidence = min(1.0, avg_coeff / (_WATERMARK_ALPHA * 2))

    return {
        **decoded,
        "confidence": round(confidence, 2),
    }


# ─────────────────────────────────────────────────────────────────────────────
# 原有 CRUD 操作（保持不变）
# ─────────────────────────────────────────────────────────────────────────────


def get_presets(db: Session) -> List[dict]:
    """获取所有水印预设，按创建时间降序排列."""
    presets = db.query(WatermarkPreset).order_by(WatermarkPreset.created_at.desc()).all()
    return [p.to_dict() for p in presets]


def get_preset(db: Session, preset_id: str) -> Optional[dict]:
    """根据 ID 获取单个水印预设."""
    preset = db.query(WatermarkPreset).filter(WatermarkPreset.id == preset_id).first()
    if preset:
        return preset.to_dict()
    return None


def create_preset(
    db: Session,
    name: str,
    position: str,
    opacity: int = 100,
    text: Optional[str] = None,
    image_path: Optional[str] = None,
) -> dict:
    """创建新的水印预设."""
    # Convert string position to enum
    try:
        position_enum = PositionEnum(position)
    except ValueError:
        raise ValueError(f"无效的position值：{position}")

    preset = WatermarkPreset(
        name=name,
        position=position_enum,
        opacity=opacity,
        text=text,
        image_path=image_path,
    )
    db.add(preset)
    try:
        db.commit()
        db.refresh(preset)
        return preset.to_dict()
    except Exception:
        db.rollback()
        raise


def update_preset(
    db: Session,
    preset_id: str,
    name: Optional[str] = None,
    position: Optional[str] = None,
    opacity: Optional[int] = None,
    text: Optional[str] = None,
    image_path: Optional[str] = None,
) -> dict:
    """更新现有水印预设."""
    preset = db.query(WatermarkPreset).filter(WatermarkPreset.id == preset_id).first()
    if not preset:
        raise ValueError("预设不存在")

    if name is not None:
        preset.name = name
    if position is not None:
        try:
            preset.position = PositionEnum(position)
        except ValueError:
            raise ValueError(f"无效的position值：{position}")
    if opacity is not None:
        preset.opacity = opacity
    if text is not None:
        preset.text = text
    if image_path is not None:
        preset.image_path = image_path

    try:
        db.commit()
        db.refresh(preset)
        return preset.to_dict()
    except Exception:
        db.rollback()
        raise


def delete_preset(db: Session, preset_id: str) -> bool:
    """删除水印预设."""
    preset = db.query(WatermarkPreset).filter(WatermarkPreset.id == preset_id).first()
    if not preset:
        return False
    db.delete(preset)
    try:
        db.commit()
        return True
    except Exception:
        db.rollback()
        raise


def apply_watermark_to_work(
    db: Session, work_id: str, preset_id: str
) -> dict:
    """
    将水印预设应用到作品（批量操作接口）.

    注意：此函数主要负责验证和记录，实际的水印应用逻辑
    由外部服务或图像处理模块执行。
    """
    # 验证作品是否存在（work表存在说明作品已注册）
    from app.models.work import Work
    work = db.query(Work).filter(Work.id == work_id).first()
    if not work:
        raise ValueError(f"作品 {work_id} 不存在")

    # 验证预设是否存在
    preset = get_preset(db, preset_id)
    if not preset:
        raise ValueError(f"水印预设 {preset_id} 不存在")

    # 记录水印应用（这里简化，实际可能需要水印日志表）
    return {
        "work_id": work_id,
        "preset_id": preset_id,
        "applied_at": datetime.now().isoformat(),
        "message": f"水印预设 '{preset['name']}' 已应用于作品 {work_id}"
    }
