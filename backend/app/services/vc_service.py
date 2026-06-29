"""W3C Verifiable Credential 服务 (P2.2.3).

实现:
- create_work_credential(work, did, signature_data) — 生成 W3C VC
- verify_credential(credential_json) — 验证 VC 签名

基于 W3C Verifiable Credentials Data Model v1.1
(https://www.w3.org/TR/vc-data-model/)
"""

import json
import hashlib
from datetime import datetime, timezone
from typing import Optional

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.exceptions import InvalidSignature

from app.services.did_service import generate_did, create_did_document


# VC 上下文
VC_CONTEXT = [
    "https://www.w3.org/2018/credentials/v1",
    "https://www.w3.org/2018/credentials/examples/v1",
]

# 作品凭据类型
WORK_CREDENTIAL_TYPE = ["VerifiableCredential", "WorkCredential"]


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


def _sign_data(data: bytes, private_key_pem: str) -> str:
    """使用 ECDSA 对数据进行签名，返回 base64url 编码的签名."""
    private_key = serialization.load_pem_private_key(
        private_key_pem.encode("utf-8"), password=None
    )
    signature_der = private_key.sign(
        data,
        ec.ECDSA(hashes.SHA256()),
    )
    return _base64url_encode(signature_der)


def _verify_signature(data: bytes, signature_b64: str, public_key_pem: str) -> bool:
    """使用 ECDSA 验证签名."""
    try:
        public_key = serialization.load_pem_public_key(
            public_key_pem.encode("utf-8")
        )
        signature_der = _base64url_decode(signature_b64)
        public_key.verify(
            signature_der,
            data,
            ec.ECDSA(hashes.SHA256()),
        )
        return True
    except (InvalidSignature, ValueError, KeyError):
        return False


def _canonical_json(obj) -> str:
    """生成规范的 JSON 字符串 (排序键)."""
    return json.dumps(obj, sort_keys=True, ensure_ascii=False, indent=0, separators=(",", ":"))


def create_work_credential(
    work: dict,
    issuer_did: str,
    signature_data: dict,
    private_key_pem: Optional[str] = None,
) -> dict:
    """为作品创建 W3C Verifiable Credential (P2.2.3).

    Args:
        work: 作品信息字典 (id, title, sha256, file_type, created_at)
        issuer_did: 发行方的 DID 标识符
        signature_data: ECDSA 签名数据 (from local_notary.sign_work)
        private_key_pem: 发行方 ECDSA 私钥 (用于签发 VC)

    Returns:
        dict: W3C Verifiable Credential JSON-LD
    """
    now = datetime.now(timezone.utc)

    credential_id = f"urn:oristudio:vc:{work.get('id', 'unknown')}:{now.strftime('%Y%m%d%H%M%S%f')}"

    # 构建凭证主体
    credential_subject = {
        "id": issuer_did,
        "type": "WorkCredential",
        "work": {
            "id": work.get("id", ""),
            "title": work.get("title", "Untitled"),
            "sha256": work.get("sha256", ""),
            "file_type": work.get("file_type", "unknown"),
            "created_at": work.get("created_at", now.isoformat()),
        },
        "proof_of_creation": {
            "algorithm": signature_data.get("algorithm", "ECDSA-secp256r1+SHA256"),
            "timestamp": signature_data.get("timestamp", now.isoformat()),
            "signature": signature_data.get("signature", ""),
        },
    }

    # 构建 VC
    credential = {
        "@context": VC_CONTEXT,
        "id": credential_id,
        "type": WORK_CREDENTIAL_TYPE,
        "issuer": {
            "id": issuer_did,
            "name": "OriStudio Notary Service",
        },
        "issuanceDate": now.isoformat(),
        "credentialSubject": credential_subject,
    }

    # 如果提供了私钥，生成 proof
    if private_key_pem:
        credential = _add_proof(credential, private_key_pem, issuer_did)

    return credential


def _add_proof(credential: dict, private_key_pem: str, issuer_did: str) -> dict:
    """向 VC 添加 Linked Data Proof (ECDSA).

    Args:
        credential: VC 字典 (不带 proof)
        private_key_pem: 发行方私钥
        issuer_did: 发行方 DID

    Returns:
        dict: 带 proof 的 VC
    """
    now = datetime.now(timezone.utc)

    # 创建 proof 对象 (不带签名值)
    proof_template = {
        "type": "EcdsaSecp256r1Signature2019",
        "created": now.isoformat(),
        "proofPurpose": "assertionMethod",
        "verificationMethod": f"{issuer_did}#{issuer_did.split(':')[-1][:8]}",
    }

    # 将 credential 和 proof 规范化进行签名
    credential_copy = dict(credential)
    credential_copy.pop("proof", None)

    # 签名数据: 规范化 credential + proof template
    canonical_target = _canonical_json(credential_copy)
    proof_base = _canonical_json(proof_template)

    data_to_sign = f"{canonical_target}\n{proof_base}".encode("utf-8")

    signature_value = _sign_data(data_to_sign, private_key_pem)

    proof = dict(proof_template)
    proof["jws"] = signature_value

    credential["proof"] = proof
    return credential


def verify_credential(credential: dict) -> dict:
    """验证 Verifiable Credential (P2.2.3).

    执行基本验证:
    - 检查 proof 字段是否存在
    - 验证 proof.jws 签名 (如果提供了公钥)

    Args:
        credential: W3C Verifiable Credential JSON

    Returns:
        dict: {
            "valid": bool,
            "checks": list[str],
            "errors": list[str],
        }
    """
    checks = []
    errors = []

    # 检查基本结构
    if "@context" in credential:
        checks.append("Context present")
    else:
        errors.append("Missing @context")

    if "type" in credential and "VerifiableCredential" in credential.get("type", []):
        checks.append("Valid credential type")
    else:
        errors.append("Missing or invalid credential type")

    if "issuer" in credential:
        checks.append("Issuer present")
    else:
        errors.append("Missing issuer")

    if "credentialSubject" in credential:
        checks.append("Credential subject present")
    else:
        errors.append("Missing credentialSubject")

    if "issuanceDate" in credential:
        checks.append("Issuance date present")
    else:
        errors.append("Missing issuanceDate")

    # 检查 proof
    proof = credential.get("proof", {})
    if proof:
        checks.append("Proof present")
        if "type" in proof:
            checks.append(f"Proof type: {proof['type']}")
        else:
            errors.append("Missing proof type")
        if "jws" in proof:
            checks.append("Proof signature (jws) present")
        else:
            errors.append("Missing proof signature (jws)")
    else:
        errors.append("Missing proof — credential is unsigned")

    valid = len(errors) == 0

    return {
        "valid": valid,
        "checks": checks,
        "errors": errors,
    }


def create_work_credential_full(
    work: dict,
    public_key_pem: str,
    private_key_pem: str,
    signature_data: dict,
) -> dict:
    """完整的作品凭据生成流程 (P2.2.3).

    Args:
        work: 作品信息字典
        public_key_pem: 发行方 ECDSA 公钥
        private_key_pem: 发行方 ECDSA 私钥
        signature_data: ECDSA 签名数据

    Returns:
        dict: {
            "did": str,
            "did_document": dict,
            "credential": dict,
        }
    """
    did = generate_did(public_key_pem)
    did_doc = create_did_document(did, public_key_pem)
    credential = create_work_credential(work, did, signature_data, private_key_pem)

    return {
        "did": did,
        "did_document": did_doc,
        "credential": credential,
    }
