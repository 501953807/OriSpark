"""API 路由模块."""

from app.routers.dashboard import router as dashboard_router
from app.routers.works import router as works_router
from app.routers.notary import router as notary_router
from app.routers.monitor import router as monitor_router
from app.routers.ipr import router as ipr_router
from app.routers.supply import router as supply_router
from app.routers.publish import router as publish_router
from app.routers.versions import router as versions_router
from app.routers.batch_works import router as batch_works_router
from app.routers.auth import router as auth_router
from app.routers.system import router as system_router

__all__ = [
    "dashboard_router",
    "works_router",
    "notary_router",
    "monitor_router",
    "ipr_router",
    "supply_router",
    "publish_router",
    "versions_router",
    "batch_works_router",
    "auth_router",
    "system_router",
]
