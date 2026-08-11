"""系统字典模块 — 字典分组和条目 CRUD."""

import logging
from typing import Optional

from sqlalchemy.orm import Session

from app.schemas.common import ApiResponse
from app.models.system import DictionaryGroup, DictionaryItem

logger = logging.getLogger(__name__)


class SystemDictModule:
    """字典管理模块."""

    def __init__(self, db: Optional[Session] = None):
        self.db = db

    def get_dict_groups(self, module: Optional[str] = None) -> ApiResponse:
        """获取字典分组列表."""
        query = self.db.query(DictionaryGroup)
        if module:
            query = query.filter(DictionaryGroup.module == module)
        groups = query.all()
        return ApiResponse(data=[
            {"id": g.id, "group_key": g.group_key, "module": g.module, "label": g.label}
            for g in groups
        ])

    def get_dict_group_items(self, group_key: str) -> ApiResponse:
        """获取字典分组条目."""
        items = self.db.query(DictionaryItem).filter(
            DictionaryItem.group_key == group_key,
            DictionaryItem.is_active == True,
        ).all()
        return ApiResponse(data=[
            {
                "id": i.id,
                "item_key": i.item_key,
                "item_value": i.item_value,
                "item_value_en": i.item_value_en,
                "extra": i.extra,
            }
            for i in items
        ])

    def get_dict_items_bulk(self, keys: Optional[str] = None) -> ApiResponse:
        """批量获取字典条目."""
        query = self.db.query(DictionaryItem).filter(DictionaryItem.is_active == True)
        if keys:
            key_list = [k.strip() for k in keys.split(",") if k.strip()]
            query = query.filter(DictionaryItem.group_key.in_(key_list))
        items = query.all()
        return ApiResponse(data=[
            {"group_key": i.group_key, "item_key": i.item_key, "item_value": i.item_value}
            for i in items
        ])

    def export_dict(self) -> ApiResponse:
        """导出所有字典数据."""
        items = self.db.query(DictionaryItem).filter(DictionaryItem.is_active == True).all()
        return ApiResponse(data=[
            {
                "group_key": i.group_key,
                "item_key": i.item_key,
                "item_value": i.item_value,
                "item_value_en": i.item_value_en,
            }
            for i in items
        ])

    def create_dict_item(self, item_data: dict) -> ApiResponse:
        """创建字典条目."""
        item = DictionaryItem(
            group_key=item_data.get("group_key"),
            item_key=item_data.get("item_key"),
            item_value=item_data.get("item_value", ""),
            item_value_en=item_data.get("item_value_en"),
            extra=item_data.get("extra"),
            is_active=item_data.get("is_active", True),
            sort_order=item_data.get("sort_order", 99),
        )
        self.db.add(item)
        try:
            self.db.commit()
            self.db.refresh(item)
        except Exception:
            self.db.rollback()
            raise
        return ApiResponse(message="字典条目已创建", data={"id": item.id})

    def update_dict_item(self, item_id: str, updates: dict) -> ApiResponse:
        """更新字典条目."""
        item = self.db.query(DictionaryItem).filter(DictionaryItem.id == item_id).first()
        if not item:
            raise Exception(f"字典条目不存在: {item_id}")
        for key, value in updates.items():
            if hasattr(item, key) and key != "id":
                setattr(item, key, value)
        try:
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise
        return ApiResponse(message="字典条目已更新")

    def delete_dict_item(self, item_id: str) -> ApiResponse:
        """删除字典条目."""
        item = self.db.query(DictionaryItem).filter(DictionaryItem.id == item_id).first()
        if not item:
            raise Exception(f"字典条目不存在: {item_id}")
        self.db.delete(item)
        try:
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise
        return ApiResponse(message="字典条目已删除")
