"""摄影师 API 路由 — 对应: Task 1 brief

端点: 7 (photographer shots workflow)
"""

from datetime import datetime
from math import radians, sin, cos, sqrt, atan2

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import Field
from sqlalchemy import func
from sqlalchemy.orm import Session
from typing import Optional

from app.database import get_db
from app.models.work_variant import WorkVariant
from app.schemas.common import ApiResponse, PaginatedResponse
from app.schemas.photographer import (
    ShotResponse,
    ShotListResponse,
    ShotStatusUpdate,
    EXIFSearchParams,
    GPSPoint,
    GPSMapResponse,
    StockChannelAdd,
    StockChannelInfo,
    StockUploadRequest,
    StockUploadResult,
    StockSalesResponse,
    StockPlatformInfo,
    StockValidateRequest,
    StockValidateResult,
    PhotographerStatsResponse,
    ShotStats,
)
from app.services.stock_service import StockService, SUPPORTED_CHANNEL_NAMES
from app.deps import require_auth

router = APIRouter()


# ============================================================================
# Helper
# ============================================================================


def _variant_to_shot(v: WorkVariant) -> dict:
    """ORM WorkVariant → 包含摄影师扩展字段的 dict."""
    return ShotResponse.model_validate(v).model_dump()


# ============================================================================
# 1. GET /api/photographer/shots — 作品列表 (含摄影师扩展字段)
# ============================================================================


