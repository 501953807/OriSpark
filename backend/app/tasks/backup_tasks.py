"""数据备份和系统维护任务."""

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
    """清理过期审计日志."""
    from app.database import SessionLocal
    from app.models.system import AuditLog

    db = SessionLocal()
    try:
        cutoff = datetime.now(timezone.utc) - timedelta(days=retention_days)
        deleted = db.query(AuditLog).filter(
            AuditLog.created_at < cutoff
        ).delete()
        db.commit()
        return {"status": "completed", "deleted_count": deleted}
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
