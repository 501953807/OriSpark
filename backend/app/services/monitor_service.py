"""MonitorService 组合入口 — 委托到子模块.

此文件保留原有接口，内部通过组合子模块实现.
"""

import logging
from datetime import datetime, timezone
from typing import Optional

from fastapi import HTTPException, Query
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.models.work import Work
from app.models.monitor import MonitorTask, MonitorResult, EvidencePackage
from app.models.monitor_ext import (
    BrandWatch, BrandScanResult, DomainWatch, WhitelistSuggestion,
)
from app.schemas.monitor import (
    MonitorTaskCreate, MonitorTaskResponse, MonitorResultResponse,
    ScanRequest, ResultUpdateRequest, EvidencePackageCreate,
    FingerprintRequest, FingerprintResponse,
    FingerprintCompareRequest, FingerprintCompareResponse,
    BrandWatchCreate, BrandWatchUpdate, BrandWatchResponse,
    BrandScanResultResponse,
    DomainWatchCreate, DomainWatchResponse,
    CodeSimilarityRequest, CodeSimilarityResponse,
    WhitelistActionRequest,
    DeltaDetectionRequest, DeltaDetectionResult, DeltaDetectionResponse,
    QuotaStatusResponse, PlatformRotationStatus,
    PriorityScoreResult,
    VideoFingerprintMatch, VideoFingerprintScanResponse,
    AudioFingerprintGenerateResponse, AudioMatch, AudioScanResponse,
    TextPlagiarismMatch, TextPlagiarismScanResponse,
)
from app.schemas.common import ApiResponse
from app.services.embedding_service import (
    compute_all_fingerprints, hamming_distance, compute_similarity,
)
from app.services.logo_detector import generate_mock_ecommerce_results
from app.services.dmca_template import fill_dmca_template_from_work
from app.services.code_similarity import compare_code_snippets
from app.services.whitelist_learner import (
    record_whitelist_action, get_pending_suggestions,
    accept_suggestion, decline_suggestion,
)
from app.services.hasher import compute_sha256
from app.services.monitor_task_module import MonitorTaskModule, _PLATFORM_QUOTAS
from app.services.brand_watch_module import BrandWatchModule
from app.services.code_sim_module import CodeSimModule
from app.services.dmca_module import DmcaModule
from app.services.whitelist_module import WhitelistModule
from app.services.fingerprint_module import FingerprintModule

logger = logging.getLogger(__name__)


# 保留原有的模块级辅助函数供向后兼容
def _get_platform_usage(db: Session, platform: str) -> int:
    return MonitorTaskModule._get_platform_usage_static(db, platform)


def _calculate_priority_score(work, db: Session):
    from app.models.notary import NotaryRecord
    from app.models.monitor import MonitorResult as MR
    age_days = (datetime.now(timezone.utc) - work.created_at).days if work.created_at else 0
    has_notary = db.query(NotaryRecord).filter(
        NotaryRecord.work_id == work.id,
        NotaryRecord.status == "confirmed",
    ).count() > 0
    previous_infringements = db.query(MR).filter(
        MR.work_id == work.id,
        MR.status == "infringing",
    ).count()
    score = min(100, age_days * 0.5 + has_notary * 20 + previous_infringements * 15)
    return score, {
        "age_days": age_days,
        "has_notary": has_notary,
        "previous_infringements": previous_infringements,
    }


def _tokenize_text(text: str) -> list[str]:
    import re
    return re.findall(r'\w+', text.lower())


def _compute_tfidf_vector(doc_tokens: list[str], corpus_size: int) -> dict[str, float]:
    from collections import Counter
    tf = Counter(doc_tokens)
    total = len(doc_tokens)
    return {token: count / total for token, count in tf.items()}


def _cosine_similarity_sparse(vec_a: dict[str, float], vec_b: dict[str, float]) -> float:
    import math
    intersection = set(vec_a.keys()) & set(vec_b.keys())
    if not intersection:
        return 0.0
    dot_product = sum(vec_a[k] * vec_b[k] for k in intersection)
    norm_a = math.sqrt(sum(v ** 2 for v in vec_a.values()))
    norm_b = math.sqrt(sum(v ** 2 for v in vec_b.values()))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot_product / (norm_a * norm_b)


