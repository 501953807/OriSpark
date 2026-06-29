"""Logo 检测与品牌模板匹配服务 (P2.3.3-P2.3.4).

使用 PIL 模板匹配作为简化的 SIFT-like 特征检测:
- 多尺度模板匹配 (缩放 + 滑动窗口)
- 归一化互相关 (NCC) 作为匹配度量
- 品牌 Logo 注册与 CRUD
"""

import io
from dataclasses import dataclass, field
from typing import Optional
from pathlib import Path

from PIL import Image
import numpy as np


@dataclass
class LogoMatchResult:
    """Logo 匹配结果."""
    brand_id: str
    brand_name: str
    matched_location: tuple[int, int] = (0, 0)  # (x, y) in target image
    match_scale: float = 1.0  # 匹配的缩放比
    confidence: float = 0.0  # 0-100
    matched_region_b64: Optional[str] = None  # 匹配区域的 base64 缩略图


@dataclass
class LogoScanResult:
    """单次扫描的综合结果."""
    target_path: str
    matches: list[LogoMatchResult] = field(default_factory=list)
    total_brands_checked: int = 0
    is_mock: bool = False
    message: str = ""


def load_image(img_input: str | bytes | Image.Image) -> Image.Image:
    """统一加载图像."""
    if isinstance(img_input, Image.Image):
        return img_input
    elif isinstance(img_input, bytes):
        return Image.open(io.BytesIO(img_input)).convert("RGB")
    else:
        return Image.open(img_input).convert("RGB")


def template_match_ncc(template: np.ndarray, target: np.ndarray) -> float:
    """归一化互相关 (Normalized Cross-Correlation) 模板匹配.

    Args:
        template: 模板灰度图 (H_t x W_t)
        target: 目标灰度图 (H_s x W_s, must be >= template)

    Returns:
        NCC 系数 [-1, 1]，1 表示完美匹配.
    """
    Ht, Wt = template.shape
    Hs, Ws = target.shape

    if Hs < Ht or Ws < Wt:
        return -1.0

    # 计算模板的统计量
    t_mean = template.mean()
    t_std = template.std()
    if t_std < 1e-8:
        return -1.0  # 模板方差过小，无效

    t_norm = template - t_mean

    best_ncc = -1.0

    # 滑动窗口
    for y in range(Hs - Ht + 1):
        for x in range(Ws - Wt + 1):
            window = target[y:y + Ht, x:x + Wt]
            w_mean = window.mean()
            w_std = window.std()
            if w_std < 1e-8:
                continue

            w_norm = window - w_mean
            ncc = np.sum(t_norm * w_norm) / (t_std * w_std * Ht * Wt)
            if ncc > best_ncc:
                best_ncc = ncc

    return best_ncc


def multi_scale_template_match(
    template: Image.Image,
    target: Image.Image,
    scales: list[float] = None,
    ncc_threshold: float = 0.55,
) -> Optional[LogoMatchResult]:
    """多尺度模板匹配.

    在不同缩放比例下匹配模板，返回最佳结果.

    Args:
        template: Logo 模板图像 (RGB)
        target: 目标搜索图像 (RGB)
        scales: 缩放比例列表，默认 [0.25, 0.5, 0.75, 1.0, 1.5, 2.0]
        ncc_threshold: NCC 阈值 (默认 0.55)

    Returns:
        最佳匹配结果，无匹配则返回 None.
    """
    if scales is None:
        scales = [0.25, 0.5, 0.75, 1.0, 1.5, 2.0]

    template_gray = np.array(template.convert("L"), dtype=np.float64)
    target_gray = np.array(target.convert("L"), dtype=np.float64)

    best_ncc = -1.0
    best_scale = 1.0
    best_location = (0, 0)

    for scale in scales:
        # 缩放模板
        new_w = max(8, int(template.width * scale))
        new_h = max(8, int(template.height * scale))
        scaled_template = np.array(
            template.resize((new_w, new_h), Image.LANCZOS).convert("L"),
            dtype=np.float64,
        )

        if scaled_template.shape[0] > target_gray.shape[0]:
            continue
        if scaled_template.shape[1] > target_gray.shape[1]:
            continue

        # 缩小搜索范围以提高性能: 对大图下采样
        search_img = target_gray
        if target_gray.shape[0] > 600 or target_gray.shape[1] > 600:
            ratio = 600.0 / max(target_gray.shape[0], target_gray.shape[1])
            new_h_s = int(target_gray.shape[0] * ratio)
            new_w_s = int(target_gray.shape[1] * ratio)
            search_img = np.array(
                Image.fromarray(target_gray.astype(np.uint8)).resize(
                    (new_w_s, new_h_s), Image.LANCZOS
                ),
                dtype=np.float64,
            )

        ncc = template_match_ncc(scaled_template, search_img)
        if ncc > best_ncc:
            best_ncc = ncc
            best_scale = scale

    if best_ncc >= ncc_threshold:
        return LogoMatchResult(
            brand_id="",
            brand_name="",
            match_scale=best_scale,
            confidence=min(100.0, max(0.0, (best_ncc + 0.5) * 100.0)),
        )

    return None


