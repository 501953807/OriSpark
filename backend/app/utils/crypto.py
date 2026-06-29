"""AES 加密工具."""

import os
import base64
import hashlib
from typing import Optional

from cryptography.fernet import Fernet

from app.config import settings


def _derive_key() -> bytes:
    """从 SECRET_KEY 派生出 32 字节密钥."""
    return base64.urlsafe_b64encode(
        hashlib.sha256(settings.SECRET_KEY.encode()).digest()
    )


def get_fernet() -> Fernet:
    """获取 Fernet 加密实例."""
    if settings.AES_KEY:
        key = settings.AES_KEY
        if isinstance(key, str):
            key = key.encode()
    else:
        key = _derive_key()
    return Fernet(key)


def encrypt(plaintext: str) -> str:
    """AES 加密字符串."""
    if not plaintext:
        return plaintext
    return get_fernet().encrypt(plaintext.encode()).decode()


def decrypt(ciphertext: str) -> str:
    """AES 解密字符串."""
    if not ciphertext:
        return ciphertext
    try:
        return get_fernet().decrypt(ciphertext.encode()).decode()
    except Exception:
        return ciphertext
