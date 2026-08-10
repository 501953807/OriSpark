"""WebSocket 广播限流器 — 同类型事件合并去重，最大 10 次/秒."""

import time
from collections import defaultdict
from typing import Dict, Optional


class BroadcastThrottle:
    """基于滑动窗口的广播限流器.

    限制同类型事件在指定时间窗口内的最大发送次数，超出时丢弃。
    默认: 10 次/秒 per event type per client.
    """

    def __init__(
        self,
        max_events: int = 10,
        window_seconds: float = 1.0,
    ):
        self.max_events = max_events
        self.window_seconds = window_seconds
        self._history: Dict[str, list[float]] = defaultdict(list)

    def allow(self, event_key: str) -> bool:
        """检查是否允许发送事件，返回 True 表示允许."""
        now = time.monotonic()
        window_start = now - self.window_seconds
        history = self._history[event_key]
        # 清理过期记录
        self._history[event_key] = [t for t in history if t > window_start]
        if len(self._history[event_key]) >= self.max_events:
            return False
        self._history[event_key].append(now)
        return True

    def reset(self, event_key: Optional[str] = None) -> None:
        """重置限流状态，不传 key 则清空全部."""
        if event_key is not None:
            self._history.pop(event_key, None)
        else:
            self._history.clear()


# 全局单例
_throttle = BroadcastThrottle(max_events=10, window_seconds=1.0)


def get_throttle() -> BroadcastThrottle:
    return _throttle