def scan_target_for_logos(
    target_path: str,
    templates: list[tuple[str, str, str]],  # [(brand_id, brand_name, logo_path), ...]
    ncc_threshold: float = 0.55,
) -> LogoScanResult:
    """扫描目标图像中是否包含注册的品牌 Logo.

    Args:
        target_path: 待扫描图像路径
        templates: 品牌模板列表 [(brand_id, brand_name, logo_path), ...]
        ncc_threshold: NCC 匹配阈值

    Returns:
        LogoScanResult 包含所有匹配.
    """
    result = LogoScanResult(target_path=target_path)

    if not Path(target_path).exists():
        result.message = f"Target file not found: {target_path}"
        return result

    try:
        target_img = load_image(target_path)
    except Exception as e:
        result.message = f"Failed to load target image: {e}"
        return result

    result.total_brands_checked = len(templates)

    for brand_id, brand_name, logo_path in templates:
        if not logo_path or not Path(logo_path).exists():
            # 模板图像不存在，返回低置信度的标记 (mock data)
            continue

        try:
            template_img = load_image(logo_path)
            match = multi_scale_template_match(
                template_img,
                target_img,
                ncc_threshold=ncc_threshold,
            )
            if match:
                match.brand_id = brand_id
                match.brand_name = brand_name
                result.matches.append(match)
        except Exception:
            continue

    return result


def generate_mock_ecommerce_results(
    brand_name: str,
    platforms: list[str],
) -> list[dict]:
    """生成模拟电商扫描结果 (当无真实数据源时使用).

    结果明确标注 is_mock=True.
    """
    import hashlib
    results = []
    mock_stores = {
        "taobao": [
            ("https://item.taobao.com/mock/item-001.htm", "爆款同款高仿商品 A"),
            ("https://item.taobao.com/mock/item-002.htm", "品牌同款热销商品 B"),
        ],
        "jd": [
            ("https://item.jd.com/mock/100001.html", "品牌风格相似商品 C"),
        ],
        "pinduoduo": [
            ("https://mobile.yangkeduo.com/mock/goods-001.html", f"{brand_name}同款低价商品 D"),
            ("https://mobile.yangkeduo.com/mock/goods-002.html", f"{brand_name}相似商品 E"),
        ],
        "amazon": [
            ("https://amazon.com/mock/dp/B00EXAMPLE1", "Similar Design Product F"),
        ],
    }

    for platform in platforms:
        for url, title in mock_stores.get(platform, []):
            h = hashlib.md5(url.encode()).hexdigest()
            results.append({
                "platform": platform,
                "item_url": url,
                "item_title": title,
                "similarity": 60.0 + (int(h[:2], 16) % 35),
                "found_at": None,  # 将由调用者设置
                "is_mock": True,
            })

    return results
