"""P3.2.1: 边缘情况单元测试 — hasher, work_service, certificate_service."""

import io
import os
import tempfile
import pytest
import random


# ====================== Hasher Edge Cases ======================


class TestHasher:
    """hasher 服务的边缘情况测试."""

    def test_compute_sha256_empty_file(self):
        """测试空文件哈希."""
        from app.services.hasher import compute_sha256

        with tempfile.NamedTemporaryFile(delete=False, suffix=".bin") as f:
            f.write(b"")
            path = f.name

        try:
            result = compute_sha256(path)
            # 空文件的 SHA-256
            assert result == "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
            assert len(result) == 64
        finally:
            os.unlink(path)

    def test_compute_sha256_small_file(self):
        """测试小文件哈希."""
        from app.services.hasher import compute_sha256

        with tempfile.NamedTemporaryFile(delete=False, suffix=".bin") as f:
            f.write(b"Hello OriSpark!")
            path = f.name

        try:
            result = compute_sha256(path)
            assert len(result) == 64
            assert result == "2af4bb05095d31ced442834f14553c434d8e9f191279beb3b6b2f631d78b2826"
        finally:
            os.unlink(path)

    def test_compute_sha256_binary_data(self):
        """测试二进制数据哈希."""
        from app.services.hasher import compute_sha256

        data = bytes(range(256)) * 100  # 25.6KB of binary
        with tempfile.NamedTemporaryFile(delete=False, suffix=".bin") as f:
            f.write(data)
            path = f.name

        try:
            result = compute_sha256(path)
            assert len(result) == 64
            # 一致性: 相同内容 = 相同哈希
            result2 = compute_sha256(path)
            assert result == result2
        finally:
            os.unlink(path)

    def test_compute_md5(self):
        """测试 MD5 计算."""
        from app.services.hasher import compute_md5

        with tempfile.NamedTemporaryFile(delete=False, suffix=".bin") as f:
            f.write(b"Test MD5 content")
            path = f.name

        try:
            result = compute_md5(path)
            assert len(result) == 32
            assert result == "94af94e04ff4a68c78c765d7175d0cb1"
        finally:
            os.unlink(path)

    def test_verify_hash_match(self):
        """测试哈希验证 — 匹配."""
        from app.services.hasher import compute_sha256, verify_hash

        with tempfile.NamedTemporaryFile(delete=False, suffix=".bin") as f:
            f.write(b"verify me")
            path = f.name

        try:
            sha = compute_sha256(path)
            assert verify_hash(path, sha) is True
        finally:
            os.unlink(path)

    def test_verify_hash_mismatch(self):
        """测试哈希验证 — 不匹配."""
        from app.services.hasher import verify_hash

        with tempfile.NamedTemporaryFile(delete=False, suffix=".bin") as f:
            f.write(b"original content")
            path = f.name

        try:
            assert verify_hash(path, "a" * 64) is False
        finally:
            os.unlink(path)

    def test_is_large_file_small(self):
        """测试大文件检测 — 小文件."""
        from app.services.hasher import is_large_file

        with tempfile.NamedTemporaryFile(delete=False, suffix=".bin") as f:
            f.write(b"small")
            path = f.name

        try:
            assert is_large_file(path) is False
        finally:
            os.unlink(path)

    def test_is_large_file_nonexistent(self):
        """测试大文件检测 — 文件不存在."""
        from app.services.hasher import is_large_file

        assert is_large_file("/nonexistent/file/path.xyz") is False


# ====================== Work Service Edge Cases ======================


class TestWorkService:
    """work_service 的边缘情况测试."""

    def test_detect_file_type_all(self):
        """测试所有文件类型检测."""
        from app.services.work_service import detect_file_type

        assert detect_file_type("jpg") == "image"
        assert detect_file_type("JPEG") == "image"
        assert detect_file_type("png") == "image"
        assert detect_file_type("webp") == "image"
        assert detect_file_type("gif") == "image"
        assert detect_file_type("svg") == "image"
        assert detect_file_type("bmp") == "image"
        assert detect_file_type("tiff") == "image"

        assert detect_file_type("mp3") == "audio"
        assert detect_file_type("wav") == "audio"
        assert detect_file_type("flac") == "audio"
        assert detect_file_type("ogg") == "audio"
        assert detect_file_type("aac") == "audio"

        assert detect_file_type("mp4") == "video"
        assert detect_file_type("mov") == "video"
        assert detect_file_type("webm") == "video"
        assert detect_file_type("avi") == "video"

        assert detect_file_type("pdf") == "document"
        assert detect_file_type("docx") == "document"
        assert detect_file_type("txt") == "document"
        assert detect_file_type("md") == "document"

        assert detect_file_type("psd") == "design"
        assert detect_file_type("ai") == "design"
        assert detect_file_type("fig") == "design"

        assert detect_file_type("py") == "code"
        assert detect_file_type("js") == "code"
        assert detect_file_type("ts") == "code"
        assert detect_file_type("html") == "code"
        assert detect_file_type("json") == "code"

    def test_detect_file_type_unknown(self):
        """测试未知扩展名."""
        from app.services.work_service import detect_file_type

        assert detect_file_type("xyz123") == "other"
        assert detect_file_type("unknown_ext") == "other"
        assert detect_file_type("") == "other"

    def test_get_image_dimensions(self):
        """测试获取图片尺寸."""
        from app.services.work_service import get_image_dimensions
        from PIL import Image

        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
            img = Image.new("RGB", (300, 200), color=(100, 150, 200))
            img.save(f.name)
            path = f.name

        try:
            w, h = get_image_dimensions(path)
            assert w == 300
            assert h == 200
        finally:
            os.unlink(path)

    def test_get_image_dimensions_nonexistent(self):
        """测试图片尺寸 — 文件不存在."""
        from app.services.work_service import get_image_dimensions
        w, h = get_image_dimensions("/nonexistent/image.png")
        assert w is None
        assert h is None


