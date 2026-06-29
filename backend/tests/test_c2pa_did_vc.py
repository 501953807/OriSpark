"""P2.2 C2PA / DID / VC 服务单元测试."""

import json
import os
from pathlib import Path


class TestC2PAService:
    """P2.2.1: C2PA Manifest 服务测试."""

    def test_generate_c2pa_manifest(self):
        """测试生成 C2PA manifest."""
        from app.services.c2pa_service import generate_c2pa_manifest

        manifest = generate_c2pa_manifest(
            work_title="测试作品",
            author_name="Test Author",
            sha256_hash="a" * 64,
        )

        assert "claim_generator" in manifest
        assert "OriStudio" in manifest["claim_generator"]
        assert "assertions" in manifest
        assert len(manifest["assertions"]) >= 2

        # 检查 CreativeWork 断言
        cw_assertions = [a for a in manifest["assertions"] if a["label"] == "stds.schema-org.CreativeWork"]
        assert len(cw_assertions) == 1
        assert cw_assertions[0]["data"]["name"] == "测试作品"
        assert cw_assertions[0]["data"]["author"][0]["name"] == "Test Author"

        # 检查哈希断言
        hash_assertions = [a for a in manifest["assertions"] if a["label"] == "oristudio.hash"]
        assert len(hash_assertions) == 1
        assert hash_assertions[0]["data"]["hash"] == "a" * 64

        # 检查 ingredients 字段
        assert "ingredients" in manifest

        # 检查签名占位
        assert "signature" in manifest
        assert manifest["signature"]["alg"] == "es256"

    def test_generate_c2pa_manifest_with_file_data(self):
        """测试使用文件数据生成 manifest."""
        from app.services.c2pa_service import generate_c2pa_manifest

        file_data = b"Hello C2PA World!"
        manifest = generate_c2pa_manifest(
            work_title="File Test",
            file_data=file_data,
        )

        hash_assertions = [a for a in manifest["assertions"] if a["label"] == "oristudio.hash"]
        assert len(hash_assertions) == 1
        assert hash_assertions[0]["data"]["c2pa_hash"] != ""

    def test_sign_and_verify_c2pa_manifest(self):
        """测试 C2PA manifest 签名和验证."""
        from app.services.c2pa_service import (
            generate_c2pa_manifest, sign_c2pa_manifest, verify_c2pa_manifest,
        )
        from app.services.local_notary import generate_ecdsa_keypair

        private_pem, public_pem = generate_ecdsa_keypair()

        manifest = generate_c2pa_manifest(
            work_title="Sign Test",
            sha256_hash="b" * 64,
        )

        # 签名前验证应该失败 (无签名)
        assert verify_c2pa_manifest(manifest, public_pem) is False

        # 签名
        signed_manifest = sign_c2pa_manifest(manifest, private_pem)

        # 签名后验证应该成功
        assert verify_c2pa_manifest(signed_manifest, public_pem) is True

        # 使用错误公钥验证应该失败
        wrong_private, wrong_public = generate_ecdsa_keypair()
        assert verify_c2pa_manifest(signed_manifest, wrong_public) is False

    def test_generate_c2pa_with_identity(self):
        """测试完整的 C2PA 身份生成."""
        from app.services.c2pa_service import generate_c2pa_with_identity

        manifest, private_pem, public_pem = generate_c2pa_with_identity(
            work_title="Identity Test",
            sha256_hash="c" * 64,
        )

        assert manifest is not None
        assert private_pem.startswith("-----BEGIN PRIVATE KEY-----")
        assert public_pem.startswith("-----BEGIN PUBLIC KEY-----")
        assert manifest["signature"]["hash"] != ""

    def test_add_ingredient(self):
        """测试添加素材引用."""
        from app.services.c2pa_service import generate_c2pa_manifest, add_ingredient

        manifest = generate_c2pa_manifest(work_title="IR Test")
        assert len(manifest["ingredients"]) == 0

        manifest = add_ingredient(manifest, "素材A", "abc123")
        assert len(manifest["ingredients"]) == 1
        assert manifest["ingredients"][0]["title"] == "素材A"

        manifest = add_ingredient(manifest, "素材B", "def456", relationship="derivedFrom")
        assert len(manifest["ingredients"]) == 2
        assert manifest["ingredients"][1]["relationship"] == "derivedFrom"

    def test_compute_c2pa_hash(self):
        """测试 C2PA 哈希计算."""
        from app.services.c2pa_service import compute_c2pa_hash

        h = compute_c2pa_hash(b"test data")
        assert isinstance(h, str)
        assert len(h) > 0


