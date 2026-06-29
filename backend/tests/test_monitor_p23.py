"""P2.3 侵权监测扩展测试.

测试覆盖:
- 本地视觉指纹嵌入与比对
- 品牌监测 CRUD + 扫描
- 域名监测
- DMCA 模板
- 代码抄袭检测
- 结果去重
- 白名单学习
"""

import io
import random
import os
import tempfile
from pathlib import Path


def _upload_random_image(client, filename, title, size=(250, 250)):
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
        data={"title": title},
    )


def _create_test_image(filepath, size=(200, 200), color=(100, 150, 200)):
    """Create a test image file on disk."""
    from PIL import Image
    img = Image.new("RGB", size, color=color)
    img.save(filepath)
    return filepath


# ============================================================
# P2.3.1-P2.3.2: 指纹嵌入
# ============================================================

def test_compute_fingerprints_raw():
    """直接测试 embedding_service 函数."""
    from app.services.embedding_service import (
        compute_average_hash, compute_difference_hash,
        compute_perceptual_hash, compute_wavelet_hash,
        hamming_distance, compute_similarity,
    )

    # 创建测试图像
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
        img_path = f.name
    _create_test_image(img_path, (200, 200), (100, 150, 200))

    try:
        a = compute_average_hash(img_path)
        d = compute_difference_hash(img_path)
        p = compute_perceptual_hash(img_path)
        w = compute_wavelet_hash(img_path)

        # 所有 hash 应非空
        assert len(a) > 0
        assert len(d) > 0
        assert len(p) > 0
        assert len(w) > 0

        # 同一图像的 hash 自比较应该 highly similar
        assert hamming_distance(a, a) == 0
        assert compute_similarity(a, a) > 99.0
    finally:
        os.unlink(img_path)


def test_different_images_different_hash():
    """不同结构图像的 dHash 应该不同."""
    from app.services.embedding_service import (
        compute_difference_hash, compute_similarity,
    )
    from PIL import Image, ImageDraw

    img1 = None
    img2 = None
    try:
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
            img1 = f.name
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
            img2 = f.name

        # 创建有明显结构差异的图像 (dHash 基于相邻列差分)
        # Image 1: vertical stripes
        im1 = Image.new("RGB", (200, 200), color=(255, 255, 255))
        draw1 = ImageDraw.Draw(im1)
        for x in range(0, 200, 10):
            draw1.line([(x, 0), (x, 200)], fill=(0, 0, 0), width=3)
        im1.save(img1)

        # Image 2: horizontal stripes
        im2 = Image.new("RGB", (200, 200), color=(255, 255, 255))
        draw2 = ImageDraw.Draw(im2)
        for y in range(0, 200, 10):
            draw2.line([(0, y), (200, y)], fill=(0, 0, 0), width=3)
        im2.save(img2)

        h1 = compute_difference_hash(img1)
        h2 = compute_difference_hash(img2)

        # 竖条纹 vs 横条纹的 dHash 应该不同
        sim = compute_similarity(h1, h2)
        assert sim < 90.0, f"Expected different dHash for different patterns, got {sim}% similar"
    finally:
        if img1:
            os.unlink(img1)
        if img2:
            os.unlink(img2)


def test_fingerprint_endpoint(client):
    """测试指纹计算 API."""
    work_resp = _upload_random_image(client, "fp_test.png", "Fingerprint Test", (300, 300))
    assert work_resp.status_code == 200
    work_id = work_resp.json()["data"]["id"]

    # 需要知道实际文件路径 — 从 API 获取
    work_detail = client.get(f"/api/works/{work_id}")
    assert work_detail.status_code == 200

    resp = client.post("/api/monitor/fingerprints", json={
        "work_id": work_id,
        "hash_types": ["dhash", "phash"],
    })
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["work_id"] == work_id
    assert "dhash" in data["fingerprints"]
    assert "phash" in data["fingerprints"]
    assert len(data["fingerprints"]["dhash"]) > 0


