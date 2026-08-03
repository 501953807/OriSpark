# -*- coding: utf-8 -*-
"""侵权监测 API 路由 — 对应: docs/modules-v5/02-rights-protection.md
Phase 1: 视频指纹监测、音频指纹、文本查重
端点: 39 (monitor)

业务逻辑已提取至 monitor_service.py.
"""

from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import require_auth
from app.schemas.monitor import (
    MonitorTaskCreate, MonitorResultResponse,
    ScanRequest, ResultUpdateRequest, EvidencePackageCreate,
    FingerprintRequest,
    FingerprintCompareRequest,
    BrandWatchCreate, BrandWatchUpdate,
    DomainWatchCreate,
    CodeSimilarityRequest,
    WhitelistActionRequest,
    DeltaDetectionRequest,
)
from app.schemas.common import ApiResponse
from app.services.monitor_service import MonitorService

router = APIRouter()


# ============================================================
# 监测任务 CRUD
# ============================================================

@router.get("/monitor/tasks", response_model=ApiResponse)
def list_monitor_tasks(
    work_id: Optional[str] = None,
    status: Optional[str] = None,
    platform: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """获取监测任务列表."""
    svc = MonitorService(db)
    return svc.list_monitor_tasks(work_id, status, platform)


@router.post(
    "/monitor/tasks",
    response_model=ApiResponse,
    dependencies=[Depends(require_auth)],
)
def create_monitor_task(data: MonitorTaskCreate, db: Session = Depends(get_db)):
    """创建监测任务."""
    svc = MonitorService(db)
    return svc.create_monitor_task(data)


@router.post(
    "/monitor/tasks/{task_id}/scan",
    response_model=ApiResponse,
    dependencies=[Depends(require_auth)],
)
def trigger_scan(task_id: str, db: Session = Depends(get_db)):
    """手动触发扫描."""
    svc = MonitorService(db)
    return svc.trigger_scan(task_id)


@router.post(
    "/monitor/scan",
    response_model=ApiResponse,
    dependencies=[Depends(require_auth)],
)
def batch_scan(data: ScanRequest, db: Session = Depends(get_db)):
    """批量手动扫描 (带去重)."""
    svc = MonitorService(db)
    return svc.batch_scan(data)


@router.get("/monitor/results", response_model=ApiResponse)
def list_monitor_results(
    task_id: Optional[str] = None,
    status: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """获取监测结果列表."""
    svc = MonitorService(db)
    return svc.list_monitor_results(task_id, status, page, page_size)


@router.patch(
    "/monitor/results/{result_id}",
    response_model=ApiResponse,
    dependencies=[Depends(require_auth)],
)
def update_result(result_id: str, data: ResultUpdateRequest, db: Session = Depends(get_db)):
    """更新监测结果状态 (含白名单学习触发)."""
    svc = MonitorService(db)
    return svc.update_result(result_id, data)


@router.post(
    "/monitor/results/{result_id}/evidence",
    response_model=ApiResponse,
    dependencies=[Depends(require_auth)],
)
def generate_evidence_package(result_id: str, data: EvidencePackageCreate, db: Session = Depends(get_db)):
    """生成维权证据包."""
    svc = MonitorService(db)
    return svc.generate_evidence_package(result_id, data)


@router.get("/monitor/evidence", response_model=ApiResponse)
def list_evidence_packages(
    work_id: Optional[str] = None,
    package_type: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """获取证据包列表."""
    svc = MonitorService(db)
    return svc.list_evidence_packages(work_id, package_type)


@router.get("/monitor/evidence/{package_id}", response_model=ApiResponse)
def get_evidence_package(package_id: str, db: Session = Depends(get_db)):
    """获取单个证据包详情."""
    svc = MonitorService(db)
    return svc.get_evidence_package(package_id)


@router.get("/monitor/quota", response_model=ApiResponse)
def get_scan_quota():
    """获取扫描配额信息."""
    svc = MonitorService()
    return svc.get_scan_quota()


# ============================================================
# 本地视觉指纹
# ============================================================

@router.post(
    "/monitor/fingerprints",
    response_model=ApiResponse,
    dependencies=[Depends(require_auth)],
)
def compute_fingerprints(data: FingerprintRequest, db: Session = Depends(get_db)):
    """计算并存储作品的感知哈希指纹."""
    svc = MonitorService(db)
    return svc.compute_fingerprints(data)


@router.post(
    "/monitor/fingerprints/compare",
    response_model=ApiResponse,
    dependencies=[Depends(require_auth)],
)
def compare_fingerprints(data: FingerprintCompareRequest, db: Session = Depends(get_db)):
    """比对两个作品的指纹相似度."""
    svc = MonitorService(db)
    return svc.compare_fingerprints(data)


# ============================================================
# 品牌监测
# ============================================================

@router.post(
    "/monitor/brand-watches",
    response_model=ApiResponse,
    dependencies=[Depends(require_auth)],
)
def create_brand_watch(data: BrandWatchCreate, db: Session = Depends(get_db)):
    """注册品牌监测."""
    svc = MonitorService(db)
    return svc.create_brand_watch(data)


@router.get("/monitor/brand-watches", response_model=ApiResponse)
def list_brand_watches(
    is_active: Optional[bool] = None,
    db: Session = Depends(get_db),
):
    """获取品牌监测列表."""
    svc = MonitorService(db)
    return svc.list_brand_watches(is_active)


@router.get("/monitor/brand-watches/{brand_id}", response_model=ApiResponse)
def get_brand_watch(brand_id: str, db: Session = Depends(get_db)):
    """获取单个品牌监测详情."""
    svc = MonitorService(db)
    return svc.get_brand_watch(brand_id)


@router.patch(
    "/monitor/brand-watches/{brand_id}",
    response_model=ApiResponse,
    dependencies=[Depends(require_auth)],
)
def update_brand_watch(brand_id: str, data: BrandWatchUpdate, db: Session = Depends(get_db)):
    """更新品牌监测."""
    svc = MonitorService(db)
    return svc.update_brand_watch(brand_id, data)


@router.delete(
    "/monitor/brand-watches/{brand_id}",
    response_model=ApiResponse,
    dependencies=[Depends(require_auth)],
)
def delete_brand_watch(brand_id: str, db: Session = Depends(get_db)):
    """删除品牌监测."""
    svc = MonitorService(db)
    return svc.delete_brand_watch(brand_id)


@router.post(
    "/monitor/brands/{brand_id}/scan",
    response_model=ApiResponse,
    dependencies=[Depends(require_auth)],
)
def trigger_brand_scan(brand_id: str, db: Session = Depends(get_db)):
    """触发品牌扫描."""
    svc = MonitorService(db)
    return svc.trigger_brand_scan(brand_id)


@router.get("/monitor/brands/{brand_id}/results", response_model=ApiResponse)
def get_brand_scan_results(
    brand_id: str,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """获取品牌扫描结果."""
    svc = MonitorService(db)
    return svc.get_brand_scan_results(brand_id, status)


# ============================================================
# 域名监测
# ============================================================

@router.post(
    "/monitor/domains/watch",
    response_model=ApiResponse,
    dependencies=[Depends(require_auth)],
)
def register_domain_watch(data: DomainWatchCreate, db: Session = Depends(get_db)):
    """注册域名监测."""
    svc = MonitorService(db)
    return svc.register_domain_watch(data)


@router.get("/monitor/domains/watch", response_model=ApiResponse)
def list_domain_watches(
    is_active: Optional[bool] = None,
    db: Session = Depends(get_db),
):
    """获取域名监测列表."""
    svc = MonitorService(db)
    return svc.list_domain_watches(is_active)


@router.delete(
    "/monitor/domains/watch/{watch_id}",
    response_model=ApiResponse,
    dependencies=[Depends(require_auth)],
)
def delete_domain_watch(watch_id: str, db: Session = Depends(get_db)):
    """删除域名监测."""
    svc = MonitorService(db)
    return svc.delete_domain_watch(watch_id)


@router.post(
    "/monitor/domains/whois-lookup",
    response_model=ApiResponse,
    dependencies=[Depends(require_auth)],
)
def whois_lookup(domain: str = Query(..., description="域名名称"), db: Session = Depends(get_db)):
    """WHOIS 信息查询 (Stub)."""
    svc = MonitorService(db)
    return svc.whois_lookup(domain)


# ============================================================
# DMCA 模板
# ============================================================

@router.get("/monitor/evidence/dmca/{work_id}", response_model=ApiResponse)
def get_dmca_template(work_id: str, db: Session = Depends(get_db)):
    """获取预填的 DMCA Takedown Notice 模板."""
    svc = MonitorService(db)
    return svc.get_dmca_template(work_id)


# ============================================================
# 代码抄袭检测
# ============================================================

@router.post(
    "/monitor/check/code",
    response_model=ApiResponse,
    dependencies=[Depends(require_auth)],
)
def check_code_similarity(data: CodeSimilarityRequest):
    """检测两个代码片段的相似度."""
    svc = MonitorService()
    return svc.check_code_similarity(data)


# ============================================================
# 白名单学习
# ============================================================

@router.get("/monitor/whitelist-suggestions", response_model=ApiResponse)
def list_whitelist_suggestions(db: Session = Depends(get_db)):
    """获取白名单自动建议."""
    svc = MonitorService(db)
    return svc.list_whitelist_suggestions()


@router.post(
    "/monitor/whitelist-suggestions/action",
    response_model=ApiResponse,
    dependencies=[Depends(require_auth)],
)
def handle_whitelist_action(data: WhitelistActionRequest, db: Session = Depends(get_db)):
    """处理白名单建议 (接受/拒绝)."""
    svc = MonitorService(db)
    return svc.handle_whitelist_action(data)


# ============================================================
# 侵权时间线
# ============================================================

@router.get("/monitor/results/{work_id}/timeline", response_model=ApiResponse)
def get_infringement_timeline(work_id: str, db: Session = Depends(get_db)):
    """获取指定作品的所有侵权检测结果时间线."""
    svc = MonitorService(db)
    return svc.get_infringement_timeline(work_id)


# ============================================================
# Delta 检测
# ============================================================

@router.post(
    "/monitor/delta",
    response_model=ApiResponse,
    dependencies=[Depends(require_auth)],
)
def delta_detection(data: DeltaDetectionRequest, db: Session = Depends(get_db)):
    """Delta 检测 — 预扫描哈希比对."""
    svc = MonitorService(db)
    return svc.delta_detection(data)


# ============================================================
# 配额轮转
# ============================================================

@router.get("/monitor/quota/rotation", response_model=ApiResponse)
def get_quota_rotation_status(db: Session = Depends(get_db)):
    """获取跨平台配额轮转状态."""
    svc = MonitorService(db)
    return svc.get_quota_rotation_status()


@router.post("/monitor/quota/rotate", response_model=ApiResponse, dependencies=[Depends(require_auth)])
def trigger_quota_rotation(platform: str = Query(...), db: Session = Depends(get_db)):
    """手动触发配额轮转."""
    svc = MonitorService(db)
    return svc.trigger_quota_rotation(platform)


# ============================================================
# 优先级评分
# ============================================================

@router.post(
    "/monitor/tasks/{task_id}/recalculate-priority",
    response_model=ApiResponse,
    dependencies=[Depends(require_auth)],
)
def recalculate_task_priority(task_id: str, db: Session = Depends(get_db)):
    """为指定监测任务重新计算优先级评分."""
    svc = MonitorService(db)
    return svc.recalculate_task_priority(task_id)


@router.get("/monitor/tasks/priorities", response_model=ApiResponse)
def list_task_priorities(
    platform: Optional[str] = None,
    min_score: float = Query(0.0, ge=0, le=100),
    db: Session = Depends(get_db),
):
    """列出所有监测任务的优先级评分."""
    svc = MonitorService(db)
    return svc.list_task_priorities(platform, min_score)


# ============================================================
# 视频指纹扫描
# ============================================================

@router.post(
    "/monitor/scan-video-fingerprint",
    response_model=ApiResponse,
    dependencies=[Depends(require_auth)],
)
def scan_video_fingerprint(task_id: str, db: Session = Depends(get_db)):
    """Scan for video fingerprint matches."""
    svc = MonitorService(db)
    return svc.scan_video_fingerprint(task_id)


# ============================================================
# 音频指纹
# ============================================================

@router.post(
    "/monitor/generate-audio-fingerprint",
    response_model=ApiResponse,
    dependencies=[Depends(require_auth)],
)
def generate_audio_fingerprint(task_id: str, db: Session = Depends(get_db)):
    """Extract audio metadata and create a spectral fingerprint."""
    svc = MonitorService(db)
    return svc.generate_audio_fingerprint(task_id)


@router.post(
    "/monitor/scan-audio-fingerprint",
    response_model=ApiResponse,
    dependencies=[Depends(require_auth)],
)
def scan_audio_fingerprint(task_id: str, top_n: int = 20, db: Session = Depends(get_db)):
    """Scan for audio fingerprint matches."""
    svc = MonitorService(db)
    return svc.scan_audio_fingerprint(task_id, top_n)


@router.get("/monitor/audio-matches", response_model=ApiResponse)
def list_audio_matches(
    work_id: Optional[str] = None,
    min_confidence: float = Query(0.0, ge=0, le=100),
    db: Session = Depends(get_db),
):
    """获取音频指纹扫描结果列表."""
    svc = MonitorService(db)
    return svc.list_audio_matches(work_id, min_confidence)


# ============================================================
# 文本抄袭检测
# ============================================================

@router.post(
    "/monitor/scan-text",
    response_model=ApiResponse,
    dependencies=[Depends(require_auth)],
)
def scan_text_plagiarism(
    work_ids: list[str] = Query(
        default=[], min_length=0, max_length=50,
        description="作品ID列表; 为空则扫描全部文本作品",
    ),
    top_n: int = Query(20, ge=1, le=100, description="返回top N匹配"),
    db: Session = Depends(get_db),
):
    """Scan for text plagiarism among works with text content."""
    svc = MonitorService(db)
    return svc.scan_text_plagiarism(work_ids, top_n)


@router.get("/monitor/text-matches", response_model=ApiResponse)
def list_text_matches(
    work_id: Optional[str] = None,
    min_similarity: float = Query(0.0, ge=0, le=100),
    db: Session = Depends(get_db),
):
    """获取文本相似度检测历史记录."""
    svc = MonitorService(db)
    return svc.list_text_matches(work_id, min_similarity)
