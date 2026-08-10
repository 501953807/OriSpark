import time
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from app.services.websocket_throttle import BroadcastThrottle

def test_allow_within_limit():
    t = BroadcastThrottle(max_events=5, window_seconds=1.0)
    assert t.allow("test") is True
    assert t.allow("test") is True
    assert t.allow("test") is True
    assert t.allow("test") is True
    assert t.allow("test") is True

def test_deny_after_limit():
    t = BroadcastThrottle(max_events=3, window_seconds=1.0)
    for _ in range(3):
        t.allow("test")
    assert t.allow("test") is False

def test_different_events_independent():
    t = BroadcastThrottle(max_events=2, window_seconds=1.0)
    t.allow("event_a")
    t.allow("event_a")
    assert t.allow("event_a") is False
    assert t.allow("event_b") is True

def test_reset_specific():
    t = BroadcastThrottle(max_events=2, window_seconds=1.0)
    t.allow("test")
    t.allow("test")
    assert t.allow("test") is False
    t.reset("test")
    assert t.allow("test") is True

def test_reset_all():
    t = BroadcastThrottle(max_events=2, window_seconds=1.0)
    t.allow("a")
    t.allow("b")
    t.reset()
    assert t.allow("a") is True
    assert t.allow("b") is True

def test_window_expiration():
    t = BroadcastThrottle(max_events=2, window_seconds=0.1)
    t.allow("test")
    t.allow("test")
    assert t.allow("test") is False
    time.sleep(0.15)
    assert t.allow("test") is True