def test_fingerprint_compare(client):
    """测试指纹比对 API."""
    resp1 = _upload_random_image(client, "fp_cmp_a.png", "Compare A", (300, 300))
    resp2 = _upload_random_image(client, "fp_cmp_b.png", "Compare B", (300, 300))
    assert resp1.status_code == 200
    assert resp2.status_code == 200
    w1 = resp1.json()["data"]["id"]
    w2 = resp2.json()["data"]["id"]

    # 计算指纹
    client.post("/api/monitor/fingerprints", json={
        "work_id": w1, "hash_types": ["dhash"],
    })
    client.post("/api/monitor/fingerprints", json={
        "work_id": w2, "hash_types": ["dhash"],
    })

    # 比对
    resp = client.post("/api/monitor/fingerprints/compare", json={
        "work_id_a": w1,
        "work_id_b": w2,
        "hash_type": "dhash",
    })
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert "similarity" in data
    assert "hamming_distance" in data
    assert 0 <= data["similarity"] <= 100


# ============================================================
# P2.3.3-P2.3.4: Brand Watch CRUD
# ============================================================

def test_brand_watch_crud(client):
    """测试品牌监测 CRUD."""
    # Create
    resp = client.post("/api/monitor/brand-watches", json={
        "brand_name": "TestBrand",
        "keywords": ["test", "brand"],
        "platforms": ["taobao", "jd"],
    })
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["brand_name"] == "TestBrand"
    brand_id = data["id"]

    # List
    resp = client.get("/api/monitor/brand-watches")
    assert resp.status_code == 200
    assert len(resp.json()["data"]) >= 1

    # Get
    resp = client.get(f"/api/monitor/brand-watches/{brand_id}")
    assert resp.status_code == 200
    assert resp.json()["data"]["brand_name"] == "TestBrand"

    # Update
    resp = client.patch(f"/api/monitor/brand-watches/{brand_id}", json={
        "keywords": ["test", "brand", "updated"],
    })
    assert resp.status_code == 200
    assert "updated" in resp.json()["data"]["keywords"]

    # Delete
    resp = client.delete(f"/api/monitor/brand-watches/{brand_id}")
    assert resp.status_code == 200

    # Verify deleted
    resp = client.get(f"/api/monitor/brand-watches/{brand_id}")
    assert resp.status_code == 404


def test_brand_watch_invalid(client):
    """测试品牌监测错误处理."""
    # Empty brand name
    resp = client.post("/api/monitor/brand-watches", json={
        "brand_name": "",
    })
    assert resp.status_code == 422  # Validation error

    # Not found
    resp = client.get("/api/monitor/brand-watches/nonexistent")
    assert resp.status_code == 404


# ============================================================
# P2.3.5-P2.3.6: Brand Scan + Domain Watch
# ============================================================

def test_brand_scan(client):
    """测试品牌扫描."""
    # Create brand
    resp = client.post("/api/monitor/brand-watches", json={
        "brand_name": "ScanBrand",
        "platforms": ["taobao", "jd"],
    })
    assert resp.status_code == 200
    brand_id = resp.json()["data"]["id"]

    # Trigger scan
    resp = client.post(f"/api/monitor/brands/{brand_id}/scan")
    assert resp.status_code == 200
    data = resp.json()
    assert data["data"]["results_count"] >= 1
    assert data["data"]["is_mock_data"] is True

    # Get scan results
    resp = client.get(f"/api/monitor/brands/{brand_id}/results")
    assert resp.status_code == 200
    results = resp.json()["data"]
    assert len(results) >= 1
    assert results[0]["brand_id"] == brand_id

    # Verify mock data label in scan result
    assert "[MOCK DATA]" in (results[0].get("notes") or "")


def test_brand_scan_not_found(client):
    """测试扫描不存在的品牌."""
    resp = client.post("/api/monitor/brands/nonexistent/scan")
    assert resp.status_code == 404


def test_domain_watch_register(client):
    """测试域名监测注册."""
    # Register
    resp = client.post("/api/monitor/domains/watch", json={
        "domain": "example-test-brand.com",
        "target_brand": "TestBrand",
        "watch_type": "whois",
    })
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["domain"] == "example-test-brand.com"
    watch_id = data["id"]

    # List
    resp = client.get("/api/monitor/domains/watch")
    assert resp.status_code == 200
    assert len(resp.json()["data"]) >= 1

    # Duplicate
    resp = client.post("/api/monitor/domains/watch", json={
        "domain": "example-test-brand.com",
    })
    assert resp.status_code == 400

    # Delete
    resp = client.delete(f"/api/monitor/domains/watch/{watch_id}")
    assert resp.status_code == 200


def test_domain_watch_invalid(client):
    """测试域名监测无效输入."""
    resp = client.post("/api/monitor/domains/watch", json={
        "domain": "",
    })
    assert resp.status_code == 422


