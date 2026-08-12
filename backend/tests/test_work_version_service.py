# -*- coding: utf-8 -*-
"""作品版本管理服务层测试."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from app.models.work import Work, WorkVersion, Project
from app.services.work_version_service import (
    list_versions,
    create_version,
    get_version,
    delete_version,
    get_version_history_timeline,
)


@pytest.fixture
def sample_user(db_session):
    from app.models.system import User
    user = User(id="user_001", username="testuser", email="test@example.com")
    db_session.add(user)
    db_session.flush()
    return user


@pytest.fixture
def sample_work(db_session, sample_user):
    work = Work(
        id="work_test_001",
        title="测试作品",
        file_path="/tmp/test.png",
        file_name="test.png",
        file_size=1024,
        file_type="image",
        file_extension="png",
        sha256="abc123" * 8,
        creator_id="user_001",
    )
    db_session.add(work)
    db_session.flush()
    return work


@pytest.fixture
def sample_versions(db_session, sample_work):
    v1 = WorkVersion(
        work_id=sample_work.id,
        version_num=1,
        file_hash="hash_v1" * 8,
        file_path="/tmp/test_v1.png",
        file_size=1000,
        notes="初版",
    )
    v2 = WorkVersion(
        work_id=sample_work.id,
        version_num=2,
        file_hash="hash_v2" * 8,
        file_path="/tmp/test_v2.png",
        file_size=2000,
        notes="修改了颜色",
    )
    v3 = WorkVersion(
        work_id=sample_work.id,
        version_num=3,
        file_hash="hash_v3" * 8,
        file_path="/tmp/test_v3.png",
        file_size=2500,
    )
    db_session.add_all([v1, v2, v3])
    db_session.flush()
    return [v1, v2, v3]


class TestListVersions:
    def test_list_versions_nonexistent_work(self, db_session):
        result = list_versions(db_session, "nonexistent")
        assert result is None

    def test_list_versions_empty(self, db_session, sample_work):
        result = list_versions(db_session, sample_work.id)
        assert isinstance(result, list)
        assert len(result) == 0

    def test_list_versions_sorted_ascending(self, db_session, sample_work, sample_versions):
        result = list_versions(db_session, sample_work.id)
        assert len(result) == 3
        nums = [v["version_num"] for v in result]
        assert nums == [1, 2, 3]

    def test_list_versions_fields(self, db_session, sample_work, sample_versions):
        result = list_versions(db_session, sample_work.id)
        v = result[0]
        assert v["work_id"] == sample_work.id
        assert v["version_num"] == 1
        assert v["file_hash"] == "hash_v1" * 8
        assert v["notes"] == "初版"
        assert v["file_size"] == 1000


class TestCreateVersion:
    def test_create_version_nonexistent_work(self, db_session):
        result = create_version(
            db_session, "nonexistent", "/tmp/x.png", "hash" * 8, 100
        )
        assert result is None

    def test_create_version_auto_increment(self, db_session, sample_work, sample_versions):
        version = create_version(
            db_session,
            sample_work.id,
            "/tmp/test_v4.png",
            "hash_v4" * 8,
            3000,
            "添加新图层",
        )
        assert version is not None
        assert version.version_num == 4
        assert version.notes == "添加新图层"
        assert version.file_size == 3000

    def test_create_version_first(self, db_session, sample_work):
        version = create_version(
            db_session,
            sample_work.id,
            "/tmp/first.png",
            "first_hash" * 8,
            500,
        )
        assert version is not None
        assert version.version_num == 1


class TestGetVersion:
    def test_get_version_nonexistent(self, db_session):
        result = get_version(db_session, "nonexistent_id")
        assert result is None

    def test_get_version_found(self, db_session, sample_versions):
        result = get_version(db_session, sample_versions[1].id)
        assert result is not None
        assert result.version_num == 2
        assert result.work_id == sample_versions[0].work_id


class TestDeleteVersion:
    def test_delete_nonexistent(self, db_session):
        result = delete_version(db_session, "nonexistent_id", "user_001")
        assert not result["success"]
        assert "不存在" in result["error"]

    def test_delete_last_version_prevented(self, db_session, sample_work):
        result = delete_version(db_session, sample_work.id, "user_001")
        # sample_work has no versions yet, so this should fail
        assert not result["success"]

    def test_delete_version_removes_it(self, db_session, sample_work, sample_versions):
        before = list_versions(db_session, sample_work.id)
        assert len(before) == 3
        result = delete_version(db_session, sample_versions[1].id, "user_001")
        assert result["success"]
        after = list_versions(db_session, sample_work.id)
        assert len(after) == 2
        assert all(v["version_num"] != 2 for v in after)

    def test_delete_all_versions_prevented(self, db_session, sample_work):
        v1 = WorkVersion(
            work_id=sample_work.id,
            version_num=1,
            file_hash="only_hash" * 8,
            file_path="/tmp/only.png",
            file_size=100,
        )
        db_session.add(v1)
        db_session.flush()
        result = delete_version(db_session, v1.id, "user_001")
        assert not result["success"]
        assert "最后一个" in result["error"]


class TestGetVersionHistoryTimeline:
    def test_timeline_nonexistent_work(self, db_session):
        result = get_version_history_timeline(db_session, "nonexistent")
        assert result == []

    def test_timeline_empty(self, db_session, sample_work):
        result = get_version_history_timeline(db_session, sample_work.id)
        assert isinstance(result, list)
        assert len(result) == 0

    def test_timeline_with_prev_next(self, db_session, sample_work, sample_versions):
        result = get_version_history_timeline(db_session, sample_work.id)
        assert len(result) == 3
        # First version has no prev
        assert result[0]["prev_version"] is None
        assert result[0]["next_version"] == {
            "version_num": 2,
            "id": sample_versions[1].id,
        }
        # Middle version has both prev and next
        assert result[1]["prev_version"] == {
            "version_num": 1,
            "id": sample_versions[0].id,
        }
        assert result[1]["next_version"] == {
            "version_num": 3,
            "id": sample_versions[2].id,
        }
        # Last version has no next
        assert result[2]["next_version"] is None
        assert result[2]["prev_version"] == {
            "version_num": 2,
            "id": sample_versions[1].id,
        }
