"""Fork-Merge 协同创作测试 — Git-style 协作工作流."""

import pytest
import uuid

from app.models.fork_merge import (
    ForkMergeWork,
    ForkMergeBranch,
    ForkMergeCommit,
    ForkMergePullRequest,
    ForkMergeCollaborator,
    ForkMergeSplitLock,
)
from app.services.fork_merge_service import ForkMergeService


def _uid(prefix="fm_"):
    return f"{prefix}{uuid.uuid4().hex[:12]}"


class TestCreateWorkspace:
    def test_create_work(self, db_session):
        work = ForkMergeService.create_work(
            db=db_session,
            original_work_id=_uid("w_"),
            title="Test Workspace",
            owner_id=_uid("u_"),
            description="A test workspace",
            visibility="public",
        )
        assert work.title == "Test Workspace"
        assert work.owner_id is not None
        assert work.status == "active"
        assert work.visibility == "public"
        assert work.base_commit_sha is not None

    def test_get_work(self, db_session):
        work = ForkMergeService.create_work(
            db=db_session,
            original_work_id=_uid("w_"),
            title="Get Test",
            owner_id=_uid("u_"),
        )
        found = ForkMergeService.get_work(db_session, work.id)
        assert found is not None
        assert found.title == "Get Test"

    def test_get_work_nonexistent_returns_none(self, db_session):
        result = ForkMergeService.get_work(db_session, "nonexistent")
        assert result is None

    def test_list_works_by_owner(self, db_session):
        owner_id = _uid("owner_")
        ForkMergeService.create_work(
            db=db_session,
            original_work_id=_uid("w_"),
            title="Owner Work 1",
            owner_id=owner_id,
        )
        ForkMergeService.create_work(
            db=db_session,
            original_work_id=_uid("w_"),
            title="Owner Work 2",
            owner_id=owner_id,
        )
        works = ForkMergeService.get_works_by_owner(
            db=db_session, owner_id=owner_id
        )
        assert len(works) >= 2

    def test_close_work(self, db_session):
        work = ForkMergeService.create_work(
            db=db_session,
            original_work_id=_uid("w_"),
            title="Close Test",
            owner_id=_uid("u_"),
        )
        closed = ForkMergeService.close_work(db_session, work.id)
        assert closed.status == "closed"

    def test_close_nonexistent_raises(self, db_session):
        with pytest.raises(ValueError, match="协同仓库不存在"):
            ForkMergeService.close_work(db_session, "fake-id")


class TestBranchOperations:
    def test_add_branch(self, db_session):
        work = ForkMergeService.create_work(
            db=db_session,
            original_work_id=_uid("w_"),
            title="Branch Test",
            owner_id=_uid("u_"),
        )
        branch = ForkMergeService.add_branch(
            db=db_session,
            work_id=work.id,
            name="feature-1",
            is_default=False,
        )
        assert branch.name == "feature-1"
        assert branch.is_default is False

    def test_add_default_branch(self, db_session):
        work = ForkMergeService.create_work(
            db=db_session,
            original_work_id=_uid("w_"),
            title="Default Branch",
            owner_id=_uid("u_"),
        )
        branch = ForkMergeService.add_branch(
            db=db_session,
            work_id=work.id,
            name="main",
            is_default=True,
        )
        assert branch.is_default is True

    def test_add_branch_to_nonexistent_work_raises(self, db_session):
        with pytest.raises(ValueError, match="协同仓库不存在"):
            ForkMergeService.add_branch(
                db=db_session,
                work_id="fake-work",
                name="test",
            )

    def test_list_branches(self, db_session):
        work = ForkMergeService.create_work(
            db=db_session,
            original_work_id=_uid("w_"),
            title="List Branches",
            owner_id=_uid("u_"),
        )
        ForkMergeService.add_branch(db_session, work.id, "main", is_default=True)
        ForkMergeService.add_branch(db_session, work.id, "develop")
        branches = ForkMergeService.get_branches(db_session, work.id)
        assert len(branches) >= 2


