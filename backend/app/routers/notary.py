"""存证确权 API 路由 — 对应: docs/modules-v5/02-rights-protection.md
端点: 18 (notary)

所有 DB 操作已提取至 notary_manager_service.py.
"""

import json
import logging
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import require_auth
from app.schemas.common import ApiResponse
from app.schemas.notary import (
    NotaryRecordCreate, NotaryRecordResponse, NotaryRecordListResponse,
    CertificateResponse, NotaryPlatformInfo,
    C2PAManifestResponse, C2PAVerifyResponse,
    DIDDocumentResponse, VCGenerateResponse, VCVerifyResponse,
    MerkleBatchRequest, MerkleBatchResponse, MerkleProofResponse,
    NotaryCompareRequest, NotaryCompareResponse, PlatformFeeItem,
    NotaryRecommendResponse,
    AuditTrailItem, AuditTrailResponse,
    NotaryVerifyResponse, EvidenceChainItem,
)
from app.services.notary_manager_service import NotaryManagerService
from app.services.certificate_service import generate_certificate_pdf
from app.services.hasher import compute_sha256
from app.services.local_notary import sign_work, save_signature, generate_ecdsa_keypair
from app.services.merkle_tree import build_merkle_tree
from app.services.c2pa_service import (
    generate_c2pa_manifest, sign_c2pa_manifest, verify_c2pa_manifest,
    generate_c2pa_with_identity, embed_c2pa_metadata, add_ingredient,
)
from app.services.did_service import generate_did, create_did_document, resolve_did
from app.services.vc_service import (
    create_work_credential, verify_credential, create_work_credential_full,
)

router = APIRouter()


class BatchNotarizePayload(BaseModel):
    work_ids: list[str]
    platform: str


class AnchorToPolygonPayload(BaseModel):
    work_id: str


class RequestTimestampPayload(BaseModel):
    work_id: str


# 存证平台配置
NOTARY_PLATFORMS = {
    "banquanjia": NotaryPlatformInfo(
        key="banquanjia",
        name="版权家",
        description="国家版权局 DCI 体系，法律效力最高",
        fee_per_record=3.0,
        legal_level="national",
        website="https://www.banquanjia.com",
    ),
    "antchain": NotaryPlatformInfo(
        key="antchain",
        name="蚂蚁链",
        description="支付宝蚂蚁区块链存证，商用级",
        fee_per_record=0.5,
        legal_level="commercial",
        website="https://antchain.antgroup.com",
    ),
    "zhixinchain": NotaryPlatformInfo(
        key="zhixinchain",
        name="至信链",
        description="腾讯/互联网法院司法链，司法级",
        fee_per_record=1.0,
        legal_level="judicial",
        website="https://zhixinchain.com",
    ),
}


# ==============================================================================
# Platform endpoints (no DB)
# ==============================================================================

@router.get("/notary/platforms", response_model=ApiResponse[list[NotaryPlatformInfo]])
def get_notary_platforms(db: Session = Depends(get_db)):
    """获取可用的存证平台列表 (P1.7.13: dictStore-backed, 硬编码为 fallback)."""
    try:
        from app.utils.system_helpers import get_dict_values_rich
        dict_entries = get_dict_values_rich("notary_platforms", db)
        if dict_entries:
            platforms = []
            for entry in dict_entries:
                extra = entry.get("extra") or {}
                platforms.append(NotaryPlatformInfo(
                    key=entry["item_key"],
                    name=entry["item_value"],
                    description=extra.get("description", ""),
                    fee_per_record=extra.get("fee_per_record", 1.0),
                    legal_level=extra.get("legal_level", "commercial"),
                    website=extra.get("url", ""),
                ))
            if platforms:
                return ApiResponse(data=platforms)
    except Exception as e:
        logging.getLogger(__name__).exception("Error in get_notary_platforms: %s", str(e))
    return ApiResponse(data=list(NOTARY_PLATFORMS.values()))


# ==============================================================================
# Records CRUD
# ==============================================================================