class TestDIDService:
    """P2.2.2: DID 服务测试."""

    def test_generate_did(self):
        """测试生成 did:key."""
        from app.services.local_notary import generate_ecdsa_keypair
        from app.services.did_service import generate_did

        _, public_pem = generate_ecdsa_keypair()
        did = generate_did(public_pem)

        assert did.startswith("did:key:z")
        assert len(did) > 20

    def test_create_did_document(self):
        """测试创建 DID Document."""
        from app.services.local_notary import generate_ecdsa_keypair
        from app.services.did_service import generate_did, create_did_document

        _, public_pem = generate_ecdsa_keypair()
        did = generate_did(public_pem)
        doc = create_did_document(did, public_pem)

        assert "@context" in doc
        assert doc["id"] == did
        assert "verificationMethod" in doc
        assert len(doc["verificationMethod"]) == 1
        assert doc["verificationMethod"][0]["type"] == "JsonWebKey2020"
        assert "authentication" in doc
        assert "assertionMethod" in doc

    def test_resolve_did_valid(self):
        """测试解析有效的 DID."""
        from app.services.local_notary import generate_ecdsa_keypair
        from app.services.did_service import generate_did, resolve_did

        _, public_pem = generate_ecdsa_keypair()
        did = generate_did(public_pem)
        doc = resolve_did(did)

        assert doc is not None
        assert doc["id"] == did
        assert "@context" in doc

    def test_resolve_did_invalid(self):
        """测试解析无效的 DID."""
        from app.services.did_service import resolve_did

        assert resolve_did("invalid") is None
        assert resolve_did("did:xxx:abc") is None
        assert resolve_did("did:key:") is None
        assert resolve_did("did:key:!!!invalid_base58!!!") is None

    def test_did_deterministic(self):
        """测试相同公钥生成相同 DID."""
        from app.services.local_notary import generate_ecdsa_keypair
        from app.services.did_service import generate_did

        _, public_pem = generate_ecdsa_keypair()
        did1 = generate_did(public_pem)
        did2 = generate_did(public_pem)

        assert did1 == did2

    def test_did_includes_curve(self):
        """测试不同的曲线生成不同前缀的 DID."""
        from cryptography.hazmat.primitives.asymmetric import ec
        from app.services.did_service import generate_did

        # P-384
        private_key = ec.generate_private_key(ec.SECP384R1())
        public_key = private_key.public_key()
        from cryptography.hazmat.primitives import serialization
        public_pem = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        ).decode("utf-8")

        did = generate_did(public_pem)
        assert did.startswith("did:key:z")