class TestCommitOperations:
    def test_add_commit(self, db_session):
        work = ForkMergeService.create_work(
            db=db_session,
            original_work_id=_uid("w_"),
            title="Commit Test",
            owner_id=_uid("u_"),
        )
        branch = ForkMergeService.add_branch(
            db=db_session, work_id=work.id, name="main", is_default=True
        )
        commit = ForkMergeService.add_commit(
            db=db_session,
            work_id=work.id,
            author_id=_uid("u_"),
            message="Initial commit",
            branch_id=branch.id,
            content_hash="abc123",
        )
        assert commit.message == "Initial commit"
        assert commit.content_hash == "abc123"
        # Verify branch HEAD was updated
        db_session.refresh(branch)
        assert branch.commit_id == commit.id

    def test_add_commit_with_metadata(self, db_session):
        work = ForkMergeService.create_work(
            db=db_session,
            original_work_id=_uid("w_"),
            title="Commit Metadata",
            owner_id=_uid("u_"),
        )
        commit = ForkMergeService.add_commit(
            db=db_session,
            work_id=work.id,
            author_id=_uid("u_"),
            message="Add AI generation",
            metadata_json={"tool": "DALL-E", "prompt": "a sunset"},
        )
        assert commit.metadata_json["tool"] == "DALL-E"

    def test_list_commits(self, db_session):
        work = ForkMergeService.create_work(
            db=db_session,
            original_work_id=_uid("w_"),
            title="List Commits",
            owner_id=_uid("u_"),
        )
        ForkMergeService.add_commit(
            db=db_session,
            work_id=work.id,
            author_id=_uid("u_"),
            message="Commit 1",
        )
        ForkMergeService.add_commit(
            db=db_session,
            work_id=work.id,
            author_id=_uid("u_"),
            message="Commit 2",
        )
        commits = ForkMergeService.get_commits(db_session, work.id)
        assert len(commits) >= 2

    def test_add_commit_to_nonexistent_work_raises(self, db_session):
        with pytest.raises(ValueError, match="协同仓库不存在"):
            ForkMergeService.add_commit(
                db=db_session,
                work_id="fake-work",
                author_id=_uid("u_"),
                message="test",
            )


class TestPullRequestOperations:
    def test_create_pull_request(self, db_session):
        work = ForkMergeService.create_work(
            db=db_session,
            original_work_id=_uid("w_"),
            title="PR Test",
            owner_id=_uid("u_"),
        )
        source = ForkMergeService.add_branch(
            db=db_session, work_id=work.id, name="feature"
        )
        target = ForkMergeService.add_branch(
            db=db_session, work_id=work.id, name="main", is_default=True
        )
        pr = ForkMergeService.create_pull_request(
            db=db_session,
            work_id=work.id,
            title="Add new feature",
            author_id=_uid("u_"),
            source_branch_id=source.id,
            target_branch_id=target.id,
            description="This PR adds a new feature.",
        )
        assert pr.title == "Add new feature"
        assert pr.status == "open"
        assert pr.source_branch_id == source.id
        assert pr.target_branch_id == target.id

    def test_create_pull_request_default_target_is_source(self, db_session):
        work = ForkMergeService.create_work(
            db=db_session,
            original_work_id=_uid("w_"),
            title="PR Default Target",
            owner_id=_uid("u_"),
        )
        branch = ForkMergeService.add_branch(
            db=db_session, work_id=work.id, name="feature"
        )
        pr = ForkMergeService.create_pull_request(
            db=db_session,
            work_id=work.id,
            title="Test",
            author_id=_uid("u_"),
            source_branch_id=branch.id,
        )
        assert pr.target_branch_id == branch.id

    def test_list_pull_requests(self, db_session):
        work = ForkMergeService.create_work(
            db=db_session,
            original_work_id=_uid("w_"),
            title="List PRs",
            owner_id=_uid("u_"),
        )
        branch = ForkMergeService.add_branch(
            db=db_session, work_id=work.id, name="feature"
        )
        ForkMergeService.create_pull_request(
            db=db_session,
            work_id=work.id,
            title="PR 1",
            author_id=_uid("u_"),
            source_branch_id=branch.id,
        )
        ForkMergeService.create_pull_request(
            db=db_session,
            work_id=work.id,
            title="PR 2",
            author_id=_uid("u_"),
            source_branch_id=branch.id,
        )
        prs = ForkMergeService.get_pull_requests(db_session, work.id)
        assert len(prs) >= 2

    def test_merge_pull_request(self, db_session):
        work = ForkMergeService.create_work(
            db=db_session,
            original_work_id=_uid("w_"),
            title="Merge PR",
            owner_id=_uid("u_"),
        )
        branch = ForkMergeService.add_branch(
            db=db_session, work_id=work.id, name="feature"
        )
        pr = ForkMergeService.create_pull_request(
            db=db_session,
            work_id=work.id,
            title="Merge Test",
            author_id=_uid("u_"),
            source_branch_id=branch.id,
        )
        merged = ForkMergeService.merge_pull_request(
            db=db_session, pr_id=pr.id, merge_method="squash"
        )
        assert merged.status == "merged"
        assert merged.merged_at is not None
        assert merged.merge_method == "squash"

    def test_merge_nonexistent_pr_raises(self, db_session):
        with pytest.raises(ValueError, match="Merge Request 不存在"):
            ForkMergeService.merge_pull_request(db_session, "fake-pr")

    def test_merge_already_merged_pr_raises(self, db_session):
        work = ForkMergeService.create_work(
            db=db_session,
            original_work_id=_uid("w_"),
            title="Double Merge",
            owner_id=_uid("u_"),
        )
        branch = ForkMergeService.add_branch(
            db=db_session, work_id=work.id, name="feature"
        )
        pr = ForkMergeService.create_pull_request(
            db=db_session,
            work_id=work.id,
            title="Merge Test",
            author_id=_uid("u_"),
            source_branch_id=branch.id,
        )
        ForkMergeService.merge_pull_request(db_session, pr.id)
        with pytest.raises(ValueError, match="只能合并开放的"):
            ForkMergeService.merge_pull_request(db_session, pr.id)

    def test_reject_pull_request(self, db_session):
        work = ForkMergeService.create_work(
            db=db_session,
            original_work_id=_uid("w_"),
            title="Reject PR",
            owner_id=_uid("u_"),
        )
        branch = ForkMergeService.add_branch(
            db=db_session, work_id=work.id, name="feature"
        )
        pr = ForkMergeService.create_pull_request(
            db=db_session,
            work_id=work.id,
            title="Reject Test",
            author_id=_uid("u_"),
            source_branch_id=branch.id,
        )
        rejected = ForkMergeService.reject_pull_request(db_session, pr.id)
        assert rejected.status == "rejected"

    def test_reject_nonexistent_pr_raises(self, db_session):
        with pytest.raises(ValueError, match="Merge Request 不存在"):
            ForkMergeService.reject_pull_request(db_session, "fake-pr")


