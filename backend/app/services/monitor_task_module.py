"""监测任务管理模块 — 任务 CRUD + 配额管理 + 扫描触发."""

import logging
from datetime import datetime, timezone
from typing import Optional

from fastapi import HTTPException, Query
from sqlalchemy.orm import Session

from app.models.work import Work
from app.models.monitor import MonitorTask, MonitorResult
from app.schemas.monitor import (
    MonitorTaskCreate, MonitorTaskResponse, MonitorResultResponse,
    ScanRequest, ResultUpdateRequest,
    QuotaStatusResponse, PlatformRotationStatus,
    PriorityScoreResult,
)
from app.schemas.common import ApiResponse
from app.services.whitelist_learner import record_whitelist_action
from app.utils.system_helpers import push_notification

logger = logging.getLogger(__name__)

# 平台配额配置
_PLATFORM_QUOTAS = {
    "baidu": {"daily_limit": 100, "fallback": "google"},
    "google": {"daily_limit": 1000, "fallback": "copyscape"},
    "copyscape": {"daily_limit": 50, "fallback": "baidu"},
    "github": {"daily_limit": 500, "fallback": "baidu"},
}


def _get_platform_usage(db: Session, platform: str) -> int:
    """获取平台今日已用配额."""
    today_tasks = (
        db.query(MonitorTask)
        .filter(MonitorTask.platform == platform)
        .all()
    )
    return sum(t.quota_used_today or 0 for t in today_tasks)


