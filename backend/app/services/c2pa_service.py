"""C2PA 元数据嵌入服务 — 纯 Python 实现，无需外部 c2patool 依赖.

P2.2.1: Pure Python C2PA Manifest 生成
- 生成符合 C2PA 规范的 manifest JSON
- 包含 claim_generator、assertion (creative_work)、签名信息、素材引用
P3: 二进制嵌入支持 PNG/JPEG
"""

import json
import logging
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec

from app.services.local_notary import generate_ecdsa_keypair


def _generate_claim_generator_id() -> str:
    """生成唯一的 claim generator ID."""
    return f"OriStudio_C2PA/1.0 c2pa-service/0.2.0"


def _public_key_to_jwk(public_key_pem: str) -> dict:
    """将 PEM 公钥转换为 JWK 格式."""
    public_key = serialization.load_pem_public_key(
        public_key_pem.encode("utf-8")
    )
    if not isinstance(public_key, ec.EllipticCurvePublicKey):
        raise ValueError("Only EC public keys are supported for JWK conversion")
    numbers = public_key.public_numbers()
    curve_size = public_key.curve.key_size
    coord_len = (curve_size + 7) // 8
    x_bytes = numbers.x.to_bytes(coord_len, "big")
    y_bytes = numbers.y.to_bytes(coord_len, "big")
    crv_map = {256: "P-256", 384: "P-384", 521: "P-521"}
    return {
        "kty": "EC",
        "crv": crv_map.get(curve_size, f"P-{curve_size}"),
        "x": _base64url_encode(x_bytes),
        "y": _base64url_encode(y_bytes),
    }


def _base64url_encode(data: bytes) -> str:
    """Base64URL 编码 (无填充)."""
    import base64
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _base64url_decode(s: str) -> bytes:
    """Base64URL 解码."""
    import base64
    padding = 4 - len(s) % 4
    if padding != 4:
        s += "=" * padding
    return base64.urlsafe_b64decode(s)


def compute_c2pa_hash(data: bytes) -> str:
    """计算 C2PA 兼容的哈希 (SHA-256, base64url 编码)."""
    h = hashlib.sha256(data)
    return _base64url_encode(h.digest())


def generate_c2pa_manifest(
    work_title: str,
    author_name: str = "OriStudio Creator",
    sha256_hash: Optional[str] = None,
    file_data: Optional[bytes] = None,
    public_key_pem: Optional[str] = None,
    ai_session_summary: Optional[dict] = None,
    creation_timeline: Optional[list[dict]] = None,
) -> dict:
    """生成完整的 C2PA-compatible manifest JSON (P2.2.1).

    纯 Python 实现，无需 c2patool。

    Args:
        work_title: 作品标题
        author_name: 作者名称
        sha256_hash: 作品的 SHA-256 hex 哈希
        file_data: 作品原始字节数据 (用于计算 C2PA hash)
        public_key_pem: PEM 格式 ECDSA 公钥

    Returns:
        dict: 完整的 C2PA manifest
    """
    timestamp = datetime.now(timezone.utc).isoformat()

    # 计算 C2PA 兼容哈希 (base64url-encoded SHA-256)
    if file_data:
        file_hash = compute_c2pa_hash(file_data)
    elif sha256_hash:
        file_hash = _base64url_encode(bytes.fromhex(sha256_hash))
    else:
        file_hash = ""

    # 生成签名者信息
    signer_info = {
        "alg": "es256",
        "issuer": "OriStudio",
        "cert_serial_number": "",
    }
    if public_key_pem:
        signer_info["public_key"] = _public_key_to_jwk(public_key_pem)

    manifest = {
        # C2PA 清单版本
        "claim_generator": _generate_claim_generator_id(),
        "claim_generator_info": [
            {
                "name": "OriStudio C2PA Service",
                "version": "0.2.0",
            }
        ],
        "vendor": "oristudio",
        "recorder": "OriStudio",
        "title": work_title,
        "format": "application/json",
        "instance_id": f"oristudio:{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S%f')}",
        "signature_info": {
            "issuer": "OriStudio",
            "time": timestamp,
            "alg": "es256",
            "ta_url": "",
        },
        # 断言列表
        "assertions": [
            # 1. CreativeWork 内容凭据 (stds.schema-org.CreativeWork)
            {
                "label": "stds.schema-org.CreativeWork",
                "data": {
                    "@context": "https://schema.org",
                    "@type": "CreativeWork",
                    "name": work_title,
                    "author": [
                        {
                            "@type": "Person",
                            "name": author_name,
                        }
                    ],
                    "dateCreated": timestamp,
                },
            },
            # 2. 内容哈希断言 (stds.exif)
            {
                "label": "stds.schema-org.ClaimReview",
                "data": {
                    "@context": "https://schema.org",
                    "@type": "ClaimReview",
                    "claimReviewed": f"Content hash for '{work_title}'",
                    "reviewAspect": "origin",
                    "datePublished": timestamp,
                },
            },
            # 3. 自定义哈希断言
            {
                "label": "oristudio.hash",
                "data": {
                    "algorithm": "SHA-256",
                    "hash": sha256_hash or "",
                    "c2pa_hash": file_hash,
                },
            },
            # 4. 签名断言
            {
                "label": "oristudio.signature",
                "data": {
                    "algorithm": "ECDSA-secp256r1+SHA256",
                    "signed_at": timestamp,
                    "signer": "OriStudio",
                },
            },
            # 5. AI 创作会话摘要 (Phase 0)
            *([{"label": "oristudio.ai_session", "data": ai_session_summary}] if ai_session_summary else []),
            # 6. 创作时间线 (Phase 0)
            *([{"label": "oristudio.creation_timeline", "data": creation_timeline}] if creation_timeline else []),
        ],
        # 素材引用
        "ingredients": [],
        # 签名占位信息
        "signature": {
            "alg": "es256",
            "hash": "",
            "pad": "",
        },
    }

    return manifest