class TestCollaboratorOperations:
    def test_add_collaborator(self, db_session):
        work = ForkMergeService.create_work(
            db=db_session,
            original_work_id=_uid("w_"),
            title="Collab Test",
            owner_id=_uid("u_"),
        )
        collab = ForkMergeService.add_collaborator(
            db=db_session,
            work_id=work.id,
            user_id=_uid("u_"),
            role="contributor",
            permissions={"can_edit": True},
        )
        assert collab.role == "contributor"
        assert collab.permissions["can_edit"] is True

    def test_remove_collaborator(self, db_session):
        work = ForkMergeService.create_work(
            db=db_session,
            original_work_id=_uid("w_"),
            title="Remove Collab",
            owner_id=_uid("u_"),
        )
        collab = ForkMergeService.add_collaborator(
            db=db_session,
            work_id=work.id,
            user_id=_uid("u_"),
            role="contributor",
        )
        removed = ForkMergeService.remove_collaborator(
            db_session, work.id, collab.user_id
        )
        assert removed.left_at is not None

    def test_list_collaborators(self, db_session):
        work = ForkMergeService.create_work(
            db=db_session,
            original_work_id=_uid("w_"),
            title="List Collabs",
            owner_id=_uid("u_"),
        )
        ForkMergeService.add_collaborator(
            db=db_session,
            work_id=work.id,
            user_id=_uid("u_1"),
        )
        ForkMergeService.add_collaborator(
            db=db_session,
            work_id=work.id,
            user_id=_uid("u_2"),
        )
        collaborators = ForkMergeService.get_collaborators(db_session, work.id)
        assert len(collaborators) >= 2

    def test_remove_nonexistent_collaborator_raises(self, db_session):
        work = ForkMergeService.create_work(
            db=db_session,
            original_work_id=_uid("w_"),
            title="Remove Nonexistent",
            owner_id=_uid("u_"),
        )
        with pytest.raises(ValueError, match="协作者不存在"):
            ForkMergeService.remove_collaborator(
                db_session, work.id, "nonexistent-user"
            )


