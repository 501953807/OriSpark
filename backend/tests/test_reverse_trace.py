"""分发回流引擎后端测试."""

import pytest
from sqlalchemy.orm import Session

from app.models.reverse_trace import ReverseTraceLink, ReverseTraceEvent
from app.services.reverse_trace_service import ReverseTraceService


@pytest.fixture
def trace_link(db_session: Session) -> ReverseTraceLink:
    link = ReverseTraceLink(
        work_id="work-001",
        user_id="user-001",
        platform_code="weixin",
        short_code="test1234",
        original_url="https://example.com/work/001",
        redirect_url="https://oristudio.app/r/test1234",
    )
    db_session.add(link)
    db_session.commit()
    db_session.refresh(link)
    return link


class TestReverseTraceLinkModel:
    def test_create_link(self, trace_link: ReverseTraceLink):
        assert trace_link.id is not None
        assert trace_link.work_id == "work-001"
        assert trace_link.platform_code == "weixin"
        assert trace_link.short_code == "test1234"

    def test_update_link_active(self, db_session: Session, trace_link: ReverseTraceLink):
        trace_link.is_active = False
        db_session.commit()
        refreshed = db_session.query(ReverseTraceLink).filter(
            ReverseTraceLink.id == trace_link.id
        ).first()
        assert refreshed.is_active is False


class TestReverseTraceEventModel:
    def test_create_event(self, db_session: Session, trace_link: ReverseTraceLink):
        event = ReverseTraceEvent(
            link_id=trace_link.id,
            event_type="click",
            ip_address="192.168.1.1",
            geo_country="CN",
            converted=False,
        )
        db_session.add(event)
        db_session.commit()
        db_session.refresh(event)
        assert event.id is not None
        assert event.link_id == trace_link.id

    def test_event_has_relationship(self, db_session: Session, trace_link: ReverseTraceLink):
        event = ReverseTraceEvent(
            link_id=trace_link.id,
            event_type="view",
        )
        db_session.add(event)
        db_session.commit()
        # Verify relationship works
        assert event.link is not None
        assert event.link.id == trace_link.id


class TestReverseTraceService:
    def test_create_link(self, db_session: Session):
        service = ReverseTraceService(db_session)
        link = service.create_link(
            work_id="work-002",
            user_id="user-002",
            platform_code="douyin",
            original_url="https://douyin.com/video/123",
        )
        assert link.id is not None
        assert link.platform_code == "douyin"
        assert link.short_code != ""
        assert len(link.short_code) == 8

    def test_get_link_by_id(self, db_session: Session, trace_link: ReverseTraceLink):
        service = ReverseTraceService(db_session)
        found = service.get_link(trace_link.id)
        assert found is not None
        assert found.id == trace_link.id

    def test_get_nonexistent_link(self, db_session: Session):
        service = ReverseTraceService(db_session)
        found = service.get_link("nonexistent")
        assert found is None

    def test_record_click_event(self, db_session: Session, trace_link: ReverseTraceLink):
        service = ReverseTraceService(db_session)
        event = service.record_event(
            link_id=trace_link.id,
            event_type="click",
            ip_address="10.0.0.1",
            geo_country="US",
        )
        assert event.id is not None
        assert event.event_type == "click"
        # Click count should be incremented
        assert trace_link.click_count >= 1

    def test_record_conversion_event(self, db_session: Session, trace_link: ReverseTraceLink):
        service = ReverseTraceService(db_session)
        event = service.record_event(
            link_id=trace_link.id,
            event_type="purchase",
            converted=True,
            conversion_value=99.99,
        )
        assert event.converted is True
        assert event.conversion_value == 99.99

    def test_list_links_filter(self, db_session: Session):
        service = ReverseTraceService(db_session)
        links = service.list_links(platform_code="weixin")
        for link in links:
            assert link.platform_code == "weixin"

    def test_attribution_summary(self, db_session: Session, trace_link: ReverseTraceLink):
        service = ReverseTraceService(db_session)
        service.record_event(trace_link.id, "click", ip_address="1.1.1.1", geo_country="CN")
        service.record_event(trace_link.id, "click", ip_address="2.2.2.2", geo_country="US")
        service.record_event(trace_link.id, "purchase", ip_address="1.1.1.1", converted=True, conversion_value=50.0)

        summary = service.get_attribution_summary(trace_link.id)
        assert summary["total_clicks"] == 3
        assert summary["unique_visitors"] == 2
        assert summary["event_breakdown"]["click"] == 2
        assert summary["event_breakdown"]["purchase"] == 1
        assert summary["total_conversions"] == 1
        assert summary["conversion_rate"] > 0
        assert summary["total_conversion_value"] == 50.0

    def test_delete_link(self, db_session: Session, trace_link: ReverseTraceLink):
        service = ReverseTraceService(db_session)
        result = service.delete_link(trace_link.id)
        assert result is True
        assert service.get_link(trace_link.id) is None

    def test_delete_nonexistent(self, db_session: Session):
        service = ReverseTraceService(db_session)
        result = service.delete_link("nonexistent")
        assert result is False
