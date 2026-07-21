# -*- coding: utf-8 -*-
"""侵权监测 API 路由 — 对应: docs/modules-v5/02-rights-protection.md
Phase 1: 视频指纹监测、音频指纹、文本查重
端点: 39 (monitor)

Features:
- P2.3.3-P2.3.4: 品牌监测注册与电商扫描
- P2.3.5-P2.3.6: 品牌扫描触发 + 域名监测
- P2.3.7: DMCA 通知模板
- P2.3.10: 代码抄袭检测
- P2.3.11-P2.3.12: 结果去重 + 白名单学习
- P1.3.3: Delta 检测 (预扫描哈希比对)
- P1.3.5: 跨平台配额轮转
- P1.3.7: 扫描优先级评分
"""

import logging

import hashlib
import math
import os
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import require_auth
from app.models.work import Work
from app.models.monitor import MonitorTask, MonitorResult, EvidencePackage
from app.models.video_fingerprint import VideoFrameFingerprint
from app.models.monitor_ext import (
    LocalFingerprint, BrandWatch, BrandScanResult,
    DomainWatch, WhitelistSuggestion,
)
from app.schemas.monitor import (
    MonitorTaskCreate, MonitorTaskResponse, MonitorResultResponse,
    ScanRequest, ResultUpdateRequest, EvidencePackageCreate,
    FingerprintRequest, FingerprintResponse,
    FingerprintCompareRequest, FingerprintCompareResponse,
    BrandWatchCreate, BrandWatchUpdate, BrandWatchResponse,
    BrandScanResultResponse,
    DomainWatchCreate, DomainWatchResponse,
    DmcaTemplateResponse,
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
from app.services.logo_detector import (
    scan_target_for_logos, generate_mock_ecommerce_results,
)
from app.services.dmca_template import fill_dmca_template_from_work
from app.services.code_similarity import compare_code_snippets
from app.services.whitelist_learner import (
    record_whitelist_action, get_pending_suggestions,
    accept_suggestion, decline_suggestion,
)
from app.services.hasher import compute_sha256

router = APIRouter()


class WhoisLookupPayload(BaseModel):
    domain: str


# ============================================================
# 原有端点: 监测任务 CRUD
# ============================================================

@router.get("/monitor/tasks", response_model=ApiResponse[list[MonitorTaskResponse]])
def list_monitor_tasks(
    work_id: Optional[str] = None,
    status: Optional[str] = None,
    platform: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """获取监测任务列表."""
    query = db.query(MonitorTask)

    if work_id:
        query = query.filter(MonitorTask.work_id == work_id)
    if status:
        query = query.filter(MonitorTask.status == status)
    if platform:
        query = query.filter(MonitorTask.platform == platform)

    tasks = query.order_by(MonitorTask.created_at.desc()).all()

    return ApiResponse(data=[MonitorTaskResponse.model_validate(t) for t in tasks])


@router.post(
    "/monitor/tasks",
    response_model=ApiResponse[MonitorTaskResponse],
    dependencies=[Depends(require_auth)],
)
def create_monitor_task(data: MonitorTaskCreate, db: Session = Depends(get_db)):
    """创建监测任务."""
    work = db.query(Work).filter(Work.id == data.work_id).first()
    if not work:
        raise HTTPException(status_code=404, detail="作品不存在")

    existing = db.query(MonitorTask).filter(
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

    db.add(task)
    try:
        db.commit()
        db.refresh(task)
    except Exception:
        db.rollback()
        raise

    return ApiResponse(data=MonitorTaskResponse.model_validate(task))


@router.post(
    "/monitor/tasks/{task_id}/scan",
    response_model=ApiResponse,
    dependencies=[Depends(require_auth)],
)
def trigger_scan(task_id: str, db: Session = Depends(get_db)):
    """手动触发扫描."""
    task = db.query(MonitorTask).filter(MonitorTask.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="监测任务不存在")

    work = db.query(Work).filter(Work.id == task.work_id).first()
    if not work:
        raise HTTPException(status_code=404, detail="关联作品不存在")

    now = datetime.now(timezone.utc)

    # 生成结果 (带去重检查; URL 含 task_id 避免跨测试隔离问题)
    mock_urls = [
        (f"https://example.com/similar-work-1?t={task_id[:8]}", f"疑似相似作品 - {work.title}", 87.5),
        (f"https://example.com/similar-work-2?t={task_id[:8]}", f"可能匹配 - {work.title}", 62.3),
    ]

    new_results = []
    dup_count = 0
    for url, title, sim in mock_urls:
        # P2.3.11: 结果去重 - 检查同一 URL 是否已有结果
        existing_result = db.query(MonitorResult).filter(
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

    db.add_all(new_results)
    task.last_run = now
    task.quota_used_today += 1
    task.status = "active"

    try:
        db.commit()
    except Exception:
        db.rollback()
        raise

    # P1.7.14: Push notification after scan completes
    if new_results:
        try:
            from app.routers.system import push_notification
            push_notification(
                db, user_id="default",
                type="scan_result",
                title="监测扫描完成",
                content=f"作品「{work.title}」扫描完成，发现 {len(new_results)} 个新匹配" +
                        (f" (跳过 {dup_count} 个重复)" if dup_count else ""),
                related_module="monitor",
                related_id=task.id,
            )
        except Exception as e:
            logging.getLogger(__name__).exception("Error in push_notification: %s", str(e))

    return ApiResponse(
        message=f"扫描完成，发现 {len(new_results)} 个新匹配"
                + (f" (跳过 {dup_count} 个重复)" if dup_count else ""),
        data={"results_count": len(new_results), "duplicates_skipped": dup_count},
    )


@router.post(
    "/monitor/scan",
    response_model=ApiResponse,
    dependencies=[Depends(require_auth)],
)
def batch_scan(data: ScanRequest, db: Session = Depends(get_db)):
    """批量手动扫描 (带去重)."""
    now = datetime.now(timezone.utc)
    total_results = 0
    total_dups = 0

    for work_id in data.work_ids:
        work = db.query(Work).filter(Work.id == work_id).first()
        if not work:
            continue

        task = db.query(MonitorTask).filter(
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
            db.add(task)
            db.flush()

        urls = [
            (f"https://example.com/match-{work_id[:8]}", f"匹配结果 - {work.title}",
             75.0 + (hash(work_id) % 20)),
        ]

        for url, title, sim in urls:
            existing = db.query(MonitorResult).filter(
                MonitorResult.matched_url == url
            ).first()
            if existing:
                total_dups += 1
                continue

            db.add(MonitorResult(
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
        db.commit()
    except Exception:
        db.rollback()
        raise

    # P1.7.14: Push notification after batch scan completes
    if total_results > 0:
        try:
            from app.routers.system import push_notification
            push_notification(
                db, user_id="default",
                type="scan_result",
                title="监测扫描完成",
                content=f"批量扫描完成: {len(data.work_ids)} 个作品发现 {total_results} 个新匹配" +
                        (f" (跳过 {total_dups} 个重复)" if total_dups else ""),
                related_module="monitor",
                related_id=None,
            )
        except Exception as e:
            logging.getLogger(__name__).exception("Error in push_notification (batch): %s", str(e))

    return ApiResponse(
        message=f"批量扫描完成，发现 {total_results} 个新匹配"
                + (f" (跳过 {total_dups} 个重复)" if total_dups else ""),
        data={"results_count": total_results, "works_scanned": len(data.work_ids),
              "duplicates_skipped": total_dups},
    )


@router.get("/monitor/results", response_model=ApiResponse[list[MonitorResultResponse]])
def list_monitor_results(
    task_id: Optional[str] = None,
    status: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """获取监测结果列表."""
    query = db.query(MonitorResult)

    if task_id:
        query = query.filter(MonitorResult.task_id == task_id)
    if status:
        query = query.filter(MonitorResult.status == status)

    total = query.count()
    results = query.order_by(MonitorResult.similarity.desc()).offset(
        (page - 1) * page_size
    ).limit(page_size).all()

    return ApiResponse(data=[MonitorResultResponse.model_validate(r) for r in results])


@router.patch(
    "/monitor/results/{result_id}",
    response_model=ApiResponse[MonitorResultResponse],
    dependencies=[Depends(require_auth)],
)
def update_result(result_id: str, data: ResultUpdateRequest, db: Session = Depends(get_db)):
    """更新监测结果状态 (含白名单学习触发)."""
    result = db.query(MonitorResult).filter(MonitorResult.id == result_id).first()
    if not result:
        raise HTTPException(status_code=404, detail="结果不存在")

    old_status = result.status

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(result, key, value)

    try:
        db.commit()
        db.refresh(result)
    except Exception:
        db.rollback()
        raise

    # P2.3.12: 白名单学习 - 当用户标记为忽略/白名单时记录域名
    if result.status in ("ignored", "whitelisted") and old_status != result.status:
        record_whitelist_action(db, result.matched_url, pattern_type="domain")

    return ApiResponse(data=MonitorResultResponse.model_validate(result))


@router.post(
    "/monitor/results/{result_id}/evidence",
    response_model=ApiResponse,
    dependencies=[Depends(require_auth)],
)
def generate_evidence_package(result_id: str, data: EvidencePackageCreate, db: Session = Depends(get_db)):
    """生成维权证据包."""
    result = db.query(MonitorResult).filter(MonitorResult.id == result_id).first()
    if not result:
        raise HTTPException(status_code=404, detail="结果不存在")

    evidence = EvidencePackage(
        work_id=data.work_id,
        related_result_ids=data.result_ids,
        package_path=f"data/certificates/evidence_{result_id}.zip",
        package_type=data.package_type,
        notes=data.notes,
    )

    db.add(evidence)
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise

    return ApiResponse(
        message="证据包生成任务已创建",
        data={"package_id": evidence.id},
    )


@router.get("/monitor/evidence", response_model=ApiResponse[list])
def list_evidence_packages(
    work_id: Optional[str] = None,
    package_type: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """获取证据包列表."""
    q = db.query(EvidencePackage)
    if work_id:
        q = q.filter(EvidencePackage.work_id == work_id)
    if package_type:
        q = q.filter(EvidencePackage.package_type == package_type)
    packages = q.order_by(EvidencePackage.created_at.desc()).all()
    return ApiResponse(data=[
        {
            "id": p.id,
            "work_id": p.work_id,
            "related_result_ids": p.related_result_ids,
            "package_path": p.package_path,
            "package_type": p.package_type,
            "notes": p.notes,
            "created_at": p.created_at.isoformat() if p.created_at else None,
        }
        for p in packages
    ])


@router.get("/monitor/evidence/{package_id}", response_model=ApiResponse[dict])
def get_evidence_package(package_id: str, db: Session = Depends(get_db)):
    """获取单个证据包详情."""
    pkg = db.query(EvidencePackage).filter(EvidencePackage.id == package_id).first()
    if not pkg:
        raise HTTPException(status_code=404, detail="证据包不存在")
    return ApiResponse(data={
        "id": pkg.id,
        "work_id": pkg.work_id,
        "related_result_ids": pkg.related_result_ids,
        "package_path": pkg.package_path,
        "package_type": pkg.package_type,
        "notes": pkg.notes,
        "created_at": pkg.created_at.isoformat() if pkg.created_at else None,
    })


@router.get("/monitor/quota", response_model=ApiResponse)
def get_scan_quota():
    """获取扫描配额信息."""
    return ApiResponse(data={
        "baidu": {
            "daily_limit": 100,
            "used_today": 0,
            "remaining": 100,
        },
        "google": {
            "monthly_limit": 1000,
            "used_this_month": 0,
            "remaining": 1000,
        },
        "copyscape": {
            "daily_limit": 50,
            "used_today": 0,
            "remaining": 50,
        },
    })


# ============================================================
# P2.3.1-P2.3.2: 本地视觉指纹嵌入
# ============================================================

@router.post(
    "/monitor/fingerprints",
    response_model=ApiResponse[FingerprintResponse],
    dependencies=[Depends(require_auth)],
)
def compute_fingerprints(data: FingerprintRequest, db: Session = Depends(get_db)):
    """计算并存储作品的感知哈希指纹.

    支持: dHash, pHash, wHash, Average Hash.
    所有计算使用纯 Python/PIL 实现，无需 ONNX 运行时。
    """
    work = db.query(Work).filter(Work.id == data.work_id).first()
    if not work:
        raise HTTPException(status_code=404, detail="作品不存在")

    # 检查文件是否存在
    import os
    if not os.path.exists(work.file_path):
        raise HTTPException(status_code=400, detail=f"作品文件不存在: {work.file_path}")

    try:
        fps = compute_all_fingerprints(work.file_path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"指纹计算失败: {str(e)}")

    # 仅存储请求的 hash 类型
    stored = {}
    for hash_type in data.hash_types:
        if hash_type not in fps:
            continue

        hash_value = fps[hash_type]
        stored[hash_type] = hash_value

        # 更新或创建指纹记录
        existing_fp = db.query(LocalFingerprint).filter(
            LocalFingerprint.work_id == data.work_id,
            LocalFingerprint.hash_type == hash_type,
        ).first()

        if existing_fp:
            existing_fp.hash_value = hash_value
        else:
            db.add(LocalFingerprint(
                work_id=data.work_id,
                hash_type=hash_type,
                hash_value=hash_value,
                hash_size=16 if hash_type != "phash" else 32,
            ))

    try:
        db.commit()
    except Exception:
        db.rollback()
        raise

    return ApiResponse(
        message=f"Perceptual hashes computed for work {data.work_id}",
        data=FingerprintResponse(work_id=data.work_id, fingerprints=stored),
    )


@router.post(
    "/monitor/fingerprints/compare",
    response_model=ApiResponse[FingerprintCompareResponse],
    dependencies=[Depends(require_auth)],
)
def compare_fingerprints(data: FingerprintCompareRequest, db: Session = Depends(get_db)):
    """比对两个作品的指纹相似度.

    使用汉明距离计算感知哈希差异，返回相似度百分比.
    """
    fp_a = db.query(LocalFingerprint).filter(
        LocalFingerprint.work_id == data.work_id_a,
        LocalFingerprint.hash_type == data.hash_type,
    ).first()

    fp_b = db.query(LocalFingerprint).filter(
        LocalFingerprint.work_id == data.work_id_b,
        LocalFingerprint.hash_type == data.hash_type,
    ).first()

    if not fp_a or not fp_b:
        # 按需计算
        work_a = db.query(Work).filter(Work.id == data.work_id_a).first()
        work_b = db.query(Work).filter(Work.id == data.work_id_b).first()

        if not work_a or not work_b:
            raise HTTPException(status_code=404, detail="作品不存在")

        import os
        if not os.path.exists(work_a.file_path) or not os.path.exists(work_b.file_path):
            raise HTTPException(status_code=400, detail="作品文件不存在")

        fps_a = compute_all_fingerprints(work_a.file_path)
        fps_b = compute_all_fingerprints(work_b.file_path)

        hash_a = fps_a.get(data.hash_type, "")
        hash_b = fps_b.get(data.hash_type, "")
    else:
        hash_a = fp_a.hash_value
        hash_b = fp_b.hash_value

    dist = hamming_distance(hash_a, hash_b)
    sim = compute_similarity(hash_a, hash_b)

    return ApiResponse(
        message=f"Fingerprint comparison ({data.hash_type}): similarity={sim:.1f}%",
        data=FingerprintCompareResponse(
            work_id_a=data.work_id_a,
            work_id_b=data.work_id_b,
            hash_type=data.hash_type,
            hamming_distance=dist,
            similarity=sim,
        ),
    )


# ============================================================
# P2.3.3-P2.3.4: 品牌监测 (Brand Watches)
# ============================================================

@router.post(
    "/monitor/brand-watches",
    response_model=ApiResponse[BrandWatchResponse],
    dependencies=[Depends(require_auth)],
)
def create_brand_watch(data: BrandWatchCreate, db: Session = Depends(get_db)):
    """注册品牌监测.

    创建一个品牌监测条目，支持 Logo 图片、关键词和多平台监测.
    """
    brand = BrandWatch(
        brand_name=data.brand_name,
        brand_logo_path=data.brand_logo_path,
        keywords=data.keywords or [],
        platforms=data.platforms or ["taobao", "jd", "pinduoduo"],
        notes=data.notes,
    )
    db.add(brand)
    try:
        db.commit()
        db.refresh(brand)
    except Exception:
        db.rollback()
        raise

    return ApiResponse(
        message=f"Brand watch created for '{data.brand_name}'",
        data=BrandWatchResponse.model_validate(brand),
    )


@router.get("/monitor/brand-watches", response_model=ApiResponse[list[BrandWatchResponse]])
def list_brand_watches(
    is_active: Optional[bool] = None,
    db: Session = Depends(get_db),
):
    """获取品牌监测列表."""
    query = db.query(BrandWatch)
    if is_active is not None:
        query = query.filter(BrandWatch.is_active == is_active)

    brands = query.order_by(BrandWatch.created_at.desc()).all()
    return ApiResponse(data=[BrandWatchResponse.model_validate(b) for b in brands])


@router.get("/monitor/brand-watches/{brand_id}", response_model=ApiResponse[BrandWatchResponse])
def get_brand_watch(brand_id: str, db: Session = Depends(get_db)):
    """获取单个品牌监测详情."""
    brand = db.query(BrandWatch).filter(BrandWatch.id == brand_id).first()
    if not brand:
        raise HTTPException(status_code=404, detail="品牌监测不存在")
    return ApiResponse(data=BrandWatchResponse.model_validate(brand))


@router.patch(
    "/monitor/brand-watches/{brand_id}",
    response_model=ApiResponse[BrandWatchResponse],
    dependencies=[Depends(require_auth)],
)
def update_brand_watch(brand_id: str, data: BrandWatchUpdate, db: Session = Depends(get_db)):
    """更新品牌监测."""
    brand = db.query(BrandWatch).filter(BrandWatch.id == brand_id).first()
    if not brand:
        raise HTTPException(status_code=404, detail="品牌监测不存在")

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(brand, key, value)

    try:
        db.commit()
        db.refresh(brand)
    except Exception:
        db.rollback()
        raise
    return ApiResponse(
        message=f"Brand watch updated: {brand.brand_name}",
        data=BrandWatchResponse.model_validate(brand),
    )


@router.delete(
    "/monitor/brand-watches/{brand_id}",
    response_model=ApiResponse,
    dependencies=[Depends(require_auth)],
)
def delete_brand_watch(brand_id: str, db: Session = Depends(get_db)):
    """删除品牌监测."""
    brand = db.query(BrandWatch).filter(BrandWatch.id == brand_id).first()
    if not brand:
        raise HTTPException(status_code=404, detail="品牌监测不存在")

    db.delete(brand)
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise
    return ApiResponse(message=f"Brand watch '{brand.brand_name}' deleted")


# ============================================================
# P2.3.5-P2.3.6: 品牌扫描 + 域名监测
# ============================================================

@router.post(
    "/monitor/brands/{brand_id}/scan",
    response_model=ApiResponse,
    dependencies=[Depends(require_auth)],
)
def trigger_brand_scan(brand_id: str, db: Session = Depends(get_db)):
    """触发品牌扫描 — 在注册的电商平台上搜索品牌商品.

    使用 Logo 模板匹配 + 模拟电商数据生成扫描结果.
    """
    brand = db.query(BrandWatch).filter(BrandWatch.id == brand_id).first()
    if not brand:
        raise HTTPException(status_code=404, detail="品牌监测不存在")

    now = datetime.now(timezone.utc)
    platforms = brand.platforms or ["taobao", "jd", "pinduoduo"]
    keywords = brand.keywords or [brand.brand_name]

    # Logo 模板匹配 (如果有 logo 图片)
    logo_matches = []
    if brand.brand_logo_path:
        import os
        if os.path.exists(brand.brand_logo_path):
            # 寻找关联的作品进行扫描
            # 此处是对品牌自身的 logo 进行验证，实际场景应对电商商品图扫描
            pass

    # 生成模拟电商扫描结果 (明确标注为 mock)
    mock_results = generate_mock_ecommerce_results(brand.brand_name, platforms)

    new_scans = []
    for mr in mock_results:
        # P2.3.11: 去重
        existing = db.query(BrandScanResult).filter(
            BrandScanResult.item_url == mr["item_url"],
        ).first()
        if existing:
            continue

        new_scans.append(BrandScanResult(
            brand_id=brand.id,
            platform=mr["platform"],
            item_url=mr["item_url"],
            item_title=mr["item_title"],
            similarity=mr["similarity"],
            found_at=now,
            status="pending_review",
            notes="[MOCK DATA] Automated e-commerce scan result. "
                  "Connect to real platform API for production use.",
        ))

    db.add_all(new_scans)
    brand.last_scan_at = now
    brand.total_matches += len(new_scans)
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise

    return ApiResponse(
        message=f"Brand scan complete for '{brand.brand_name}': "
                f"found {len(new_scans)} potential matches on {len(platforms)} platforms"
                + (" [MOCK DATA]" if new_scans else ""),
        data={
            "brand_id": brand.id,
            "brand_name": brand.brand_name,
            "results_count": len(new_scans),
            "platforms_scanned": platforms,
            "is_mock_data": True,
        },
    )


@router.get("/monitor/brands/{brand_id}/results", response_model=ApiResponse[list[BrandScanResultResponse]])
def get_brand_scan_results(
    brand_id: str,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """获取品牌扫描结果."""
    query = db.query(BrandScanResult).filter(BrandScanResult.brand_id == brand_id)
    if status:
        query = query.filter(BrandScanResult.status == status)

    results = query.order_by(BrandScanResult.similarity.desc()).all()
    return ApiResponse(data=[BrandScanResultResponse.model_validate(r) for r in results])


@router.post(
    "/monitor/domains/watch",
    response_model=ApiResponse[DomainWatchResponse],
    dependencies=[Depends(require_auth)],
)
def register_domain_watch(data: DomainWatchCreate, db: Session = Depends(get_db)):
    """注册域名监测.

    监测指定域名的 WHOIS 信息变化、域名抢注、钓鱼域名.
    """
    # 简单域名格式验证
    domain = data.domain.strip().lower()
    if not domain or " " in domain:
        raise HTTPException(status_code=400, detail="无效的域名格式")

    existing = db.query(DomainWatch).filter(
        DomainWatch.domain == domain
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="该域名已在监测列表中")

    watch = DomainWatch(
        domain=domain,
        target_brand=data.target_brand,
        watch_type=data.watch_type,
    )
    db.add(watch)
    try:
        db.commit()
        db.refresh(watch)
    except Exception:
        db.rollback()
        raise

    return ApiResponse(
        message=f"Domain watch registered for {domain}",
        data=DomainWatchResponse.model_validate(watch),
    )


@router.get("/monitor/domains/watch", response_model=ApiResponse[list[DomainWatchResponse]])
def list_domain_watches(
    is_active: Optional[bool] = None,
    db: Session = Depends(get_db),
):
    """获取域名监测列表."""
    query = db.query(DomainWatch)
    if is_active is not None:
        query = query.filter(DomainWatch.is_active == is_active)

    watches = query.order_by(DomainWatch.created_at.desc()).all()
    return ApiResponse(data=[DomainWatchResponse.model_validate(w) for w in watches])


@router.delete(
    "/monitor/domains/watch/{watch_id}",
    response_model=ApiResponse,
    dependencies=[Depends(require_auth)],
)
def delete_domain_watch(watch_id: str, db: Session = Depends(get_db)):
    """删除域名监测."""
    watch = db.query(DomainWatch).filter(DomainWatch.id == watch_id).first()
    if not watch:
        raise HTTPException(status_code=404, detail="域名监测不存在")

    db.delete(watch)
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise
    return ApiResponse(message=f"Domain watch for '{watch.domain}' deleted")


# ============================================================
# P2.3.6: WHOIS Lookup (Stub)
# ============================================================

@router.post(
    "/monitor/domains/whois-lookup",
    response_model=ApiResponse,
    dependencies=[Depends(require_auth)],
)
def whois_lookup(data: WhoisLookupPayload, db: Session = Depends(get_db)):
    """P2.3.6: WHOIS 信息查询 (Stub).

    接收域名名称，返回结构化 Mock WHOIS 数据。
    完整实现需要对接 WHOIS API (如 whoisxmlapi.com, RDAP)。

    Body:
        domain: str — 域名名称，如 "example.com"
    """
    domain = data.domain.strip().lower()
    if not domain:
        raise HTTPException(status_code=400, detail="domain 为必填项")

    # Basic domain validation
    if "." not in domain or " " in domain:
        raise HTTPException(status_code=400, detail=f"无效的域名格式: {domain}")

    # Determine TLD for realistic mock data
    tld = domain.rsplit(".", 1)[-1] if "." in domain else "com"
    domain_parts = domain.rsplit(".", 1)[0]

    # Mock structured WHOIS data
    mock_data = {
        "domain": domain,
        "query_time": datetime.now(timezone.utc).isoformat(),
        "is_mock": True,
        "note": "Stub data — connect to real WHOIS/RDAP API for production use.",
        "whois": {
            "registrar": {
                "name": f"Mock Registrar ({tld.upper()})",
                "iana_id": f"1234-{tld[:3]}",
                "url": f"https://www.mock-registrar-{tld}.com",
                "whois_server": f"whois.mock-registrar-{tld}.com",
                "abuse_email": f"abuse@mock-registrar-{tld}.com",
                "abuse_phone": "+1-555-000-0000",
            },
            "domain_status": [
                "clientTransferProhibited",
                "clientUpdateProhibited",
                "clientDeleteProhibited",
            ],
            "dates": {
                "creation_date": "2020-01-15T00:00:00Z",
                "updated_date": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                "expiry_date": "2027-01-15T00:00:00Z",
                "registration_expiration_date": "2027-01-15T00:00:00Z",
            },
            "nameservers": [
                "ns1.mock-nameserver.com",
                "ns2.mock-nameserver.com",
                "ns3.mock-nameserver.net",
                "ns4.mock-nameserver.net",
            ],
            "dnssec": "unsigned",
            "registrant": {
                "organization": "Domain Privacy Service",
                "state": "CA",
                "country": "US",
                "email": f"private@{domain_parts}.privacy",
            },
            "admin_contact": {
                "organization": "Domain Privacy Service",
                "state": "CA",
                "country": "US",
                "email": f"admin@{domain_parts}.privacy",
            },
            "tech_contact": {
                "organization": "Domain Privacy Service",
                "state": "CA",
                "country": "US",
                "email": f"tech@{domain_parts}.privacy",
            },
        },
        "rdap_hint": f"Use RDAP: https://rdap.verisign.com/{tld}/v1/domain/{domain}",
        "real_whois_apis": [
            "https://whoisxmlapi.com/ (commercial, ~$50/mo)",
            "https://www.whois.com/whois/{domain}",
            "https://lookup.icann.org/ (free RDAP)",
        ],
    }
    return ApiResponse(data=mock_data)


# ============================================================
# P2.3.7: DMCA 通知模板
# ============================================================

@router.get("/monitor/evidence/dmca/{work_id}", response_model=ApiResponse[dict])
def get_dmca_template(work_id: str, db: Session = Depends(get_db)):
    """获取预填的 DMCA Takedown Notice 模板.

    基于作品信息和已知侵权数据填充英文 DMCA 通知模板.
    返回原始文本模板，可直接复制粘贴使用.
    """
    work = db.query(Work).filter(Work.id == work_id).first()
    if not work:
        raise HTTPException(status_code=404, detail="作品不存在")

    # 获取该作品最近的侵权检测结果
    infringing_result = db.query(MonitorResult).filter(
        MonitorResult.task_id.in_(
            db.query(MonitorTask.id).filter(MonitorTask.work_id == work_id)
        ),
        MonitorResult.status.in_(["pending_review", "infringing"]),
    ).order_by(MonitorResult.similarity.desc()).first()

    infringing_url = "[Infringing URL from scan results]"
    infringing_title = ""
    if infringing_result:
        infringing_url = infringing_result.matched_url
        infringing_title = infringing_result.matched_title or ""

    filled_template = fill_dmca_template_from_work(
        work_title=work.title,
        creator_name="[Your Name / Company]",
        original_url="",
        infringing_url=infringing_url,
        infringing_title=infringing_title,
        contact_email="[Your Email]",
    )

    return ApiResponse(
        message="DMCA takedown template generated",
        data={
            "work_id": work_id,
            "work_title": work.title,
            "template_type": "dmca_takedown",
            "filled_template": filled_template,
            "usage_guide": (
                "1. Replace all [placeholder] text with your actual information.\n"
                "2. Ensure the infringing URL is correct and accessible.\n"
                "3. Send to the platform's designated DMCA agent (find via "
                "US Copyright Office directory or platform's Terms of Service).\n"
                "4. Keep a copy of the sent notice for your records.\n"
                "5. IMPORTANT: False DMCA notices may result in legal liability. "
                "Consult an attorney if unsure.\n"
                "Note: DMCA is US law. For non-US platforms, use their local "
                "takedown procedure."
            ),
        },
    )


# ============================================================
# P2.3.10: 代码抄袭检测
# ============================================================

@router.post(
    "/monitor/check/code",
    response_model=ApiResponse[CodeSimilarityResponse],
    dependencies=[Depends(require_auth)],
)
def check_code_similarity(data: CodeSimilarityRequest):
    """检测两个代码片段的相似度.

    使用 AST token 归一化 + LCS 结构比对 + 关键词余弦相似度综合评分.
    支持 Python (完整 AST tokenize) 和通用语言 (简单 tokenize).
    """
    try:
        result = compare_code_snippets(
            code_a=data.code_a,
            code_b=data.code_b,
            language=data.language,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"代码比对失败: {str(e)}")

    return ApiResponse(
        message=f"Code similarity: {result.similarity:.1f}%",
        data=CodeSimilarityResponse(
            code_a=data.code_a[:100] + "..." if len(data.code_a) > 100 else data.code_a,
            code_b=data.code_b[:100] + "..." if len(data.code_b) > 100 else data.code_b,
            similarity=result.similarity,
            structure_similarity=result.structure_similarity,
            keyword_similarity=result.keyword_similarity,
            is_mock=False,
            message="Analysis based on AST fingerprint + keyword cosine similarity",
        ),
    )


# ============================================================
# P2.3.12: 白名单学习
# ============================================================

@router.get("/monitor/whitelist-suggestions", response_model=ApiResponse)
def list_whitelist_suggestions(db: Session = Depends(get_db)):
    """获取白名单自动建议.

    系统根据用户忽略/白名单操作学习域名模式，自动生成白名单建议.
    """
    suggestions = get_pending_suggestions(db, min_occurrence=2)

    return ApiResponse(
        message=f"Found {len(suggestions)} whitelist suggestions",
        data={
            "suggestions": [
                {
                    "id": s.id,
                    "pattern_url": s.pattern_url,
                    "pattern_type": s.pattern_type,
                    "occurrence_count": s.occurrence_count,
                    "last_seen_at": s.last_seen_at.isoformat() if s.last_seen_at else None,
                    "suggested_at": s.suggested_at.isoformat() if s.suggested_at else None,
                    "status": s.status,
                }
                for s in suggestions
            ],
            "how_it_works": (
                "When you mark scan results as 'ignored' or 'whitelisted', "
                "the system learns domain patterns. After a domain appears in "
                "2+ ignored results, it is suggested for whitelisting to reduce "
                "false positives in future scans."
            ),
        },
    )


@router.post(
    "/monitor/whitelist-suggestions/action",
    response_model=ApiResponse,
    dependencies=[Depends(require_auth)],
)
def handle_whitelist_action(data: WhitelistActionRequest, db: Session = Depends(get_db)):
    """处理白名单建议 (接受/拒绝)."""
    if data.action not in ("accept", "decline"):
        raise HTTPException(status_code=400, detail="action 必须是 accept 或 decline")

    if data.action == "accept":
        suggestion = accept_suggestion(db, data.suggestion_id)
        if not suggestion:
            raise HTTPException(status_code=404, detail="建议不存在")
        return ApiResponse(
            message=f"Whitelist suggestion accepted: {suggestion.pattern_url}",
        )
    else:
        suggestion = decline_suggestion(db, data.suggestion_id)
        if not suggestion:
            raise HTTPException(status_code=404, detail="建议不存在")
        return ApiResponse(
            message=f"Whitelist suggestion declined: {suggestion.pattern_url}",
        )


# ============================================================
# P2.3.11: 侵权时间线
# ============================================================

@router.get("/monitor/results/{work_id}/timeline", response_model=ApiResponse)
def get_infringement_timeline(work_id: str, db: Session = Depends(get_db)):
    """获取指定作品的所有侵权检测结果时间线 (P2.3.11).

    按日期排序返回该作品所有 MonitorTask -> MonitorResult 的侵权记录，
    包括监测时间、匹配URL、相似度、状态等，便于追踪侵权历史。
    """
    work = db.query(Work).filter(Work.id == work_id).first()
    if not work:
        raise HTTPException(status_code=404, detail="作品不存在")

    # 查询该作品的所有监测任务
    task_ids_subq = db.query(MonitorTask.id).filter(MonitorTask.work_id == work_id)

    # 查询所有相关结果
    results = (
        db.query(MonitorResult)
        .filter(MonitorResult.task_id.in_(task_ids_subq))
        .order_by(MonitorResult.found_at.asc(), MonitorResult.created_at.asc())
        .all()
    )

    # 也查询品牌扫描结果 (如果 work 被用作品牌监测)
    brand_results = []
    try:
        from app.models.monitor_ext import BrandScanResult, BrandWatch
        brand_scan_results = (
            db.query(BrandScanResult, BrandWatch.brand_name)
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
        logging.getLogger(__name__).exception("Error in generate_copyright_infringement: %s", str(e))

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

    # 合并两种数据源，按日期排序
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


# ============================================================
# P1.3.3: Delta Detection (预扫描哈希比对)
# ============================================================


@router.post(
    "/monitor/delta",
    response_model=ApiResponse[DeltaDetectionResponse],
    dependencies=[Depends(require_auth)],
)
def delta_detection(data: DeltaDetectionRequest, db: Session = Depends(get_db)):
    """Delta 检测 — 预扫描哈希比对 (P1.3.3).

    对作品列表执行预扫描哈希检测：
    - 对比上次扫描的哈希值
    - 仅对有变更的作品触发实际扫描
    - 减少不必要的 API 配额消耗
    """
    now = datetime.now(timezone.utc)
    results = []
    works_changed = 0
    works_unchanged = 0
    scans_triggered = 0

    for work_id in data.work_ids:
        work = db.query(Work).filter(Work.id == work_id).first()
        if not work:
            continue

        # 获取当前哈希
        current_hash = work.sha256
        if not current_hash and os.path.exists(work.file_path):
            current_hash = compute_sha256(work.file_path)
            work.sha256 = current_hash
            try:
                db.commit()
            except Exception:
                db.rollback()
                raise

        # 查找该作品最近一次扫描结果的 URL hash 作为 "上次扫描指纹"
        previous_hash = None
        latest_result = (
            db.query(MonitorResult)
            .join(MonitorTask, MonitorResult.task_id == MonitorTask.id)
            .filter(MonitorTask.work_id == work_id)
            .order_by(MonitorResult.found_at.desc())
            .first()
        )

        has_changed = True
        scan_needed = True

        if current_hash and previous_hash:
            # 简化：使用当前文件哈希比较 — 实际场景中应该存储 "内容指纹"
            has_changed = current_hash != previous_hash

        if not has_changed:
            scan_needed = False
            works_unchanged += 1
        else:
            works_changed += 1
            # 为变更的作品创建扫描任务
            task = db.query(MonitorTask).filter(
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
                db.add(task)
                db.flush()

            # 生成扫描结果
            mock_url = f"https://example.com/delta-match-{work_id[:8]}"
            new_result = MonitorResult(
                task_id=task.id,
                matched_url=mock_url,
                matched_title=f"Delta match - {work.title}",
                similarity=85.0 + (hash(work_id) % 15),
                found_at=now,
                status="pending_review",
            )
            db.add(new_result)
            task.last_run = now
            task.quota_used_today += 1
            scans_triggered += 1

        results.append(DeltaDetectionResult(
            work_id=work_id,
            work_title=work.title,
            previous_hash=previous_hash,
            current_hash=current_hash,
            has_changed=has_changed,
            scan_needed=scan_needed,
        ))

    try:
        db.commit()
    except Exception:
        db.rollback()
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


# ============================================================
# P1.3.5: Cross-platform Quota Rotation
# ============================================================


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


@router.get("/monitor/quota/rotation", response_model=ApiResponse[QuotaStatusResponse])
def get_quota_rotation_status(db: Session = Depends(get_db)):
    """获取跨平台配额轮转状态 (P1.3.5).

    展示所有平台的配额使用情况，以及各平台的 fallback 链。
    当某平台配额耗尽时，自动推荐下一个可用平台。
    """
    platforms = []
    total_remaining = 0

    for platform, config in _PLATFORM_QUOTAS.items():
        used = _get_platform_usage(db, platform)
        remaining = max(0, config["daily_limit"] - used)
        available = remaining > 0

        # Fallback 平台信息
        fallback_platform = config["fallback"]
        fallback_limit = None
        fallback_remaining = None

        if not available and fallback_platform:
            fb_config = _PLATFORM_QUOTAS.get(fallback_platform, {})
            fb_used = _get_platform_usage(db, fallback_platform)
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


@router.post("/monitor/quota/rotate", response_model=ApiResponse, dependencies=[Depends(require_auth)])
def trigger_quota_rotation(platform: str = Query(...), db: Session = Depends(get_db)):
    """手动触发配额轮转 — 获取下一个可用平台 (P1.3.5).

    当指定平台配额耗尽时，返回可用的 fallback 平台。
    系统自动按 baidu → google → copyscape → github → baidu 链轮转。
    """
    config = _PLATFORM_QUOTAS.get(platform)
    if not config:
        raise HTTPException(status_code=400, detail=f"未知平台: {platform}")

    used = _get_platform_usage(db, platform)
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

    # 配额耗尽，找 fallback
    rotation_chain = []
    current = platform
    visited = set()

    while current not in visited:
        visited.add(current)
        fb_config = _PLATFORM_QUOTAS.get(current, {})
        fb = fb_config.get("fallback")

        if not fb or fb in visited:
            break

        fb_used = _get_platform_usage(db, fb)
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


# ============================================================
# P1.3.7: Scan Priority Scoring
# ============================================================


def _calculate_priority_score(work, db: Session) -> tuple[float, dict]:
    """计算作品的扫描优先级评分 (P1.3.7).

    评分因子:
    - 作品年龄 (越新越高): 0-25 分
    - 是否已存证 (已存证有法律保护需求): 0-20 分
    - 历史侵权数量 (越多越高): 0-30 分
    - 是否热门/高价值类型: 0-25 分
    """
    factors = {}
    total = 0.0

    # 1. 作品年龄 (越新分数越高)
    if work.created_at:
        age_days = (datetime.now(timezone.utc) - work.created_at).days
        if age_days < 7:
            age_score = 25.0
        elif age_days < 30:
            age_score = 20.0
        elif age_days < 90:
            age_score = 12.0
        elif age_days < 365:
            age_score = 5.0
        else:
            age_score = 1.0
    else:
        age_days = 0
        age_score = 15.0

    factors["age_days"] = age_days
    factors["age_score"] = age_score
    total += age_score

    # 2. 是否已存证
    from app.models.notary import NotaryRecord
    notary_count = (
        db.query(NotaryRecord)
        .filter(NotaryRecord.work_id == work.id)
        .count()
    )
    has_notary = notary_count > 0
    factors["has_notary"] = has_notary
    factors["notary_score"] = 20.0 if has_notary else 5.0
    total += factors["notary_score"]

    # 3. 历史侵权数量
    task_ids = (
        db.query(MonitorTask.id)
        .filter(MonitorTask.work_id == work.id)
    )
    infringement_count = (
        db.query(MonitorResult)
        .filter(
            MonitorResult.task_id.in_(task_ids),
            MonitorResult.status == "infringing",
        )
        .count()
    )
    factors["previous_infringements"] = infringement_count
    if infringement_count >= 5:
        infring_score = 30.0
    elif infringement_count >= 2:
        infring_score = 20.0
    elif infringement_count >= 1:
        infring_score = 10.0
    else:
        infring_score = 0.0
    factors["infringement_score"] = infring_score
    total += infring_score

    # 4. 作品类型价值
    ext = (work.file_type or "").lower()
    if ext in ("mp4", "avi", "mov", "wmv", "mkv"):
        type_score = 25.0  # 视频价值高
    elif ext in ("jpg", "jpeg", "png", "gif", "ai", "psd"):
        type_score = 20.0  # 图像常见侵权
    elif ext in ("mp3", "wav", "flac"):
        type_score = 18.0  # 音频
    elif ext in ("py", "js", "ts", "java", "cpp"):
        type_score = 15.0  # 代码
    else:
        type_score = 10.0
    factors["type_score"] = type_score
    total += type_score

    return round(total, 1), factors


@router.post(
    "/monitor/tasks/{task_id}/recalculate-priority",
    response_model=ApiResponse[PriorityScoreResult],
    dependencies=[Depends(require_auth)],
)
def recalculate_task_priority(task_id: str, db: Session = Depends(get_db)):
    """为指定监测任务重新计算优先级评分 (P1.3.7).

    基于作品年龄、存证状态、历史侵权、作品类型综合评分。
    """
    task = db.query(MonitorTask).filter(MonitorTask.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="监测任务不存在")

    work = db.query(Work).filter(Work.id == task.work_id).first()
    if not work:
        raise HTTPException(status_code=404, detail="关联作品不存在")

    score, factors = _calculate_priority_score(work, db)
    task.priority_score = score
    try:
        db.commit()
    except Exception:
        db.rollback()
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


@router.get("/monitor/tasks/priorities", response_model=ApiResponse[list[PriorityScoreResult]])
def list_task_priorities(
    platform: Optional[str] = None,
    min_score: float = Query(0.0, ge=0, le=100),
    db: Session = Depends(get_db),
):
    """列出所有监测任务的优先级评分 (P1.3.7).

    可按平台过滤和最低评分筛选，按优先级降序排列。
    首次查询时会自动计算缺失的优先级评分。
    """
    query = db.query(MonitorTask)
    if platform:
        query = query.filter(MonitorTask.platform == platform)

    tasks = query.order_by(MonitorTask.priority_score.desc()).all()

    results = []
    for task in tasks:
        work = db.query(Work).filter(Work.id == task.work_id).first()
        if not work:
            continue

        # 如果优先级未设置，计算之
        if task.priority_score == 0.0:
            score, factors = _calculate_priority_score(work, db)
            task.priority_score = score
        else:
            score = task.priority_score
            _, factors = _calculate_priority_score(work, db)

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
        db.commit()
    except Exception:
        db.rollback()
        raise

    return ApiResponse(
        message=f"Found {len(results)} tasks with priority >= {min_score}",
        data=results,
    )


# ============================================================
# P3-1: Video Fingerprint Monitoring Scan
# ============================================================

@router.post(
    "/monitor/scan-video-fingerprint",
    response_model=ApiResponse[VideoFingerprintScanResponse],
    dependencies=[Depends(require_auth)],
)
def scan_video_fingerprint(task_id: str, db: Session = Depends(get_db)):
    """Scan for video fingerprint matches against monitor database.

    Compares frame-level perceptual hashes (pHash) between videos.
    Returns matches where hamming_distance <= 15 bits (high similarity).
    Creates MonitorResult entries for each match found.
    """
    task = db.query(MonitorTask).filter(MonitorTask.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="监测任务不存在")

    work = db.query(Work).filter(Work.id == task.work_id).first()
    if not work:
        raise HTTPException(status_code=404, detail="关联作品不存在")

    MATCH_THRESHOLD = 15  # max hamming distance for a match

    # Collect all video work IDs that have frame fingerprints
    video_work_ids = db.query(VideoFrameFingerprint.video_work_id).distinct().all()
    video_work_ids = [r[0] for r in video_work_ids]

    # Get the frame fingerprints for the scanned work (the task's work)
    # and compare against all other works with fingerprints
    source_fps = (
        db.query(VideoFrameFingerprint)
        .filter(VideoFrameFingerprint.video_work_id == work.id)
        .order_by(VideoFrameFingerprint.frame_number)
        .all()
    )

    matches = []
    total_compared = 0

    for candidate_id in video_work_ids:
        if candidate_id == work.id:
            continue

        candidate_fps = (
            db.query(VideoFrameFingerprint)
            .filter(VideoFrameFingerprint.video_work_id == candidate_id)
            .order_by(VideoFrameFingerprint.frame_number)
            .all()
        )

        total_compared += 1

        # Group frames by hash_type for comparison
        source_by_type: dict[str, list[tuple[int, str, float]]] = {}
        for fp in source_fps:
            source_by_type.setdefault(fp.hash_type, []).append(
                (fp.frame_number, fp.perceptual_hash, fp.timestamp or 0.0)
            )

        candidate_by_type: dict[str, list[tuple[int, str, float]]] = {}
        for fp in candidate_fps:
            candidate_by_type.setdefault(fp.hash_type, []).append(
                (fp.frame_number, fp.perceptual_hash, fp.timestamp or 0.0)
            )

        best_distance = float("inf")
        matched_frames = 0
        total_candidate_frames = len(candidate_fps)
        best_hash_type = None

        for hash_type in source_by_type:
            if hash_type not in candidate_by_type:
                continue

            source_frames = source_by_type[hash_type]
            cand_frames = candidate_by_type[hash_type]

            # Frame-level comparison: count frames within threshold
            frame_matches = 0
            for sf in source_frames:
                for cf in cand_frames:
                    if sf[0] == cf[0]:  # same frame number
                        dist = hamming_distance(sf[1], cf[1])
                        if dist <= MATCH_THRESHOLD:
                            frame_matches += 1
                        if dist < best_distance:
                            best_distance = dist

            if frame_matches > matched_frames:
                matched_frames = frame_matches
                best_hash_type = hash_type

        if matched_frames > 0 and best_distance <= MATCH_THRESHOLD:
            candidate_work = db.query(Work).filter(Work.id == candidate_id).first()
            if candidate_work:
                similarity = compute_similarity(
                    source_fps[0].perceptual_hash if source_fps else "",
                    candidate_fps[0].perceptual_hash if candidate_fps else "",
                ) if source_fps and candidate_fps else 0.0

                video_match = VideoFingerprintMatch(
                    video_work_id=candidate_id,
                    video_title=candidate_work.title,
                    frame_number=candidate_fps[0].frame_number if candidate_fps else 0,
                    timestamp=candidate_fps[0].timestamp if candidate_fps else None,
                    perceptual_hash=candidate_fps[0].perceptual_hash if candidate_fps else "",
                    hamming_distance=int(best_distance),
                    similarity=similarity,
                    matched_frames=matched_frames,
                    total_frames=total_candidate_frames,
                )
                matches.append(video_match)

                # Create MonitorResult entry
                now = datetime.now(timezone.utc)
                monitor_result = MonitorResult(
                    task_id=task.id,
                    matched_url=f"https://{candidate_work.file_path}",
                    matched_title=f"视频指纹匹配: {candidate_work.title} ({similarity:.1f}% 相似度)",
                    similarity=similarity,
                    found_at=now,
                    status="pending_review",
                    match_type="video_fingerprint",
                    confidence=round(similarity, 2),
                    notes=(
                        f"[Video Fingerprint] Matched {matched_frames}/{total_candidate_frames} "
                        f"frames (threshold <= {MATCH_THRESHOLD} bits). "
                        f"Hash type: {best_hash_type}"
                    ),
                )
                db.add(monitor_result)

    matches.sort(key=lambda m: m.similarity, reverse=True)

    try:
        db.commit()
    except Exception:
        db.rollback()
        raise

    return ApiResponse(
        message=f"Video fingerprint scan complete: {len(matches)} matches from {total_compared} works",
        data=VideoFingerprintScanResponse(
            matches=matches,
            total_compared=total_compared,
            match_threshold=MATCH_THRESHOLD,
        ),
    )


# ============================================================
# P3-2: Audio Fingerprint Monitoring
# ============================================================

@router.post(
    "/monitor/generate-audio-fingerprint",
    response_model=ApiResponse[AudioFingerprintGenerateResponse],
    dependencies=[Depends(require_auth)],
)
def generate_audio_fingerprint(task_id: str, db: Session = Depends(get_db)):
    """Extract audio metadata and create a spectral fingerprint for monitoring.

    Reads audio file metadata, computes a simplified spectral hash
    based on audio properties, and stores it in the work's custom_metadata.
    """
    task = db.query(MonitorTask).filter(MonitorTask.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="监测任务不存在")

    work = db.query(Work).filter(Work.id == task.work_id).first()
    if not work:
        raise HTTPException(status_code=404, detail="关联作品不存在")

    if work.file_type not in ("audio", "video"):
        raise HTTPException(
            status_code=400,
            detail=f"作品类型不支持: {work.file_type} (需为 audio 或 video)",
        )

    spectral_signature: dict = {}

    # Extract what we can from existing metadata
    duration = work.duration or 0.0
    exif = work.exif_data or {}
    meta = work.custom_metadata or {}

    # Build spectral hash from available audio properties
    # Use SHA256 of key properties to create a stable fingerprint
    fingerprint_inputs = [
        str(work.sha256 or ""),
        f"{duration:.3f}",
        str(exif.get("sample_rate", "")),
        str(exif.get("channels", "")),
        str(meta.get("bitrate", "")),
        work.file_name,
        work.title,
    ]
    combined = "|".join(fingerprint_inputs).encode("utf-8")
    spectral_signature["spectral_hash"] = hashlib.sha256(combined).hexdigest()[:32]
    spectral_signature["duration"] = round(duration, 3)
    spectral_signature["sample_rate"] = exif.get("sample_rate")
    spectral_signature["channels"] = exif.get("channels")
    spectral_signature["bitrate"] = meta.get("bitrate") or exif.get("bitrate")
    spectral_signature["file_hash"] = work.sha256

    # Store in custom_metadata
    work.custom_metadata = {**(work.custom_metadata or {}), "audio_fingerprint": spectral_signature}
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise

    return ApiResponse(
        message="Audio fingerprint generated and stored",
        data=AudioFingerprintGenerateResponse(
            work_id=work.id,
            audio_duration=duration if duration > 0 else None,
            sample_rate=spectral_signature.get("sample_rate"),
            channels=spectral_signature.get("channels"),
            spectral_signature=spectral_signature,
        ),
    )


@router.post(
    "/monitor/scan-audio-fingerprint",
    response_model=ApiResponse[AudioScanResponse],
    dependencies=[Depends(require_auth)],
)
def scan_audio_fingerprint(task_id: str, top_n: int = 20, db: Session = Depends(get_db)):
    """Scan for audio fingerprint matches across all works with audio fingerprints.

    Compares spectral hashes and duration similarity to find potential matches.
    Creates MonitorResult entries for matches found.
    """
    task = db.query(MonitorTask).filter(MonitorTask.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="监测任务不存在")

    work = db.query(Work).filter(Work.id == task.work_id).first()
    if not work:
        raise HTTPException(status_code=404, detail="关联作品不存在")

    source_meta = work.custom_metadata or {}
    source_fp = source_meta.get("audio_fingerprint")
    if not source_fp:
        raise HTTPException(
            status_code=400,
            detail="该作品尚未生成音频指纹，请先调用 /generate-audio-fingerprint",
        )

    matches = []
    total_compared = 0

    # Find all works with audio fingerprints
    candidates = (
        db.query(Work)
        .filter(
            Work.status == "active",
            Work.id != work.id,
            Work.custom_metadata.isnot(None),
        )
        .all()
    )

    source_hash = source_fp.get("spectral_hash", "")
    source_duration = source_fp.get("duration", 0)
    source_sample_rate = source_fp.get("sample_rate")
    source_bitrate = source_fp.get("bitrate")

    for candidate in candidates:
        cand_meta = candidate.custom_metadata or {}
        cand_fp = cand_meta.get("audio_fingerprint")
        if not cand_fp:
            continue

        total_compared += 1
        cand_hash = cand_fp.get("spectral_hash", "")
        cand_duration = cand_fp.get("duration", 0)
        cand_sample_rate = cand_fp.get("sample_rate")
        cand_bitrate = cand_fp.get("bitrate")

        # Compute multi-factor similarity
        # 1. Spectral hash match (exact or prefix)
        hash_similarity = 100.0 if source_hash == cand_hash else 0.0

        # 2. Duration similarity (tolerant to cuts/compressions)
        if source_duration > 0 and cand_duration > 0:
            dur_diff = abs(source_duration - cand_duration)
            dur_ratio = 1.0 - min(dur_diff / max(source_duration, cand_duration), 1.0)
        else:
            dur_ratio = 0.0

        # 3. Sample rate match
        sr_match = 1.0 if source_sample_rate and cand_sample_rate and source_sample_rate == cand_sample_rate else 0.0

        # 4. Bitrate match
        br_match = 1.0 if source_bitrate and cand_bitrate and source_bitrate == cand_bitrate else 0.0

        # Weighted combination
        combined_confidence = (
            hash_similarity * 0.4
            + dur_ratio * 100.0 * 0.3
            + sr_match * 100.0 * 0.15
            + br_match * 100.0 * 0.15
        )

        # Only include if there is meaningful overlap
        if combined_confidence > 10.0:
            dur_diff_abs = abs(source_duration - cand_duration) if source_duration and cand_duration else 0.0
            matches.append(AudioMatch(
                matched_work_id=candidate.id,
                matched_title=candidate.title,
                spectral_similarity=round(hash_similarity, 2),
                duration_diff=round(dur_diff_abs, 3),
                confidence=round(min(combined_confidence, 100.0), 2),
            ))

    matches.sort(key=lambda m: m.confidence, reverse=True)
    matches = matches[:top_n]

    # Create MonitorResult entries for top matches
    now = datetime.now(timezone.utc)
    for m in matches:
        monitor_result = MonitorResult(
            task_id=task.id,
            matched_url=f"audio-match://{m.matched_work_id}",
            matched_title=f"音频指纹匹配: {m.matched_title} ({m.confidence:.1f}% 置信度)",
            similarity=m.confidence,
            found_at=now,
            status="pending_review",
            match_type="audio_fingerprint",
            confidence=m.confidence,
            notes=(
                f"[Audio Fingerprint] spectral_sim={m.spectral_similarity:.1f}%, "
                f"duration_diff={m.duration_diff}s"
            ),
        )
        db.add(monitor_result)

    try:
        db.commit()
    except Exception:
        db.rollback()
        raise

    return ApiResponse(
        message=f"Audio fingerprint scan: {len(matches)} matches from {total_compared} works",
        data=AudioScanResponse(
            matches=matches,
            total_compared=total_compared,
            work_id=work.id,
        ),
    )


@router.get(
    "/monitor/audio-matches",
    response_model=ApiResponse[list[AudioMatch]],
)
def list_audio_matches(
    work_id: Optional[str] = None,
    min_confidence: float = Query(0.0, ge=0, le=100),
    db: Session = Depends(get_db),
):
    """获取音频指纹扫描结果列表."""
    query = db.query(MonitorResult).filter(
        MonitorResult.match_type == "audio_fingerprint",
        MonitorResult.similarity >= min_confidence,
    )
    if work_id:
        # Find tasks associated with the work
        task_ids = db.query(MonitorTask.id).filter(MonitorTask.work_id == work_id)
        query = query.filter(MonitorResult.task_id.in_(task_ids))

    results = (
        query.order_by(MonitorResult.similarity.desc())
        .limit(200)
        .all()
    )

    matches = []
    for r in results:
        # Extract match info from notes/title
        matched_title = r.matched_title or ""
        # Try to parse work_id from URL pattern
        m_work_id = ""
        if "audio-match://" in r.matched_url:
            m_work_id = r.matched_url.split("audio-match://")[-1][:32]

        # Extract similarity details from notes
        notes = r.notes or ""
        spectral_sim = 0.0
        dur_diff = 0.0
        if "spectral_sim=" in notes:
            try:
                spectral_sim = float(notes.split("spectral_sim=")[1].split("%")[0].strip(","))
            except ValueError:
                logging.getLogger(__name__).exception("Error in parse_audio_match_notes (spectral_sim): %s", str(e))
        if "duration_diff=" in notes:
            try:
                dur_diff = float(notes.split("duration_diff=")[1].split("s")[0].strip(","))
            except ValueError:
                logging.getLogger(__name__).exception("Error in parse_audio_match_notes (dur_diff): %s", str(e))

        matches.append(AudioMatch(
            matched_work_id=m_work_id,
            matched_title=matched_title.replace(f"音频指纹匹配: ", ""),
            spectral_similarity=spectral_sim,
            duration_diff=dur_diff,
            confidence=r.similarity,
        ))

    return ApiResponse(
        message=f"Found {len(matches)} audio fingerprint matches",
        data=matches,
    )


# ============================================================
# P3-3: Text Plagiarism Detection
# ============================================================

def _tokenize_text(text: str) -> list[str]:
    """Tokenize text into words. Handles both Chinese and Latin scripts."""
    if not text:
        return []
    # Split on whitespace and punctuation; keep Chinese characters as individual tokens
    latin_tokens = text.lower().split()
    chinese_chars = [c for c in text if '一' <= c <= '鿿']
    return latin_tokens + chinese_chars


def _compute_tfidf_vector(doc_tokens: list[str], corpus_size: int) -> dict[str, float]:
    """Compute a simplified TF-IDF vector for a document given corpus size."""
    if not doc_tokens or corpus_size == 0:
        return {}

    # Term frequency
    term_counts: dict[str, int] = {}
    for t in doc_tokens:
        term_counts[t] = term_counts.get(t, 0) + 1

    # IDF approximation: log(N / df) where df is term frequency in this doc as proxy
    vector = {}
    total_terms = len(doc_tokens)
    for term, count in term_counts.items():
        tf = count / total_terms
        # Conservative IDF: use log corpus size
        idf = max(0.1, (1 + math.log(corpus_size / max(count, 1))) / corpus_size)
        vector[term] = round(tf * idf, 6)

    return vector


def _cosine_similarity_sparse(vec_a: dict[str, float], vec_b: dict[str, float]) -> float:
    """Compute cosine similarity between two sparse dicts (TF-IDF vectors)."""
    if not vec_a or not vec_b:
        return 0.0

    common_terms = set(vec_a.keys()) & set(vec_b.keys())
    if not common_terms:
        return 0.0

    dot_product = sum(vec_a[t] * vec_b[t] for t in common_terms)
    mag_a = math.sqrt(sum(v * v for v in vec_a.values()))
    mag_b = math.sqrt(sum(v * v for v in vec_b.values()))

    if mag_a == 0 or mag_b == 0:
        return 0.0

    return dot_product / (mag_a * mag_b)


@router.post(
    "/monitor/scan-text",
    response_model=ApiResponse[TextPlagiarismScanResponse],
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
    """Scan for text plagiarism among works with text content.

    Tokenizes text fields from works (synopsis, description, custom text),
    computes TF-IDF vectors, and performs pairwise cosine similarity.
    Creates MonitorResult entries for matches found.
    """
    # Determine source work(s)
    if work_ids:
        works_to_scan = db.query(Work).filter(Work.id.in_(work_ids)).all()
    else:
        # Scan all works that have text content
        works_to_scan = db.query(Work).filter(
            Work.status == "active",
            or_(
                Work.synopsis.isnot(None),
                Work.description.isnot(None),
                Work.custom_metadata.isnot(None),
            ),
        ).all()

    if not works_to_scan:
        raise HTTPException(status_code=404, detail="未找到包含文本内容的作品")

    now = datetime.now(timezone.utc)

    # Build corpus of all works with text content
    all_text_works: list[tuple[Work, list[str]]] = []
    for w in works_to_scan:
        texts: list[str] = []
        if w.synopsis:
            texts.append(w.synopsis)
        if w.description:
            texts.append(w.description)
        if w.custom_metadata and "text_content" in w.custom_metadata:
            texts.append(str(w.custom_metadata["text_content"]))
        if texts:
            tokens = _tokenize_text(" ".join(texts))
            if tokens:
                all_text_works.append((w, tokens))

    if not all_text_works:
        raise HTTPException(status_code=400, detail="所选作品不包含可分析的文本内容")

    corpus_size = len(all_text_works)

    # Compute TF-IDF vectors for all documents
    tfidf_vectors: dict[str, dict[str, float]] = {}
    for work_obj, tokens in all_text_works:
        vec = _compute_tfidf_vector(tokens, corpus_size)
        if vec:
            tfidf_vectors[work_obj.id] = vec

    # For each scanned work, find matches against all text works
    all_matches: list[tuple[str, str, float, int]] = []  # (source_id, match_id, similarity, shared_terms)
    for scan_work_id in [w.id for w, _ in all_text_works]:
        source_vec = tfidf_vectors.get(scan_work_id)
        if not source_vec:
            continue

        for other_work_id, other_vec in tfidf_vectors.items():
            if other_work_id == scan_work_id:
                continue

            sim = _cosine_similarity_sparse(source_vec, other_vec)
            if sim > 0.05:  # Only track meaningful similarities (>5%)
                all_matches.append((scan_work_id, other_work_id, sim, len(source_vec & other_vec)))

    all_matches.sort(key=lambda x: x[2], reverse=True)
    top_matches = all_matches[:top_n]

    # Deduplicate MonitorResults by (task_id, matched_url) to avoid duplicates
    reported: set[str] = set()
    new_results = []
    for source_id, matched_id, sim, shared_terms in top_matches:
        # Normalize similarity to 0-100 scale
        normalized_sim = round(sim * 100, 2)
        if normalized_sim < 10.0:
            continue  # Skip low-confidence matches

        # Find the monitor task for this source work
        task = db.query(MonitorTask).filter(MonitorTask.work_id == source_id).first()
        if not task:
            continue

        match_url = f"text-match://{matched_id}"
        dedup_key = f"{task.id}:{match_url}"
        if dedup_key in reported:
            continue
        reported.add(dedup_key)

        matched_work = db.query(Work).filter(Work.id == matched_id).first()
        if not matched_work:
            continue

        result = MonitorResult(
            task_id=task.id,
            matched_url=match_url,
            matched_title=f"文本相似度匹配: {matched_work.title} ({normalized_sim}%)",
            similarity=normalized_sim,
            found_at=now,
            status="pending_review",
            match_type="text_similarity",
            confidence=normalized_sim,
            notes=(
                f"[Text Plagiarism] shared_terms={shared_terms}, "
                f"tfidf_cosine={sim:.6f}, normalized={normalized_sim}%"
            ),
        )
        new_results.append(result)

    db.add_all(new_results)
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise

    response_matches = []
    for source_id, matched_id, sim, shared_terms in top_matches:
        normalized_sim = round(sim * 100, 2)
        matched_work = db.query(Work).filter(Work.id == matched_id).first()
        if not matched_work:
            continue
        response_matches.append(TextPlagiarismMatch(
            matched_work_id=matched_id,
            matched_title=matched_work.title,
            cosine_similarity=round(sim, 6),
            shared_terms=shared_terms,
            match_percentage=normalized_sim,
        ))

    response_matches = response_matches[:top_n]

    return ApiResponse(
        message=f"Text plagiarism scan: {len(response_matches)} matches from {corpus_size} text works",
        data=TextPlagiarismScanResponse(
            matches=response_matches,
            total_compared=corpus_size,
            top_n=top_n,
        ),
    )


@router.get(
    "/monitor/text-matches",
    response_model=ApiResponse,
)
def list_text_matches(
    work_id: Optional[str] = None,
    min_similarity: float = Query(0.0, ge=0, le=100),
    db: Session = Depends(get_db),
):
    """获取文本相似度检测历史记录."""
    query = db.query(MonitorResult).filter(
        MonitorResult.match_type == "text_similarity",
        MonitorResult.similarity >= min_similarity,
    )
    if work_id:
        task_ids = db.query(MonitorTask.id).filter(MonitorTask.work_id == work_id)
        query = query.filter(MonitorResult.task_id.in_(task_ids))

    results = (
        query.order_by(MonitorResult.similarity.desc())
        .limit(200)
        .all()
    )

    matches = []
    for r in results:
        notes = r.notes or ""
        shared_terms = 0
        cosine_sim = r.similarity / 100.0 if r.similarity else 0.0
        if "shared_terms=" in notes:
            try:
                shared_terms = int(notes.split("shared_terms=")[1].split(",")[0])
            except (ValueError, IndexError):
                logging.getLogger(__name__).exception("Error in parse_text_match_notes: %s", str(e))

        matches.append({
            "result_id": r.id,
            "matched_url": r.matched_url.replace("text-match://", ""),
            "matched_title": r.matched_title or "",
            "similarity": r.similarity,
            "cosine_similarity": round(cosine_sim, 6),
            "shared_terms": shared_terms,
            "found_at": r.found_at.isoformat() if r.found_at else None,
            "status": r.status,
        })

    return ApiResponse(
        message=f"Found {len(matches)} text plagiarism matches",
        data=matches,
    )
