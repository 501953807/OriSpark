"""本地视觉指纹嵌入服务 (P2.3.1-P2.3.2).

使用纯 Python/PIL 实现感知哈希，无需 ONNX 运行时:
- Average Hash (aHash): 缩放 + 平均值二值化
- Difference Hash (dHash): 水平梯度二值化
- Perceptual Hash (pHash): DCT 变换二值化
- Wavelet Hash (wHash): 小波变换二值化
"""

import hashlib
from dataclasses import dataclass
from typing import Optional
from pathlib import Path

from PIL import Image
import numpy as np


@dataclass
class FingerprintResult:
    """指纹计算结果."""
    work_id: str
    hash_type: str  # dhash/phash/whash/average_hash
    hash_value: str  # hex string
    hash_size: int = 16
    matched_work_id: Optional[str] = None
    hamming_distance: Optional[int] = None
    similarity: Optional[float] = None  # 0-100


def _load_image(file_path: str) -> Image.Image:
    """加载并预处理图像（灰度 + 抗锯齿缩放）."""
    img = Image.open(file_path).convert("L")
    return img


def compute_average_hash(file_path: str, hash_size: int = 16) -> str:
    """计算平均值哈希 (aHash).

    算法: 缩放为 hash_size x hash_size → 计算均值 → 按均值二值化.
    """
    img = _load_image(file_path)
    img = img.resize((hash_size, hash_size), Image.LANCZOS)
    pixels = np.array(img, dtype=np.float64)
    avg = pixels.mean()
    bits = (pixels > avg).flatten()
    return _bits_to_hex(bits)


def compute_difference_hash(file_path: str, hash_size: int = 16) -> str:
    """计算差异哈希 (dHash).

    算法: 缩放为 (hash_size+1) x hash_size → 比较相邻列 → 二值化.
    """
    img = _load_image(file_path)
    img = img.resize((hash_size + 1, hash_size), Image.LANCZOS)
    pixels = np.array(img, dtype=np.float64)
    # 水平相邻差分
    diff = pixels[:, 1:] > pixels[:, :-1]
    bits = diff.flatten()
    return _bits_to_hex(bits)


