import os
import sys
from pathlib import Path

# Ensure backend package is importable
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

import pytest
from app.services.certification_service import compute_sha256, certify_single, batch_certify


def test_compute_sha256(sample_work_file):
    """SHA-256 of known content has length 64 and matches expected."""
    h = compute_sha256(sample_work_file)
    assert len(h) == 64
    # 'hello world for sha256 test' → 15f2655a...
    assert h == "15f2655a72630de3ee8d389c534c14856cd9550ee1b89396bba66e8fcde89f65"


def test_batch_certify_limits():
    """Batch > 10000 raises ValueError."""
    with pytest.raises(ValueError, match="不能超过10,000件"):
        batch_certify(None, ["id"] * 10001)
