"""作品管理 API 测试."""

import io
import os
import tempfile
import random


def test_health_check(client):
    """测试健康检查."""
    resp = client.get("/api/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert data["app"] == "OriStudio"


def test_list_works_empty(client):
    """测试空作品列表."""
    resp = client.get("/api/works")
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert data["data"]["total"] >= 0


def _upload_unique_image(client, filename, title, size=(100, 100)):
    """Helper: upload a unique image to avoid SHA-256 dedup."""
    from PIL import Image
    r, g, b = random.randint(1, 254), random.randint(1, 254), random.randint(1, 254)
    img = Image.new("RGB", size, color=(r, g, b))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    buf.name = filename
    return client.post(
        "/api/works",
        files={"file": (filename, buf, "image/png")},
        data={"title": title, "tags": "测试, 插画"},
    )


def test_upload_and_get_work(client):
    """测试上传作品并获取详情."""
    resp = _upload_unique_image(client, "test_upload.png", "测试作品", (150, 150))
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    work = data["data"]
    assert work["title"] == "测试作品"
    assert work["file_type"] == "image"
    assert work["file_extension"] == "png"
    assert work["sha256"] is not None
    assert len(work["tags"]) >= 2

    detail_resp = client.get(f"/api/works/{work['id']}")
    assert detail_resp.status_code == 200
    assert detail_resp.json()["data"]["title"] == "测试作品"


def test_update_work(client):
    """测试更新作品信息."""
    resp = _upload_unique_image(client, "test_update.png", "原始标题", (102, 102))
    assert resp.status_code == 200
    work_id = resp.json()["data"]["id"]

    resp = client.patch(f"/api/works/{work_id}", json={"title": "新标题", "tags": ["新标签"]})
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["title"] == "新标题"
    assert len(data["tags"]) == 1
    assert data["tags"][0]["tag"] == "新标签"


def test_delete_work(client):
    """测试软删除."""
    resp = _upload_unique_image(client, "test_delete.png", "待删除", (103, 103))
    assert resp.status_code == 200
    work_id = resp.json()["data"]["id"]

    resp = client.delete(f"/api/works/{work_id}")
    assert resp.status_code == 200

    detail_resp = client.get(f"/api/works/{work_id}")
    assert detail_resp.json()["data"]["status"] == "trashed"


def test_search_works(client):
    """测试作品搜索和筛选."""
    created = []
    for i in range(3):
        resp = _upload_unique_image(
            client, f"search_{i}.png", f"搜索测试{i}", (101 + i, 101 + i)
        )
        if resp.status_code == 200:
            created.append(resp.json()["data"])

    assert len(created) >= 3, f"Only created {len(created)} works"

    # FTS5/LIKE search
    resp = client.get("/api/works", params={"search": "搜索测试"})
    assert resp.status_code == 200
    assert resp.json()["data"]["total"] >= 1

    # Type filter
    resp = client.get("/api/works", params={"file_type": "image"})
    assert resp.json()["data"]["total"] >= 1

    # Status filter
    resp = client.get("/api/works", params={"status": "active"})
    assert resp.status_code == 200


# ==================== P1.1.2: Hash-only upload ====================

def test_hash_only_upload(client):
    """测试 hash-only 上传."""
    import hashlib
    sha = hashlib.sha256(b"test hash only data").hexdigest()
    resp = client.post("/api/works/hash-only", json={
        "sha256": sha,
        "file_name": "hash_test.png",
        "file_size": 2048,
        "file_type": "image",
        "file_extension": "png",
        "title": "哈希注册作品",
        "description": "仅哈希注册",
        "tags": ["哈希", "注册"],
    })
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["sha256"] == sha
    assert data["import_mode"] == "hash_only"
    assert data["file_url"] is None  # no file stored

    # Duplicate should 409
    resp2 = client.post("/api/works/hash-only", json={
        "sha256": sha,
        "file_name": "hash_test2.png",
        "file_size": 1024,
    })
    assert resp2.status_code == 409


# ==================== P1.1.3: Lowres upload ====================

def test_lowres_upload(client):
    """测试 lowres 上传."""
    import io
    import hashlib
    from PIL import Image

    sha = hashlib.sha256(b"lowres test data").hexdigest()
    thumb = Image.new("RGB", (64, 64), color=(100, 200, 50))
    buf = io.BytesIO()
    thumb.save(buf, format="JPEG")
    buf.seek(0)
    buf.name = "thumb.jpg"

    resp = client.post(
        "/api/works/lowres",
        files={"thumbnail": ("thumb.jpg", buf, "image/jpeg")},
        data={
            "sha256": sha,
            "file_name": "original_hd.png",
            "file_size": 5000000,
            "file_type": "image",
            "file_extension": "png",
            "title": "低分辨率注册",
            "tags": "测试,lowres",
            "width": 4000,
            "height": 3000,
        },
    )
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["import_mode"] == "lowres"
    assert data["sha256"] == sha
    assert data["width"] == 4000
    assert data["height"] == 3000
    assert data["thumbnail_url"] is not None


# ==================== P1.1.5: File replace ====================

def test_replace_work_file(client):
    """测试文件替换 + 自动版本快照."""
    import io
    from PIL import Image

    # Upload original
    resp = _upload_unique_image(client, "original.png", "原始文件", (100, 100))
    assert resp.status_code == 200
    work = resp.json()["data"]
    work_id = work["id"]
    old_sha = work["sha256"]

    # Replace file
    img = Image.new("RGB", (200, 200), color=(255, 128, 0))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    buf.name = "replaced.png"

    resp2 = client.post(
        f"/api/works/{work_id}/replace",
        files={"file": ("replaced.png", buf, "image/png")},
        data={"notes": "替换测试"},
    )
    assert resp2.status_code == 200
    new_work = resp2.json()["data"]
    assert new_work["sha256"] != old_sha
    assert new_work["file_name"] == "replaced.png"
    assert new_work["import_mode"] == "full"

    # Verify version snapshot created
    vers_resp = client.get(f"/api/works/{work_id}/versions")
    assert vers_resp.status_code == 200
    versions = vers_resp.json()["data"]
    assert len(versions) >= 1
    assert versions[0]["file_hash"] == old_sha


# ==================== P1.1.6: Fork ====================

def test_fork_work(client):
    """测试作品 Fork."""
    resp = _upload_unique_image(client, "source.png", "源作品", (100, 100))
    assert resp.status_code == 200
    work = resp.json()["data"]
    work_id = work["id"]

    fork_resp = client.post(f"/api/works/{work_id}/fork")
    assert fork_resp.status_code == 200
    fork = fork_resp.json()["data"]
    assert "Fork" in fork["title"]
    assert fork["parent_work_id"] == work_id
    assert fork["sha256"] == work["sha256"]
    assert fork["file_type"] == work["file_type"]

    # Verify original has fork relationship
    detail_resp = client.get(f"/api/works/{work_id}")
    assert detail_resp.status_code == 200

    # Fork of non-existent
    bad_resp = client.post("/api/works/nonexistent_id/fork")
    assert bad_resp.status_code == 404


# ==================== P1.1.8: Rights management ====================

def test_update_work_rights(client):
    """测试版权信息更新."""
    resp = _upload_unique_image(client, "rights_test.png", "版权测试", (100, 100))
    assert resp.status_code == 200
    work_id = resp.json()["data"]["id"]

    rights_data = {
        "rights": {"holder": "张三", "year": "2025", "rights_type": "all_rights_reserved"},
        "license_type": "cc-by-nc",
    }
    patch_resp = client.patch(f"/api/works/{work_id}/rights", json=rights_data)
    assert patch_resp.status_code == 200
    updated = patch_resp.json()["data"]
    assert updated["rights"]["holder"] == "张三"
    assert updated["license_type"] == "cc-by-nc"

    # Partial update
    part_resp = client.patch(f"/api/works/{work_id}/rights", json={"license_type": "cc-by"})
    assert part_resp.status_code == 200
    part = part_resp.json()["data"]
    assert part["license_type"] == "cc-by"
    assert part["rights"]["holder"] == "张三"  # unchanged

    # 404
    bad_resp = client.patch("/api/works/nonexistent/rights", json=rights_data)
    assert bad_resp.status_code == 404


# ==================== P1.1.9: Rights declaration PDF ====================

def test_generate_rights_declaration(client):
    """测试生成版权声明 PDF."""
    resp = _upload_unique_image(client, "declaration_test.png", "声明测试", (100, 100))
    assert resp.status_code == 200
    work_id = resp.json()["data"]["id"]

    # Set rights first
    client.patch(f"/api/works/{work_id}/rights", json={
        "rights": {"holder": "测试作者", "year": "2026"},
        "license_type": "cc-by-sa",
    })

    pdf_resp = client.post(f"/api/works/{work_id}/rights-declaration")
    assert pdf_resp.status_code == 200
    data = pdf_resp.json()["data"]
    assert "pdf_url" in data
    assert data["pdf_url"].startswith("/api/files/")

    # Verify the file exists
    from pathlib import Path
    pdf_path = Path("data/certificates") / f"rights_declaration_{work_id}.pdf"
    assert pdf_path.exists()
    assert pdf_path.stat().st_size > 0

    # 404 on bad work_id
    bad_resp = client.post("/api/works/nonexistent/rights-declaration")
    assert bad_resp.status_code == 404


# ==================== P1.1.19: AI tag suggestion ====================

def test_suggest_tags_ai_rule_fallback(client):
    """测试 AI 标签推荐 (规则回退，Ollama 不可用时)."""
    resp = client.post("/api/tags/suggest-ai", json={
        "file_name": "cyberpunk_city.jpg",
        "file_type": "image",
        "description": "赛博朋克风格城市夜景",
    })
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert "tags" in data
    assert "source" in data
    # Should have rule-based tags
    tags = data["tags"]
    assert any("赛博朋克" in t for t in tags) or any("图片" in t for t in tags) or any("JPEG" in t for t in tags)
    assert data["source"] in ("rule", "rule+ai")  # Ollama may or may not be running

    # Test with no file
    resp2 = client.post("/api/tags/suggest-ai", json={
        "file_name": "",
        "file_type": "audio",
        "description": "",
    })
    assert resp2.status_code == 200
    data2 = resp2.json()["data"]
    assert "音频" in data2["tags"]
    assert data2["source"] in ("rule", "rule+ai")


def test_suggest_tags_ai_with_exif(client):
    """测试 AI 标签推荐 (含 EXIF 数据)."""
    resp = client.post("/api/tags/suggest-ai", json={
        "file_name": "DSC_0001.jpg",
        "file_type": "image",
        "exif_data": {"Model": "Nikon D850"},
    })
    assert resp.status_code == 200
    tags = resp.json()["data"]["tags"]
    assert "相机拍摄" in tags


def test_suggest_tags_ai_style_detection(client):
    """测试 AI 标签推荐的风格检测."""
    resp = client.post("/api/tags/suggest-ai", json={
        "file_name": "kawaii_cat_sticker.png",
        "file_type": "image",
        "description": "可爱的猫咪贴纸",
    })
    assert resp.status_code == 200
    tags = resp.json()["data"]["tags"]
    assert any("可爱" in t for t in tags)
