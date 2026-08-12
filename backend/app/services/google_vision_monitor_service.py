"""Google Vision 侵权监测服务."""

import asyncio
from datetime import datetime, timezone

from app.config import settings
from app.gateway.google_vision import GoogleVisionGateway
from app.models.monitor import MonitorResult, MonitorTask
from app.database import get_db


class GoogleVisionMonitorService:
    """基于 Google Vision API 的侵权检测."""

    def __init__(self, db=None):
        self._gateway = GoogleVisionGateway()
        self._db = db

    def detect_infringement(self, image_path: str, work_id: str):
        """调用 Google Vision 检测侵权，记录结果到数据库."""
        db = self._db or next(get_db())
        task = db.query(MonitorTask).filter(MonitorTask.work_id == work_id).first()
        if not task:
            from app.models.work import Work
            work = db.query(Work).filter(Work.id == work_id).first()
            if not work:
                raise ValueError(f"作品 {work_id} 不存在")
            task = MonitorTask(
                work_id=work_id,
                search_type="image",
                platform="google_vision",
                interval="manual",
            )
            db.add(task)
            db.flush()

        results = asyncio.run(self._gateway.search_image(image_path))

        final_results = []
        for r in results:
            mr = MonitorResult(
                task_id=task.id,
                matched_url=r.url,
                matched_title=r.title,
                similarity=r.similarity,
                found_at=datetime.now(timezone.utc),
                status="pending_review",
                match_type="image_similarity",
                confidence=r.similarity,
                is_mock=1 if settings.GOOGLE_VISION_API_KEY is None else 0,
            )
            db.add(mr)
            final_results.append({
                "url": r.url,
                "title": r.title,
                "similarity": r.similarity,
            })

        db.commit()
        return final_results