class TestVCService:
    """P2.2.3: Verifiable Credential 服务测试."""

    def test_create_work_credential(self):
        """测试创建作品 VC."""
        from app.services.local_notary import sign_work, generate_ecdsa_keypair
        from app.services.did_service import generate_did
        from app.services.vc_service import create_work_credential

        work = {
            "id": "test_work_001",
            "title": "测试作品",
            "sha256": "d" * 64,
            "file_type": "image",
            "created_at": "2025-01-01T00:00:00Z",
        }

        sig_data = sign_work(work["sha256"])
        private_pem, public_pem = generate_ecdsa_keypair()
        did = generate_did(public_pem)

        credential = create_work_credential(work, did, sig_data, private_pem)

        assert "@context" in credential
        assert "VerifiableCredential" in credential["type"]
        assert "WorkCredential" in credential["type"]
        assert credential["issuer"]["id"] == did
        assert "credentialSubject" in credential
        assert credential["credentialSubject"]["work"]["title"] == "测试作品"
        assert credential["credentialSubject"]["work"]["sha256"] == "d" * 64
        assert "proof" in credential

    def test_verify_valid_credential(self):
        """测试验证有效的 VC."""
        from app.services.local_notary import sign_work, generate_ecdsa_keypair
        from app.services.did_service import generate_did
        from app.services.vc_service import create_work_credential, verify_credential

        work = {
            "id": "test_work_002",
            "title": "验证测试",
            "sha256": "e" * 64,
            "file_type": "image",
            "created_at": "2025-01-01T00:00:00Z",
        }

        sig_data = sign_work(work["sha256"])
        private_pem, public_pem = generate_ecdsa_keypair()
        did = generate_did(public_pem)

        credential = create_work_credential(work, did, sig_data, private_pem)
        result = verify_credential(credential)

        assert result["valid"] is True
        assert len(result["errors"]) == 0
        assert len(result["checks"]) > 0

    def test_verify_invalid_credential(self):
        """测试验证无效的 VC."""
        from app.services.vc_service import verify_credential

        result = verify_credential({})
        assert result["valid"] is False
        assert len(result["errors"]) > 0

    def test_verify_unsigned_credential(self):
        """测试验证未签名的 VC."""
        from app.services.local_notary import sign_work
        from app.services.did_service import generate_did
        from app.services.local_notary import generate_ecdsa_keypair
        from app.services.vc_service import create_work_credential, verify_credential

        work = {
            "id": "test_work_003",
            "title": "未签名",
            "sha256": "f" * 64,
            "file_type": "audio",
            "created_at": "2025-01-01T00:00:00Z",
        }

        sig_data = sign_work(work["sha256"])
        _, public_pem = generate_ecdsa_keypair()
        did = generate_did(public_pem)

        # 不提供私钥，不签名
        credential = create_work_credential(work, did, sig_data, private_key_pem=None)
        result = verify_credential(credential)

        # 无 proof 应该有效但缺少 proof
        assert result["valid"] is False
        errors_text = " ".join(result["errors"])
        assert "proof" in errors_text.lower()

    def test_create_work_credential_full(self):
        """测试完整 VC 生成流程."""
        from app.services.local_notary import sign_work, generate_ecdsa_keypair
        from app.services.vc_service import create_work_credential_full

        work = {
            "id": "test_work_004",
            "title": "完整流程",
            "sha256": "a" * 64,
            "file_type": "video",
            "created_at": "2025-06-01T10:00:00Z",
        }

        sig_data = sign_work(work["sha256"])
        private_pem, public_pem = generate_ecdsa_keypair()

        result = create_work_credential_full(work, public_pem, private_pem, sig_data)

        assert "did" in result
        assert result["did"].startswith("did:key:z")
        assert "did_document" in result
        assert "credential" in result
        assert result["credential"]["issuer"]["id"] == result["did"]


class TestNotaryC2PAEndpoints:
    """P2.2.4: C2PA API 端点测试."""

    def test_generate_and_verify_c2pa(self, client):
        """测试 C2PA 完整流程: 生成 -> 验证."""
        from PIL import Image
        import io

        # 上传作品
        img = Image.new("RGB", (100, 100), color=(100, 150, 200))
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        buf.seek(0)
        buf.name = "c2pa_test.png"

        work_resp = client.post(
            "/api/works",
            files={"file": ("c2pa_test.png", buf, "image/png")},
            data={"title": "C2PA 测试作品"},
        )
        assert work_resp.status_code == 200
        work_id = work_resp.json()["data"]["id"]

        # 生成 C2PA manifest
        gen_resp = client.post(f"/api/notary/c2pa/{work_id}/generate")
        assert gen_resp.status_code == 200
        gen_data = gen_resp.json()["data"]
        assert gen_data["work_id"] == work_id
        assert "manifest" in gen_data
        assert "assertions" in gen_data["manifest"]
        assert gen_data["manifest"]["signature"]["hash"] != ""

        # 验证 C2PA manifest
        verify_resp = client.get(f"/api/notary/verify/c2pa/{work_id}")
        assert verify_resp.status_code == 200
        verify_data = verify_resp.json()["data"]
        assert verify_data["status"] == "valid"
        assert verify_data["is_valid"] is True
        assert "manifest" in verify_data

    def test_verify_nonexistent_c2pa(self, client):
        """测试验证不存在 C2PA 的作品."""
        resp = client.get("/api/notary/verify/c2pa/nonexistent_work_id")
        assert resp.status_code == 404  # 作品不存在

    def test_generate_c2pa_nonexistent(self, client):
        """测试为不存在的作品生成 C2PA."""
        resp = client.post("/api/notary/c2pa/nonexistent_work_id/generate")
        assert resp.status_code == 404


