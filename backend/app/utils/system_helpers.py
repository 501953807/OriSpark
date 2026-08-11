"""跨层共享工具函数 — 统一导出点，消除 service → router 反向导入."""

from app.services.system_service import (
    get_dict_values,
    get_dict_values_rich,
    push_notification,
)
from app.services.auth_service import _hash_password as hash_password

__all__ = [
    "get_dict_values",
    "get_dict_values_rich",
    "push_notification",
    "hash_password",
]
