"""数据备份和系统维护任务."""

import gzip
import json
import shutil
from datetime import datetime, timedelta, timezone
from pathlib import Path

from app.tasks.celery_app import celery_app


@celery_app.task
def create_backup_task(include_files: bool = True):
    """创建数据备份."""
    from app.database import SessionLocal
    from app.models.system import BackupRecord

    db = SessionLocal()
    try:
        backup_dir = Path("data/backups")
        backup_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        backup_name = f"backup_{timestamp}.zip"

        # 备份数据库
        db_path = Path("data/oristudio.db")
        if db_path.exists():
            shutil.copy2(db_path, backup_dir / f"db_{timestamp}.bak")

        backup_path = backup_dir / backup_name

        record = BackupRecord(
            path=str(backup_path),
            size=backup_path.stat().st_size if backup_path.exists() else 0,
            type="auto",
            includes_files=include_files,
        )
        db.add(record)
        db.commit()

        return {"status": "completed", "backup_path": str(backup_path)}
    finally:
        db.close()


@celery_app.task
def cleanup_audit_logs(retention_days: int = 90):
    """清理过期审计日志，归档到 data/audit_archive/.

    返回包含删除数、归档文件路径和归档数目的结果。
    """
    from app.database import SessionLocal
    from app.models.system import AuditLog

    db = SessionLocal()
    try:
        now_utc = datetime.now(timezone.utc)
        cutoff = now_utc.replace(tzinfo=None) - timedelta(days=retention_days)
        old_logs = db.query(AuditLog).filter(AuditLog.created_at < cutoff).all()
        deleted_count = len(old_logs)

        archive_dir = Path("data/audit_archive")
        archive_dir.mkdir(parents=True, exist_ok=True)

        if old_logs:
            today_str = now_utc.strftime("%Y-%m-%d")
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

            db.query(AuditLog).filter(AuditLog.created_at < cutoff).delete()
            db.commit()

        return {
            "status": "completed",
            "deleted_count": deleted_count,
            "archived": deleted_count > 0,
            "archive_path": str(archive_path) if old_logs else None,
        }
    finally:
        db.close()


@celery_app.task
def auto_backup():
    """定时自动备份."""
    return create_backup_task.delay(include_files=True).get()


@celery_app.task
def check_reminders():
    """检查并发送到期提醒."""
    from app.database import SessionLocal
    from app.models.supply import Reminder

    db = SessionLocal()
    try:
        now = datetime.now(timezone.utc)
        window = now + timedelta(hours=24)

        pending = db.query(Reminder).filter(
            Reminder.status == "pending",
            Reminder.remind_at <= window,
        ).all()

        notified = 0
        for r in pending:
            # 实际发送通知的逻辑 (后续集成 WebSocket / email)
            r.status = "sent"
            notified += 1

        db.commit()
        return {"status": "completed", "notified_count": notified}
    finally:
        db.close()
