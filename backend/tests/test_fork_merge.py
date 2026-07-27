"""Fork-Merge 协同创作路由测试 — workspaces, branches, commits, PRs, collaborators, split locks."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

import pytest


@pytest.fixture
def creator_user(db_session):
    from app.models.system import User
    user = User(
        id="creator001",
        username="test_creator",
        email="creator@test.com",
        role="creator",
        status="active",
    )
    db_session.add(user)
    db_session.commit()
    return user


@pytest.fixture
def collab_user(db_session):
    from app.models.system import User
    user = User(
        id="collab001",
        username="test_collab",
        email="collab@test.com",
        role="creator",
        status="active",
    )
    db_session.add(user)
    db_session.commit()
    return user


_BASE = "/api/fork-merge/fork-merge"


def _create_workspace(db_session, work_id="work001", owner_id="creator001"):
    """Create a workspace with default main branch."""
    from app.models.fork_merge import ForkMergeWork, ForkMergeBranch
    work = ForkMergeWork(
        id=work_id,
        original_work_id="orig_work_001",
        title="Test Workspace",
        description="A test project",
        owner_id=owner_id,
        status="open",
        visibility="private",
    )
    db_session.add(work)
    branch = ForkMergeBranch(
        id="branch_main",
        work_id=work_id,
        name="main",
        is_default=True,
    )
    db_session.add(branch)
    db_session.commit()
    return work


def _create_branch(db_session, work_id, name="feature/test"):
    from app.models.fork_merge import ForkMergeBranch
    branch = ForkMergeBranch(
        id=f"br_{name.replace('/', '_')}",
        work_id=work_id,
        name=name,
    )
    db_session.add(branch)
    db_session.commit()
    return branch


# ── Workspace CRUD ──────────────────────────────────────────────────

class TestWorkspace:

    def test_get_workspace(self, client, db_session, creator_user):
        _create_workspace(db_session)
        resp = client.get(f"{_BASE}/workspaces/work001")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["title"] == "Test Workspace"
        assert data["owner_id"] == "creator001"

    def test_list_workspaces_by_owner(self, client, db_session, creator_user):
        _create_workspace(db_session)
        resp = client.get(f"{_BASE}/workspaces", params={"owner_id": "creator001"})
        assert resp.status_code == 200
        items = resp.json()["data"]["items"]
        assert len(items) >= 1
        assert any(w["id"] == "work001" for w in items)

    def test_close_workspace(self, client, db_session, creator_user):
        _create_workspace(db_session)
        resp = client.patch(f"{_BASE}/workspaces/work001/close")
        assert resp.status_code == 200
        assert resp.json()["data"]["status"] == "closed"

    def test_close_nonexistent_workspace(self, client):
        resp = client.patch(f"{_BASE}/workspaces/nonexist/close")
        assert resp.status_code == 400

    def test_get_nonexistent_workspace(self, client):
        resp = client.get(f"{_BASE}/workspaces/nonexist")
        assert resp.status_code == 404


# ── Branches ─────────────────────────────────────────────────────────

class TestBranches:

    def test_create_branch(self, client, db_session, creator_user):
        _create_workspace(db_session)
        resp = client.post(
            f"{_BASE}/workspaces/work001/branches",
            json={"name": "feature/illustration"},
        )
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["name"] == "feature/illustration"
        assert data["work_id"] == "work001"

    def test_list_branches(self, client, db_session, creator_user):
        _create_workspace(db_session)
        client.post(
            f"{_BASE}/workspaces/work001/branches",
            json={"name": "feature/test"},
        )
        resp = client.get(f"{_BASE}/workspaces/work001/branches")
        assert resp.status_code == 200
        items = resp.json()["data"]["items"]
        assert len(items) >= 2

    def test_create_branch_on_nonexistent_work(self, client):
        resp = client.post(
            f"{_BASE}/workspaces/nonexist/branches",
            json={"name": "bad_branch"},
        )
        assert resp.status_code == 400


# ── Commits ──────────────────────────────────────────────────────────

class TestCommits:

    def test_create_commit(self, client, db_session, creator_user):
        _create_workspace(db_session)
        resp = client.post(
            f"{_BASE}/workspaces/work001/commits",
            json={
                "author_id": "creator001",
                "message": "Initial sketch",
                "branch_id": "branch_main",
            },
        )
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["message"] == "Initial sketch"
        assert data["author_id"] == "creator001"

    def test_list_commits(self, client, db_session, creator_user):
        _create_workspace(db_session)
        client.post(
            f"{_BASE}/workspaces/work001/commits",
            json={"author_id": "creator001", "message": "Commit 1", "branch_id": "branch_main"},
        )
        client.post(
            f"{_BASE}/workspaces/work001/commits",
            json={"author_id": "creator001", "message": "Commit 2", "branch_id": "branch_main"},
        )
        resp = client.get(f"{_BASE}/workspaces/work001/commits")
        assert resp.status_code == 200
        items = resp.json()["data"]["items"]
        assert len(items) >= 2

    def test_list_commits_filtered_by_author(self, client, db_session, creator_user):
        _create_workspace(db_session)
        client.post(
            f"{_BASE}/workspaces/work001/commits",
            json={"author_id": "creator001", "message": "Author commit", "branch_id": "branch_main"},
        )
        resp = client.get(
            f"{_BASE}/workspaces/work001/commits",
            params={"author_id": "creator001"},
        )
        assert resp.status_code == 200
        items = resp.json()["data"]["items"]
        assert all(c["author_id"] == "creator001" for c in items)


# ── Pull Requests ────────────────────────────────────────────────────

class TestPullRequests:

    def test_create_pr(self, client, db_session, creator_user):
        _create_workspace(db_session)
        br_resp = client.post(
            f"{_BASE}/workspaces/work001/branches",
            json={"name": "feature/new-art"},
        )
        assert br_resp.status_code == 200
        branch_id = br_resp.json()["data"]["id"]
        resp = client.post(
            f"{_BASE}/workspaces/work001/pull-requests",
            json={
                "title": "Add new artwork",
                "author_id": "creator001",
                "source_branch_id": branch_id,
            },
        )
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["title"] == "Add new artwork"
        assert data["status"] == "open"

    def test_list_pull_requests(self, client, db_session, creator_user):
        _create_workspace(db_session)
        br_resp = client.post(
            f"{_BASE}/workspaces/work001/branches",
            json={"name": "feature/pr-test"},
        )
        branch_id = br_resp.json()["data"]["id"]
        client.post(
            f"{_BASE}/workspaces/work001/pull-requests",
            json={
                "title": "PR Test",
                "author_id": "creator001",
                "source_branch_id": branch_id,
            },
        )
        resp = client.get(f"{_BASE}/workspaces/work001/pull-requests")
        assert resp.status_code == 200
        items = resp.json()["data"]["items"]
        assert len(items) >= 1

    def test_merge_pull_request(self, client, db_session, creator_user):
        _create_workspace(db_session)
        br_resp = client.post(
            f"{_BASE}/workspaces/work001/branches",
            json={"name": "feature/merge-me"},
        )
        branch_id = br_resp.json()["data"]["id"]
        pr_resp = client.post(
            f"{_BASE}/workspaces/work001/pull-requests",
            json={
                "title": "Merge Me",
                "author_id": "creator001",
                "source_branch_id": branch_id,
            },
        )
        pr_id = pr_resp.json()["data"]["id"]
        merge_resp = client.post(
            f"{_BASE}/pull-requests/{pr_id}/merge",
            json={"merge_method": "merge"},
        )
        assert merge_resp.status_code == 200
        assert merge_resp.json()["data"]["status"] == "merged"

    def test_reject_pull_request(self, client, db_session, creator_user):
        _create_workspace(db_session)
        br_resp = client.post(
            f"{_BASE}/workspaces/work001/branches",
            json={"name": "feature/reject-me"},
        )
        branch_id = br_resp.json()["data"]["id"]
        pr_resp = client.post(
            f"{_BASE}/workspaces/work001/pull-requests",
            json={
                "title": "Reject Me",
                "author_id": "creator001",
                "source_branch_id": branch_id,
            },
        )
        pr_id = pr_resp.json()["data"]["id"]
        reject_resp = client.post(f"{_BASE}/pull-requests/{pr_id}/reject")
        assert reject_resp.status_code == 200
        assert reject_resp.json()["data"]["status"] == "rejected"

    def test_cannot_merge_already_merged_pr(self, client, db_session, creator_user):
        _create_workspace(db_session)
        br_resp = client.post(
            f"{_BASE}/workspaces/work001/branches",
            json={"name": "feature/double-merge"},
        )
        branch_id = br_resp.json()["data"]["id"]
        pr_resp = client.post(
            f"{_BASE}/workspaces/work001/pull-requests",
            json={
                "title": "Double Merge",
                "author_id": "creator001",
                "source_branch_id": branch_id,
            },
        )
        pr_id = pr_resp.json()["data"]["id"]
        client.post(f"{_BASE}/pull-requests/{pr_id}/merge")
        resp = client.post(f"{_BASE}/pull-requests/{pr_id}/merge")
        assert resp.status_code == 400


# ── Collaborators ────────────────────────────────────────────────────

class TestCollaborators:

    def test_add_collaborator(self, client, db_session, creator_user, collab_user):
        _create_workspace(db_session)
        resp = client.post(
            f"{_BASE}/workspaces/work001/collaborators",
            json={"user_id": "collab001", "role": "contributor"},
        )
        assert resp.status_code == 200
        assert resp.json()["data"]["user_id"] == "collab001"

    def test_list_collaborators(self, client, db_session, creator_user, collab_user):
        _create_workspace(db_session)
        client.post(
            f"{_BASE}/workspaces/work001/collaborators",
            json={"user_id": "collab001", "role": "reviewer"},
        )
        resp = client.get(f"{_BASE}/workspaces/work001/collaborators")
        assert resp.status_code == 200
        items = resp.json()["data"]["items"]
        assert len(items) >= 1
        assert any(c["user_id"] == "collab001" for c in items)

    def test_remove_collaborator(self, client, db_session, creator_user, collab_user):
        _create_workspace(db_session)
        client.post(
            f"{_BASE}/workspaces/work001/collaborators",
            json={"user_id": "collab001", "role": "contributor"},
        )
        del_resp = client.delete(f"{_BASE}/workspaces/work001/collaborators/collab001")
        assert del_resp.status_code == 200
        list_resp = client.get(f"{_BASE}/workspaces/work001/collaborators")
        items = list_resp.json()["data"]["items"]
        assert not any(c["user_id"] == "collab001" for c in items)


# ── Split Locks ──────────────────────────────────────────────────────

class TestSplitLocks:

    def test_lock_split(self, client, db_session, creator_user):
        _create_workspace(db_session)
        br_resp = client.post(
            f"{_BASE}/workspaces/work001/branches",
            json={"name": "feature/split-lock"},
        )
        branch_id = br_resp.json()["data"]["id"]
        pr_resp = client.post(
            f"{_BASE}/workspaces/work001/pull-requests",
            json={
                "title": "Split Lock Test",
                "author_id": "creator001",
                "source_branch_id": branch_id,
            },
        )
        pr_id = pr_resp.json()["data"]["id"]
        lock_resp = client.post(
            f"{_BASE}/pull-requests/{pr_id}/split-locks",
            json={
                "work_id": "work001",
                "contributor_id": "creator001",
                "split_pct": 0.7,
                "locked_by": "creator001",
            },
        )
        assert lock_resp.status_code == 200
        data = lock_resp.json()["data"]
        assert data["split_pct"] == 0.7
        assert data["contributor_id"] == "creator001"

    def test_list_split_locks(self, client, db_session, creator_user):
        _create_workspace(db_session)
        br_resp = client.post(
            f"{_BASE}/workspaces/work001/branches",
            json={"name": "feature/list-locks"},
        )
        branch_id = br_resp.json()["data"]["id"]
        pr_resp = client.post(
            f"{_BASE}/workspaces/work001/pull-requests",
            json={
                "title": "List Locks",
                "author_id": "creator001",
                "source_branch_id": branch_id,
            },
        )
        pr_id = pr_resp.json()["data"]["id"]
        client.post(
            f"{_BASE}/pull-requests/{pr_id}/split-locks",
            json={
                "work_id": "work001",
                "contributor_id": "creator001",
                "split_pct": 0.7,
                "locked_by": "creator001",
            },
        )
        resp = client.get(f"{_BASE}/pull-requests/{pr_id}/split-locks")
        assert resp.status_code == 200
        items = resp.json()["data"]["items"]
        assert len(items) >= 1

    def test_release_split_lock(self, client, db_session, creator_user):
        _create_workspace(db_session)
        br_resp = client.post(
            f"{_BASE}/workspaces/work001/branches",
            json={"name": "feature/release-lock"},
        )
        branch_id = br_resp.json()["data"]["id"]
        pr_resp = client.post(
            f"{_BASE}/workspaces/work001/pull-requests",
            json={
                "title": "Release Lock",
                "author_id": "creator001",
                "source_branch_id": branch_id,
            },
        )
        pr_id = pr_resp.json()["data"]["id"]
        lock_resp = client.post(
            f"{_BASE}/pull-requests/{pr_id}/split-locks",
            json={
                "work_id": "work001",
                "contributor_id": "creator001",
                "split_pct": 0.7,
                "locked_by": "creator001",
            },
        )
        lock_id = lock_resp.json()["data"]["id"]
        rel_resp = client.post(f"{_BASE}/split-locks/{lock_id}/release")
        assert rel_resp.status_code == 200
        assert rel_resp.json()["data"]["status"] == "released"
