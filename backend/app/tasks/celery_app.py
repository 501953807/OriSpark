"""Celery 应用配置."""

import os
from celery import Celery

from app.config import settings

celery_app = Celery(
    "oristudio",
    broker=settings.REDIS_URL or "redis://localhost:6379/0",
    backend=settings.REDIS_URL or "redis://localhost:6379/0",
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Shanghai",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=600,  # 10 分钟超时
    task_soft_time_limit=540,
    worker_max_tasks_per_child=200,
    imports=[
        "app.tasks.hash_tasks",
        "app.tasks.monitor_tasks",
        "app.tasks.cert_tasks",
        "app.tasks.backup_tasks",
    ],
)

# Beat 定时任务配置
celery_app.conf.beat_schedule = {
    "scheduled-scan-daily": {
        "task": "app.tasks.monitor_tasks.run_scheduled_scans",
        "schedule": 3600.0,  # 每小时检查一次
    },
    "cleanup-audit-logs": {
        "task": "app.tasks.backup_tasks.cleanup_audit_logs",
        "schedule": 86400.0,  # 每天
    },
    "auto-backup": {
        "task": "app.tasks.backup_tasks.auto_backup",
        "schedule": 604800.0,  # 每周
    },
    "check-reminders": {
        "task": "app.tasks.backup_tasks.check_reminders",
        "schedule": 3600.0,  # 每小时
    },
}