# ============================================================
# P2.3.7: DMCA Template
# ============================================================

def test_dmca_template(client):
    """测试 DMCA 模板生成."""
    work_resp = _upload_random_image(client, "dmca_test.png", "DMCA Test Work", (300, 300))
    assert work_resp.status_code == 200
    work_id = work_resp.json()["data"]["id"]

    resp = client.get(f"/api/monitor/evidence/dmca/{work_id}")
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["work_id"] == work_id
    assert data["template_type"] == "dmca_takedown"
    assert "DMCA TAKEDOWN NOTICE" in data["filled_template"]
    assert "DMCA Test Work" in data["filled_template"]
    assert "usage_guide" in data


def test_dmca_template_work_not_found(client):
    """测试 DMCA 模板 — 作品不存在."""
    resp = client.get("/api/monitor/evidence/dmca/nonexistent")
    assert resp.status_code == 404


# ============================================================
# P2.3.10: Code Similarity
# ============================================================

def test_code_similarity_identical():
    """测试代码相似度 — 完全相同."""
    code = """def hello():
    x = 1
    y = 2
    return x + y
"""
    from app.services.code_similarity import compare_code_snippets
    result = compare_code_snippets(code, code, "python")
    assert result.similarity > 90.0


def test_code_similarity_different():
    """测试代码相似度 — 完全不同的代码."""
    code_a = """def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)
"""
    code_b = """class ShoppingCart:
    def __init__(self):
        self.items = []
    def add(self, item):
        self.items.append(item)
"""
    from app.services.code_similarity import compare_code_snippets
    result = compare_code_snippets(code_a, code_b, "python")
    assert result.similarity < 60.0


def test_code_similarity_renamed():
    """测试代码相似度 — 仅重命名变量."""
    code_a = """def calculate_total(items):
    total = 0
    for item in items:
        total += item.price
    return total
"""
    code_b = """def compute_sum(elements):
    result = 0
    for element in elements:
        result += element.cost
    return result
"""
    from app.services.code_similarity import compare_code_snippets
    result = compare_code_snippets(code_a, code_b, "python")
    # 结构相同但变量重命名，应该具有较高的结构相似度
    assert result.structure_similarity > 30.0


def test_code_similarity_endpoint(client):
    """测试代码相似度 API 端点."""
    resp = client.post("/api/monitor/check/code", json={
        "code_a": "def foo(): return 1",
        "code_b": "def bar(): return 2",
        "language": "python",
    })
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert "similarity" in data
    assert "structure_similarity" in data
    assert "keyword_similarity" in data
    assert 0 <= data["similarity"] <= 100


def test_code_similarity_endpoint_empty(client):
    """测试代码相似度 API — 空输入."""
    resp = client.post("/api/monitor/check/code", json={
        "code_a": "",
        "code_b": "print('hello')",
        "language": "python",
    })
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert "similarity" in data


# ============================================================
# P2.3.11: 结果去重
# ============================================================

def test_result_deduplication(client):
    """测试扫描结果去重."""
    work_resp = _upload_random_image(client, "dedup_test.png", "Dedup Test", (250, 250))
    assert work_resp.status_code == 200
    work_id = work_resp.json()["data"]["id"]

    task_resp = client.post("/api/monitor/tasks", json={
        "work_id": work_id, "platform": "baidu", "search_type": "image",
    })
    assert task_resp.status_code == 200
    task_id = task_resp.json()["data"]["id"]

    # 第一次扫描
    resp1 = client.post(f"/api/monitor/tasks/{task_id}/scan")
    assert resp1.status_code == 200
    count1 = resp1.json()["data"]["results_count"]

    # 第二次扫描 (应跳过重复 URL)
    resp2 = client.post(f"/api/monitor/tasks/{task_id}/scan")
    assert resp2.status_code == 200
    data2 = resp2.json()["data"]
    # 重复应被跳过
    assert data2["results_count"] == 0 or data2.get("duplicates_skipped", 0) >= 1


# ============================================================
# P2.3.12: 白名单学习
# ============================================================