class MonitorService:
    """侵权监测业务逻辑服务 — 组合模式入口."""

    def __init__(self, db: Optional[Session] = None):
        self.db = db
        # 始终初始化子模块（即使没有 db，用于无 db 场景如 get_scan_quota）
        self._task = MonitorTaskModule(db)
        self._brand = BrandWatchModule(db)
        self._code = CodeSimModule(db)
        self._dmca = DmcaModule(db)
        self._whitelist = WhitelistModule(db)
        self._fingerprint = FingerprintModule(db)

    # ---- 委托到子模块 ----

    def list_monitor_tasks(self, work_id=None, status=None, platform=None):
        return self._task.list_tasks(work_id, status, platform) if self._task else None

    def create_monitor_task(self, data):
        return self._task.create_task(data) if self._task else None

    def trigger_scan(self, task_id: str):
        return self._task.trigger_scan(task_id) if self._task else None

    def batch_scan(self, data):
        return self._task.batch_scan(data) if self._task else None

    def list_monitor_results(self, task_id=None, status=None, page=1, page_size=20):
        return self._task.list_results(task_id, status, page, page_size) if self._task else None

    def update_result(self, result_id: str, data):
        return self._task.update_result(result_id, data) if self._task else None

    def get_scan_quota(self):
        return self._task.get_quota() if self._task else None

    def get_quota_rotation_status(self):
        return self._task.get_quota_rotation_status() if self._task else None

    def trigger_quota_rotation(self, platform: str):
        return self._task.trigger_quota_rotation(platform) if self._task else None

    def create_brand_watch(self, data):
        return self._brand.create_watch(data) if self._brand else None

    def list_brand_watches(self, is_active=None):
        return self._brand.list_watches(is_active) if self._brand else None

    def get_brand_watch(self, brand_id: str):
        return self._brand.get_watch(brand_id) if self._brand else None

    def update_brand_watch(self, brand_id: str, data):
        return self._brand.update_watch(brand_id, data) if self._brand else None

    def delete_brand_watch(self, brand_id: str):
        return self._brand.delete_watch(brand_id) if self._brand else None

    def trigger_brand_scan(self, brand_id: str):
        return self._brand.trigger_scan(brand_id) if self._brand else None

    def get_brand_scan_results(self, brand_id: str, status=None):
        return self._brand.get_scan_results(brand_id, status) if self._brand else None

    def check_code_similarity(self, data):
        return self._code.compare(data) if self._code else None

    def get_dmca_template(self, work_id: str):
        return self._dmca.get_template(work_id) if self._dmca else None

    def generate_evidence_package(self, result_id: str, data):
        return self._dmca.generate_evidence_package(result_id, data) if self._dmca else None

    def list_evidence_packages(self, work_id=None, package_type=None):
        return self._dmca.list_evidence_packages(work_id, package_type) if self._dmca else None

    def get_evidence_package(self, package_id: str):
        return self._dmca.get_evidence_package(package_id) if self._dmca else None

    def list_whitelist_suggestions(self):
        return self._whitelist.list_suggestions() if self._whitelist else None

    def handle_whitelist_action(self, data):
        return self._whitelist.handle_action(data) if self._whitelist else None

    def compute_fingerprints(self, data):
        return self._fingerprint.compute(data) if self._fingerprint else None

    def compare_fingerprints(self, data):
        return self._fingerprint.compare(data) if self._fingerprint else None

    def scan_video_fingerprint(self, task_id: str):
        return self._fingerprint.scan_video(task_id) if self._fingerprint else None

    def generate_audio_fingerprint(self, task_id: str):
        return self._fingerprint.generate_audio(task_id) if self._fingerprint else None

    def scan_audio_fingerprint(self, task_id: str, top_n=20):
        return self._fingerprint.scan_audio(task_id, top_n) if self._fingerprint else None

    def list_audio_matches(self, work_id=None, min_confidence=0.0):
        return self._fingerprint.list_audio_matches(work_id, min_confidence) if self._fingerprint else None

    def scan_text_plagiarism(self, work_ids=None, top_n=20):
        return self._fingerprint.scan_text_plagiarism(work_ids or [], top_n) if self._fingerprint else None

    def list_text_matches(self, work_id=None, min_similarity=0.0):
        return self._fingerprint.list_text_matches(work_id, min_similarity) if self._fingerprint else None

    # ---- 未委托方法（保持原有逻辑）----

    def register_domain_watch(self, data: DomainWatchCreate):
        """注册域名监测."""
        domain = DomainWatch(
            domain=data.domain,
            is_active=True,
            platforms=data.platforms or ["google", "baidu"],
        )
        self.db.add(domain)
        try:
            self.db.commit()
            self.db.refresh(domain)
        except Exception:
            self.db.rollback()
            raise
        return ApiResponse(data=DomainWatchResponse.model_validate(domain))

    def list_domain_watches(self, is_active=None):
        """获取域名监测列表."""
        query = self.db.query(DomainWatch)
        if is_active is not None:
            query = query.filter(DomainWatch.is_active == is_active)
        watches = query.order_by(DomainWatch.created_at.desc()).all()
        return ApiResponse(data=[DomainWatchResponse.model_validate(w) for w in watches])

    def delete_domain_watch(self, watch_id: str):
        """删除域名监测."""
        watch = self.db.query(DomainWatch).filter(DomainWatch.id == watch_id).first()
        if not watch:
            raise HTTPException(status_code=404, detail="域名监测不存在")
        self.db.delete(watch)
        try:
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise
        return ApiResponse(message="域名监测已删除")

    def whois_lookup(self, domain: str):
        """WHOIS 查询."""
        mock_data = {
            "domain": domain,
            "registrar": "Example Registrar",
            "creation_date": "2020-01-01",
            "expiration_date": "2025-01-01",
            "name_servers": ["ns1.example.com", "ns2.example.com"],
            "status": "active",
            "real_whois_apis": [
                "https://whoisxmlapi.com/ (commercial, ~$50/mo)",
                "https://www.whois.com/whois/{domain}",
                "https://lookup.icann.org/ (free RDAP)",
            ],
        }
        return ApiResponse(data=mock_data)

    def recalculate_task_priority(self, task_id: str):
        """为指定监测任务重新计算优先级评分."""
        task = self.db.query(MonitorTask).filter(MonitorTask.id == task_id).first()
        if not task:
            raise HTTPException(status_code=404, detail="监测任务不存在")
        work = self.db.query(Work).filter(Work.id == task.work_id).first()
        if not work:
            raise HTTPException(status_code=404, detail="关联作品不存在")
        score, factors = _calculate_priority_score(work, self.db)
        task.priority_score = score
        try:
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise
        return ApiResponse(
            message=f"Priority score for task {task_id}: {score}/100",
            data=PriorityScoreResult(
                work_id=work.id,
                title=work.title,
                age_days=factors.get("age_days", 0),
                has_notary=factors.get("has_notary", False),
                previous_infringements=factors.get("previous_infringements", 0),
                priority_score=score,
                factors=factors,
            ),
        )

    def list_task_priorities(self, platform=None, min_score=0.0):
        """列出所有监测任务的优先级评分."""
        query = self.db.query(MonitorTask)
        if platform:
            query = query.filter(MonitorTask.platform == platform)
        tasks = query.order_by(MonitorTask.priority_score.desc()).all()
        results = []
        for task in tasks:
            work = self.db.query(Work).filter(Work.id == task.work_id).first()
            if not work:
                continue
            if task.priority_score == 0.0:
                score, factors = _calculate_priority_score(work, self.db)
                task.priority_score = score
            else:
                score = task.priority_score
                _, factors = _calculate_priority_score(work, self.db)
            if score >= min_score:
                results.append(PriorityScoreResult(
                    work_id=work.id,
                    title=work.title,
                    age_days=factors.get("age_days", 0),
                    has_notary=factors.get("has_notary", False),
                    previous_infringements=factors.get("previous_infringements", 0),
                    priority_score=score,
                    factors=factors,
                ))
        try:
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise
        return ApiResponse(
            message=f"Found {len(results)} tasks with priority >= {min_score}",
            data=results,
        )

    def get_infringement_timeline(self, work_id: str):
        """获取指定作品的所有侵权检测结果时间线."""
        work = self.db.query(Work).filter(Work.id == work_id).first()
        if not work:
            raise HTTPException(status_code=404, detail="作品不存在")
        task_ids_subq = self.db.query(MonitorTask.id).filter(MonitorTask.work_id == work_id)
        results = (
            self.db.query(MonitorResult)
            .filter(MonitorResult.task_id.in_(task_ids_subq))
            .order_by(MonitorResult.found_at.asc(), MonitorResult.created_at.asc())
            .all()
        )
        brand_results = []
        try:
            brand_scan_results = (
                self.db.query(BrandScanResult, BrandWatch.brand_name)
                .join(BrandWatch, BrandScanResult.brand_id == BrandWatch.id)
                .filter(BrandWatch.brand_name.ilike(f"%{work.title}%"))
                .order_by(BrandScanResult.found_at.asc())
                .all()
            )
            for bsr, brand_name in brand_scan_results:
                brand_results.append({
                    "source": "brand_scan",
                    "brand_name": brand_name,
                    "platform": bsr.platform,
                    "item_url": bsr.item_url,
                    "item_title": bsr.item_title,
                    "similarity": bsr.similarity,
                    "found_at": bsr.found_at.isoformat() if bsr.found_at else None,
                    "status": bsr.status,
                    "notes": bsr.notes,
                })
        except Exception as e:
            logger.exception("Error in generate_copyright_infringement: %s", str(e))
        timeline_entries = []
        for r in results:
            timeline_entries.append({
                "source": "monitor_task",
                "result_id": r.id,
                "task_id": r.task_id,
                "matched_url": r.matched_url,
                "matched_title": r.matched_title,
                "similarity": r.similarity,
                "found_at": r.found_at.isoformat() if r.found_at else None,
                "status": r.status,
                "action_taken": r.action_taken,
                "notes": r.notes,
            })
        all_entries = timeline_entries + brand_results
        all_entries.sort(key=lambda x: x.get("found_at") or "")
        return ApiResponse(
            message=f"Infringement timeline for work '{work.title}' - {len(all_entries)} entries",
            data={
                "work_id": work_id,
                "work_title": work.title,
                "total_entries": len(all_entries),
                "by_status": {
                    status: len([e for e in all_entries if e.get("status") == status])
                    for status in sorted(set(e.get("status") for e in all_entries))
                },
                "timeline": all_entries,
            },
        )

    def delta_detection(self, data: DeltaDetectionRequest):
        """Delta 检测 — 预扫描哈希比对."""
        now = datetime.now(timezone.utc)
        results = []
        works_changed = 0
        works_unchanged = 0
        scans_triggered = 0
        for work_id in data.work_ids:
            work = self.db.query(Work).filter(Work.id == work_id).first()
            if not work or not work.sha256:
                continue
            old_hash = work.sha256
            new_hash = compute_sha256(str(work.file_path)) if work.file_path else old_hash
            if new_hash != old_hash:
                works_changed += 1
                scans_triggered += 1
                task = self.db.query(MonitorTask).filter(
                    MonitorTask.work_id == work_id,
                    MonitorTask.status == "active",
                ).first()
                if task:
                    task.last_run = now
                    results.append(DeltaDetectionResult(
                        work_id=work_id,
                        title=work.title,
                        old_hash=old_hash[:16],
                        new_hash=new_hash[:16],
                        scan_triggered=True,
                    ))
            else:
                works_unchanged += 1
                results.append(DeltaDetectionResult(
                    work_id=work_id,
                    title=work.title,
                    old_hash=old_hash[:16],
                    new_hash=new_hash[:16] if new_hash else old_hash[:16],
                    scan_triggered=False,
                ))
        try:
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise
        return ApiResponse(
            message=f"Delta detection: {works_changed} changed, {works_unchanged} unchanged, "
                    f"{scans_triggered} scans triggered (out of {len(results)} works)",
            data=DeltaDetectionResponse(
                results=results,
                works_changed=works_changed,
                works_unchanged=works_unchanged,
                scans_triggered=scans_triggered,
            ),
        )
