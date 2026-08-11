"""系统插件模块 — 插件注册和管理."""

import logging
from typing import Optional

from sqlalchemy.orm import Session

from app.schemas.common import ApiResponse
from app.models.system import Plugin

logger = logging.getLogger(__name__)


class SystemPluginModule:
    """插件管理模块."""

    def __init__(self, db: Optional[Session] = None):
        self.db = db

    def list_plugins(self) -> ApiResponse:
        """获取插件列表."""
        plugins = self.db.query(Plugin).all()
        return ApiResponse(data=[
            {
                "id": p.id,
                "name": p.name,
                "display_name": p.display_name,
                "version": p.version,
                "enabled": p.enabled,
                "created_at": p.created_at.isoformat() if p.created_at else None,
            }
            for p in plugins
        ])

    def register_plugin(self, plugin_data: dict) -> ApiResponse:
        """注册插件."""
        plugin = Plugin(
            name=plugin_data.get("name"),
            display_name=plugin_data.get("display_name"),
            version=plugin_data.get("version", "1.0.0"),
            description=plugin_data.get("description"),
            author=plugin_data.get("author"),
            enabled=plugin_data.get("enabled", True),
            config=plugin_data.get("config", {}),
        )
        self.db.add(plugin)
        try:
            self.db.commit()
            self.db.refresh(plugin)
        except Exception:
            self.db.rollback()
            raise
        return ApiResponse(message="插件注册成功", data={"id": plugin.id})

    def update_plugin(self, plugin_id: str, updates: dict) -> ApiResponse:
        """更新插件."""
        plugin = self.db.query(Plugin).filter(Plugin.id == plugin_id).first()
        if not plugin:
            raise Exception(f"插件不存在: {plugin_id}")
        for key, value in updates.items():
            if hasattr(plugin, key) and key != "id":
                setattr(plugin, key, value)
        try:
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise
        return ApiResponse(message="插件已更新")

    def delete_plugin(self, plugin_id: str) -> ApiResponse:
        """删除插件."""
        plugin = self.db.query(Plugin).filter(Plugin.id == plugin_id).first()
        if not plugin:
            raise Exception(f"插件不存在: {plugin_id}")
        self.db.delete(plugin)
        try:
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise
        return ApiResponse(message="插件已删除")