def sign_c2pa_manifest(
    manifest: dict,
    private_key_pem: str,
) -> dict:
    """对 C2PA manifest 进行 ECDSA 签名 (P2.2.1).

    Args:
        manifest: C2PA manifest dict
        private_key_pem: PEM 格式的 ECDSA 私钥

    Returns:
        dict: 已签名的 manifest (包含签名值)
    """
    private_key = serialization.load_pem_private_key(
        private_key_pem.encode("utf-8"), password=None
    )

    # 对 manifest 的断言部分进行规范化后签名
    data_to_sign = json.dumps(
        manifest.get("assertions", []), sort_keys=True, ensure_ascii=False
    ).encode("utf-8")

    signature_der = private_key.sign(
        data_to_sign,
        ec.ECDSA(hashes.SHA256()),
    )

    manifest["signature"] = {
        "alg": "es256",
        "hash": _base64url_encode(signature_der),
        "pad": "",
        "signed_at": datetime.now(timezone.utc).isoformat(),
    }

    return manifest


def generate_c2pa_with_identity(
    work_title: str,
    author_name: str = "OriStudio Creator",
    sha256_hash: Optional[str] = None,
    file_data: Optional[bytes] = None,
    ai_session_summary: Optional[dict] = None,
    creation_timeline: Optional[list[dict]] = None,
) -> tuple[dict, str, str]:
    """生成完整的 C2PA manifest 并附带身份密钥对 (P2.2.1).

    Returns:
        tuple: (manifest, private_key_pem, public_key_pem)
    """
    private_pem, public_pem = generate_ecdsa_keypair()

    manifest = generate_c2pa_manifest(
        work_title=work_title,
        author_name=author_name,
        sha256_hash=sha256_hash,
        file_data=file_data,
        public_key_pem=public_pem,
        ai_session_summary=ai_session_summary,
        creation_timeline=creation_timeline,
    )

    manifest = sign_c2pa_manifest(manifest, private_pem)

    return manifest, private_pem, public_pem


def add_ingredient(
    manifest: dict,
    ingredient_title: str,
    ingredient_hash: str,
    relationship: str = "componentOf",
) -> dict:
    """向 manifest 添加素材引用 (ingredient).

    Args:
        manifest: C2PA manifest
        ingredient_title: 素材名称
        ingredient_hash: 素材的 SHA-256 哈希
        relationship: 素材关系 (componentOf, derivedFrom, etc.)

    Returns:
        dict: 更新后的 manifest
    """
    ingredient = {
        "title": ingredient_title,
        "relationship": relationship,
        "hash": ingredient_hash,
        "hash_algorithm": "sha256",
        "instance_id": f"oristudio:ingredient:{ingredient_title[:32]}:{ingredient_hash[:16]}",
    }
    manifest["ingredients"].append(ingredient)
    return manifest