@router.get("/notary/records", response_model=ApiResponse[NotaryRecordListResponse])
def list_notary_records(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[str] = None,
    platform: Optional[str] = None,
    work_id: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """获取存证记录列表."""
    svc = NotaryManagerService(db)
    result = svc.list_notary_records(page, page_size, status, platform, work_id)
    return ApiResponse(data=NotaryRecordListResponse(**result))


@router.post("/notary/records", response_model=ApiResponse[NotaryRecordResponse])
def create_notary_record(
    data: NotaryRecordCreate,
    db: Session = Depends(get_db),
    _auth=Depends(require_auth),
):
    """创建存证记录 (含 ECDSA L1 本地签名)."""
    svc = NotaryManagerService(db)

    work = svc.get_work(data.work_id)
    if not work:
        raise HTTPException(status_code=404, detail="作品不存在")

    if data.platform not in NOTARY_PLATFORMS:
        raise HTTPException(status_code=400, detail="不支持的存证平台")

    platform_info = NOTARY_PLATFORMS[data.platform]
    return ApiResponse(data=svc.create_notary_record(data, platform_info, work))


@router.get("/notary/records/{record_id}", response_model=ApiResponse[NotaryRecordResponse])
def get_notary_record(record_id: str, db: Session = Depends(get_db)):
    """获取存证记录详情."""
    svc = NotaryManagerService(db)
    return ApiResponse(data=svc.get_notary_record(record_id))


@router.post("/notary/records/{record_id}/confirm", response_model=ApiResponse[NotaryRecordResponse])
def confirm_notary_record(
    record_id: str,
    data: Optional[dict] = None,
    transaction_hash: Optional[str] = None,
    block_height: Optional[str] = None,
    platform_url: Optional[str] = None,
    db: Session = Depends(get_db),
    _auth=Depends(require_auth),
):
    """确认存证完成并生成证书."""
    svc = NotaryManagerService(db)

    # 兼容 JSON body 和 query params
    if data:
        transaction_hash = data.get("transaction_hash", transaction_hash)
        block_height = data.get("block_height", block_height)
        platform_url = data.get("platform_url", platform_url)

    try:
        record = svc.confirm_notary_record_with_all_ops(
            record_id, transaction_hash, block_height, platform_url,
        )
    except HTTPException:
        raise
    except Exception as e:
        logging.getLogger(__name__).exception("Error in confirm_notary_record: %s", str(e))
        raise HTTPException(status_code=500, detail=f"确认存证失败: {str(e)}")

    # P1.7.14: Push notification after notary record confirmed
    try:
        work = svc.get_work(record.work_id)
        from app.utils.system_helpers import push_notification
        push_notification(
            db, user_id="default",
            type="cert_ready",
            title="存证确认完成",
            content=f"作品「{work.title if work else '未知'}」的存证已确认完成，证书已生成。",
            related_module="notary",
            related_id=record.id,
        )
    except Exception as e:
        logging.getLogger(__name__).exception("Error pushing notification: %s", str(e))

    return ApiResponse(data=record)


@router.post("/notary/batch", response_model=ApiResponse)
def batch_notarize(
    data: BatchNotarizePayload,
    db: Session = Depends(get_db),
    _auth=Depends(require_auth),
):
    """批量创建存证记录."""
    from app.models.work import Work
    svc = NotaryManagerService(db)

    platform: str = data.platform
    if platform not in NOTARY_PLATFORMS:
        raise HTTPException(status_code=400, detail="不支持的存证平台")

    platform_info = NOTARY_PLATFORMS[platform]
    count = svc.batch_notarize(data.work_ids, platform, platform_info)

    return ApiResponse(
        message=f"成功创建 {count} 条存证记录",
        data={"count": count},
    )


# ==============================================================================
# Certificates
# ==============================================================================

@router.get("/notary/certificates/{cert_id}", response_model=ApiResponse[CertificateResponse])
def get_certificate(cert_id: str, db: Session = Depends(get_db)):
    """获取证书详情."""
    svc = NotaryManagerService(db)
    return ApiResponse(data=svc.get_certificate(cert_id))


@router.get("/notary/certificates/{cert_id}/download")
def download_certificate(cert_id: str, db: Session = Depends(get_db)):
    """下载证书 PDF 文件."""
    svc = NotaryManagerService(db)
    cert = svc.get_certificate_record(cert_id)

    cert_path = Path(cert.cert_path)
    if not cert_path.exists():
        raise HTTPException(status_code=404, detail="证书文件不存在")

    filename = f"certificate_{cert_id[:12]}.pdf"
    return FileResponse(
        path=str(cert_path),
        media_type="application/pdf",
        filename=filename,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


# ==============================================================================
# C2PA
# ==============================================================================

@router.post("/notary/c2pa/{work_id}/generate", response_model=ApiResponse[C2PAManifestResponse])
def generate_c2pa_for_work(
    work_id: str,
    db: Session = Depends(get_db),
    _auth=Depends(require_auth),
):
    """生成并存储 C2PA manifest (P2.2.4)."""
    svc = NotaryManagerService(db)

    work = svc.get_work(work_id)
    if not work:
        raise HTTPException(status_code=404, detail="作品不存在")

    if not work.sha256:
        raise HTTPException(status_code=400, detail="作品文件不存在，无法计算哈希")

    file_data = None
    if os.path.exists(work.file_path):
        with open(work.file_path, "rb") as f:
            file_data = f.read()

    manifest, private_pem, public_pem = generate_c2pa_with_identity(
        work_title=work.title,
        author_name="OriStudio Creator",
        sha256_hash=work.sha256,
        file_data=file_data,
    )

    c2pa_dir = Path("data/c2pa")
    c2pa_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = c2pa_dir / f"{work_id}.c2pa.json"

    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)

    keys_dir = Path("data/certificates/signatures")
    keys_dir.mkdir(parents=True, exist_ok=True)
    key_path = keys_dir / f"{work_id}_c2pa_key.json"
    key_data = {
        "private_key_pem": private_pem,
        "public_key_pem": public_pem,
        "algorithm": "ECDSA-secp256r1+SHA256",
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    with open(key_path, "w", encoding="utf-8") as f:
        json.dump(key_data, f, ensure_ascii=False, indent=2)

    return ApiResponse(
        message="C2PA manifest 生成成功",
        data=svc.generate_c2pa_for_work(work, manifest),
    )


@router.get("/notary/verify/c2pa/{work_id}", response_model=ApiResponse[C2PAVerifyResponse])
def verify_c2pa_for_work(work_id: str, db: Session = Depends(get_db)):
    """验证作品的 C2PA manifest (P2.2.4)."""
    svc = NotaryManagerService(db)

    work = svc.get_work(work_id)
    if not work:
        raise HTTPException(status_code=404, detail="作品不存在")

    manifest_path = Path("data/c2pa") / f"{work_id}.c2pa.json"
    if not manifest_path.exists():
        return ApiResponse(data=C2PAVerifyResponse(
            work_id=work_id,
            status="no_manifest",
            is_valid=False,
            details={"error": "C2PA manifest 不存在，请先生成"},
        ))

    try:
        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest = json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        return ApiResponse(data=C2PAVerifyResponse(
            work_id=work_id,
            status="error",
            is_valid=False,
            details={"error": f"读取 manifest 失败: {str(e)}"},
        ))

    keys_dir = Path("data/certificates/signatures")
    key_path = keys_dir / f"{work_id}_c2pa_key.json"

    is_valid = False
    details = {
        "has_claim_generator": "claim_generator" in manifest,
        "has_assertions": "assertions" in manifest,
        "assertion_count": len(manifest.get("assertions", [])),
        "has_signature": bool(manifest.get("signature", {}).get("hash")),
        "has_ingredients": "ingredients" in manifest,
        "ingredient_count": len(manifest.get("ingredients", [])),
    }

    if key_path.exists():
        try:
            with open(key_path, "r", encoding="utf-8") as f:
                key_data = json.load(f)
            public_key_pem = key_data.get("public_key_pem")
            if public_key_pem:
                is_valid = verify_c2pa_manifest(manifest, public_key_pem)
                details["signature_verified"] = is_valid
            else:
                details["signature_verified"] = None
                details["error"] = "未找到公钥"
        except (json.JSONDecodeError, IOError, KeyError) as e:
            details["signature_verified"] = None
            details["error"] = f"加载密钥失败: {str(e)}"
    else:
        details["signature_verified"] = None
        details["error"] = "未找到签名密钥"

    status = "valid" if is_valid else "invalid_or_unsigned"

    return ApiResponse(data=C2PAVerifyResponse(
        work_id=work_id,
        status=status,
        manifest=manifest,
        is_valid=is_valid,
        details=details,
    ))


# ==============================================================================
# DID + VC endpoints (no DB)
# ==============================================================================

@router.post("/notary/did/generate", response_model=ApiResponse[DIDDocumentResponse])
def generate_did_endpoint(_auth=Depends(require_auth)):
    """生成 W3C DID 标识符和 DID Document (P2.2.2)."""
    private_pem, public_pem = generate_ecdsa_keypair()
    did = generate_did(public_pem)
    did_doc = create_did_document(did, public_pem)

    return ApiResponse(data=DIDDocumentResponse(
        did=did,
        did_document=did_doc,
        public_key_pem=public_pem,
    ))


@router.get("/notary/did/resolve", response_model=ApiResponse[DIDDocumentResponse])
def resolve_did_endpoint(did: str = Query(..., description="要解析的 DID 标识符")):
    """解析 W3C DID 并返回 DID Document (P2.2.2)."""
    did_doc = resolve_did(did)
    if did_doc is None:
        raise HTTPException(status_code=400, detail="无法解析该 DID (仅支持 did:key 方法)")

    return ApiResponse(data=DIDDocumentResponse(
        did=did,
        did_document=did_doc,
        public_key_pem="",
    ))


@router.post("/notary/vc/{work_id}/generate", response_model=ApiResponse[VCGenerateResponse])
def generate_vc_for_work(
    work_id: str,
    db: Session = Depends(get_db),
    _auth=Depends(require_auth),
):
    """生成作品的 W3C Verifiable Credential (P2.2.3)."""
    svc = NotaryManagerService(db)

    work = svc.get_work(work_id)
    if not work:
        raise HTTPException(status_code=404, detail="作品不存在")

    if not work.sha256:
        raise HTTPException(status_code=400, detail="作品文件不存在")

    signature_data = sign_work(work.sha256)
    private_pem, public_pem = generate_ecdsa_keypair()

    work_dict = {
        "id": work.id,
        "title": work.title,
        "sha256": work.sha256,
        "file_type": work.file_type,
        "created_at": work.created_at.isoformat() if work.created_at else None,
    }

    vc_data = create_work_credential_full(
        work=work_dict,
        public_key_pem=public_pem,
        private_key_pem=private_pem,
        signature_data=signature_data,
    )

    vc_dir = Path("data/vc")
    vc_dir.mkdir(parents=True, exist_ok=True)
    vc_path = vc_dir / f"{work_id}.vc.json"
    with open(vc_path, "w", encoding="utf-8") as f:
        json.dump(vc_data["credential"], f, ensure_ascii=False, indent=2)

    keys_dir = Path("data/certificates/signatures")
    keys_dir.mkdir(parents=True, exist_ok=True)
    key_path = keys_dir / f"{work_id}_vc_key.json"
    key_info = {
        "did": vc_data["did"],
        "private_key_pem": private_pem,
        "public_key_pem": public_pem,
    }
    with open(key_path, "w", encoding="utf-8") as f:
        json.dump(key_info, f, ensure_ascii=False, indent=2)

    return ApiResponse(
        message="Verifiable Credential 生成成功",
        data=VCGenerateResponse(
            work_id=work_id,
            did=vc_data["did"],
            did_document=vc_data["did_document"],
            credential=vc_data["credential"],
        ),
    )


@router.post("/notary/vc/verify", response_model=ApiResponse[VCVerifyResponse])
def verify_vc_endpoint(credential: dict, _auth=Depends(require_auth)):
    """验证 W3C Verifiable Credential (P2.2.3)."""
    result = verify_credential(credential)
    return ApiResponse(
        message="验证完成" if result["valid"] else "验证失败",
        data=VCVerifyResponse(
            valid=result["valid"],
            checks=result["checks"],
            errors=result["errors"],
        ),
    )


# ==============================================================================
# Merkle Tree
# ==============================================================================

@router.post("/notary/merkle/batch", response_model=ApiResponse[MerkleBatchResponse])
def merkle_batch_anchor(
    data: MerkleBatchRequest,
    db: Session = Depends(get_db),
    _auth=Depends(require_auth),
):
    """批量作品 Merkle Tree 锚定 (P1.2.1)."""
    svc = NotaryManagerService(db)

    if data.platform not in NOTARY_PLATFORMS:
        raise HTTPException(status_code=400, detail="不支持的存证平台")

    work_hashes, work_map = svc.collect_work_hashes(data.work_ids)

    if len(work_hashes) < 2:
        raise HTTPException(status_code=400, detail="至少需要 2 个有 hash 的作品")

    tree = build_merkle_tree(work_hashes)
    root = tree.get_root()

    proofs = []
    for work_hash, work in work_map.items():
        proof = tree.get_proof(work_hash)
        if proof:
            proofs.append(MerkleProofResponse(
                work_id=work.id,
                leaf_hash=proof["leaf"],
                leaf_index=proof["leaf_index"],
                root=proof["root"],
                proof=proof["proof"],
                tree_depth=proof["tree_depth"],
                total_leaves=proof["total_leaves"],
            ))

    return ApiResponse(
        message=f"Merkle tree built: root={root[:16]}..., {len(proofs)} works anchored",
        data=MerkleBatchResponse(
            root=root,
            total_works=len(work_map),
            tree_depth=len(tree.levels),
            proofs=proofs,
        ),
    )


# ==============================================================================
# Platform comparison (no DB)
# ==============================================================================

_PLATFORM_PROFILES = {
    "banquanjia": {
        "pros": ["DCI 法律效力最高", "国家版权局体系", "司法认可度强"],
        "cons": ["费用较高", "处理时间较长", "批量支持一般"],
        "priority": ["legal", "national"],
    },
    "antchain": {
        "pros": ["费用最低", "蚂蚁区块链技术", "批量处理强", "速度快"],
        "cons": ["法律效力中等", "商用场景为主"],
        "priority": ["cost", "speed"],
    },
    "zhixinchain": {
        "pros": ["司法链背书", "互联网法院认可", "性价比高"],
        "cons": ["平台接入门槛"],
        "priority": ["judicial", "cost"],
    },
}

_WORK_TYPE_SCORES = {
    "image": {"banquanjia": 9, "antchain": 8, "zhixinchain": 9},
    "text": {"banquanjia": 8, "antchain": 8, "zhixinchain": 8},
    "audio": {"banquanjia": 7, "antchain": 8, "zhixinchain": 7},
    "video": {"banquanjia": 6, "antchain": 7, "zhixinchain": 6},
    "code": {"banquanjia": 5, "antchain": 8, "zhixinchain": 6},
}


def _score_platform(key: str, platform_info, work_type: str, budget: float,
                    legal_level: str, work_count: int, priority: str) -> tuple:
    """综合评分一个平台，返回 (score, reasons)."""
    reasons = []
    score = 50

    profile = _PLATFORM_PROFILES.get(key, {"pros": [], "cons": [], "priority": []})

    total_fee = platform_info.fee_per_record * work_count
    if total_fee <= budget:
        score += 20
        reasons.append(f"总费用 {total_fee:.2f} 元在预算 {budget:.2f} 元内")
    else:
        score -= 15
        reasons.append(f"总费用 {total_fee:.2f} 元超出预算 {budget:.2f} 元")

    legal_map = {"national": 30, "judicial": 20, "commercial": 10}
    if platform_info.legal_level == legal_level:
        score += legal_map.get(legal_level, 10)
        reasons.append(f"法律等级 '{platform_info.legal_level}' 匹配需求")
    elif legal_level == "national" and platform_info.legal_level == "judicial":
        score += 10
        reasons.append(f"法律等级接近需求 (judicial vs national)")

    wt_score = _WORK_TYPE_SCORES.get(work_type, {}).get(key, 5)
    score += wt_score * 2
    reasons.append(f"作品类型 '{work_type}' 适配评分: {wt_score}/10")

    if priority in profile.get("priority", []):
        score += 15
        reasons.append(f"优先维度 '{priority}' 平台优势匹配")

    fee_rank = {"antchain": 15, "zhixinchain": 8, "banquanjia": 0}
    score += fee_rank.get(key, 0)
    if key == "antchain":
        reasons.append("费用最低")

    return score, reasons


@router.get("/notary/compare", response_model=ApiResponse[NotaryCompareResponse])
def compare_notary_platforms(
    work_count: int = Query(1, ge=1, le=1000),
    work_type: str = Query("image"),
    budget: float = Query(50.0, ge=0),
    legal_level: str = Query("commercial"),
    priority: str = Query("cost"),
):
    """存证平台费用比较 + AI 推荐 (P1.2.6)."""
    platforms = []
    best_key = None
    best_score = -1

    for key, info in NOTARY_PLATFORMS.items():
        profile = _PLATFORM_PROFILES.get(key, {"pros": [], "cons": []})
        total_fee = info.fee_per_record * work_count

        score, reasons = _score_platform(
            key, info, work_type, budget, legal_level, work_count, priority
        )

        platforms.append(PlatformFeeItem(
            key=key,
            name=info.name,
            fee_per_record=info.fee_per_record,
            legal_level=info.legal_level,
            estimated_total=round(total_fee, 2),
            pros=profile["pros"],
            cons=profile["cons"],
        ))

        if score > best_score:
            best_score = score
            best_key = key

    platforms.sort(key=lambda p: p.estimated_total)

    _, best_reasons = _score_platform(
        best_key, NOTARY_PLATFORMS[best_key], work_type, budget,
        legal_level, work_count, priority
    )

    return ApiResponse(
        message=f"推荐平台: {NOTARY_PLATFORMS[best_key].name}",
        data=NotaryCompareResponse(
            work_count=work_count,
            work_type=work_type,
            budget=budget,
            legal_level=legal_level,
            platforms=platforms,
            recommended=best_key,
            reasons=best_reasons,
        ),
    )


@router.post("/notary/recommend", response_model=ApiResponse[NotaryRecommendResponse])
def recommend_notary_platform(
    work_id: str = Query(...),
    db: Session = Depends(get_db),
    _auth=Depends(require_auth),
):
    """为指定作品推荐最佳存证平台 (P1.2.6)."""
    svc = NotaryManagerService(db)

    work = svc.get_work_for_recommend(work_id)
    if not work:
        raise HTTPException(status_code=404, detail="作品不存在")

    ext = (work.file_type or "").lower()
    if ext in ("jpg", "jpeg", "png", "gif", "bmp", "webp", "svg"):
        work_type = "image"
    elif ext in ("txt", "md", "pdf", "doc", "docx", "epub"):
        work_type = "text"
    elif ext in ("mp3", "wav", "ogg", "flac", "aac"):
        work_type = "audio"
    elif ext in ("mp4", "avi", "mov", "wmv", "mkv", "webm"):
        work_type = "video"
    elif ext in ("py", "js", "ts", "java", "cpp", "c", "rs", "go"):
        work_type = "code"
    else:
        work_type = "image"

    budget = 50.0
    legal_level = "commercial"
    priority = "cost"

    best_key = None
    best_score = -1

    for key, info in NOTARY_PLATFORMS.items():
        score, _ = _score_platform(key, info, work_type, budget, legal_level, 1, priority)
        if score > best_score:
            best_score = score
            best_key = key

    _, reasons = _score_platform(
        best_key, NOTARY_PLATFORMS[best_key], work_type, budget,
        legal_level, 1, priority
    )

    return ApiResponse(
        message=f"为作品 '{work.title}' 推荐平台: {NOTARY_PLATFORMS[best_key].name}",
        data=NotaryRecommendResponse(
            work_id=work_id,
            recommended_platform=best_key,
            platform_name=NOTARY_PLATFORMS[best_key].name,
            estimated_fee=NOTARY_PLATFORMS[best_key].fee_per_record,
            reasons=reasons,
        ),
    )


# ==============================================================================
# Audit Trail
# ==============================================================================

@router.get("/notary/records/{record_id}/audit-trail", response_model=ApiResponse[AuditTrailResponse])
def get_notary_audit_trail(record_id: str, db: Session = Depends(get_db)):
    """获取存证记录的审计追踪 (P1.2.7)."""
    svc = NotaryManagerService(db)
    result = svc.get_notary_audit_trail(record_id)
    return ApiResponse(
        message=f"Found {len(result['steps'])} audit trail steps",
        data=AuditTrailResponse(**result),
    )


# ==============================================================================
# Polygon + DigiCert TSA
# ==============================================================================

@router.post("/notary/polygon", response_model=ApiResponse)
def anchor_to_polygon(
    data: AnchorToPolygonPayload,
    db: Session = Depends(get_db),
    _auth=Depends(require_auth),
):
    """将作品哈希锚定到 Polygon 公链 (Phase 0)."""
    from app.gateway.polygon import PolygonNotaryGateway
    svc = NotaryManagerService(db)

    work_id = data.work_id
    work = svc.get_work(work_id)
    if not work:
        raise HTTPException(status_code=404, detail="作品不存在")

    if not work.sha256:
        raise HTTPException(status_code=400, detail="作品需要先计算哈希")

    gateway = PolygonNotaryGateway()
    anchor = gateway.anchor(work.sha256)

    if not anchor:
        raise HTTPException(status_code=500, detail="Polygon 锚定失败")

    svc.create_polygon_record(work_id, anchor)

    return ApiResponse(
        message=f"已锚定到 Polygon: {anchor.tx_hash[:20]}...",
        data={
            "tx_hash": anchor.tx_hash,
            "block_number": anchor.block_number,
            "contract_address": anchor.contract_address,
        },
    )


@router.post("/notary/timestamp", response_model=ApiResponse)
async def request_timestamp(
    data: RequestTimestampPayload,
    db: Session = Depends(get_db),
    _auth=Depends(require_auth),
):
    """请求 RFC 3161 时间戳 (Phase 0)."""
    from app.services.timestamp_service import TimestampService
    svc = NotaryManagerService(db)

    work_id = data.work_id
    work = svc.get_work(work_id)
    if not work:
        raise HTTPException(status_code=404, detail="作品不存在")

    if not work.file_path or not os.path.exists(work.file_path):
        raise HTTPException(status_code=400, detail="作品文件不存在")

    service = TimestampService()
    token = await service.timestamp_file(work.file_path)

    if not token:
        raise HTTPException(status_code=500, detail="时间戳请求失败")

    ts_path = await service.save_timestamp(token, work_id)
    svc.get_or_create_timestamp_record(work_id, ts_path)

    return ApiResponse(
        message="RFC 3161 时间戳生成成功",
        data={"timestamp_path": str(ts_path)},
    )


# ==============================================================================
# Universal Verify Endpoint
# ==============================================================================

@router.get("/notary/verify/{record_id}", response_model=ApiResponse[NotaryVerifyResponse])
def verify_notary_record(record_id: str, db: Session = Depends(get_db)):
    """通用存证验证端点 (P0)."""
    from app.models.notary import C2PARecord
    svc = NotaryManagerService(db)

    record, work = svc.get_verify_record(record_id)

    l1_status = "verified" if record.notes and "L1 Signature" in (record.notes or "") else "pending"
    evidence_chain = [EvidenceChainItem(
        level="L1", type="ECDSA 本地签名", status=l1_status,
        details={"sig_ref": "data/certificates/signatures"} if l1_status == "verified" else None,
    )]

    l2_status = "verified" if record.status == "confirmed" else ("pending" if record.status == "pending" else "failed")
    evidence_chain.append(EvidenceChainItem(
        level="L2", type=f"区块链 ({NOTARY_PLATFORMS.get(record.platform, {}).get('name', record.platform)})",
        status=l2_status,
        details={
            "tx_hash": record.transaction_hash,
            "block_height": record.block_height,
            "platform_url": record.platform_url,
        } if l2_status == "verified" else None,
    ))

    c2pa_record = svc.get_c2pa_record(record.work_id)
    if c2pa_record:
        manifest = c2pa_record.manifest_json
        is_valid = False
        if isinstance(manifest, dict):
            sig_hash = manifest.get("signature", {}).get("hash", "")
            has_assertions = len(manifest.get("assertions", [])) > 0
            is_valid = bool(sig_hash and has_assertions)
        evidence_chain.append(EvidenceChainItem(
            level="L3", type="C2PA 内容凭证",
            status="verified" if is_valid else "pending",
            details={"manifest_exists": True} if is_valid else {"manifest_exists": True, "incomplete": True},
        ))
    else:
        evidence_chain.append(EvidenceChainItem(
            level="L3", type="C2PA 内容凭证", status="not_started",
        ))

    ts_record = svc.get_timestamp_record(record.work_id)
    if ts_record and ts_record.status == "confirmed":
        evidence_chain.append(EvidenceChainItem(
            level="L4", type="RFC 3161 时间戳 (DigiCert TSA)", status="verified",
            details={"timestamp_path": ts_record.notes},
        ))
    else:
        evidence_chain.append(EvidenceChainItem(
            level="L4", type="RFC 3161 时间戳 (DigiCert TSA)", status="not_started",
        ))

    valid = l1_status == "verified" and l2_status == "verified"

    return ApiResponse(data=NotaryVerifyResponse(
        valid=valid,
        record_id=record.id,
        work_id=record.work_id,
        work_title=work.title or "",
        sha256=work.sha256 or "",
        platform=record.platform,
        confirmed_at=record.confirmed_at,
        evidence_chain=evidence_chain,
    ))


# ==============================================================================
# AIGC Trace Audit
# ==============================================================================

@router.post("/trace/audit/build", response_model=ApiResponse[dict])
def build_provenance_chain_endpoint(
    data: dict = None,
    db: Session = Depends(get_db),
    _auth=Depends(require_auth),
):
    """构建完整 AIGC 溯源链并持久化 (P0-05)."""
    from app.models.work import Work
    from app.services.aigc_trace_audit_hub import AIGCTraceAuditHub

    if not data:
        raise HTTPException(status_code=400, detail="请求体不能为空")

    work_id = data.get("work_id")
    if not work_id:
        raise HTTPException(status_code=400, detail="缺少 work_id")

    svc = NotaryManagerService(db)
    work = svc.get_trace_audit_work(work_id)
    if not work:
        raise HTTPException(status_code=404, detail="作品不存在")

    file_path = data.get("file_path") or work.file_path
    if not os.path.exists(file_path):
        raise HTTPException(status_code=400, detail=f"作品文件不存在: {file_path}")

    author_name = data.get("author_name", "OriStudio Creator")
    include_ai_sessions = data.get("include_ai_sessions", True)

    try:
        result = AIGCTraceAuditHub.build_provenance_chain(
            db=db,
            work_id=work_id,
            file_path=file_path,
            author_name=author_name,
            include_ai_sessions=include_ai_sessions,
        )
        return ApiResponse(message="溯源链构建成功", data=result)
    except Exception as e:
        logging.getLogger(__name__).exception("Failed to build provenance chain: %s", str(e))
        raise HTTPException(status_code=500, detail=f"溯源链构建失败: {str(e)}")


@router.get("/trace/audit/verify/{work_id}", response_model=ApiResponse[dict])
def verify_provenance_chain_endpoint(
    work_id: str,
    file_hash: Optional[str] = Query(None, description="可选的文件哈希用于重新验证"),
    db: Session = Depends(get_db),
):
    """验证作品的完整溯源链 (P0-05)."""
    from app.models.work import Work
    from app.services.aigc_trace_audit_hub import AIGCTraceAuditHub

    svc = NotaryManagerService(db)
    work = svc.get_trace_audit_work(work_id)
    if not work:
        raise HTTPException(status_code=404, detail="作品不存在")

    try:
        result = AIGCTraceAuditHub.verify_provenance_chain(
            db=db,
            work_id=work_id,
            file_hash=file_hash,
        )
        return ApiResponse(
            message="溯源链验证完成" if result["verified"] else "溯源链验证未通过",
            data=result,
        )
    except Exception as e:
        logging.getLogger(__name__).exception("Failed to verify provenance chain: %s", str(e))
        raise HTTPException(status_code=500, detail=f"溯源链验证失败: {str(e)}")


@router.get("/trace/audit/status/{work_id}", response_model=ApiResponse[dict])
def get_trace_audit_status(
    work_id: str,
    db: Session = Depends(get_db),
):
    """获取作品的溯源审计状态摘要 (P0-05)."""
    from pathlib import Path
    svc = NotaryManagerService(db)

    c2pa_count = svc.get_c2pa_count(work_id)
    notary_count = svc.get_notary_record_count(work_id)
    sig_path = Path("data/certificates/signatures") / f"{work_id}.json"
    has_signature = sig_path.exists()

    return ApiResponse(
        data={
            "work_id": work_id,
            "has_c2pa_record": c2pa_count > 0,
            "c2pa_record_count": c2pa_count,
            "has_notary_record": notary_count > 0,
            "notary_record_count": notary_count,
            "has_local_signature": has_signature,
            "provenance_complete": c2pa_count > 0 and notary_count > 0 and has_signature,
        }
    )


# ==============================================================================
# Triple Authentication Pipeline
# ==============================================================================

@router.post("/trace/triple/authenticate", response_model=ApiResponse[dict])
def run_triple_authentication_endpoint(
    data: dict = None,
    db: Session = Depends(get_db),
    _auth=Depends(require_auth),
):
    """执行 C2PA/TSA/Blockchain 三重认证管线 (P0-06)."""
    from app.models.work import Work
    from app.services.triple_auth_pipeline import TripleAuthenticationPipeline

    if not data:
        raise HTTPException(status_code=400, detail="请求体不能为空")

    work_id = data.get("work_id")
    if not work_id:
        raise HTTPException(status_code=400, detail="缺少 work_id")

    svc = NotaryManagerService(db)
    work = svc.get_triple_auth_work(work_id)
    if not work:
        raise HTTPException(status_code=404, detail="作品不存在")

    file_path = data.get("file_path") or work.file_path
    if not os.path.exists(file_path):
        raise HTTPException(status_code=400, detail=f"作品文件不存在: {file_path}")

    blockchain_platform = data.get("blockchain_platform", "local_ecdsa")

    try:
        result = TripleAuthenticationPipeline.run_triple_authentication(
            db=db,
            work_id=work_id,
            file_path=file_path,
            author_name=data.get("author_name", "OriStudio Creator"),
            blockchain_platform=blockchain_platform,
        )
        return ApiResponse(
            message="三重认证成功" if result["overall_status"] == "authenticated" else "三重认证失败",
            data=result,
        )
    except NotImplementedError as e:
        raise HTTPException(status_code=501, detail=str(e))
    except Exception as e:
        logging.getLogger(__name__).exception("Triple authentication failed: %s", str(e))
        raise HTTPException(status_code=500, detail=f"三重认证失败: {str(e)}")


@router.get("/trace/triple/verify/{work_id}", response_model=ApiResponse[dict])
def verify_triple_authentication_endpoint(
    work_id: str,
    file_hash: Optional[str] = Query(None, description="可选的文件哈希用于重新验证"),
    db: Session = Depends(get_db),
):
    """验证作品的三重认证结果 (P0-06)."""
    from app.models.work import Work
    from app.services.triple_auth_pipeline import TripleAuthenticationPipeline

    svc = NotaryManagerService(db)
    work = svc.get_triple_auth_work(work_id)
    if not work:
        raise HTTPException(status_code=404, detail="作品不存在")

    try:
        result = TripleAuthenticationPipeline.verify_triple_authentication(
            db=db,
            work_id=work_id,
            file_hash=file_hash,
        )
        return ApiResponse(
            message="三重认证验证完成" if result["verified"] else "三重认证未完全通过",
            data=result,
        )
    except Exception as e:
        logging.getLogger(__name__).exception("Failed to verify triple auth: %s", str(e))
        raise HTTPException(status_code=500, detail=f"三重认证验证失败: {str(e)}")
