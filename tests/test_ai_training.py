import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

import pytest
from app.services.ai_training_service import generate_exclude_clause, upsert_ai_license
from app.models.ai_training_license import CCProtocol


def test_generate_exclude_clause_cc0():
    clause = generate_exclude_clause(CCProtocol.CC0)
    assert "AI Training Exclusion" in clause
    assert "Machine Learning" in clause


def test_generate_exclude_clause_cc_by_nc():
    clause = generate_exclude_clause(CCProtocol.CC_BY_NC)
    assert "AI Training Exclusion" in clause
    assert "CC-BY-NC already restricts commercial use" in clause


def test_generate_exclude_clause_other():
    # CC-BY has no special exclusion needed (non-commercial already implied)
    clause = generate_exclude_clause(CCProtocol.CC_BY)
    assert clause == ""
