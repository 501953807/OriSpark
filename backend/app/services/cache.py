"""TTL 缓存服务 — 为昂贵 API 调用/重复查询提供轻量级内存缓存."""

import time
import threading
from typing import Any, Callable, Dict, Optional, Tuple
from functools import wraps


class TTLCache:
    """简单的 TTL 内存缓存，支持最大容量和时间过期."""

    def __init__(self, max_size: int = 256, default_ttl: int = 60):
        """
        Args:
            max_size: 最大缓存条目数
            default_ttl: 默认 TTL (秒)
        """
        self._cache: Dict[str, Tuple[Any, float]] = {}
        self._lock = threading.Lock()
        self.max_size = max_size
        self.default_ttl = default_ttl

    def get(self, key: str) -> Optional[Any]:
        """获取缓存值，过期返回 None."""
        with self._lock:
            entry = self._cache.get(key)
            if entry is None:
                return None
            value, expiry = entry
            if time.monotonic() > expiry:
                del self._cache[key]
                return None
            return value

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """设置缓存值."""
        ttl_seconds = ttl if ttl is not None else self.default_ttl
        expiry = time.monotonic() + ttl_seconds
        with self._lock:
            # 驱逐最旧条目 (简单 LRU: 超过 max_size 删除第一个)
            while len(self._cache) >= self.max_size:
                oldest_key = next(iter(self._cache))
                del self._cache[oldest_key]
            self._cache[key] = (value, expiry)

    def delete(self, key: str) -> None:
        """删除缓存条目."""
        with self._lock:
            self._cache.pop(key, None)

    def clear(self) -> None:
        """清空缓存."""
        with self._lock:
            self._cache.clear()

    def prune_expired(self) -> int:
        """清理过期条目，返回清除数量."""
        now = time.monotonic()
        removed = 0
        with self._lock:
            expired = [k for k, (_, exp) in self._cache.items() if now > exp]
            for k in expired:
                del self._cache[k]
            removed = len(expired)
        return removed

    def __len__(self) -> int:
        return len(self._cache)


# 全局单例
_global_cache = TTLCache(max_size=128, default_ttl=300)


def cached(ttl: int = 60, key_prefix: str = ""):
    """
    TTL 缓存装饰器。

    用法:
        @cached(ttl=120, key_prefix="search")
        def expensive_query(query: str) -> list: ...

    缓存键由 key_prefix + 函数参数值拼接生成。
    """

    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # 构建缓存键
            parts = [key_prefix or func.__name__]
            parts.extend(str(a) for a in args)
            parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
            cache_key = ":".join(parts)

            result = _global_cache.get(cache_key)
            if result is not None:
                return result

            result = func(*args, **kwargs)
            _global_cache.set(cache_key, result, ttl=ttl)
            return result

        wrapper.cache_clear = lambda: _global_cache.clear()
        return wrapper

    return decorator


def get_global_cache() -> TTLCache:
    """获取全局缓存实例."""
    return _global_cache
