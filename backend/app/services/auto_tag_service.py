"""自动标签生成 + 搜索建议."""

from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


# 关键词-标签映射
CATEGORY_KEYWORDS = {
    "插画": ["插画", "illustration", "手绘", "绘画", "art"],
    "照片": ["照片", "摄影", "photo", "拍照", "风景"],
    "设计": ["设计", "design", "平面", "UI", "UX", "logo", "海报"],
    "AIGC": ["ai", "生成", "midjourney", "stable diffusion", "dalle"],
    "音频": ["音乐", "歌曲", "音频", "music", "audio", "录音"],
    "视频": ["视频", "video", "短片", "动画", "剪辑"],
    "文档": ["文档", "文章", "小说", "读书", "document"],
    "代码": ["代码", "程序", "code", "算法", "函数"],
    "3D": ["3d", "模型", "blender", "渲染", "model"],
    "表情": ["表情", "meme", "梗图", "贴纸", "sticker"],
}

# 时间标签模板
TIME_PERIODS = [
    (1, "今天"), (3, "近3天"), (7, "本周"),
    (30, "本月"), (90, "本季"), (365, "今年"),
]


def auto_generate_tags(
    file_name: str,
    file_type: str,
    exif_data: Optional[dict] = None,
    created_at: Optional[datetime] = None,
    max_tags: int = 8,
) -> list[str]:
    """基于文件名/类型/EXIF 自动生成建议标签.

    不依赖 AI，使用规则引擎生成.
    """
    tags = set()

    # 1. 文件类型标签
    type_tags = {
        "image": "图片",
        "audio": "音频",
        "video": "视频",
        "document": "文档",
        "design": "设计",
        "code": "代码",
    }
    if file_type in type_tags:
        tags.add(type_tags[file_type])

    # 2. 扩展名标签
    ext = Path(file_name).suffix.lower().lstrip(".")
    ext_map = {"jpg": "JPEG", "jpeg": "JPEG", "png": "PNG", "gif": "GIF",
               "mp4": "MP4", "mp3": "MP3", "pdf": "PDF", "psd": "PSD"}
    if ext in ext_map:
        tags.add(ext_map[ext])
    elif ext:
        tags.add(ext.upper())

    # 3. 文件名关键词匹配
    name_lower = Path(file_name).stem.lower().replace("_", " ").replace("-", " ")
    for category, keywords in CATEGORY_KEYWORDS.items():
        for kw in keywords:
            if kw.lower() in name_lower:
                tags.add(category)

    # 4. EXIF 数据提取
    if exif_data:
        # 相机型号
        if exif_data.get("Model"):
            tags.add("相机拍摄")
        # 地理位置
        if exif_data.get("GPSInfo"):
            tags.add("有定位")

    # 5. 时间标签
    if created_at:
        now = datetime.now(timezone.utc)
        days_ago = (now - created_at).days
        for threshold, label in TIME_PERIODS:
            if days_ago <= threshold:
                tags.add(label)
                break

    # 6. 限定数量
    return list(tags)[:max_tags]


def suggest_tags(
    partial: str,
    existing_tags: Optional[list[str]] = None,
    limit: int = 10,
) -> list[str]:
    """标签智能联想 (输入补全)."""
    partial_lower = partial.lower().strip()
    if not partial_lower:
        return []

    # 收集所有可能的标签
    all_keywords = set()
    for keywords in CATEGORY_KEYWORDS.values():
        all_keywords.update(keywords)

    # 内置常用标签
    common_tags = [
        "原创", "插画", "设计", "AIGC", "摄影", "手绘",
        "角色设计", "场景", "UI", "Logo", "海报", "表情包",
        "视频", "音频", "音乐", "3D", "像素", "概念设计",
        "2024", "2025", "2026", "新年", "春节", "圣诞",
    ]
    all_keywords.update(common_tags)

    # 排除已有标签
    existing = set(existing_tags or [])

    # 匹配
    suggestions = []
    for kw in all_keywords:
        if kw.lower().startswith(partial_lower) or partial_lower in kw.lower():
            if kw not in existing:
                suggestions.append(kw)

    return sorted(suggestions, key=lambda x: len(x))[:limit]
