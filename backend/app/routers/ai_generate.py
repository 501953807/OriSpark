"""AI 文案引擎 API 路由 — Phase 0.

Auto-tag, auto-description, article drafting, content moderation.
"""

import time
from collections import defaultdict
from functools import wraps
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse

from app.schemas.ai_generate import (
    AutoTagRequest,
    AutoTagResponse,
    AutoDescriptionRequest,
    AutoDescriptionResponse,
    ArticleDraftRequest,
    ProductDescRequest,
    MusicDescRequest,
    ModerateRequest,
    ModerateResponse,
    AIConfigResponse,
)
from app.schemas.common import ApiResponse
from app.services.ai_service import AIService
from app.deps import require_auth

router = APIRouter(prefix="/ai/generate", tags=["AI"])

# AI generation rate limiter: 10 requests per 60s per IP
_ai_rate_store: dict[str, list[float]] = defaultdict(list)
_AI_RATE_LIMIT = 10
_AI_RATE_WINDOW = 60


def _ai_rate_limiter(request: Request) -> Optional[JSONResponse]:
    """Return a 429 response if the AI rate limit is exceeded."""
    client_ip = request.client.host if request.client else "unknown"
    now = time.time()
    window_start = now - _AI_RATE_WINDOW
    _ai_rate_store[client_ip] = [t for t in _ai_rate_store[client_ip] if t > window_start]
    if len(_ai_rate_store[client_ip]) >= _AI_RATE_LIMIT:
        return JSONResponse(
            status_code=429,
            content={"detail": "AI 生成请求过于频繁，请稍后再试"},
        )
    _ai_rate_store[client_ip].append(now)
    return None


def _get_service():
    """Return an AI service instance (dependency)."""
    return AIService()


# ── endpoints ─────────────────────────────────────────────────


@router.post("/tags", response_model=ApiResponse[AutoTagResponse], dependencies=[Depends(require_auth)])
async def auto_tag(
    req: AutoTagRequest,
    request: Request,
    svc = Depends(_get_service),
):
    """自动为作品生成标签。"""
    if limit := _ai_rate_limiter(request):
        return limit
    if not svc._is_configured():
        return ApiResponse(
            success=False,
            message="AI 服务未配置，请设置环境变量 AI_API_KEY",
        )

    try:
        content = f"work_id: {req.work_id}"
        result = await svc.auto_tag(req.work_id, content, "illustration")
        return ApiResponse(
            data=AutoTagResponse(**result),
        )
    except RuntimeError:
        raise HTTPException(status_code=503, detail="AI 提供商不可用")
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"AI 生成失败: {str(e)}")


@router.post("/description", response_model=ApiResponse[AutoDescriptionResponse], dependencies=[Depends(require_auth)])
async def auto_description(
    req: AutoDescriptionRequest,
    request: Request,
    svc = Depends(_get_service),
):
    """自动为作品生成描述文案。"""
    if limit := _ai_rate_limiter(request):
        return limit
    if not svc._is_configured():
        return ApiResponse(
            success=False,
            message="AI 服务未配置，请设置环境变量 AI_API_KEY",
        )

    try:
        description = await svc.auto_description(req.work_id, "未知作品", [], "illustration")
        return ApiResponse(
            data=AutoDescriptionResponse(description=description),
        )
    except RuntimeError:
        raise HTTPException(status_code=503, detail="AI 提供商不可用")
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"AI 生成失败: {str(e)}")


@router.post("/article", response_model=ApiResponse[str], dependencies=[Depends(require_auth)])
async def draft_article(
    req: ArticleDraftRequest,
    request: Request,
    svc = Depends(_get_service),
):
    """AI 辅助文章/书籍起草。"""
    if limit := _ai_rate_limiter(request):
        return limit
    if not svc._is_configured():
        return ApiResponse(
            success=False,
            message="AI 服务未配置，请设置环境变量 AI_API_KEY",
        )

    try:
        content = await svc.draft_article(req.prompt, req.tone, req.max_words)
        return ApiResponse(data=content)
    except RuntimeError:
        raise HTTPException(status_code=503, detail="AI 提供商不可用")
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"AI 生成失败: {str(e)}")


@router.post("/product-desc", response_model=ApiResponse[str], dependencies=[Depends(require_auth)])
async def draft_product_desc(
    req: ProductDescRequest,
    request: Request,
    svc = Depends(_get_service),
):
    """AI 生成手工艺品商品描述。"""
    if limit := _ai_rate_limiter(request):
        return limit
    if not svc._is_configured():
        return ApiResponse(
            success=False,
            message="AI 服务未配置，请设置环境变量 AI_API_KEY",
        )

    try:
        content = await svc.draft_product_description(
            req.product_name, req.materials, req.techniques,
        )
        return ApiResponse(data=content)
    except RuntimeError:
        raise HTTPException(status_code=503, detail="AI 提供商不可用")
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"AI 生成失败: {str(e)}")


@router.post("/music-desc", response_model=ApiResponse[str], dependencies=[Depends(require_auth)])
async def draft_music_desc(
    req: MusicDescRequest,
    request: Request,
    svc = Depends(_get_service),
):
    """AI 生成音乐作品发行描述。"""
    if limit := _ai_rate_limiter(request):
        return limit
    if not svc._is_configured():
        return ApiResponse(
            success=False,
            message="AI 服务未配置，请设置环境变量 AI_API_KEY",
        )

    try:
        content = await svc.draft_music_description(req.title, req.genre, req.mood, req.bpm)
        return ApiResponse(data=content)
    except RuntimeError:
        raise HTTPException(status_code=503, detail="AI 提供商不可用")
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"AI 生成失败: {str(e)}")


@router.post("/moderate", response_model=ApiResponse[ModerateResponse], dependencies=[Depends(require_auth)])
async def moderate_content(
    req: ModerateRequest,
    request: Request,
    svc = Depends(_get_service),
):
    """内容安全审核。"""
    if limit := _ai_rate_limiter(request):
        return limit
    if not svc._is_configured():
        return ApiResponse(
            success=False,
            message="AI 服务未配置，请设置环境变量 AI_API_KEY",
        )

    try:
        result = await svc.moderate_content(req.text)
        return ApiResponse(
            data=ModerateResponse(
                safe=result.get("safe", True),
                categories=result.get("categories", {}),
                reason=result.get("reason", ""),
            ),
        )
    except RuntimeError:
        raise HTTPException(status_code=503, detail="AI 提供商不可用")
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"AI 审核失败: {str(e)}")


@router.get("/config", response_model=ApiResponse[AIConfigResponse])
async def get_ai_config():
    """查询 AI 服务配置状态。"""
    cfg = AIService.check_configured()
    return ApiResponse(data=AIConfigResponse(**cfg))