class MonitorTaskModule:
    """监测任务管理模块."""

    def __init__(self, db: Session):
        self.db = db

    def list_tasks(
        self,
        work_id: Optional[str] = None,
        status: Optional[str] = None,
        platform: Optional[str] = None,
    ) -> ApiResponse:
        """获取监测任务列表."""
        query = self.db.query(MonitorTask)
        if work_id:
            query = query.filter(MonitorTask.work_id == work_id)
        if status:
            query = query.filter(MonitorTask.status == status)
        if platform:
            query = query.filter(MonitorTask.platform == platform)
        tasks = query.order_by(MonitorTask.created_at.desc()).all()
        return ApiResponse(data=[MonitorTaskResponse.model_validate(t) for t in tasks])

    def create_task(self, data: MonitorTaskCreate) -> ApiResponse:
        """创建监测任务."""
        work = self.db.query(Work).filter(Work.id == data.work_id).first()
        if not work:
            raise HTTPException(status_code=404, detail="作品不存在")
        existing = self.db.query(MonitorTask).filter(
            MonitorTask.work_id == data.work_id,
            MonitorTask.platform == data.platform,
            MonitorTask.search_type == data.search_type,
            MonitorTask.status == "active",
        ).first()
        if existing:
            raise HTTPException(status_code=400, detail="该作品已有相同的监测任务")
        task = MonitorTask(
            work_id=data.work_id,
            search_type=data.search_type,
            platform=data.platform,
            interval=data.interval,
        )
        self.db.add(task)
        try:
            self.db.commit()
            self.db.refresh(task)
        except Exception:
            self.db.rollback()
            raise
        return ApiResponse(data=MonitorTaskResponse.model_validate(task))

    def trigger_scan(self, task_id: str) -> ApiResponse:
        """手动触发扫描."""
        task = self.db.query(MonitorTask).filter(MonitorTask.id == task_id).first()
        if not task:
            raise HTTPException(status_code=404, detail="监测任务不存在")
        work = self.db.query(Work).filter(Work.id == task.work_id).first()
        if not work:
            raise HTTPException(status_code=404, detail="关联作品不存在")
        now = datetime.now(timezone.utc)
        mock_urls = [
            (f"https://example.com/similar-work-1?t={task_id[:8]}", f"疑似相似作品 - {work.title}", 87.5),
            (f"https://example.com/similar-work-2?t={task_id[:8]}", f"可能匹配 - {work.title}", 62.3),
        ]
        new_results = []
        dup_count = 0
        for url, title, sim in mock_urls:
            existing_result = self.db.query(MonitorResult).filter(
                MonitorResult.matched_url == url,
            ).first()
            if existing_result:
                dup_count += 1
                continue
            new_results.append(MonitorResult(
                task_id=task.id,
                matched_url=url,
                matched_title=title,
                similarity=sim,
                found_at=now,
                status="pending_review",
                is_mock=True,
                notes="[模拟数据] 当前扫描功能使用模拟结果，尚未接入真实API",
            ))
        self.db.add_all(new_results)
        task.last_run = now
        task.quota_used_today += 1
        task.status = "active"
        try:
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise
        if new_results:
            try:
                push_notification(
                    self.db, user_id="default",
                    type="scan_result",
                    title="监测扫描完成",
                    content=f"作品「{work.title}」扫描完成，发现 {len(new_results)} 个新匹配" +
                            (f" (跳过 {dup_count} 个重复)" if dup_count else ""),
                    related_module="monitor",
                    related_id=task.id,
                )
            except Exception as e:
                logger.exception("Error in push_notification: %s", str(e))
        return ApiResponse(
            message=f"扫描完成，发现 {len(new_results)} 个新匹配"
                    + (f" (跳过 {dup_count} 个重复)" if dup_count else ""),
            data={"results_count": len(new_results), "duplicates_skipped": dup_count},
        )

    def batch_scan(self, data: ScanRequest) -> ApiResponse:
        """批量手动扫描 (带去重)."""
        now = datetime.now(timezone.utc)
        total_results = 0
        total_dups = 0
        for work_id in data.work_ids:
            work = self.db.query(Work).filter(Work.id == work_id).first()
            if not work:
                continue
            task = self.db.query(MonitorTask).filter(
                MonitorTask.work_id == work_id,
                MonitorTask.platform == data.platform,
            ).first()
            if not task:
                task = MonitorTask(
                    work_id=work_id,
                    platform=data.platform,
                    search_type="image",
                    interval="manual",
                )
                self.db.add(task)
                self.db.flush()
            urls = [
                (f"https://example.com/match-{work_id[:8]}", f"匹配结果 - {work.title}",
                 75.0 + (hash(work_id) % 20)),
            ]
            for url, title, sim in urls:
                existing = self.db.query(MonitorResult).filter(
                    MonitorResult.matched_url == url
                ).first()
                if existing:
                    total_dups += 1
                    continue
                self.db.add(MonitorResult(
                    task_id=task.id,
                    matched_url=url,
                    matched_title=title,
                    similarity=sim,
                    found_at=now,
                    status="pending_review",
                ))
                total_results += 1
            task.last_run = now
            task.quota_used_today += 1
        try:
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise
        if total_results > 0:
            try:
                push_notification(
                    self.db, user_id="default",
                    type="scan_result",
                    title="监测扫描完成",
                    content=f"批量扫描完成: {len(data.work_ids)} 个作品发现 {total_results} 个新匹配" +
                            (f" (跳过 {total_dups} 个重复)" if total_dups else ""),
                    related_module="monitor",
                    related_id=None,
                )
            except Exception as e:
                logger.exception("Error in push_notification (batch): %s", str(e))
        return ApiResponse(
            message=f"批量扫描完成，发现 {total_results} 个新匹配"
                    + (f" (跳过 {total_dups} 个重复)" if total_dups else ""),
            data={"results_count": total_results, "works_scanned": len(data.work_ids),
                  "duplicates_skipped": total_dups},
        )

    def list_results(
        self,
        task_id: Optional[str] = None,
        status: Optional[str] = None,
        page: int = Query(1, ge=1),
        page_size: int = Query(20, ge=1, le=100),
    ) -> ApiResponse:
        """获取监测结果列表."""
        query = self.db.query(MonitorResult)
        if task_id:
            query = query.filter(MonitorResult.task_id == task_id)
        if status:
            query = query.filter(MonitorResult.status == status)
        results = query.order_by(MonitorResult.similarity.desc()).offset(
            (page - 1) * page_size
        ).limit(page_size).all()
        return ApiResponse(data=[MonitorResultResponse.model_validate(r) for r in results])

    def update_result(self, result_id: str, data: ResultUpdateRequest) -> ApiResponse:
        """更新监测结果状态 (含白名单学习触发)."""
        result = self.db.query(MonitorResult).filter(MonitorResult.id == result_id).first()
        if not result:
            raise HTTPException(status_code=404, detail="结果不存在")
        old_status = result.status
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(result, key, value)
        try:
            self.db.commit()
            self.db.refresh(result)
        except Exception:
            self.db.rollback()
            raise
        if result.status in ("ignored", "whitelisted") and old_status != result.status:
            record_whitelist_action(self.db, result.matched_url, pattern_type="domain")
        return ApiResponse(data=MonitorResultResponse.model_validate(result))

    def get_quota(self) -> ApiResponse:
        """获取扫描配额信息."""
        return ApiResponse(data={
            "baidu": {"daily_limit": 100, "used_today": 0, "remaining": 100},
            "google": {"monthly_limit": 1000, "used_this_month": 0, "remaining": 1000},
            "copyscape": {"daily_limit": 50, "used_today": 0, "remaining": 50},
        })

    def get_quota_rotation_status(self) -> ApiResponse:
        """获取跨平台配额轮转状态."""
        platforms = []
        total_remaining = 0
        for platform, config in _PLATFORM_QUOTAS.items():
            used = _get_platform_usage(self.db, platform)
            remaining = max(0, config["daily_limit"] - used)
            available = remaining > 0
            fallback_platform = config["fallback"]
            fallback_limit = None
            fallback_remaining = None
            if not available and fallback_platform:
                fb_config = _PLATFORM_QUOTAS.get(fallback_platform, {})
                fb_used = _get_platform_usage(self.db, fallback_platform)
                fallback_limit = fb_config.get("daily_limit", 0)
                fallback_remaining = max(0, fallback_limit - fb_used)
            total_remaining += remaining
            platforms.append(PlatformRotationStatus(
                platform=platform,
                daily_limit=config["daily_limit"],
                used_today=used,
                remaining=remaining,
                available=available,
                fallback_platform=fallback_platform if not available else None,
                fallback_limit=fallback_limit,
                fallback_remaining=fallback_remaining,
            ))
        return ApiResponse(
            message=f"Quota rotation: {total_remaining} total scans remaining across all platforms",
            data=QuotaStatusResponse(
                platforms=platforms,
                total_remaining=total_remaining,
                rotation_enabled=True,
            ),
        )

    def trigger_quota_rotation(self, platform: str) -> ApiResponse:
        """手动触发配额轮转."""
        config = _PLATFORM_QUOTAS.get(platform)
        if not config:
            raise HTTPException(status_code=400, detail=f"未知平台: {platform}")
        used = _get_platform_usage(self.db, platform)
        remaining = max(0, config["daily_limit"] - used)
        if remaining > 0:
            return ApiResponse(
                message=f"Platform '{platform}' still has {remaining} scans remaining",
                data={
                    "current_platform": platform,
                    "remaining": remaining,
                    "rotation_needed": False,
                },
            )
        rotation_chain = []
        current = platform
        visited = set()
        while current not in visited:
            visited.add(current)
            fb_config = _PLATFORM_QUOTAS.get(current, {})
            fb = fb_config.get("fallback")
            if not fb or fb in visited:
                break
            fb_used = _get_platform_usage(self.db, fb)
            fb_limit = _PLATFORM_QUOTAS.get(fb, {}).get("daily_limit", 0)
            fb_remaining = max(0, fb_limit - fb_used)
            rotation_chain.append({
                "platform": current,
                "fallback": fb,
                "fallback_remaining": fb_remaining,
            })
            if fb_remaining > 0:
                return ApiResponse(
                    message=f"Quota exhausted for '{platform}'. "
                            f"Rotated to '{fb}' ({fb_remaining} scans available)",
                    data={
                        "current_platform": platform,
                        "exhausted": True,
                        "rotated_to": fb,
                        "fallback_remaining": fb_remaining,
                        "rotation_chain": rotation_chain,
                    },
                )
            current = fb
        return ApiResponse(
            message=f"All platforms in rotation chain exhausted for '{platform}'",
            data={
                "current_platform": platform,
                "exhausted": True,
                "all_exhausted": True,
                "rotation_chain": rotation_chain,
            },
        )