class TestCertificateService:
    """certificate_service 的边缘情况测试."""

    def test_format_file_size(self):
        """测试文件大小格式化."""
        from app.services.certificate_service import format_file_size

        assert format_file_size(0) == "0 B"
        assert format_file_size(512) == "512 B"
        assert format_file_size(1024) == "1.0 KB"
        assert format_file_size(1536) == "1.5 KB"
        assert format_file_size(1024 * 1024) == "1.0 MB"
        assert format_file_size(1536 * 1024) == "1.5 MB"
        assert format_file_size(1024 * 1024 * 1024) == "1.00 GB"
        assert format_file_size(1536 * 1024 * 1024) == "1.50 GB"

    def test_format_file_size_large(self):
        """测试大文件大小格式化."""
        from app.services.certificate_service import format_file_size

        assert format_file_size(5 * 1024 * 1024 * 1024) == "5.00 GB"
        assert format_file_size(1024 * 1024 * 1024 * 1024) == "1024.00 GB"


# ====================== Cache Service Tests ======================


class TestCacheService:
    """cache 服务的单元测试."""

    def test_set_and_get(self):
        """测试基本设置和获取."""
        from app.services.cache import TTLCache

        cache = TTLCache(max_size=10, default_ttl=60)
        cache.set("key1", "value1")
        assert cache.get("key1") == "value1"

    def test_ttl_expiry(self):
        """测试 TTL 过期."""
        import time
        from app.services.cache import TTLCache

        cache = TTLCache(max_size=10, default_ttl=0)  # 0 TTL — 立即过期
        cache.set("key1", "value1")
        time.sleep(0.01)
        assert cache.get("key1") is None

    def test_missing_key(self):
        """测试不存在的键."""
        from app.services.cache import TTLCache

        cache = TTLCache(max_size=10, default_ttl=60)
        assert cache.get("nonexistent") is None

    def test_delete(self):
        """测试删除键."""
        from app.services.cache import TTLCache

        cache = TTLCache(max_size=10, default_ttl=60)
        cache.set("key1", "value1")
        cache.delete("key1")
        assert cache.get("key1") is None

    def test_clear(self):
        """测试清空."""
        from app.services.cache import TTLCache

        cache = TTLCache(max_size=10, default_ttl=60)
        cache.set("k1", "v1")
        cache.set("k2", "v2")
        cache.clear()
        assert cache.get("k1") is None
        assert cache.get("k2") is None

    def test_max_size_eviction(self):
        """测试超过最大容量时的驱逐."""
        from app.services.cache import TTLCache

        cache = TTLCache(max_size=3, default_ttl=3600)
        cache.set("k1", "v1")
        cache.set("k2", "v2")
        cache.set("k3", "v3")
        cache.set("k4", "v4")  # 应驱逐 k1

        assert cache.get("k1") is None
        assert cache.get("k4") == "v4"
        assert len(cache) <= 3

    def test_prune_expired(self):
        """测试清理过期条目."""
        from app.services.cache import TTLCache

        cache = TTLCache(max_size=10, default_ttl=0)
        cache.set("k1", "v1")
        cache.set("k2", "v2")
        import time
        time.sleep(0.01)

        removed = cache.prune_expired()
        assert removed == 2
        assert len(cache) == 0

    def test_cached_decorator(self):
        """测试 cached 装饰器."""
        from app.services.cache import cached, get_global_cache

        get_global_cache().clear()

        call_count = [0]

        @cached(ttl=60, key_prefix="test")
        def expensive_func(x, y=0):
            call_count[0] += 1
            return x + y

        assert expensive_func(1, y=2) == 3
        assert call_count[0] == 1

        # 第二次调用应命中缓存
        assert expensive_func(1, y=2) == 3
        assert call_count[0] == 1

        # 不同参数应计算
        assert expensive_func(2, y=3) == 5
        assert call_count[0] == 2

        get_global_cache().clear()