@router.get("/photographer/shots", response_model=ApiResponse[ShotListResponse])
def list_shots(
    shot_status: Optional[str] = Query(None),
    camera_model: Optional[str] = Query(None),
    group_id: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """获取作品变体列表，含相机型号、ISO、光圈等摄影师扩展字段。

    支持按 shot_status、camera_model、group_id 过滤，分页返回。
    """
    q = db.query(WorkVariant)
    if shot_status:
        q = q.filter(WorkVariant.shot_status == shot_status)
    if camera_model:
        q = q.filter(WorkVariant.camera_model == camera_model)
    if group_id:
        q = q.filter(WorkVariant.group_id == group_id)

    total = q.count()
    items = (
        q.order_by(WorkVariant.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    total_pages = max(1, (total + page_size - 1) // page_size)

    return ApiResponse(
        data=ShotListResponse(
            items=[_variant_to_shot(v) for v in items],
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )
    )


# ============================================================================
# 2. POST /api/photographer/shots/{id}/shot-status — 更新选片状态
# ============================================================================


@router.post(
    "/photographer/shots/{variant_id}/shot-status",
    response_model=ApiResponse[ShotResponse],
    dependencies=[Depends(require_auth)],
)
def update_shot_status(
    variant_id: str,
    payload: ShotStatusUpdate,
    db: Session = Depends(get_db),
):
    """更新作品变体的选片状态 (unreviewed → pass/hold/reject/shortlist)。"""
    variant = db.query(WorkVariant).filter(WorkVariant.id == variant_id).first()
    if not variant:
        raise HTTPException(status_code=404, detail="作品变体不存在")

    variant.shot_status = payload.shot_status
    if payload.shot_notes is not None:
        variant.shot_notes = payload.shot_notes
    variant.updated_at = datetime.utcnow()
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise
    db.refresh(variant)

    return ApiResponse(
        data=_variant_to_shot(variant),
        message="选片状态已更新",
    )


# ============================================================================
# 3. GET /api/photographer/exif/search — EXIF 高级搜索
# ============================================================================


@router.get("/photographer/exif/search", response_model=ApiResponse[ShotListResponse])
def search_exif(
    camera_model: Optional[str] = Query(None),
    lens: Optional[str] = Query(None),
    iso_min: Optional[int] = Query(None),
    iso_max: Optional[int] = Query(None),
    aperture: Optional[str] = Query(None),
    shutter_speed: Optional[str] = Query(None),
    focal_length: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """按 EXIF 参数搜索作品变体。

    支持的搜索条件: 相机型号、镜头、ISO 范围、光圈、快门速度、焦距。
    """
    q = db.query(WorkVariant).filter(WorkVariant.camera_model.isnot(None))

    if camera_model:
        q = q.filter(WorkVariant.camera_model.ilike(f"%{camera_model}%"))
    if lens:
        q = q.filter(WorkVariant.lens.ilike(f"%{lens}%"))
    if iso_min is not None:
        q = q.filter(WorkVariant.iso >= iso_min)
    if iso_max is not None:
        q = q.filter(WorkVariant.iso <= iso_max)
    if aperture:
        q = q.filter(WorkVariant.aperture == aperture)
    if shutter_speed:
        q = q.filter(WorkVariant.shutter_speed == shutter_speed)
    if focal_length:
        q = q.filter(WorkVariant.focal_length == focal_length)

    total = q.count()
    items = (
        q.order_by(WorkVariant.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    total_pages = max(1, (total + page_size - 1) // page_size)

    return ApiResponse(
        data=ShotListResponse(
            items=[_variant_to_shot(v) for v in items],
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )
    )


# ============================================================================
# 4. GET /api/photographer/gps/map — GPS 地图数据
# ============================================================================


@router.get("/photographer/gps/map", response_model=ApiResponse[GPSMapResponse])
def get_gps_map(
    group_id: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    """获取所有带 GPS 坐标的作品变体位置数据，用于地图展示。"""
    q = db.query(WorkVariant).filter(
        WorkVariant.gps_latitude.isnot(None),
        WorkVariant.gps_longitude.isnot(None),
    )
    if group_id:
        q = q.filter(WorkVariant.group_id == group_id)

    points = [
        GPSPoint(
            id=v.id,
            name=v.name,
            latitude=v.gps_latitude,  # type: ignore[arg-type]
            longitude=v.gps_longitude,  # type: ignore[arg-type]
            altitude=v.gps_altitude,  # type: ignore[arg-type]
            camera_model=v.camera_model,
        )
        for v in q.order_by(WorkVariant.created_at.desc()).all()
    ]

    return ApiResponse(
        data=GPSMapResponse(points=points, total=len(points)),
    )


# ============================================================================
# 5. POST /api/photographer/stock/channels — 添加图库渠道
# ============================================================================


@router.post(
    "/photographer/stock/channels",
    response_model=ApiResponse[StockChannelInfo],
    dependencies=[Depends(require_auth)],
)
def add_stock_channel(
    variant_id: str = Query(..., min_length=1),
    payload: StockChannelAdd = ...,
    db: Session = Depends(get_db),
):
    """将作品变体添加到图库销售渠道。"""
    variant = db.query(WorkVariant).filter(WorkVariant.id == variant_id).first()
    if not variant:
        raise HTTPException(status_code=404, detail="作品变体不存在")

    channels = variant.stock_channels or []
    # Replace or append
    existing_idx = next(
        (i for i, c in enumerate(channels) if c.get("channel") == payload.channel),
        None,
    )
    channel_entry = {
        "channel": payload.channel,
        "status": payload.status,
        "remote_id": payload.remote_id,
        "updated_at": datetime.utcnow().isoformat(),
    }
    if existing_idx is not None:
        channels[existing_idx] = channel_entry
    else:
        channels.append(channel_entry)

    variant.stock_channels = channels
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise
    db.refresh(variant)

    return ApiResponse(
        data=StockChannelInfo(
            channel=payload.channel,
            status=payload.status,
            remote_id=payload.remote_id,
            updated_at=datetime.fromisoformat(channel_entry["updated_at"]),
        ),
        message="图库渠道已添加",
    )


# ============================================================================
# 6. DELETE /api/photographer/stock/channels/{channel} — 移除图库渠道
# ============================================================================


@router.delete(
    "/photographer/stock/channels/{channel}",
    response_model=ApiResponse,
    dependencies=[Depends(require_auth)],
)
def remove_stock_channel(
    channel: str,
    variant_id: str = Query(..., min_length=1),
    db: Session = Depends(get_db),
):
    """从作品变体移除指定的图库销售渠道。"""
    variant = db.query(WorkVariant).filter(WorkVariant.id == variant_id).first()
    if not variant:
        raise HTTPException(status_code=404, detail="作品变体不存在")

    channels = variant.stock_channels or []
    updated_channels = [c for c in channels if c.get("channel") != channel]

    if len(updated_channels) == len(channels):
        raise HTTPException(status_code=404, detail=f"渠道 {channel} 未找到")

    variant.stock_channels = updated_channels
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise

    return ApiResponse(data=None, message=f"渠道 {channel} 已移除")


# ============================================================================
# 7. GET /api/photographer/stats — 摄影师统计
# ============================================================================


@router.get(
    "/photographer/stats",
    response_model=ApiResponse[PhotographerStatsResponse],
)
def get_photographer_stats(
    group_id: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    """获取摄影师工作台统计面板数据。

    包含: 各选片状态计数、RAW 文件数、图库渠道数、GPS 追踪数。
    """
    q = db.query(WorkVariant)
    if group_id:
        q = q.filter(WorkVariant.group_id == group_id)

    total = q.count()
    pass_count = db.query(func.count(WorkVariant.id)).filter(
        WorkVariant.shot_status == "pass",
    ).count()
    hold_count = db.query(func.count(WorkVariant.id)).filter(
        WorkVariant.shot_status == "hold",
    ).count()
    reject_count = db.query(func.count(WorkVariant.id)).filter(
        WorkVariant.shot_status == "reject",
    ).count()
    shortlist_count = db.query(func.count(WorkVariant.id)).filter(
        WorkVariant.shot_status == "shortlist",
    ).count()
    unreviewed_count = db.query(func.count(WorkVariant.id)).filter(
        WorkVariant.shot_status == "unreviewed",
    ).count()
    raw_file_count = db.query(func.count(WorkVariant.id)).filter(
        WorkVariant.raw_file_path.isnot(None),
    ).count()
    stock_channel_count = db.query(func.count(WorkVariant.id)).filter(
        WorkVariant.stock_channels.isnot(None),
    ).count()
    gps_tracked_count = db.query(func.count(WorkVariant.id)).filter(
        WorkVariant.gps_latitude.isnot(None),
        WorkVariant.gps_longitude.isnot(None),
    ).count()

    recent = (
        db.query(WorkVariant)
        .order_by(WorkVariant.created_at.desc())
        .limit(10)
        .all()
    )
    recent_activity = [
        {
            "id": v.id,
            "name": v.name,
            "shot_status": v.shot_status,
            "created_at": v.created_at.isoformat() if v.created_at else None,
        }
        for v in recent
    ]

    return ApiResponse(
        data=PhotographerStatsResponse(
            stats=ShotStats(
                total_variants=total,
                pass_count=pass_count,
                hold_count=hold_count,
                reject_count=reject_count,
                shortlist_count=shortlist_count,
                unreviewed_count=unreviewed_count,
                raw_file_count=raw_file_count,
                stock_channel_count=stock_channel_count,
                gps_tracked_count=gps_tracked_count,
            ),
            recent_activity=recent_activity,
        )
    )


# ============================================================================
# 8. POST /api/photographer/stock/upload — Upload work to stock platform
# ============================================================================


@router.post(
    "/photographer/stock/upload",
    response_model=ApiResponse[StockUploadResult],
    dependencies=[Depends(require_auth)],
)
def stock_upload(
    payload: StockUploadRequest,
    db: Session = Depends(get_db),
):
    """将作品上传到指定的图库销售渠道。

    流程:
    1. 验证书件规格是否符合平台要求
    2. 调用对应的网关执行上传
    3. 在本地库存 stock_uploads 表中创建记录
    """
    svc = StockService(db)
    result = svc.upload_to_channel(
        channel_id=payload.channel_id,
        work_id=payload.work_id,
        file_path=payload.file_path,
        keywords=payload.keywords,
        categories=payload.categories,
    )
    return ApiResponse(
        data=StockUploadResult(**result),
        message="上传已提交",
    )


# ============================================================================
# 9. GET /api/photographer/stock/uploads — Upload history
# ============================================================================


@router.get(
    "/photographer/stock/uploads",
    response_model=ApiResponse[PaginatedResponse[StockUploadResult]],
)
def stock_uploads_list(
    channel_id: Optional[str] = Query(None, description="Filter by channel"),
    status: Optional[str] = Query(None, description="Filter by status"),
    work_id: Optional[str] = Query(None, description="Filter by work"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """查询图库上传历史记录（分页）。

    可选过滤: channel_id, status, work_id。
    """
    from app.models.reserved_photographer import StockUpload as SU
    q = db.query(SU)
    if channel_id:
        q = q.filter(SU.channel_id == channel_id)
    if status:
        q = q.filter(SU.status == status)
    if work_id:
        q = q.filter(SU.work_id == work_id)

    total = q.count()
    items = (
        q.order_by(SU.uploaded_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    total_pages = max(1, (total + page_size - 1) // page_size)

    return ApiResponse(
        data=PaginatedResponse(
            items=[
                StockUploadResult(
                    id=i.id,
                    channel_id=i.channel_id,
                    work_id=i.work_id,
                    remote_id=i.remote_id or "",
                    status=i.status,
                    uploaded_at=i.uploaded_at.isoformat()
                                if i.uploaded_at else None,
                )
                for i in items
            ],
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )
    )


# ============================================================================
# 10. GET /api/photographer/stock/sales — Sales summary
# ============================================================================


@router.get(
    "/photographer/stock/sales",
    response_model=ApiResponse[StockSalesResponse],
)
def stock_sales(
    channel_id: str = Query(..., min_length=1),
    start_date: Optional[str] = Query(None, description="YYYY-MM-DD"),
    end_date: Optional[str] = Query(None, description="YYYY-MM-DD"),
    db: Session = Depends(get_db),
):
    """按渠道汇总销售数据。

    若不提供日期范围则汇总全部。
    """
    from app.models.reserved_photographer import StockSale as SS
    from app.models.reserved_photographer import StockChannel as SC
    from sqlalchemy import func

    ch = db.query(SC).filter(SC.id == channel_id).first()
    if not ch:
        raise HTTPException(status_code=404, detail=f"Channel {channel_id} not found")

    q = db.query(SS).filter(
        SS.sale_amount.isnot(None),
    )

    if start_date:
        q = q.filter(SS.sale_date >= datetime.fromisoformat(start_date))
    if end_date:
        q = q.filter(SS.sale_date <= datetime.fromisoformat(end_date))

    total_sales = q.count()
    total_rev = q.with_entities(func.coalesce(func.sum(SS.sale_amount))).scalar() or 0.0
    currency = q.with_entities(func.coalesce(func.max(SS.currency))).scalar() or "USD"

    records = q.order_by(SS.sale_date.desc()).limit(50).all()

    return ApiResponse(
        data=StockSalesResponse(
            channel_name=ch.channel_name,
            total_sales=total_sales,
            total_revenue=round(total_rev, 2),
            currency=currency,
            records=[
                {
                    "id": r.id,
                    "sale_amount": r.sale_amount,
                    "license_type": r.license_type,
                    "sale_date": r.sale_date.isoformat()
                                 if r.sale_date else None,
                }
                for r in records
            ],
        )
    )


# ============================================================================
# 11. POST /api/photographer/stock/sync-sales — Trigger sales sync
# ============================================================================


@router.post(
    "/photographer/stock/sync-sales",
    response_model=ApiResponse[StockSalesResponse],
    dependencies=[Depends(require_auth)],
)
def sync_sales(
    channel_id: str = Query(..., min_length=1),
    start_date: str = Query("2020-01-01", description="YYYY-MM-DD"),
    end_date: str = Query(None, description="YYYY-MM-DD, default today"),
    db: Session = Depends(get_db),
):
    """从图库平台拉取销售数据并存入本地 stock_sales 表。

    返回当前渠道的销售汇总（含刚同步的记录）。
    """
    svc = StockService(db)
    sd = datetime.fromisoformat(start_date)
    ed = datetime.fromisoformat(end_date) if end_date else datetime.now(timezone.utc)
    svc.sync_sales(channel_id, sd, ed)

    # Refresh summary from DB (now includes synced records).
    from app.models.reserved_photographer import StockSale as SS
    from app.models.reserved_photographer import StockChannel as SC
    from sqlalchemy import func

    ch = db.query(SC).filter(SC.id == channel_id).first()
    if not ch:
        raise HTTPException(status_code=404, detail=f"Channel {channel_id} not found")

    total_sales = db.query(func.count(SS.id)).filter(
        SS.sale_amount.isnot(None),
        SS.sale_date >= sd,
        SS.sale_date <= ed,
    ).scalar() or 0
    total_rev = db.query(func.coalesce(func.sum(SS.sale_amount))).filter(
        SS.sale_date >= sd, SS.sale_date <= ed,
    ).scalar() or 0.0

    return ApiResponse(
        data=StockSalesResponse(
            channel_name=ch.channel_name,
            total_sales=total_sales,
            total_revenue=round(float(total_rev), 2),
            records=[],
        ),
        message=f"销售数据同步完成 ({total_sales} 条)",
    )


# ============================================================================
# 12. GET /api/photographer/stock/validate — Pre-validate file specs
# ============================================================================


@router.get(
    "/photographer/stock/validate",
    response_model=ApiResponse[StockValidateResult],
    dependencies=[Depends(require_auth)],
)
def validate_stock_file(
    work_id: str = Query(..., min_length=1, description="Work variant to validate"),
    channel_name: str = Query(..., min_length=1,
                               description="shutterstock|adobe|getty|500px|tuchong"),
    db: Session = Depends(get_db),
):
    """预检文件规格是否符合目标平台上传要求。

    返回分辨率、文件大小、格式等信息以及通过/警告/阻塞列表。
    不调用外部 API —— 纯本地校验。
    """
    from app.models.work_variant import WorkVariant
    v = db.query(WorkVariant).filter(WorkVariant.id == work_id).first()
    if not v:
        raise HTTPException(status_code=404, detail="Work variant not found")

    file_path = v.storage_path if hasattr(v, "storage_path") and v.storage_path else None
    if not file_path:
        # Fallback: check work table
        from app.models.work import Work
        w = None
        if hasattr(v, "group") and hasattr(v.group, "work_id"):
            w = db.query(Work).filter(Work.id == v.group.work_id).first()
        elif hasattr(v, "work_id"):
            w = db.query(Work).filter(Work.id == v.work_id).first()
        if w and hasattr(w, "file_path") and w.file_path:
            file_path = w.file_path

    if not file_path:
        raise HTTPException(
            status_code=400,
            detail="No file path found for work variant",
        )

    svc = StockService(db)
    return ApiResponse(
        data=StockValidateResult(
            **svc.validate_file(v.id, channel_name, file_path),
        ),
    )


# ============================================================================
# 13. GET /api/photographer/stock/platforms — List supported platforms
# ============================================================================


@router.get(
    "/photographer/stock/platforms",
    response_model=ApiResponse[list[StockPlatformInfo]],
)
def list_stock_platforms():
    """列出所有支持的图库平台及其上传规格要求。

    不含认证凭据 —— 供前端展示选择器及规格说明。
    """
    return ApiResponse(
        data=[StockPlatformInfo(**p) for p in StockService.list_platforms()],
    )
