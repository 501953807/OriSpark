"""OriStudio FastAPI 应用."""

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.database import engine, Base
from app.routers import works, notary, monitor, dashboard, ipr, supply, publish, system, versions, batch_works, auth, subscription, commission, factory, subtitle, video_fingerprint, metadata_templates, watermark, work_variants, photographer, craftsman, musician, writer, certification, ai_training
from app.routers.websocket_router import router as ws_router
from app import mcp_server
from app.middleware.logging import LoggingMiddleware
from app.middleware.audit import AuditMiddleware
from app.middleware.rate_limit import RateLimitMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理 — 自动初始化所有依赖."""
    data_dir = Path("data")
    for subdir in ["certificates", "thumbnails", "backups", "logs", "config", "workspace"]:
        (data_dir / subdir).mkdir(parents=True, exist_ok=True)

    # 数据库表自动创建
    from app.models.base import target_metadata
    target_metadata.create_all(bind=engine, checkfirst=True)

    # FTS5 全文搜索
    from app.services.search_service import setup_fts5
    setup_fts5()

    # 种子数据初始化 (字典数据中心)
    from app.database import SessionLocal
    db = SessionLocal()
    try:
        from app.services.dict_seed import seed_dictionaries
        seed_dictionaries(db)

        # Seed default watermark presets
        from app.services.watermark_seed import seed_default_presets
        seed_default_presets(db)

        # 迁移 users.json → SQLite
        from app.routers.auth import _migrate_json_users
        _migrate_json_users(db)
    finally:
        db.close()

    yield
    engine.dispose()


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="个人创作者全链路助手工具 — API 服务",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# 中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "X-Requested-With"],
)
app.add_middleware(GZipMiddleware, minimum_size=1024)
app.add_middleware(RateLimitMiddleware, max_requests=200, window_seconds=60)
app.add_middleware(AuditMiddleware)
app.add_middleware(LoggingMiddleware)

# 挂载静态文件目录（缩略图 + 工作区文件可通过 /api/files/ 访问）
static_data = Path("data")
static_data.mkdir(parents=True, exist_ok=True)
app.mount("/api/files", StaticFiles(directory=str(static_data.resolve())), name="files")

# 注册路由
app.include_router(dashboard.router, prefix="/api", tags=["Dashboard"])
app.include_router(works.router, prefix="/api", tags=["Works"])
app.include_router(notary.router, prefix="/api", tags=["Notary"])
app.include_router(monitor.router, prefix="/api", tags=["Monitor"])
app.include_router(ipr.router, prefix="/api", tags=["IPR"])
app.include_router(supply.router, prefix="/api", tags=["SupplyChain"])
app.include_router(publish.router, prefix="/api", tags=["Publish"])
app.include_router(versions.router, prefix="/api", tags=["Versions"])
app.include_router(batch_works.router, prefix="/api", tags=["BatchWorks"])
app.include_router(auth.router, prefix="/api", tags=["Auth"])
app.include_router(system.router, prefix="/api", tags=["System"])
app.include_router(video_fingerprint.router, prefix="/api", tags=["VideoFingerprint"])
app.include_router(subscription.router, prefix="/api", tags=["Subscription"])
app.include_router(commission.router, prefix="/api", tags=["Commission"])
app.include_router(factory.router, prefix="/api", tags=["Factory"])
app.include_router(subtitle.router, prefix="/api", tags=["Subtitle"])
app.include_router(metadata_templates.router, prefix="/api", tags=["MetadataTemplates"])
app.include_router(watermark.router, prefix="/api", tags=["Watermark"])
app.include_router(mcp_server.router, prefix="/api", tags=["MCP"])
app.include_router(work_variants.router, prefix="/api", tags=["WorkVariants"])
app.include_router(photographer.router, prefix="/api", tags=["Photographer"])
app.include_router(craftsman.router, prefix="/api", tags=["Craftsman"])
app.include_router(musician.router, prefix="/api", tags=["Musician"])
app.include_router(writer.router, prefix="/api", tags=["Writer"])
app.include_router(certification.router, prefix="/api", tags=["Certification"])
app.include_router(ws_router, tags=["WebSocket"])

# Phase 0: 新路由
from app.routers.risk_warning import router as risk_warning_router
from app.routers.ai_session import router as ai_session_router

app.include_router(risk_warning_router)
app.include_router(ai_session_router)
from app.routers.ai_generate import router as ai_generate_router
app.include_router(ai_generate_router)


@app.get("/api/health")
async def health_check():
    """健康检查端点."""
    return {
        "status": "ok",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
    }
