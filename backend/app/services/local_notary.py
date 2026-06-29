"""ECDSA L1 本地签名服务.

使用 ECDSA secp256r1 (NIST P-256) 对 SHA-256 哈希 + ISO 时间戳签名，
支持签名生成、验证及签名文件的持久化存储。
"""

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.asymmetric.utils import (
    encode_dss_signature,
    decode_dss_signature,
)
from cryptography.exceptions import InvalidSignature

# 签名文件存储目录
SIGNATURES_DIR = Path("data/certificates/signatures")


def _ensure_signatures_dir() -> Path:
    """确保签名存储目录存在."""
    SIGNATURES_DIR.mkdir(parents=True, exist_ok=True)
    return SIGNATURES_DIR


def generate_ecdsa_keypair():
    """生成 ECDSA secp256r1 密钥对.

    Returns:
        tuple: (private_key_pem: str, public_key_pem: str)
    """
    private_key = ec.generate_private_key(ec.SECP256R1())
    public_key = private_key.public_key()

    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    ).decode("utf-8")

    public_pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    ).decode("utf-8")

    return private_pem, public_pem


def sign_work(file_hash: str, private_key_pem: Optional[str] = None) -> dict:
    """对文件哈希进行 ECDSA 签名.

    Args:
        file_hash: 文件的 SHA-256 哈希 (hex 字符串)
        private_key_pem: PEM 格式的 ECDSA 私钥; 若为 None 则自动生成

    Returns:
        dict: {
            "signature": hex 编码的 DER 签名,
            "public_key": PEM 格式的公钥,
            "timestamp": ISO 8601 UTC 时间戳,
            "algorithm": "ECDSA-secp256r1+SHA256",
        }
    """
    # 加载或生成密钥
    if private_key_pem:
        private_key = serialization.load_pem_private_key(
            private_key_pem.encode("utf-8"), password=None
        )
    else:
        private_key = ec.generate_private_key(ec.SECP256R1())

    public_key = private_key.public_key()
    public_pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    ).decode("utf-8")

    # 签名数据: SHA-256 哈希 + ISO 时间戳
    timestamp = datetime.now(timezone.utc).isoformat()
    message = f"{file_hash}:{timestamp}".encode("utf-8")

    # 使用 ECDSA with SHA-256 签名
    der_signature = private_key.sign(
        message,
        ec.ECDSA(hashes.SHA256()),
    )

    signature_hex = der_signature.hex()

    return {
        "signature": signature_hex,
        "public_key": public_pem,
        "timestamp": timestamp,
        "algorithm": "ECDSA-secp256r1+SHA256",
    }


def verify_work_signature(file_hash: str, signature_data: dict) -> bool:
    """验证 ECDSA 签名.

    Args:
        file_hash: 文件的 SHA-256 哈希 (hex 字符串)
        signature_data: sign_work 返回的签名字典

    Returns:
        bool: 签名有效则为 True
    """
    try:
        # 加载公钥
        public_key = serialization.load_pem_public_key(
            signature_data["public_key"].encode("utf-8")
        )

        # 重建签名消息
        timestamp = signature_data["timestamp"]
        message = f"{file_hash}:{timestamp}".encode("utf-8")

        # DER 签名
        der_signature = bytes.fromhex(signature_data["signature"])

        # 验证
        public_key.verify(
            der_signature,
            message,
            ec.ECDSA(hashes.SHA256()),
        )
        return True
    except (InvalidSignature, KeyError, ValueError):
        return False


def save_signature(work_id: str, signature_data: dict) -> str:
    """将签名数据保存到 JSON 文件.

    Args:
        work_id: 作品/记录 ID
        signature_data: sign_work 返回的签名字典

    Returns:
        str: 签名文件的路径
    """
    _ensure_signatures_dir()
    sig_path = SIGNATURES_DIR / f"{work_id}.json"

    with open(sig_path, "w", encoding="utf-8") as f:
        json.dump(signature_data, f, ensure_ascii=False, indent=2)

    return str(sig_path.resolve())


def load_signature(work_id: str) -> Optional[dict]:
    """从 JSON 文件加载签名数据.

    Args:
        work_id: 作品/记录 ID

    Returns:
        dict or None: 签名数据; 文件不存在时返回 None
    """
    sig_path = SIGNATURES_DIR / f"{work_id}.json"
    if not sig_path.exists():
        return None

    with open(sig_path, "r", encoding="utf-8") as f:
        return json.load(f)
