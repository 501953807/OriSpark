"""摄影师 API 路由 — 对应: Task 1 brief

端点: 7 (photographer shots workflow)

所有 DB 操作已提取至 photographer_manager_service.py.
"""

from datetime import datetime, timezone
from math import radians, sin, cos, sqrt, atan2

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from pydantic import Field
from sqlalchemy.orm import Session

from app.database import get_db
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
    RawFormatSchema,
    RawFormatCreate,
    RawFormatUpdate,
    DigitalDownloadSchema,
    DigitalDownloadCreate,
    DigitalDownloadUpdate,
    FineArtPrintConfigSchema,
    FineArtPrintConfigCreate,
    FineArtPrintConfigUpdate,
)
from app.services.photographer_manager_service import PhotographerManagerService
from app.services.stock_service import StockService, SUPPORTED_CHANNEL_NAMES
from app.deps import require_auth

router = APIRouter()


# ============================================================================
# 1. GET /api/photographer/shots — 作品列表 (含摄影师扩展字段)
# ============================================================================


@router.get("/photographer/shots", response_model=ApiResponse[ShotListResponse])
def list_shots(
    shot_status: str = Query(None),
    camera_model: str = Query(None),
    group_id: str = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """获取作品变体列表，含相机型号、ISO、光圈等摄影师扩展字段."""
    svc = PhotographerManagerService(db)
    result = svc.list_shots(shot_status, camera_model, group_id, page, page_size)
    return ApiResponse(
        data=ShotListResponse(
            items=result["items"],
            total=result["total"],
            page=result["page"],
            page_size=result["page_size"],
            total_pages=result["total_pages"],
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
    """更新作品变体的选片状态 (unreviewed → pass/hold/reject/shortlist)."""
    svc = PhotographerManagerService(db)
    return ApiResponse(
        data=svc.update_shot_status(variant_id, payload),
        message="选片状态已更新",
    )


# ============================================================================
# 3. GET /api/photographer/exif/search — EXIF 高级搜索
# ============================================================================


@router.get("/photographer/exif/search", response_model=ApiResponse[ShotListResponse])
def search_exif(
    camera_model: str = Query(None),
    lens: str = Query(None),
    iso_min: int = Query(None),
    iso_max: int = Query(None),
    aperture: str = Query(None),
    shutter_speed: str = Query(None),
    focal_length: str = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """按 EXIF 参数搜索作品变体."""
    svc = PhotographerManagerService(db)
    result = svc.search_exif(
        camera_model, lens, iso_min, iso_max, aperture, shutter_speed,
        focal_length, page, page_size,
    )
    return ApiResponse(
        data=ShotListResponse(
            items=result["items"],
            total=result["total"],
            page=result["page"],
            page_size=result["page_size"],
            total_pages=result["total_pages"],
        )
    )


# ============================================================================
# 4. GET /api/photographer/gps/map — GPS 地图数据
# ============================================================================


@router.get("/photographer/gps/map", response_model=ApiResponse[GPSMapResponse])
def get_gps_map(
    group_id: str = Query(None),
    db: Session = Depends(get_db),
):
    """获取所有带 GPS 坐标的作品变体位置数据，用于地图展示."""
    svc = PhotographerManagerService(db)
    result = svc.get_gps_map(group_id)
    return ApiResponse(data=GPSMapResponse(**result))


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
    """将作品变体添加到图库销售渠道."""
    svc = PhotographerManagerService(db)
    return ApiResponse(
        data=svc.add_stock_channel(variant_id, payload.channel, payload.status, payload.remote_id),
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
    """从作品变体移除指定的图库销售渠道."""
    svc = PhotographerManagerService(db)
    svc.remove_stock_channel(variant_id, channel)
    return ApiResponse(data=None, message=f"渠道 {channel} 已移除")


# ============================================================================
# 7. GET /api/photographer/stats — 摄影师统计
# ============================================================================


@router.get(
    "/photographer/stats",
    response_model=ApiResponse[PhotographerStatsResponse],
)
def get_photographer_stats(
    group_id: str = Query(None),
    db: Session = Depends(get_db),
):
    """获取摄影师工作台统计面板数据."""
    svc = PhotographerManagerService(db)
    result = svc.get_photographer_stats(group_id)
    return ApiResponse(data=PhotographerStatsResponse(**result))


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
    """将作品上传到指定的图库销售渠道."""
    import asyncio
    svc = StockService(db)
    result = asyncio.run(svc.upload_to_channel(
        channel_id=payload.channel_id,
        work_id=payload.work_id,
        file_path=payload.file_path,
        keywords=payload.keywords,
        categories=payload.categories,
    ))
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
    channel_id: str = Query(None, description="Filter by channel"),
    status: str = Query(None, description="Filter by status"),
    work_id: str = Query(None, description="Filter by work"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """查询图库上传历史记录（分页）."""
    svc = PhotographerManagerService(db)
    result = svc.list_stock_uploads(channel_id, status, work_id, page, page_size)
    return ApiResponse(
        data=PaginatedResponse(
            items=result["items"],
            total=result["total"],
            page=result["page"],
            page_size=result["page_size"],
            total_pages=result["total_pages"],
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
    start_date: str = Query(None, description="YYYY-MM-DD"),
    end_date: str = Query(None, description="YYYY-MM-DD"),
    db: Session = Depends(get_db),
):
    """按渠道汇总销售数据."""
    svc = PhotographerManagerService(db)
    result = svc.get_stock_sales(channel_id, start_date, end_date)
    return ApiResponse(data=StockSalesResponse(**result))


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
    """从图库平台拉取销售数据并存入本地 stock_sales 表."""
    svc = StockService(db)
    sd = datetime.fromisoformat(start_date)
    ed = datetime.fromisoformat(end_date) if end_date else datetime.now(timezone.utc)
    import asyncio
    asyncio.run(svc.sync_sales(channel_id, sd, ed))

    # Refresh summary from DB
    svc_mgr = PhotographerManagerService(db)
    result = svc_mgr.sync_sales_summary(channel_id, sd, ed)
    return ApiResponse(
        data=StockSalesResponse(**result),
        message=f"销售数据同步完成 ({result['total_sales']} 条)",
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
    """预检文件规格是否符合目标平台上传要求."""
    svc = PhotographerManagerService(db)
    svc.validate_stock_file(work_id)  # validates variant exists
    stock_svc = StockService(db)
    v, file_path = svc.get_variant_with_file_path(work_id)
    if not file_path:
        raise HTTPException(status_code=400, detail="No file path found for work variant")
    import asyncio
    result = asyncio.run(stock_svc.validate_file(v.id, channel_name, file_path))
    return ApiResponse(
        data=StockValidateResult(**result),
    )


# ============================================================================
# 13. GET /api/photographer/stock/platforms — List supported platforms
# ============================================================================


@router.get(
    "/photographer/stock/platforms",
    response_model=ApiResponse[list[StockPlatformInfo]],
)
def list_stock_platforms():
    """列出所有支持的图库平台及其上传规格要求."""
    return ApiResponse(
        data=[StockPlatformInfo(**p) for p in StockService.list_platforms()],
    )


# ============================================================================
# RAW Format management (v2)
# ============================================================================


@router.get("/photographer/raw-formats", response_model=ApiResponse[list[RawFormatSchema]])
def list_raw_formats(db: Session = Depends(get_db)):
    """获取 RAW 格式记录列表."""
    svc = PhotographerManagerService(db)
    return ApiResponse(data=svc.list_raw_formats())


@router.post("/photographer/raw-formats", response_model=ApiResponse[dict], dependencies=[Depends(require_auth)])
def create_raw_format(payload: RawFormatCreate, db: Session = Depends(get_db)):
    """创建 RAW 格式记录."""
    svc = PhotographerManagerService(db)
    return ApiResponse(data=svc.create_raw_format(
        payload.work_id, payload.file_extension, payload.file_size_bytes,
        payload.sensor_width, payload.sensor_height, payload.color_space,
    ), message="RAW 格式记录已创建")


@router.patch("/photographer/raw-formats/{raw_id}", response_model=ApiResponse[dict], dependencies=[Depends(require_auth)])
def update_raw_format(raw_id: str, payload: RawFormatUpdate, db: Session = Depends(get_db)):
    """更新 RAW 格式记录."""
    svc = PhotographerManagerService(db)
    svc.update_raw_format(raw_id, payload.model_dump(exclude_unset=True))
    return ApiResponse(data={"id": raw_id}, message="RAW 格式记录已更新")


@router.delete("/photographer/raw-formats/{raw_id}", response_model=ApiResponse, dependencies=[Depends(require_auth)])
def delete_raw_format(raw_id: str, db: Session = Depends(get_db)):
    """删除 RAW 格式记录."""
    svc = PhotographerManagerService(db)
    svc.delete_raw_format(raw_id)
    return ApiResponse(message="RAW 格式记录已删除")


# ============================================================================
# Digital Download (v2)
# ============================================================================


@router.get("/photographer/digital-downloads", response_model=ApiResponse[list[DigitalDownloadSchema]])
def list_digital_downloads(db: Session = Depends(get_db)):
    """获取数字预设包列表."""
    svc = PhotographerManagerService(db)
    return ApiResponse(data=svc.list_digital_downloads())


@router.post("/photographer/digital-downloads", response_model=ApiResponse[dict], dependencies=[Depends(require_auth)])
def create_digital_download(payload: DigitalDownloadCreate, db: Session = Depends(get_db)):
    """创建数字预设包."""
    svc = PhotographerManagerService(db)
    return ApiResponse(data=svc.create_digital_download(
        payload.work_id, payload.product_id, payload.download_url, payload.max_downloads,
    ), message="数字预设包已创建")


@router.patch("/photographer/digital-downloads/{dd_id}", response_model=ApiResponse[dict], dependencies=[Depends(require_auth)])
def update_digital_download(dd_id: str, payload: DigitalDownloadUpdate, db: Session = Depends(get_db)):
    """更新数字预设包."""
    svc = PhotographerManagerService(db)
    svc.update_digital_download(dd_id, payload.model_dump(exclude_unset=True))
    return ApiResponse(data={"id": dd_id}, message="数字预设包已更新")


@router.delete("/photographer/digital-downloads/{dd_id}", response_model=ApiResponse, dependencies=[Depends(require_auth)])
def delete_digital_download(dd_id: str, db: Session = Depends(get_db)):
    """删除数字预设包."""
    svc = PhotographerManagerService(db)
    svc.delete_digital_download(dd_id)
    return ApiResponse(message="数字预设包已删除")


# ============================================================================
# Fine Art Print (v2)
# ============================================================================


@router.get("/photographer/fine-art-prints", response_model=ApiResponse[list[FineArtPrintConfigSchema]])
def list_fine_art_prints(db: Session = Depends(get_db)):
    """获取艺术微喷配置列表."""
    svc = PhotographerManagerService(db)
    return ApiResponse(data=svc.list_fine_art_prints())


@router.post("/photographer/fine-art-prints", response_model=ApiResponse[dict], dependencies=[Depends(require_auth)])
def create_fine_art_print(payload: FineArtPrintConfigCreate, db: Session = Depends(get_db)):
    """创建艺术微喷配置."""
    svc = PhotographerManagerService(db)
    return ApiResponse(data=svc.create_fine_art_print(
        payload.work_id, payload.paper_type, payload.max_width_cm,
        payload.max_height_cm, payload.framing_available, payload.price_multiplier,
    ), message="艺术微喷配置已创建")


@router.patch("/photographer/fine-art-prints/{fap_id}", response_model=ApiResponse[dict], dependencies=[Depends(require_auth)])
def update_fine_art_print(fap_id: str, payload: FineArtPrintConfigUpdate, db: Session = Depends(get_db)):
    """更新艺术微喷配置."""
    svc = PhotographerManagerService(db)
    svc.update_fine_art_print(fap_id, payload.model_dump(exclude_unset=True))
    return ApiResponse(data={"id": fap_id}, message="艺术微喷配置已更新")


@router.delete("/photographer/fine-art-prints/{fap_id}", response_model=ApiResponse, dependencies=[Depends(require_auth)])
def delete_fine_art_print(fap_id: str, db: Session = Depends(get_db)):
    """删除艺术微喷配置."""
    svc = PhotographerManagerService(db)
    svc.delete_fine_art_print(fap_id)
    return ApiResponse(message="艺术微喷配置已删除")


# ============================================================================
# RAW Batch Parse (v2)
# ============================================================================

@router.post("/photographer/raw/parse", response_model=ApiResponse[list[dict]], dependencies=[Depends(require_auth)])
async def batch_parse_raw(files: list[UploadFile] = File(...), db: Session = Depends(get_db)):
    """批量解析 RAW 文件."""
    from app.services.raw_decode_service import create_raw_decode_service
    import tempfile, os

    svc = create_raw_decode_service()
    results = []

    with tempfile.TemporaryDirectory() as tmpdir:
        paths = []
        for f in files:
            ext = os.path.splitext(f.filename or "")[1].lower().lstrip(".")
            if not svc.is_supported(ext):
                results.append({"success": False, "error": f"不支持的格式: {ext}", "filename": f.filename})
                continue
            fp = os.path.join(tmpdir, f.filename or "raw")
            content = await f.read()
            with open(fp, "wb") as out:
                out.write(content)
            paths.append(fp)

        batch_results = svc.batch_parse(paths)
        for br in batch_results:
            results.append({
                "success": br.success,
                "filename": getattr(br, "file_path", ""),
                "camera_make": br.camera_make,
                "camera_model": br.camera_model,
                "width": br.width,
                "height": br.height,
                "bit_depth": br.bit_depth,
                "error": br.error,
            })

    return ApiResponse(data=results, message=f"解析完成: {len([r for r in results if r['success']])}/{len(results)} 成功")


@router.get("/photographer/raw/export-csv", response_model=ApiResponse[dict], dependencies=[Depends(require_auth)])
def export_raw_csv(results_json: str = Query(..., description="JSON 格式的解析结果列表")):
    """导出 RAW 解析结果为 CSV."""
    import json, csv, io

    results_data = json.loads(results_json)
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["file_path", "success", "camera_make", "camera_model", "width", "height", "bit_depth", "error"])
    for r in results_data:
        writer.writerow([r.get("file_path", ""), r.get("success", False), r.get("camera_make", ""),
                         r.get("camera_model", ""), r.get("width", 0), r.get("height", 0),
                         r.get("bit_depth", 0), r.get("error", "")])

    return ApiResponse(data={"csv_content": output.getvalue(), "record_count": len(results_data)}, message="CSV 导出成功")
