"""哈希计算异步任务 (含 WebSocket 进度推送 P1.2.12)."""

import hashlib
from pathlib import Path
from typing import Optional

from app.tasks.celery_app import celery_app


def _notify_hash_progress(work_id: str, progress: float, detail: str):
    """通过 WebSocket 推送哈希计算进度 (P1.2.12)."""
    try:
        # 使用同步方式导入 manager — Celery task 内为同步上下文
        import asyncio
        from app.services.websocket_manager import manager

        loop = asyncio.new_event_loop()
        try:
            loop.run_until_complete(manager.notify_task_progress(
                task_id=f"hash:{work_id}",
                progress=progress,
                detail=detail,
            ))
        finally:
            loop.close()
    except Exception:
        # WebSocket 推送失败不影响主任务
        pass


@celery_app.task(bind=True, max_retries=3)
def compute_file_hash(self, file_path: str, hash_type: str = "sha256") -> Optional[str]:
    """异步计算单个文件哈希 (P1.2.12: 增强进度推送).

    进度推送:
    - 0% → 启动计算
    - 50% → 对较大文件报告半途进度
    - 100% → 计算完成
    """
    try:
        if not Path(file_path).exists():
            raise FileNotFoundError(f"文件不存在: {file_path}")

        # 通知开始
        work_id = Path(file_path).stem
        _notify_hash_progress(work_id, 0.0, f"Starting {hash_type} hash computation")

        file_size = Path(file_path).stat().st_size
        hasher = hashlib.sha256() if hash_type == "sha256" else hashlib.md5()
        bytes_read = 0

        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):  # 64KB chunks
                hasher.update(chunk)
                bytes_read += len(chunk)

                # 对大文件 (>1MB) 推送进度
                if file_size > 1048576:  # 1MB
                    progress = min(95.0, (bytes_read / file_size) * 100)
                    if int(progress) % 10 == 0:  # 每 10% 推送
                        _notify_hash_progress(
                            work_id, progress,
                            f"Hash: {bytes_read // 1024}/{file_size // 1024} KB"
                        )

        result = hasher.hexdigest()
        _notify_hash_progress(work_id, 100.0, f"{hash_type}: {result[:16]}...")
        return result
    except Exception as exc:
        work_id = Path(file_path).stem if file_path else "unknown"
        _notify_hash_progress(work_id, -1, f"Failed: {str(exc)}")
        self.retry(exc=exc, countdown=60)


@celery_app.task(bind=True, max_retries=2)
def batch_compute_hashes(self, file_paths: list[str]) -> dict[str, str]:
    """批量计算文件哈希 (P1.2.12: 增强进度推送).

    每完成一个文件推送批次进度百分比。
    """
    results = {}
    total = len(file_paths)

    _notify_hash_progress("batch", 0.0, f"Batch hashing {total} files started")

    for idx, path in enumerate(file_paths):
        attempt = compute_file_hash.delay(path)
        results[path] = attempt.get(timeout=300)  # 5 min per file

        progress = ((idx + 1) / total) * 100
        _notify_hash_progress("batch", progress, f"Completed {idx + 1}/{total}: {Path(path).name}")

    _notify_hash_progress("batch", 100.0, f"Batch hashing complete: {total} files")
    return results


@celery_app.task
def update_work_hash(work_id: str, sha256: str):
    """更新作品的 SHA-256 哈希到数据库."""
    from app.database import SessionLocal
    from app.models.work import Work

    db = SessionLocal()
    try:
        work = db.query(Work).filter(Work.id == work_id).first()
        if work:
            work.sha256 = sha256
            db.commit()
            _notify_hash_progress(work_id, 100.0, f"Hash stored to DB: {sha256[:16]}...")
    finally:
        db.close()
