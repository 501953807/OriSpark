"""分发回流引擎 API 路由."""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.common import ApiResponse
from app.schemas.reverse_trace import (
    TraceLinkCreate,
    TraceLinkUpdate,
    TraceLinkSchema,
    TraceEventCreate,
    TraceEventSchema,
    AttributionSummary,
)
from app.services.reverse_trace_service import ReverseTraceService

router = APIRouter()


@router.post("/trace/links", response_model=ApiResponse)
def create_link(body: TraceLinkCreate, db: Session = Depends(get_db)):
    """创建可信短链."""
    service = ReverseTraceService(db)
    link = service.create_link(
        work_id=body.work_id,
        user_id="local",  # TODO: from auth
        platform_code=body.platform_code,
        original_url=body.original_url,
        redirect_url=body.redirect_url,
        utm_source=body.utm_source,
        utm_medium=body.utm_medium,
        utm_campaign=body.utm_campaign,
        expire_at=body.expire_at,
    )
    db.commit()
    db.refresh(link)
    return ApiResponse(data=TraceLinkSchema.model_validate(link).model_dump(), message="链接已创建")


@router.get("/trace/links", response_model=ApiResponse)
def list_links(platform_code: Optional[str] = None, is_active: Optional[bool] = None, db: Session = Depends(get_db)):
    """列出短链."""
    service = ReverseTraceService(db)
    links = service.list_links(platform_code=platform_code, is_active=is_active)
    return ApiResponse(data=[TraceLinkSchema.model_validate(l).model_dump() for l in links])


@router.get("/trace/links/{link_id}", response_model=ApiResponse)
def get_link(link_id: str, db: Session = Depends(get_db)):
    """获取链接详情."""
    service = ReverseTraceService(db)
    link = service.get_link(link_id)
    if not link:
        raise HTTPException(status_code=404, detail="链接不存在")
    return ApiResponse(data=TraceLinkSchema.model_validate(link).model_dump())


@router.patch("/trace/links/{link_id}", response_model=ApiResponse)
def update_link(link_id: str, body: TraceLinkUpdate, db: Session = Depends(get_db)):
    """更新链接."""
    service = ReverseTraceService(db)
    link = service.update_link(link_id, **body.model_dump(exclude_unset=True))
    if not link:
        raise HTTPException(status_code=404, detail="链接不存在")
    db.commit()
    db.refresh(link)
    return ApiResponse(data=TraceLinkSchema.model_validate(link).model_dump())


@router.delete("/trace/links/{link_id}", response_model=ApiResponse)
def delete_link(link_id: str, db: Session = Depends(get_db)):
    """删除链接."""
    service = ReverseTraceService(db)
    if not service.delete_link(link_id):
        raise HTTPException(status_code=404, detail="链接不存在")
    db.commit()
    return ApiResponse(message="链接已删除")


@router.get("/trace/redirect/{short_code}", response_model=ApiResponse)
def redirect_link(short_code: str, db: Session = Depends(get_db)):
    """短链跳转 — 记录 click 事件并重定向."""
    service = ReverseTraceService(db)
    link = service.get_link_by_code(short_code)
    if not link:
        raise HTTPException(status_code=404, detail="链接不存在或已失效")
    if not link.is_active:
        raise HTTPException(status_code=410, detail="链接已过期")

    # Record click event
    service.record_event(link.id, "click")
    db.commit()

    return ApiResponse(data={"redirect_to": link.redirect_url})


@router.post("/trace/events", response_model=ApiResponse)
def record_event(body: TraceEventCreate, db: Session = Depends(get_db)):
    """记录归因事件."""
    service = ReverseTraceService(db)
    event = service.record_event(
        link_id=body.link_id,
        event_type=body.event_type,
        ip_address=body.ip_address,
        user_agent=body.user_agent,
        referrer=body.referrer,
        geo_country=body.geo_country,
        geo_region=body.geo_region,
        geo_city=body.geo_city,
        device_type=body.device_type,
        browser=body.browser,
        os_name=body.os_name,
        custom_params=body.custom_params,
        converted=body.converted,
        conversion_value=body.conversion_value,
    )
    db.commit()
    db.refresh(event)
    return ApiResponse(data=TraceEventSchema.model_validate(event).model_dump())


@router.get("/trace/analytics/{link_id}", response_model=ApiResponse)
def get_analytics(link_id: str, db: Session = Depends(get_db)):
    """归因分析摘要."""
    service = ReverseTraceService(db)
    summary = service.get_attribution_summary(link_id)
    return ApiResponse(data=AttributionSummary(**summary).model_dump())
