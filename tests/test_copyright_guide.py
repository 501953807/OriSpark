"""Tests for copyright registration guide module."""

from datetime import date, datetime
from unittest.mock import MagicMock, patch

import pytest

from app.services.copyright_guide_service import (
    get_all_guides,
    get_guide_by_work_type,
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

    @patch("app.services.copyright_guide_service.SessionLocal")
    def test_get_all_guides_returns_list(self, mock_session):
        db = MagicMock()
        mock_session.return_value = db
        result = get_all_guides()
        assert isinstance(result, list)
        assert len(result) == 4

    @patch("app.services.copyright_guide_service.SessionLocal")
    def test_get_guide_by_work_type(self, mock_session):
        db = MagicMock()
        mock_session.return_value = db
        guide = get_guide_by_work_type("illustration")
        assert guide is not None
        assert guide["work_type"] == "illustration"

    @patch("app.services.copyright_guide_service.SessionLocal")
    def test_get_guide_by_unknown_work_type(self, mock_session):
        db = MagicMock()
        mock_session.return_value = db
        guide = get_guide_by_work_type("unknown_type")
        assert guide is None


class TestRegistrationCRUD:
    """Test registration CRUD operations."""

    @pytest.fixture
    def mock_db(self):
        db = MagicMock()
        db.add = MagicMock()
        db.commit = MagicMock()
        db.refresh = MagicMock()
        return db

    @patch("app.services.copyright_guide_service.SessionLocal")
    def test_create_registration(self, mock_session, mock_db):
        mock_session.return_value = mock_db
        mock_db.query = MagicMock()
        mock_db.query.return_value.filter = MagicMock()
        mock_db.query.return_value.filter.return_value.order_by = MagicMock()
        mock_db.query.return_value.filter.return_value.order_by.return_value.first = MagicMock(
            return_value=None
        )

        result = create_registration(
            mock_db, user_id="u1", title="Test Work", work_type="illustration"
        )
        assert result is not None
        assert result["title"] == "Test Work"
        assert result["work_type"] == "illustration"
        assert result["status"] == "draft"
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()

    @patch("app.services.copyright_guide_service.SessionLocal")
    def test_list_registrations_empty(self, mock_session):
        db = MagicMock()
        mock_session.return_value = db
        db.query = MagicMock()
        db.query.return_value.filter = MagicMock()
        db.query.return_value.filter.return_value.order_by = MagicMock()
        db.query.return_value.filter.return_value.order_by.return_value.all = MagicMock(
            return_value=[]
        )

        result = list_registrations(db, user_id="u1")
        assert result == []

    @patch("app.services.copyright_guide_service.SessionLocal")
    def test_registration_summary_empty(self, mock_session):
        db = MagicMock()
        mock_session.return_value = db
        db.query = MagicMock()
        db.query.return_value.filter = MagicMock()
        db.query.return_value.filter.return_value.all = MagicMock(return_value=[])

        summary = get_registration_summary(db, user_id="u1")
        assert summary["total"] == 0
        assert summary["total_fees_yuan"] == 0


class TestRegistrationSummary:
    """Test registration summary aggregation."""

    @patch("app.services.copyright_guide_service.SessionLocal")
    def test_summary_with_multiple_registrations(self, mock_session):
        db = MagicMock()
        mock_session.return_value = db
        db.query = MagicMock()

        reg1 = MagicMock()
        reg1.id = "r1"
        reg1.status = "submitted"
        reg1.work_type = "illustration"
        reg1.fee_yuan = 200.0
        reg1.title = "Work A"

        reg2 = MagicMock()
        reg2.id = "r2"
        reg2.status = "approved"
        reg2.work_type = "photo"
        reg2.fee_yuan = 150.0
        reg2.title = "Work B"

        reg3 = MagicMock()
        reg3.id = "r3"
        reg3.status = "submitted"
        reg3.work_type = "illustration"
        reg3.fee_yuan = None
        reg3.title = "Work C"

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
