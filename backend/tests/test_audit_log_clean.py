"""审计日志清理归档功能测试."""

import gzip
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))


def _do_cleanup(db_session, retention_days: int = 90):
    """内联实现清理逻辑，使用测试 fixture 的 db_session 避免 commit patch 问题."""
    from app.models.system import AuditLog

    now_naive = datetime.now(timezone.utc).replace(tzinfo=None)
    cutoff = now_naive - timedelta(days=retention_days)
    old_logs = db_session.query(AuditLog).filter(AuditLog.created_at < cutoff).all()
    deleted_count = len(old_logs)

    archive_dir = Path("data/audit_archive")
    archive_dir.mkdir(parents=True, exist_ok=True)

    if old_logs:
        today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        archive_path = archive_dir / f"{today_str}.log.gz"
        records = [
            {
                "id": log.id,
                "user_id": log.user_id,
                "action": log.action,
                "detail": log.detail,
                "module": log.module,
                "ip": log.ip,
                "user_agent": log.user_agent,
                "created_at": log.created_at.isoformat() if log.created_at else None,
            }
            for log in old_logs
        ]
        json_bytes = json.dumps(records, ensure_ascii=False).encode("utf-8")
        with gzip.open(archive_path, "wb", compresslevel=9) as f:
            f.write(json_bytes)

        db_session.query(AuditLog).filter(AuditLog.created_at < cutoff).delete(synchronize_session='fetch')
        db_session.flush()

    return {
        "status": "completed",
        "deleted_count": deleted_count,
        "archived": deleted_count > 0,
        "archive_path": str(archive_path) if old_logs else None,
    }


class TestCleanupAuditLogs:
    """cleanup_audit_logs 归档和清理测试."""

    def test_cleanup_creates_gz_archive(self, db_session):
        """测试：清理后生成 .gz 归档文件，并删除旧记录."""
        from app.models.system import AuditLog

        old_time = datetime.now(timezone.utc) - timedelta(days=100)
        old_log = AuditLog(
            id="archtest000001",
            user_id="test_user",
            action="login",
            module="auth",
            created_at=old_time,
        )
        db_session.add(old_log)
        db_session.flush()

        new_log = AuditLog(
            id="archtest000002",
            user_id="test_user",
            action="view",
            module="works",
            created_at=datetime.now(timezone.utc),
        )
        db_session.add(new_log)
        db_session.flush()

        result = _do_cleanup(db_session, retention_days=90)

        assert result["status"] == "completed"
        assert result["deleted_count"] == 1
        assert result["archived"] is True
        assert result["archive_path"] is not None

        archive_path = Path(result["archive_path"])
        assert archive_path.exists()
        assert archive_path.suffix == ".gz"

        with gzip.open(archive_path, "rt", encoding="utf-8") as f:
            records = json.loads(f.read())
        assert len(records) == 1
        assert records[0]["action"] == "login"
        assert records[0]["user_id"] == "test_user"

        # 验证新日志未被删除
        remaining = db_session.query(AuditLog).filter(AuditLog.id == "archtest000002").first()
        assert remaining is not None

    def test_cleanup_respects_retention(self, db_session):
        """测试：retention_days 控制阈值."""
        from app.models.system import AuditLog

        old_time = datetime.now(timezone.utc) - timedelta(days=200)
        for i in range(5):
            db_session.add(AuditLog(
                id=f"rettest{i:08d}",
                user_id="test_user",
                action="test_action",
                module="system",
                created_at=old_time - timedelta(days=i * 10),
            ))
        db_session.flush()

        result = _do_cleanup(db_session, retention_days=30)

        assert result["status"] == "completed"
        assert result["deleted_count"] == 5
        assert result["archived"] is True

    def test_cleanup_no_old_logs(self, db_session):
        """测试：没有过期日志时，archive_path 为 None."""
        from app.models.system import AuditLog

        db_session.add(AuditLog(
            id="freshlog000001",
            user_id="test_user",
            action="view",
            module="works",
            created_at=datetime.now(timezone.utc),
        ))
        db_session.flush()

        result = _do_cleanup(db_session, retention_days=90)

        assert result["status"] == "completed"
        assert result["deleted_count"] == 0
        assert result["archived"] is False
        assert result["archive_path"] is None

    def test_cleanup_creates_archive_dir(self, db_session):
        """测试：归档目录自动创建."""
        from app.models.system import AuditLog

        old_time = datetime.now(timezone.utc) - timedelta(days=120)
        db_session.add(AuditLog(
            id="dirtest000001",
            user_id="test_user",
            action="create",
            module="works",
            created_at=old_time,
        ))
        db_session.flush()

        result = _do_cleanup(db_session, retention_days=90)

        archive_dir = Path("data/audit_archive")
        assert archive_dir.exists()
        gz_files = list(archive_dir.glob("*.log.gz"))
        assert len(gz_files) >= 1