class TestSplitLockOperations:
    def test_lock_split(self, db_session):
        work = ForkMergeService.create_work(
            db=db_session,
            original_work_id=_uid("w_"),
            title="Split Lock",
            owner_id=_uid("u_"),
        )
        branch = ForkMergeService.add_branch(
            db=db_session, work_id=work.id, name="feature"
        )
        pr = ForkMergeService.create_pull_request(
            db=db_session,
            work_id=work.id,
            title="Split Lock PR",
            author_id=_uid("u_"),
            source_branch_id=branch.id,
        )
        split_lock = ForkMergeService.lock_split(
            db=db_session,
            pr_id=pr.id,
            work_id=work.id,
            contributor_id=_uid("u_"),
            split_pct=50.0,
            locked_by=_uid("u_"),
        )
        assert split_lock.split_pct == 50.0
        assert split_lock.status == "locked"

    def test_list_split_locks(self, db_session):
        work = ForkMergeService.create_work(
            db=db_session,
            original_work_id=_uid("w_"),
            title="List Split Locks",
            owner_id=_uid("u_"),
        )
        branch = ForkMergeService.add_branch(
            db=db_session, work_id=work.id, name="feature"
        )
        pr = ForkMergeService.create_pull_request(
            db=db_session,
            work_id=work.id,
            title="List Split Locks PR",
            author_id=_uid("u_"),
            source_branch_id=branch.id,
        )
        ForkMergeService.lock_split(
            db=db_session,
            pr_id=pr.id,
            work_id=work.id,
            contributor_id=_uid("u_1"),
            split_pct=60.0,
            locked_by=_uid("u_"),
        )
        ForkMergeService.lock_split(
            db=db_session,
            pr_id=pr.id,
            work_id=work.id,
            contributor_id=_uid("u_2"),
            split_pct=40.0,
            locked_by=_uid("u_"),
        )
        locks = ForkMergeService.get_split_locks(db_session, pr.id)
        assert len(locks) >= 2

    def test_release_split_lock(self, db_session):
        work = ForkMergeService.create_work(
            db=db_session,
            original_work_id=_uid("w_"),
            title="Release Split Lock",
            owner_id=_uid("u_"),
        )
        branch = ForkMergeService.add_branch(
            db=db_session, work_id=work.id, name="feature"
        )
        pr = ForkMergeService.create_pull_request(
            db=db_session,
            work_id=work.id,
            title="Release Split Lock PR",
            author_id=_uid("u_"),
            source_branch_id=branch.id,
        )
        split_lock = ForkMergeService.lock_split(
            db=db_session,
            pr_id=pr.id,
            work_id=work.id,
            contributor_id=_uid("u_"),
            split_pct=50.0,
            locked_by=_uid("u_"),
        )
        released = ForkMergeService.release_split_lock(
            db_session, split_lock.id
        )
        assert released.status == "released"

    def test_release_nonexistent_split_lock_raises(self, db_session):
        with pytest.raises(ValueError, match="分润锁定不存在"):
            ForkMergeService.release_split_lock(db_session, "fake-lock")

    def test_lock_split_nonexistent_pr_raises(self, db_session):
        with pytest.raises(ValueError, match="Merge Request 不存在"):
            ForkMergeService.lock_split(
                db=db_session,
                pr_id="fake-pr",
                work_id=_uid("w_"),
                contributor_id=_uid("u_"),
                split_pct=50.0,
                locked_by=_uid("u_"),
            )


class TestEndToEndWorkflow:
    """端到端测试：完整的 Fork-Merge 协同创作流程."""

    def test_full_workflow(self, db_session):
        # 1. 创作者 A 创建协同仓库
        work = ForkMergeService.create_work(
            db=db_session,
            original_work_id=_uid("w_"),
            title="Joint Creation Project",
            owner_id="owner_a",
            visibility="public",
        )
        assert work.status == "active"

        # 2. 自动创建默认分支 main
        main_branch = ForkMergeService.add_branch(
            db=db_session, work_id=work.id, name="main", is_default=True
        )

        # 3. 创作者 B 加入为协作者
        collaborator = ForkMergeService.add_collaborator(
            db=db_session,
            work_id=work.id,
            user_id="user_b",
            role="contributor",
        )
        assert collaborator.role == "contributor"

        # 4. 创作者 B 创建功能分支
        feature_branch = ForkMergeService.add_branch(
            db=db_session, work_id=work.id, name="feature/collab"
        )

        # 5. 创作者 B 提交代码
        commit = ForkMergeService.add_commit(
            db=db_session,
            work_id=work.id,
            author_id="user_b",
            message="Add collaborative content",
            branch_id=feature_branch.id,
            metadata_json={"tool": "AI Assistant", "type": "text"},
        )
        assert commit.author_id == "user_b"

        # 6. 创作者 B 发起 Merge Request
        pr = ForkMergeService.create_pull_request(
            db=db_session,
            work_id=work.id,
            title="Merge collaborative content",
            author_id="user_b",
            source_branch_id=feature_branch.id,
            target_branch_id=main_branch.id,
            description="Please review and merge.",
        )
        assert pr.status == "open"

        # 7. 联合确权，锁定分润比例
        ForkMergeService.lock_split(
            db=db_session,
            pr_id=pr.id,
            work_id=work.id,
            contributor_id="owner_a",
            split_pct=60.0,
            locked_by="owner_a",
        )
        ForkMergeService.lock_split(
            db=db_session,
            pr_id=pr.id,
            work_id=work.id,
            contributor_id="user_b",
            split_pct=40.0,
            locked_by="owner_a",
        )

        locks = ForkMergeService.get_split_locks(db_session, pr.id)
        assert len(locks) == 2
        total_pct = sum(lock.split_pct for lock in locks)
        assert total_pct == 100.0

        # 8. 合并 Merge Request
        merged = ForkMergeService.merge_pull_request(
            db=db_session, pr_id=pr.id, merge_method="merge"
        )
        assert merged.status == "merged"
        assert merged.merged_at is not None

        # 9. 验证最终状态
        work = ForkMergeService.get_work(db_session, work.id)
        assert work.status == "active"