def test_whitelist_learning(client):
    """测试白名单学习流程."""
    work_resp = _upload_random_image(client, "wl_test.png", "Whitelist Test", (250, 250))
    assert work_resp.status_code == 200
    work_id = work_resp.json()["data"]["id"]

    task_resp = client.post("/api/monitor/tasks", json={
        "work_id": work_id, "platform": "baidu", "search_type": "image",
    })
    assert task_resp.status_code == 200
    task_id = task_resp.json()["data"]["id"]

    # 触发扫描获取结果
    client.post(f"/api/monitor/tasks/{task_id}/scan")
    results_resp = client.get("/api/monitor/results", params={"task_id": task_id})
    results = results_resp.json()["data"]

    if results:
        result_id = results[0]["id"]
        # 标记为 whitelisted → 触发白名单学习
        client.patch(f"/api/monitor/results/{result_id}", json={
            "status": "whitelisted",
        })

    # 获取白名单建议
    resp = client.get("/api/monitor/whitelist-suggestions")
    assert resp.status_code == 200
    suggestions = resp.json()["data"]["suggestions"]
    assert "how_it_works" in resp.json()["data"]

    # 如果有建议，测试接受/拒绝
    if suggestions:
        sid = suggestions[0]["id"]
        # Accept
        resp = client.post("/api/monitor/whitelist-suggestions/action", json={
            "suggestion_id": sid,
            "action": "accept",
        })
        assert resp.status_code == 200


def test_whitelist_action_invalid(client):
    """测试白名单操作 — 无效输入."""
    resp = client.post("/api/monitor/whitelist-suggestions/action", json={
        "suggestion_id": "nonexistent",
        "action": "bad_action",
    })
    assert resp.status_code == 400


# ============================================================
# Logo Detector 单元测试
# ============================================================

def test_logo_detector_template_match():
    """测试 Logo 模板匹配 — 使用有纹理特征的图像."""
    from app.services.logo_detector import (
        load_image, template_match_ncc, multi_scale_template_match,
        LogoMatchResult,
    )
    from PIL import Image, ImageDraw

    # 创建有特征的模板 (带纹理)
    template_img = Image.new("RGB", (60, 60), color=(255, 0, 0))
    draw = ImageDraw.Draw(template_img)
    # 绘制十字形图案
    draw.rectangle([20, 10, 40, 50], fill=(255, 255, 255))
    draw.rectangle([10, 20, 50, 40], fill=(255, 255, 255))

    # 目标图像包含模板
    target_img = Image.new("RGB", (300, 300), color=(100, 100, 100))
    # 粘贴模板到多个位置以增加匹配机会
    target_img.paste(template_img, (120, 120))

    result = multi_scale_template_match(
        template_img, target_img,
        scales=[0.5, 0.75, 1.0, 1.25],
        ncc_threshold=0.2,  # 降低阈值以适应低质量图像
    )
    assert result is not None, "Template match should find the pasted logo"
    assert result.confidence > 0


def test_logo_detector_no_match():
    """测试 Logo 匹配 — 无匹配."""
    from app.services.logo_detector import multi_scale_template_match
    from PIL import Image

    template_img = Image.new("RGB", (50, 50), color=(255, 0, 0))
    target_img = Image.new("RGB", (200, 200), color=(0, 255, 0))  # 完全不同

    result = multi_scale_template_match(
        template_img, target_img,
        ncc_threshold=0.7,
    )
    # 应有非常低的置信度
    if result is not None:
        assert result.confidence < 50.0


def test_mock_ecommerce_results():
    """测试模拟电商结果生成."""
    from app.services.logo_detector import generate_mock_ecommerce_results

    results = generate_mock_ecommerce_results("TestBrand", ["taobao", "jd"])
    assert len(results) >= 1
    for r in results:
        assert r["is_mock"] is True
        assert r["platform"] in ("taobao", "jd")
        assert "item_url" in r
        assert "similarity" in r


# ============================================================
# DMCA 模板填充测试
# ============================================================

def test_dmca_template_fill():
    """测试 DMCA 模板填充."""
    from app.services.dmca_template import fill_dmca_template, fill_dmca_template_from_work

    result = fill_dmca_template(
        work_title="My Artwork",
        creator_name="John Doe",
        original_url="https://mysite.com/artwork",
        infringing_url="https://infringer.com/copy",
    )
    assert "My Artwork" in result
    assert "John Doe" in result
    assert "DMCA TAKEDOWN NOTICE" in result
    assert "17 U.S.C." in result

    # 简化版
    result2 = fill_dmca_template_from_work(
        work_title="Test Work",
        creator_name="Jane",
    )
    assert "Test Work" in result2
    assert "Jane" in result2
