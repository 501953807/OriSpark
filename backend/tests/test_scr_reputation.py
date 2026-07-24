"""SCR 分布式信誉系统测试."""

from decimal import Decimal
from unittest.mock import patch

import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.orm import Session

from app.models.scr_reputation import SCRScore, SCRHistory
from app.services.scr_reputation_service import (
    get_or_create_score,
    update_score,
    get_leaderboard,
    _compute_rating,
    SCORE_DELTA,
)


class TestGetOrCreateScore:
    def test_returns_existing_score(self, db_session: Session):
        score = SCRScore(
            user_id="test-user-001",
            overall_score=Decimal("75.00"),
            rating_level="silver",
        )
        db_session.add(score)
        db_session.commit()

        result = get_or_create_score(db_session, "test-user-001")
        assert result.id == score.id
        assert float(result.overall_score) == 75.0

    def test_creates_new_score(self, db_session: Session):
        result = get_or_create_score(db_session, "new-user-001")
        assert result.user_id == "new-user-001"
        assert float(result.overall_score) == 50.0
        assert result.rating_level == "starter"
        assert result.fulfillment_count == 0

    def test_different_users_get_separate_scores(self, db_session: Session):
        s1 = get_or_create_score(db_session, "user-a")
        s2 = get_or_create_score(db_session, "user-b")
        assert s1.id != s2.id
        assert s1.user_id == "user-a"
        assert s2.user_id == "user-b"


class TestUpdateScore:
    def test_fulfillment_increases_score(self, db_session: Session):
        score = get_or_create_score(db_session, "test-user-001")
        updated = update_score(db_session, "test-user-001", reason="fulfillment")
        assert float(updated.overall_score) == 55.0
        assert updated.rating_level == "bronze"
        assert updated.fulfillment_count == 1

        # Verify history record
        hist = db_session.query(SCRHistory).filter(
            SCRHistory.user_id == "test-user-001"
        ).first()
        assert hist is not None
        assert hist.reason == "fulfillment"
        assert float(hist.score_delta) == 5.0

    def test_default_decreases_score(self, db_session: Session):
        score = get_or_create_score(db_session, "test-user-001")
        updated = update_score(db_session, "test-user-001", reason="default")
        assert float(updated.overall_score) == 40.0
        assert updated.default_count == 1

    def test_late_review_small_penalty(self, db_session: Session):
        score = get_or_create_score(db_session, "test-user-001")
        updated = update_score(db_session, "test-user-001", reason="late_review")
        assert float(updated.overall_score) == 47.0
        assert updated.late_review_count == 1

    def test_complaint_penalty(self, db_session: Session):
        score = get_or_create_score(db_session, "test-user-001")
        updated = update_score(db_session, "test-user-001", reason="complaint")
        assert float(updated.overall_score) == 45.0
        assert updated.complaint_count == 1

    def test_cleared_restores_points(self, db_session: Session):
        score = get_or_create_score(db_session, "test-user-001")
        updated = update_score(db_session, "test-user-001", reason="cleared")
        assert float(updated.overall_score) == 53.0
        assert updated.cleared_count == 1

    def test_score_clamped_to_100(self, db_session: Session):
        # Start at 98, fulfillment adds 5 → should cap at 100
        existing = SCRScore(user_id="clamp-user", overall_score=Decimal("98.00"))
        db_session.add(existing)
        db_session.commit()

        updated = update_score(db_session, "clamp-user", reason="fulfillment")
        assert float(updated.overall_score) == 100.0

    def test_score_clamped_to_0(self, db_session: Session):
        existing = SCRScore(user_id="low-user", overall_score=Decimal("3.00"))
        db_session.add(existing)
        db_session.commit()

        updated = update_score(db_session, "low-user", reason="default")
        assert float(updated.overall_score) == 0.0

    def test_rating_level_changes(self, db_session: Session):
        """Test rating transitions through multiple events."""
        user_id = "rating-test-user"
        score = get_or_create_score(db_session, user_id)

        # starter → silver (50 + 5*5 = 75, 75 is silver boundary)
        for _ in range(5):
            update_score(db_session, user_id, reason="fulfillment")
        score = db_session.query(SCRScore).filter(SCRScore.user_id == user_id).first()
        assert score.rating_level == "silver"

        # silver → gold (75 + 3*5 = 90)
        for _ in range(3):
            update_score(db_session, user_id, reason="fulfillment")
        score = db_session.query(SCRScore).filter(SCRScore.user_id == user_id).first()
        assert score.rating_level == "gold"

    def test_unknown_reason_no_change(self, db_session: Session):
        score = get_or_create_score(db_session, "test-user-001")
        initial_score = float(score.overall_score)
        updated = update_score(db_session, "test-user-001", reason="unknown_event")
        assert float(updated.overall_score) == initial_score

    def test_history_records_all_events(self, db_session: Session):
        user_id = "history-test-user"
        get_or_create_score(db_session, user_id)

        update_score(db_session, user_id, reason="fulfillment")
        update_score(db_session, user_id, reason="default")
        update_score(db_session, user_id, reason="late_review")

        records = db_session.query(SCRHistory).filter(
            SCRHistory.user_id == user_id
        ).order_by(SCRHistory.created_at).all()
        assert len(records) == 3
        assert records[0].reason == "fulfillment"
        assert float(records[0].score_delta) == 5.0
        assert records[1].reason == "default"
        assert float(records[1].score_delta) == -10.0
        assert records[2].reason == "late_review"
        assert float(records[2].score_delta) == -3.0


class TestComputeRating:
    def test_gold_range(self):
        assert _compute_rating(90.0) == "gold"
        assert _compute_rating(95.0) == "gold"
        assert _compute_rating(100.0) == "gold"

    def test_silver_range(self):
        assert _compute_rating(75.0) == "silver"
        assert _compute_rating(85.0) == "silver"

    def test_bronze_range(self):
        assert _compute_rating(55.0) == "bronze"
        assert _compute_rating(65.0) == "bronze"

    def test_starter_range(self):
        assert _compute_rating(0.0) == "starter"
        assert _compute_rating(50.0) == "starter"
        assert _compute_rating(54.9) == "starter"


class TestLeaderboard:
    def test_leaderboard_sorted_by_score(self, db_session: Session):
        users = ["u1", "u2", "u3"]
        scores = [Decimal("90.00"), Decimal("50.00"), Decimal("75.00")]
        for uid, sc in zip(users, scores):
            s = SCRScore(user_id=uid, overall_score=sc, rating_level="gold" if sc >= 90 else "starter")
            db_session.add(s)
        db_session.commit()

        result = get_leaderboard(db_session, limit=50)
        assert len(result) == 3
        assert float(result[0].overall_score) == 90.0
        assert float(result[1].overall_score) == 75.0
        assert float(result[2].overall_score) == 50.0

    def test_leaderboard_respects_limit(self, db_session: Session):
        for i in range(10):
            s = SCRScore(user_id=f"lb-user-{i}", overall_score=Decimal("50.00"))
            db_session.add(s)
        db_session.commit()

        result = get_leaderboard(db_session, limit=5)
        assert len(result) == 5
