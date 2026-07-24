"""SCR 分布式信誉系统测试."""

import pytest
import uuid

from app.models.scr import SCRRating, SCRBehavior, SCRTrustLink
from app.services.scr_service import SCRRatingService


def _uid(prefix="scr_"):
    return f"{prefix}{uuid.uuid4().hex[:12]}"


class TestCreateRating:
    def test_create_rating(self, db_session):
        rating = SCRRatingService.create_rating(
            db=db_session,
            user_id=_uid("user_"),
            rater_id=_uid("rater_"),
            rating_type="overall",
            initial_score=0.0,
            min_consensus=3,
        )
        assert rating.id is not None
        assert rating.user_id is not None
        assert rating.status == "active"
        assert rating.tier == "draft"
        assert rating.raw_score == 0.0
        assert rating.confidence == 0.0
        assert rating.consensus_count == 0

    def test_get_rating(self, db_session):
        rating = SCRRatingService.create_rating(
            db=db_session,
            user_id=_uid("user_"),
            rater_id=_uid("rater_"),
        )
        found = SCRRatingService.get_rating(db_session, rating.id)
        assert found is not None
        assert found.id == rating.id

    def test_get_rating_nonexistent_returns_none(self, db_session):
        result = SCRRatingService.get_rating(db_session, "nonexistent")
        assert result is None

    def test_get_ratings_by_user(self, db_session):
        user_id = _uid("user_")
        for i in range(3):
            SCRRatingService.create_rating(
                db=db_session,
                user_id=user_id,
                rater_id=_uid("rater_"),
            )
        ratings = SCRRatingService.get_ratings_by_user(db_session, user_id)
        assert len(ratings) >= 3


class TestAddBehavior:
    def test_add_behavior_updates_score(self, db_session):
        rating = SCRRatingService.create_rating(
            db=db_session,
            user_id=_uid("user_"),
            rater_id=_uid("rater_"),
        )
        new_rating, behavior = SCRRatingService.add_behavior(
            db=db_session,
            rating_id=rating.id,
            behavior_type="work_submitted",
            score_delta=2.0,
        )
        assert new_rating.raw_score == 2.0
        assert new_rating.consensus_count == 1
        assert behavior.behavior_type == "work_submitted"

    def test_add_behavior_exceeds_min_consensus(self, db_session):
        rating = SCRRatingService.create_rating(
            db=db_session,
            user_id=_uid("user_"),
            rater_id=_uid("rater_"),
            min_consensus=3,
        )
        for i in range(3):
            rating, _ = SCRRatingService.add_behavior(
                db=db_session,
                rating_id=rating.id,
                behavior_type="work_approved",
                score_delta=5.0,
            )
        assert rating.consensus_count == 3
        assert rating.tier == "confirmed"
        assert rating.confidence == 1.0

    def test_add_behavior_to_nonexistent_raises(self, db_session):
        with pytest.raises(ValueError):
            SCRRatingService.add_behavior(
                db=db_session,
                rating_id="nonexistent",
                behavior_type="test",
                score_delta=1.0,
            )

    def test_apply_scr_behavior_clamps_score(self, db_session):
        rating = SCRRatingService.create_rating(
            db=db_session,
            user_id=_uid("user_"),
            rater_id=_uid("rater_"),
        )
        # Add enough negative behaviors to go below 0
        for _ in range(10):
            rating, _ = SCRRatingService.add_behavior(
                db=db_session,
                rating_id=rating.id,
                behavior_type="negative_feedback",
                score_delta=-10.0,
            )
        assert rating.raw_score >= 0.0
        assert rating.raw_score <= 100.0


