"""Celery 异步任务模块."""

from app.tasks.celery_app import celery_app
from app.tasks.hash_tasks import compute_file_hash, batch_compute_hashes, update_work_hash
from app.tasks.monitor_tasks import run_scan_for_task, run_scheduled_scans
from app.tasks.cert_tasks import generate_certificate_async, batch_generate_certificates
from app.tasks.backup_tasks import create_backup_task, cleanup_audit_logs, auto_backup, check_reminders

__all__ = [
    "celery_app",
    "compute_file_hash",
    "batch_compute_hashes",
    "update_work_hash",
    "run_scan_for_task",
    "run_scheduled_scans",
    "generate_certificate_async",
    "batch_generate_certificates",
    "create_backup_task",
    "cleanup_audit_logs",
    "auto_backup",
    "check_reminders",
]