def compute_perceptual_hash(file_path: str, hash_size: int = 32) -> str:
    """计算感知哈希 (pHash).

    算法: 缩放 → DCT → 取左上角低频 → 按中值二值化.
    hash_size 控制 DCT 截取区域 (实际 hash 值为 hash_size//2 平方的比特数).
    """
    img = _load_image(file_path)
    # 缩放到 hash_size x hash_size
    img_small = img.resize((hash_size, hash_size), Image.LANCZOS)
    pixels = np.array(img_small, dtype=np.float64)

    # 2D DCT-II
    dct = _dct2d(pixels)
    # 取左上角低频区域 (半个尺寸)
    low_freq = dct[:hash_size // 2, :hash_size // 2]
    median = np.median(low_freq)
    bits = (low_freq > median).flatten()
    return _bits_to_hex(bits)


def compute_wavelet_hash(file_path: str, hash_size: int = 16) -> str:
    """计算小波哈希 (wHash).

    算法: 缩放 → Daubechies-like 5/3 小波变换 → 低低频子带 → 按均值二值化.

    注意: 这是纯 Python 实现，性能较低但对于小于 512px 的图像足够,
    主要用于与 dHash/pHash 交叉验证结果。
    """
    img = _load_image(file_path)
    # 缩放为 2 的幂次方
    size = 1
    while size * 2 <= hash_size * 4:
        size *= 2
    # 确保至少有 min_size
    size = max(size, hash_size)
    img = img.resize((size, size), Image.LANCZOS)
    pixels = np.array(img, dtype=np.float64)

    coeffs = _wavelet_53_decompose(pixels, levels=2)
    # 递归解包 (LL, (LH, HL, HH)) 直到获得真正的 2D 数组
    ll = _unwrap_ll(coeffs)

    # 确保 ll 足够大以裁剪
    if ll.shape[0] >= hash_size and ll.shape[1] >= hash_size:
        final = ll[:hash_size, :hash_size]
    else:
        # 如果不够大，使用整个 LL 并缩放
        from PIL import Image as PILImage
        ll_img = PILImage.fromarray(
            ((ll - ll.min()) / (ll.max() - ll.min() + 1e-8) * 255).astype(np.uint8)
        )
        ll_img = ll_img.resize((hash_size, hash_size), Image.LANCZOS)
        final = np.array(ll_img, dtype=np.float64)

    avg = final.mean()
    bits = (final > avg).flatten()
    return _bits_to_hex(bits)


def _unwrap_ll(coeffs):
    """从递归小波系数结构中提取 LL 子带 (2D numpy 数组)."""
    if isinstance(coeffs, np.ndarray):
        return coeffs
    if isinstance(coeffs, tuple):
        # 格式: (LL, (LH, HL, HH)), 其中 LL 可能仍是递归的
        ll = coeffs[0]
        if isinstance(ll, np.ndarray):
            return ll
        if isinstance(ll, tuple):
            return _unwrap_ll(ll)
    # fallback
    return np.array([])


def _bits_to_hex(bits: np.ndarray) -> str:
    """将布尔数组转为 hex 字符串."""
    # 每 4 个比特组成一个 hex 字符
    hex_chars = []
    for i in range(0, len(bits), 4):
        chunk = bits[i:i + 4]
        val = 0
        for j, b in enumerate(chunk):
            if b:
                val |= 1 << (3 - j)
        hex_chars.append(f"{val:x}")
    return "".join(hex_chars)


def _dct2d(matrix: np.ndarray) -> np.ndarray:
    """2D DCT-II 纯 NumPy 实现."""
    M, N = matrix.shape
    dct = np.zeros((M, N), dtype=np.float64)

    for u in range(M):
        for v in range(N):
            total = 0.0
            for x in range(M):
                for y in range(N):
                    total += (
                        matrix[x, y]
                        * np.cos(np.pi * u * (2 * x + 1) / (2 * M))
                        * np.cos(np.pi * v * (2 * y + 1) / (2 * N))
                    )
            dct[u, v] = total

    return dct


def _wavelet_53_decompose(matrix: np.ndarray, levels: int = 1):
    """Le Gall 5/3 小波分解 (JPEG2000 无损变换).

    返回: 递归元组结构 (LL, (LH, HL, HH)).
    """
    if levels == 0:
        return matrix

    # 行变换
    rows, cols = matrix.shape
    row_low = np.zeros((rows, (cols + 1) // 2), dtype=np.float64)
    row_high = np.zeros((rows, cols // 2), dtype=np.float64)

    for i in range(rows):
        row = matrix[i, :]
        # Lifting steps for Le Gall 5/3
        low = np.zeros((cols + 1) // 2, dtype=np.float64)
        high = np.zeros(cols // 2, dtype=np.float64)

        for j in range(0, cols, 2):
            idx = j // 2
            low[idx] = row[j]
        for j in range(1, cols - 1, 2):
            idx = j // 2
            high[idx] = row[j] - (row[j - 1] + row[j + 1]) / 2
        # 最后奇数边界
        if cols % 2 == 0 and cols > 1:
            high[-1] = row[-1] - row[-2]

        row_low[i, :] = low
        row_high[i, :] = high

    # 列变换
    col_low_ll = np.zeros(((rows + 1) // 2, (cols + 1) // 2), dtype=np.float64)
    col_high_lh = np.zeros((rows // 2, (cols + 1) // 2), dtype=np.float64)
    col_low_hl = np.zeros(((rows + 1) // 2, cols // 2), dtype=np.float64)
    col_high_hh = np.zeros((rows // 2, cols // 2), dtype=np.float64)

    # 对 row_low 矩阵进行列变换
    for j in range(row_low.shape[1]):
        col = row_low[:, j]
        low = np.zeros((rows + 1) // 2, dtype=np.float64)
        high = np.zeros(rows // 2, dtype=np.float64)
        for i in range(0, rows, 2):
            low[i // 2] = col[i]
        for i in range(1, rows - 1, 2):
            high[i // 2] = col[i] - (col[i - 1] + col[i + 1]) / 2
        if rows % 2 == 0 and rows > 1:
            high[-1] = col[-1] - col[-2]
        col_low_ll[:, j] = low
        col_high_lh[:, j] = high

    # 对 row_high 矩阵进行列变换
    for j in range(row_high.shape[1]):
        col = row_high[:, j]
        low = np.zeros((rows + 1) // 2, dtype=np.float64)
        high = np.zeros(rows // 2, dtype=np.float64)
        for i in range(0, rows, 2):
            low[i // 2] = col[i]
        for i in range(1, rows - 1, 2):
            high[i // 2] = col[i] - (col[i - 1] + col[i + 1]) / 2
        if rows % 2 == 0 and rows > 1:
            high[-1] = col[-1] - col[-2]
        col_low_hl[:, j] = low
        col_high_hh[:, j] = high

    # 递归分解 LL
    ll_recursive = _wavelet_53_decompose(col_low_ll, levels - 1)

    return (ll_recursive, (col_high_lh, col_low_hl, col_high_hh))


def hamming_distance(hash1: str, hash2: str) -> int:
    """计算两个 hex 哈希字符串之间的汉明距离."""
    if len(hash1) != len(hash2):
        # 对齐到较短长度
        min_len = min(len(hash1), len(hash2))
        hash1, hash2 = hash1[:min_len], hash2[:min_len]

    h1_bits = _hex_to_bits(hash1)
    h2_bits = _hex_to_bits(hash2)

    dist = 0
    for b1, b2 in zip(h1_bits, h2_bits):
        if b1 != b2:
            dist += 1
    return dist


def _hex_to_bits(hex_str: str) -> list[int]:
    """将 hex 字符串展开为比特列表."""
    bits = []
    for ch in hex_str:
        val = int(ch, 16)
        for shift in range(3, -1, -1):
            bits.append((val >> shift) & 1)
    return bits


def compute_similarity(hash1: str, hash2: str, total_bits: Optional[int] = None) -> float:
    """基于汉明距离计算相似度 (百分比 0-100).

    相似度 = (1 - hamming / total_bits) * 100.
    """
    if total_bits is None:
        # 按 hex 长度估算
        total_bits = min(len(hash1), len(hash2)) * 4

    dist = hamming_distance(hash1, hash2)
    if total_bits == 0:
        return 100.0
    return max(0.0, (1.0 - dist / total_bits) * 100.0)


def compute_all_fingerprints(file_path: str) -> dict[str, str]:
    """计算所有类型的感知哈希."""
    return {
        "average_hash": compute_average_hash(file_path),
        "dhash": compute_difference_hash(file_path),
        "phash": compute_perceptual_hash(file_path),
        "whash": compute_wavelet_hash(file_path),
    }
