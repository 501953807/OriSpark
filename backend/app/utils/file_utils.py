"""文件处理工具."""

import os
import shutil
from pathlib import Path
from typing import Optional


def safe_filename(filename: str) -> str:
    """生成安全的文件名."""
    # 移除危险字符
    safe = "".join(c for c in filename if c.isalnum() or c in "._- ()[]")
    return safe or "unnamed"


def get_unique_path(base_dir: Path, filename: str) -> Path:
    """生成唯一文件路径，避免覆盖."""
    base_dir = Path(base_dir)
    base_dir.mkdir(parents=True, exist_ok=True)

    stem = Path(filename).stem
    ext = Path(filename).suffix
    path = base_dir / filename
    counter = 1

    while path.exists():
        path = base_dir / f"{stem}_{counter}{ext}"
        counter += 1

    return path


def copy_file_safe(src: str, dst_dir: str) -> Optional[str]:
    """安全复制文件到目标目录."""
    src_path = Path(src)
    if not src_path.exists():
        return None

    dst_path = get_unique_path(Path(dst_dir), src_path.name)
    shutil.copy2(src_path, dst_path)
    return str(dst_path)


def delete_file_safe(path: str) -> bool:
    """安全删除文件."""
    try:
        os.remove(path)
        return True
    except OSError:
        return False


def get_file_size_formatted(file_path: str) -> str:
    """获取格式化的文件大小."""
    size = os.path.getsize(file_path)
    if size < 1024:
        return f"{size} B"
    elif size < 1024 * 1024:
        return f"{size / 1024:.1f} KB"
    elif size < 1024 * 1024 * 1024:
        return f"{size / (1024 * 1024):.1f} MB"
    return f"{size / (1024 * 1024 * 1024):.2f} GB"