class TestTrustLinks:
    def _create_rating(self, db_session):
        return SCRRatingService.create_rating(
            db=db_session,
            user_id=_uid("user_"),
            rater_id=_uid("rater_"),
        )

    def test_update_trust_link_creates(self, db_session):
        rating = self._create_rating(db_session)
        link = SCRRatingService.update_trust_link(
            db=db_session,
            source_user_id=_uid("u_"),
            target_user_id=_uid("u_"),
            trust_score=0.8,
            weight=1.0,
            rating_id=rating.id,
        )
        assert link.trust_score == 0.8
        assert link.weight == 1.0
        assert link.rating_id == rating.id

    def test_update_trust_link_upserts(self, db_session):
        rating = self._create_rating(db_session)
        source = _uid("u_")
        target = _uid("u_")
        link1 = SCRRatingService.update_trust_link(
            db=db_session,
            source_user_id=source,
            target_user_id=target,
            trust_score=0.5,
            rating_id=rating.id,
        )
        link2 = SCRRatingService.update_trust_link(
            db=db_session,
            source_user_id=source,
            target_user_id=target,
            trust_score=0.9,
            rating_id=rating.id,
        )
        assert link1.id == link2.id
        assert link2.trust_score == 0.9

    def test_get_trust_links(self, db_session):
        rating = self._create_rating(db_session)
        user_id = _uid("u_")
        for i in range(2):
            SCRRatingService.update_trust_link(
                db=db_session,
                source_user_id=user_id,
                target_user_id=_uid("u_"),
                trust_score=0.5 + i * 0.1,
                rating_id=rating.id,
            )
        links = SCRRatingService.get_trust_links(db_session, user_id)
        assert len(links) >= 2


class TestDistributedScore:
    def test_calculate_distributed_score_no_ratings(self, db_session):
        result = SCRRatingService.calculate_distributed_score(db_session, _uid("u_"))
        assert result["total_score"] == 0.0
        assert result["confidence"] == 0.0
        assert result["tier"] == "unrated"
        assert result["rating_count"] == 0

    def test_calculate_distributed_score_with_ratings(self, db_session):
        user_id = _uid("u_")
        for i in range(3):
            rating = SCRRatingService.create_rating(
                db=db_session,
                user_id=user_id,
                rater_id=_uid("rater_"),
                initial_score=80.0,
            )
            rating, _ = SCRRatingService.add_behavior(
                db=db_session,
                rating_id=rating.id,
                behavior_type="work_approved",
                score_delta=5.0,
            )
        result = SCRRatingService.calculate_distributed_score(db_session, user_id)
        assert result["rating_count"] >= 3
        assert result["total_score"] > 0.0


class TestRevokeSuspend:
    def test_revoke_rating(self, db_session):
        rating = SCRRatingService.create_rating(
            db=db_session,
            user_id=_uid("user_"),
            rater_id=_uid("rater_"),
        )
        revoked = SCRRatingService.revoke_rating(db_session, rating.id)
        assert revoked.status == "revoked"

    def test_suspend_rating(self, db_session):
        rating = SCRRatingService.create_rating(
            db=db_session,
            user_id=_uid("user_"),
            rater_id=_uid("rater_"),
        )
        suspended = SCRRatingService.suspend_rating(db_session, rating.id)
        assert suspended.status == "suspended"

    def test_revoke_nonexistent_raises(self, db_session):
        with pytest.raises(ValueError):
            SCRRatingService.revoke_rating(db_session, "nonexistent")

    def test_suspend_nonexistent_raises(self, db_session):
        with pytest.raises(ValueError):
            SCRRatingService.suspend_rating(db_session, "nonexistent")


class TestEndToEndWorkflow:
    def test_full_workflow(self, db_session):
        # Create rating
        rating = SCRRatingService.create_rating(
            db=db_session,
            user_id=_uid("user_"),
            rater_id=_uid("rater_"),
            min_consensus=3,
        )
        assert rating.tier == "draft"

        # Add behaviors to build consensus
        for i in range(3):
            rating, _ = SCRRatingService.add_behavior(
                db=db_session,
                rating_id=rating.id,
                behavior_type="work_approved",
                score_delta=5.0,
            )
        assert rating.tier == "confirmed"
        assert rating.confidence == 1.0

        # Calculate distributed score
        score = SCRRatingService.calculate_distributed_score(db_session, rating.user_id)
        assert score["rating_count"] >= 1

        # Update trust link
        link = SCRRatingService.update_trust_link(
            db=db_session,
            source_user_id=rating.user_id,
            target_user_id=_uid("target_"),
            trust_score=0.9,
            rating_id=rating.id,
        )
        assert link.trust_score == 0.9

        # Get trust links
        links = SCRRatingService.get_trust_links(db_session, rating.user_id)
        assert len(links) >= 1

        # Suspend and revoke
        suspended = SCRRatingService.suspend_rating(db_session, rating.id)
        assert suspended.status == "suspended"

        revoked = SCRRatingService.revoke_rating(db_session, rating.id)
        assert revoked.status == "revoked"
