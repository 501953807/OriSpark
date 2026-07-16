"""Tests for copyright registration guide module."""

from unittest.mock import MagicMock, PropertyMock

import pytest

from app.services.copyright_guide_service import (
    get_or_create_guides,
    get_guide,
    list_registrations,
    create_registration,
    get_registration_summary,
    DEFAULT_GUIDES,
)


class TestDefaultGuides:
    """Test that default guides are properly seeded."""

    def test_default_guides_exist(self):
        assert len(DEFAULT_GUIDES) == 4

    def test_default_guide_work_types(self):
        work_types = {g["work_type"] for g in DEFAULT_GUIDES}
        assert work_types == {"illustration", "photo", "music", "writing"}

    def test_default_guide_has_steps(self):
        for guide in DEFAULT_GUIDES:
            assert len(guide["steps"]) == 5
            for step in guide["steps"]:
                assert "step" in step
                assert "title" in step
                assert "description" in step
                assert "required_files" in step

    def test_default_guide_estimated_days(self):
        for guide in DEFAULT_GUIDES:
            assert isinstance(guide["estimated_days"], int)
            assert guide["estimated_days"] > 0

    def test_default_guide_estimated_fee(self):
        for guide in DEFAULT_GUIDES:
            assert isinstance(guide["estimated_fee_yuan"], (int, float))
            assert guide["estimated_fee_yuan"] > 0


class TestGetGuides:
    """Test guide retrieval functions."""

    def test_get_or_create_guides_seeds_missing(self):
        db = MagicMock()
        db.query = MagicMock()

        # First query returns empty (guide not found)
        db.query.return_value.filter.return_value.first = MagicMock(return_value=None)
        # Second query returns all guides
        db.query.return_value.filter.return_value.all = MagicMock(return_value=[])

        result = get_or_create_guides(db)
        assert isinstance(result, list)
        # Should have called add and commit to seed guides
        calls = db.add.call_count
        assert calls >= 1

    def test_get_guide_returns_existing(self):
        db = MagicMock()
        mock_guide = MagicMock(work_type="illustration", is_active=True)
        db.query.return_value.filter.return_value.first = MagicMock(return_value=mock_guide)

        result = get_guide(db, "illustration")
        assert result == mock_guide

    def test_get_guide_returns_none_for_unknown(self):
        db = MagicMock()
        db.query.return_value.filter.return_value.first = MagicMock(return_value=None)

        result = get_guide(db, "unknown_type")
        assert result is None


class TestRegistrationCRUD:
    """Test registration CRUD operations."""

    @pytest.fixture
    def mock_db(self):
        db = MagicMock()
        db.add = MagicMock()
        db.commit = MagicMock()
        db.flush = MagicMock()
        return db

    def test_create_registration(self, mock_db):
        """SQLAlchemy column defaults fire on flush, not __init__, so mock needs help."""
        from app.models.copyright_guide import GuideRegistration

        original_init = GuideRegistration.__init__

        def patched_init(self, **kwargs):
            original_init(self, **kwargs)
            if self.status is None:
                self.status = "draft"

        try:
            GuideRegistration.__init__ = patched_init
            result = create_registration(
                mock_db, user_id="u1", title="Test Work", work_type="illustration"
            )
            assert result is not None
            assert result["status"] == "draft"
            mock_db.add.assert_called_once()
            mock_db.flush.assert_called_once()
        finally:
            GuideRegistration.__init__ = original_init

    def test_list_registrations_empty(self, mock_db):
        mock_db.query.return_value.filter.return_value.order_by.return_value.all = MagicMock(
            return_value=[]
        )
        result = list_registrations(mock_db, user_id="u1")
        assert result == []

    def test_update_registration_success(self, mock_db):
        from app.services.copyright_guide_service import update_registration

        mock_reg = MagicMock()
        mock_db.query.return_value.filter.return_value.first = MagicMock(return_value=mock_reg)

        result = update_registration(mock_db, "u1", "r1", {"status": "submitted"})
        assert result is True

    def test_update_registration_not_found(self, mock_db):
        from app.services.copyright_guide_service import update_registration

        mock_db.query.return_value.filter.return_value.first = MagicMock(return_value=None)

        result = update_registration(mock_db, "u1", "r1", {"status": "submitted"})
        assert result is False


class TestRegistrationSummary:
    """Test registration summary aggregation."""

    def test_summary_empty(self):
        db = MagicMock()
        db.query.return_value.filter.return_value.all = MagicMock(return_value=[])

        summary = get_registration_summary(db, user_id="u1")
        assert summary["total"] == 0
        assert summary["total_fees_yuan"] == 0

    def test_summary_with_multiple_registrations(self):
        db = MagicMock()

        reg1 = MagicMock()
        reg1.id = "r1"
        reg1.status = "submitted"
        reg1.work_type = "illustration"
        reg1.fee_yuan = 200.0

        reg2 = MagicMock()
        reg2.id = "r2"
        reg2.status = "approved"
        reg2.work_type = "photo"
        reg2.fee_yuan = 150.0

        reg3 = MagicMock()
        reg3.id = "r3"
        reg3.status = "submitted"
        reg3.work_type = "illustration"
        reg3.fee_yuan = None

        db.query.return_value.filter.return_value.all = MagicMock(
            return_value=[reg1, reg2, reg3]
        )

        summary = get_registration_summary(db, user_id="u1")
        assert summary["total"] == 3
        assert summary["by_status"]["submitted"] == 2
        assert summary["by_status"]["approved"] == 1
        assert summary["by_type"]["illustration"] == 2
        assert summary["by_type"]["photo"] == 1
        assert summary["total_fees_yuan"] == 350.0
