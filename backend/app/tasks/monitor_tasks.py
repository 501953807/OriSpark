"""监测扫描异步任务."""

import time
from datetime import datetime, timedelta, timezone

from app.tasks.celery_app import celery_app


@celery_app.task(bind=True, max_retries=2)
def run_scan_for_task(self, task_id: str, file_path: str):
    """对单个监测任务执行扫描."""
    from app.database import SessionLocal
    from app.models.monitor import MonitorTask, MonitorResult

    db = SessionLocal()
    try:
        task = db.query(MonitorTask).filter(MonitorTask.id == task_id).first()
        if not task:
            return {"status": "not_found"}

        # 模拟扫描延迟
        time.sleep(1.5)

        # 生成模拟结果
        results = [
            MonitorResult(
                task_id=task_id,
                matched_url=f"https://auto-scan.example.com/match-{time.time_ns()}",
                matched_title=f"自动扫描结果 - {task.work_id[:8]}",
                similarity=round(60 + (hash(task.work_id) % 35), 1),
                found_at=datetime.now(timezone.utc),
                status="pending_review",
            )
            for _ in range(2)
        ]

        db.add_all(results)
        task.last_run = datetime.now(timezone.utc)
        task.quota_used_today = (task.quota_used_today or 0) + 1
        db.commit()

        return {
            "status": "completed",
            "task_id": task_id,
            "results_count": len(results),
        }
    except Exception as exc:
        db.rollback()
        raise self.retry(exc=exc, countdown=120)
    finally:
        db.close()


@celery_app.task
def run_scheduled_scans():
    """定时扫描：检查所有待扫描的 schedule 并执行."""
    from app.database import SessionLocal
    from app.models.monitor import ScanSchedule, MonitorTask, MonitorResult
    from app.models.work import Work

    db = SessionLocal()
    try:
        schedules = db.query(ScanSchedule).filter(
            ScanSchedule.is_enabled == True,
            ScanSchedule.next_run_at <= datetime.now(timezone.utc),
        ).all()

        results_count = 0
        for sched in schedules:
            # 获取范围内的作品
            query = db.query(Work).filter(Work.status == "active")
            if sched.scan_scope == "project" and sched.scope_value:
                query = query.filter(Work.project_id == sched.scope_value)

            works = query.all()

            for work in works:
                # 查找或创建监测任务
                task = db.query(MonitorTask).filter(
                    MonitorTask.work_id == work.id,
                    MonitorTask.platform == "baidu",
                ).first()

                if not task:
                    task = MonitorTask(
                        work_id=work.id,
                        search_type=sched.scan_type,
                        platform="baidu",
                        interval="daily",
                    )
                    db.add(task)
                    db.flush()

                # 创建扫描结果
                result = MonitorResult(
                    task_id=task.id,
                    matched_url=f"https://scheduled.example.com/{work.id[:8]}",
                    matched_title=f"定时扫描 - {work.title}",
                    similarity=round(55 + (hash(work.id) % 40), 1),
                    found_at=datetime.now(timezone.utc),
                    status="pending_review",
                )
                db.add(result)
                results_count += 1

            # 更新下次运行时间
            sched.last_run_at = datetime.now(timezone.utc)
            sched.next_run_at = datetime.now(timezone.utc) + timedelta(hours=24)

        db.commit()
        return {"status": "completed", "results_count": results_count}
    finally:
        db.close()
