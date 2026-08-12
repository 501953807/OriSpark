# -*- coding: utf-8 -*-
"""项目分组管理服务层测试."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from app.models.work import Work, Project
from app.services.project_service import (
    list_projects,
    create_project,
    add_work_to_project,
    remove_work_from_project,
    list_project_works,
    delete_project,
)


@pytest.fixture
def sample_user(db_session):
    from app.models.system import User
    user = User(id="user_001", username="testuser", email="test@example.com")
    db_session.add(user)
    db_session.flush()
    return user


@pytest.fixture
def sample_projects(db_session):
    p1 = Project(id="proj_a", name="项目A", description="测试项目A")
    p2 = Project(id="proj_b", name="项目B", description="测试项目B")
    db_session.add_all([p1, p2])
    db_session.flush()
    return {"a": p1, "b": p2}


@pytest.fixture
def sample_works(db_session, sample_user, sample_projects):
    w1 = Work(
        id="work_a1",
        title="作品A1",
        file_path="/tmp/a1.png",
        file_name="a1.png",
        file_size=100,
        file_type="image",
        file_extension="png",
        creator_id="user_001",
        project_id="proj_a",
    )
    w2 = Work(
        id="work_a2",
        title="作品A2",
        file_path="/tmp/a2.png",
        file_name="a2.png",
        file_size=200,
        file_type="image",
        file_extension="png",
        creator_id="user_001",
        project_id="proj_a",
    )
    w3 = Work(
        id="work_b1",
        title="作品B1",
        file_path="/tmp/b1.png",
        file_name="b1.png",
        file_size=300,
        file_type="image",
        file_extension="png",
        creator_id="user_001",
        project_id="proj_b",
    )
    w4 = Work(
        id="work_unassigned",
        title="未分配作品",
        file_path="/tmp/unassigned.png",
        file_name="unassigned.png",
        file_size=400,
        file_type="image",
        file_extension="png",
        creator_id="user_001",
    )
    db_session.add_all([w1, w2, w3, w4])
    db_session.flush()
    return {"a1": w1, "a2": w2, "b1": w3, "unassigned": w4}


class TestListProjects:
    def test_list_projects_empty(self, db_session):
        result = list_projects(db_session, "user_001")
        assert isinstance(result, list)
        assert len(result) == 0

    def test_list_projects_with_data(self, db_session, sample_projects):
        result = list_projects(db_session, "user_001")
        assert len(result) == 2
        names = {p["name"] for p in result}
        assert names == {"项目A", "项目B"}

    def test_list_projects_contains_work_count(self, db_session, sample_projects, sample_works):
        result = list_projects(db_session, "user_001")
        proj_a = next(p for p in result if p["name"] == "项目A")
        assert proj_a["work_count"] == 2
        proj_b = next(p for p in result if p["name"] == "项目B")
        assert proj_b["work_count"] == 1


class TestCreateProject:
    def test_create_project(self, db_session):
        project = create_project(db_session, "user_001", "新项目", "描述")
        assert project is not None
        assert project.name == "新项目"
        assert project.description == "描述"

    def test_create_project_no_description(self, db_session):
        project = create_project(db_session, "user_001", "无描述项目")
        assert project is not None
        assert project.name == "无描述项目"
        assert project.description is None


class TestAddWorkToProject:
    def test_add_to_nonexistent_project(self, db_session, sample_works):
        result = add_work_to_project(db_session, "nonexistent", sample_works["a1"].id)
        assert not result["success"]
        assert "项目不存在" in result["error"]

    def test_add_nonexistent_work(self, db_session, sample_projects):
        result = add_work_to_project(db_session, sample_projects["a"].id, "no_such_work")
        assert not result["success"]
        assert "作品不存在" in result["error"]

    def test_add_work_success(self, db_session, sample_projects, sample_works):
        result = add_work_to_project(
            db_session, sample_projects["a"].id, sample_works["unassigned"].id
        )
        assert result["success"]
        # Verify work was reassigned
        updated = db_session.query(Work).filter(
            Work.id == sample_works["unassigned"].id
        ).first()
        assert updated.project_id == sample_projects["a"].id

    def test_add_work_sets_cover(self, db_session, sample_projects, sample_works):
        project = db_session.query(Project).filter(
            Project.id == sample_projects["a"].id
        ).first()
        assert project.cover_work_id is None
        add_work_to_project(db_session, project.id, sample_works["unassigned"].id)
        project = db_session.query(Project).filter(Project.id == project.id).first()
        assert project.cover_work_id == sample_works["unassigned"].id


class TestRemoveWorkFromProject:
    def test_remove_nonexistent_work(self, db_session, sample_projects):
        result = remove_work_from_project(db_session, sample_projects["a"].id, "no_such")
        assert not result["success"]

    def test_remove_work_not_in_project(self, db_session, sample_projects, sample_works):
        result = remove_work_from_project(
            db_session, sample_projects["a"].id, sample_works["b1"].id
        )
        assert not result["success"]
        assert "不属于" in result["error"]

    def test_remove_work_success(self, db_session, sample_projects, sample_works):
        result = remove_work_from_project(
            db_session, sample_projects["a"].id, sample_works["a1"].id
        )
        assert result["success"]
        updated = db_session.query(Work).filter(Work.id == sample_works["a1"].id).first()
        assert updated.project_id is None


class TestListProjectWorks:
    def test_list_nonexistent_project(self, db_session):
        result = list_project_works(db_session, "nonexistent")
        assert result is None

    def test_list_project_works(self, db_session, sample_projects, sample_works):
        result = list_project_works(db_session, sample_projects["a"].id)
        assert result is not None
        assert len(result) == 2
        ids = {w["id"] for w in result}
        assert ids == {"work_a1", "work_a2"}

    def test_list_project_works_excludes_unassigned(self, db_session, sample_projects, sample_works):
        result = list_project_works(db_session, sample_projects["a"].id)
        ids = [w["id"] for w in result]
        assert "work_unassigned" not in ids


class TestDeleteProject:
    def test_delete_nonexistent(self, db_session):
        result = delete_project(db_session, "nonexistent", "user_001")
        assert not result["success"]
        assert "不存在" in result["error"]

    def test_delete_project_clears_works(self, db_session, sample_projects, sample_works):
        result = delete_project(db_session, sample_projects["a"].id, "user_001")
        assert result["success"]
        # Works previously in project should now have no project
        for work_id in ["work_a1", "work_a2"]:
            w = db_session.query(Work).filter(Work.id == work_id).first()
            assert w.project_id is None

    def test_delete_project_removes_it(self, db_session, sample_projects):
        delete_project(db_session, sample_projects["a"].id, "user_001")
        remaining = list_projects(db_session, "user_001")
        assert all(p["name"] != "项目A" for p in remaining)
