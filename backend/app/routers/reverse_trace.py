"""分发回流引擎 API 路由."""

import re
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Header
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
from app.deps import require_auth

router = APIRouter()

# UA 正则
_IOS_RE = re.compile(r'\b(iPhone|iPad|iPod)\b')
_ANDROID_RE = re.compile(r'\b(Android)\b')


@router.post("/trace/links", response_model=ApiResponse)
def create_link(body: TraceLinkCreate, db: Session = Depends(get_db), user_id: str = Depends(require_auth)):
    """创建可信短链."""
    service = ReverseTraceService(db)
    link = service.create_link(
        work_id=body.work_id,
        user_id=user_id,  # Use authenticated user ID from auth header
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
def redirect_link(short_code: str, user_agent: Optional[str] = Header(None), db: Session = Depends(get_db)):
    """短链跳转 — 记录 click 事件并根据 UA 返回设备适配的重定向."""
    service = ReverseTraceService(db)
    link = service.get_link_by_code(short_code)
    if not link:
        raise HTTPException(status_code=404, detail="链接不存在或已失效")
    if not link.is_active:
        raise HTTPException(status_code=410, detail="链接已过期")

    # Record click event with UA info
    service.record_event(link.id, "click", user_agent=user_agent)
    db.commit()

    # UA-based deep link routing
    device_target = _resolve_device_target(user_agent, link)

    return ApiResponse(data={
        "redirect_to": device_target,
        "device_type": _detect_device_type(user_agent),
    })


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


@router.get("/trace/config/ios")
def get_ios_config():
    """返回 iOS Universal Links 配置 (Associated Domains)."""
    return {
        "version": 1,
        "applications": [{
            "appId": "com.oristudio.app",  # 替换为实际 App ID
            "details": [{
                "appID": "com.oristudio.app",
                "components": [{
                    "/": "/trace/redirect/*",
                    "comment": "匹配所有短链跳转"
                }]
            }]
        }]
    }


@router.get("/trace/config/android/{packageName}")
def get_android_config(packageName: str):
    """返回 Android App Links 配置 (assetlinks.json)."""
    return [{
        "relation": ["delegate_permission/common.handle_all_urls"],
        "target": {
            "namespace": "web",
            "site": "https://router.oristudio.com"
        }
    }]


def _detect_device_type(user_agent: Optional[str]) -> str:
    """根据 UA 检测设备类型."""
    if not user_agent:
        return "desktop"
    if _IOS_RE.search(user_agent):
        return "ios"
    if _ANDROID_RE.search(user_agent):
        return "android"
    return "desktop"


def _resolve_device_target(user_agent: Optional[str], link) -> str:
    """根据设备类型返回对应的 deep link 目标."""
    device = _detect_device_type(user_agent)
    base = "https://oristudio.app"
    target_path = f"/trace/redirect/{link.short_code}"

    if device == "ios":
        return f"{base}/link{target_path}"
    elif device == "android":
        return f"oristudio://link{target_path}"
    else:
        return f"{base}{target_path}"
