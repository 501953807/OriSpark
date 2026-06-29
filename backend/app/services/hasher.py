"""文件哈希计算服务 — 大文件优化."""

import hashlib
import os
from pathlib import Path
from typing import Optional, Callable

CHUNK_SIZE = 64 * 1024  # 64KB 分块大小
LARGE_FILE_THRESHOLD = 100 * 1024 * 1024  # 100MB 阈值


def compute_sha256(file_path: str, progress_cb: Optional[Callable[[float], None]] = None) -> str:
    """计算文件 SHA-256 哈希，支持进度回调."""
    sha256 = hashlib.sha256()
    file_size = os.path.getsize(file_path)

    with open(file_path, "rb") as f:
        processed = 0
        while True:
            chunk = f.read(CHUNK_SIZE)
            if not chunk:
                break
            sha256.update(chunk)
            processed += len(chunk)
            if progress_cb and file_size > LARGE_FILE_THRESHOLD:
                progress_cb(processed / file_size * 100)

    return sha256.hexdigest()


def compute_md5(file_path: str) -> str:
    """计算文件 MD5 哈希."""
    md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(CHUNK_SIZE), b""):
            md5.update(chunk)
    return md5.hexdigest()


def verify_hash(file_path: str, expected_hash: str) -> bool:
    """验证文件哈希."""
    actual = compute_sha256(file_path)
    return actual == expected_hash


def is_large_file(file_path: str) -> bool:
    """检查是否为大文件."""
    try:
        return os.path.getsize(file_path) > LARGE_FILE_THRESHOLD
    except OSError:
        return False