def verify_c2pa_manifest(manifest: dict, public_key_pem: str) -> bool:
    """验证 C2PA manifest 的 ECDSA 签名 (P2.2.1).

    Args:
        manifest: C2PA manifest dict (含签名字段)
        public_key_pem: PEM 格式的 ECDSA 公钥

    Returns:
        bool: 签名有效则为 True
    """
    from cryptography.exceptions import InvalidSignature

    try:
        public_key = serialization.load_pem_public_key(
            public_key_pem.encode("utf-8")
        )

        signature_hash = manifest.get("signature", {}).get("hash", "")
        if not signature_hash:
            return False

        signature_der = _base64url_decode(signature_hash)

        data_to_sign = json.dumps(
            manifest.get("assertions", []), sort_keys=True, ensure_ascii=False
        ).encode("utf-8")

        public_key.verify(
            signature_der,
            data_to_sign,
            ec.ECDSA(hashes.SHA256()),
        )
        return True
    except (InvalidSignature, KeyError, ValueError):
        return False


def verify_c2pa_metadata(file_path: str) -> Optional[dict]:
    """验证文件中的 C2PA 元数据 (前端兼容).

    注意: 纯 Python 实现无法从二进制文件中提取 C2PA 元数据。
    此函数尝试通过文件名关联查找 manifest 记录。
    """
    # 尝试从对应的 JSON 文件中加载元数据
    meta_path = Path(file_path + ".c2pa.json")
    if meta_path.exists():
        try:
            with open(meta_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            pass

    return {"status": "no_manifest_found", "note": "Pure Python — c2patool not used"}


def embed_c2pa_metadata(
    file_path: str,
    manifest: dict,
    output_path: Optional[str] = None,
) -> Optional[str]:
    """将 C2PA manifest 嵌入文件 (PNG/JPEG 二进制嵌入 + 卫星 fallback).

    支持格式:
    - PNG: 在 IEND 之前插入 c2pa chunk
    - JPEG: 在 APP13 segment 中嵌入 XMP metadata
    - Fallback: 卫星 JSON 文件

    Args:
        file_path: 源文件路径
        manifest: C2PA manifest dict
        output_path: 输出文件路径

    Returns:
        嵌入成功返回文件路径，失败返回卫星文件路径或 None
    """
    ext = Path(file_path).suffix.lower()

    # Serialize manifest to bytes
    manifest_json = json.dumps(manifest, ensure_ascii=False, indent=2).encode("utf-8")

    try:
        if ext in (".png",):
            return _embed_png(file_path, manifest_json, output_path)
        elif ext in (".jpg", ".jpeg"):
            return _embed_jpeg(file_path, manifest_json, output_path)
        else:
            logging.getLogger(__name__).info("No binary embedder for %s, using satellite mode", ext)
    except Exception as e:
        logging.getLogger(__name__).warning("Binary embedding failed for %s: %s, falling back to satellite", ext, e)

    # Fallback: satellite JSON
    return _save_satellite_manifest(file_path, manifest)


def _embed_png(file_path: str, manifest_bytes: bytes, output_path: Optional[str]) -> Optional[str]:
    """Embed C2PA manifest into PNG binary."""
    from app.services.c2pa_embedder import embed_into_png

    result = embed_into_png(file_path, manifest_bytes, output_path)
    if result:
        return result

    # If embed_into_png fails, fall through to satellite
    return None


def _embed_jpeg(file_path: str, manifest_bytes: bytes, output_path: Optional[str]) -> Optional[str]:
    """Embed C2PA manifest into JPEG as XMP in APP13 segment."""
    from app.services.c2pa_embedder import embed_into_jpeg

    # Convert manifest JSON to XMP format
    xmp_template = """<?xpacket begin='' id='W5M0MpCehiHzreSzNTczkc9d'?>
<x:xmpmeta xmlns:x='adobe:ns:meta/'>
 <rdf:RDF xmlns:rdf='http://www.w3.org/1999/02/22-rdf-syntax-ns#'>
  <rdf:Description rdf:about=''
    xmlns:c2pa='{manifest_vendor}'>
   <c2pa:manifestHash>{manifest_hash}</c2pa:manifestHash>
  </rdf:Description>
 </rdf:RDF>
</x:xmpmeta>
<?xpacket end='w'?>"""

    import hashlib
    manifest_hash = hashlib.sha256(manifest_bytes).hexdigest()
    vendor = "oristudio"
    xmp_data = xmp_template.format(
        manifest_vendor=vendor,
        manifest_hash=manifest_hash,
    ).encode("utf-8")

    result = embed_into_jpeg(file_path, xmp_data, output_path)
    if result:
        return result

    return None


def _save_satellite_manifest(file_path: str, manifest: dict) -> Optional[str]:
    """Save C2PA manifest as satellite JSON file."""
    output_path = file_path + ".c2pa.json"
    try:
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        manifest_with_ref = dict(manifest)
        manifest_with_ref["source_file"] = file_path
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(manifest_with_ref, f, ensure_ascii=False, indent=2)
        return output_path
    except Exception as e:
        print(f"C2PA embedding error: {e}")
        return None