class TestNotaryDIDEndpoints:
    """P2.2.2: DID API 端点测试."""

    def test_generate_did(self, client):
        """测试生成 DID."""
        resp = client.post("/api/notary/did/generate")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["did"].startswith("did:key:z")
        assert "did_document" in data
        assert data["did_document"]["id"] == data["did"]
        assert "verificationMethod" in data["did_document"]
        assert data["public_key_pem"].startswith("-----BEGIN PUBLIC KEY-----")

    def test_resolve_did(self, client):
        """测试解析 DID."""
        # 先生成一个 DID
        gen_resp = client.post("/api/notary/did/generate")
        did = gen_resp.json()["data"]["did"]

        # 解析它
        resolve_resp = client.get(f"/api/notary/did/resolve?did={did}")
        assert resolve_resp.status_code == 200
        data = resolve_resp.json()["data"]
        assert data["did"] == did
        assert "did_document" in data

    def test_resolve_invalid_did(self, client):
        """测试解析无效 DID."""
        resp = client.get("/api/notary/did/resolve?did=invalid:did")
        assert resp.status_code == 400


class TestNotaryVCEndpoints:
    """P2.2.3: VC API 端点测试."""

    def test_generate_vc(self, client):
        """测试生成 VC."""
        from PIL import Image
        import io

        # 上传作品
        img = Image.new("RGB", (100, 100), color=(255, 200, 100))
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        buf.seek(0)
        buf.name = "vc_test.png"

        work_resp = client.post(
            "/api/works",
            files={"file": ("vc_test.png", buf, "image/png")},
            data={"title": "VC 测试作品"},
        )
        assert work_resp.status_code == 200
        work_id = work_resp.json()["data"]["id"]

        # 生成 VC
        vc_resp = client.post(f"/api/notary/vc/{work_id}/generate")
        assert vc_resp.status_code == 200
        vc_data = vc_resp.json()["data"]
        assert vc_data["work_id"] == work_id
        assert vc_data["did"].startswith("did:key:z")
        assert "credential" in vc_data
        assert "VerifiableCredential" in vc_data["credential"]["type"]
        assert "proof" in vc_data["credential"]

    def test_verify_vc(self, client):
        """测试验证 VC."""
        # 生成一个 VC
        from PIL import Image
        import io

        img = Image.new("RGB", (100, 100), color=(100, 255, 100))
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        buf.seek(0)
        buf.name = "vc_verify_test.png"

        work_resp = client.post(
            "/api/works",
            files={"file": ("vc_verify_test.png", buf, "image/png")},
            data={"title": "VC 验证测试"},
        )
        work_id = work_resp.json()["data"]["id"]

        vc_resp = client.post(f"/api/notary/vc/{work_id}/generate")
        credential = vc_resp.json()["data"]["credential"]

        # 调用验证 endpoint
        verify_resp = client.post("/api/notary/vc/verify", json=credential)
        assert verify_resp.status_code == 200
        result = verify_resp.json()["data"]
        assert result["valid"] is True
        assert len(result["errors"]) == 0

    def test_verify_invalid_vc(self, client):
        """测试验证无效 VC."""
        resp = client.post("/api/notary/vc/verify", json={"invalid": True})
        assert resp.status_code == 200
        result = resp.json()["data"]
        assert result["valid"] is False
        assert len(result["errors"]) > 0
