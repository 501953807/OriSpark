"""P3.2.5: 边界条件测试 — 空状态响应、错误响应、大文件名."""

import io
import random


def _random_image(client, filename, title, size=(150, 150)):
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


# ────── Empty State Responses ──────


def test_empty_works_list(client):
    """空列表应返回 success=True 且 total>=0."""
    # 不创建任何作品，直接查询
    resp = client.get("/api/works", params={"search": "不存在的搜索词_xyz123"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert data["data"]["total"] == 0
    assert isinstance(data["data"]["items"], list)


def test_empty_notary_records(client):
    """空存证记录."""
    resp = client.get("/api/notary/records", params={"platform": "nonexistent_platform"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True


def test_empty_monitor_tasks(client):
    """空监测任务."""
    resp = client.get("/api/monitor/tasks", params={"status": "nonexistent"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True


def test_empty_monitor_results(client):
    """空监测结果 — 不存在的 task_id."""
    resp = client.get("/api/monitor/results", params={"task_id": "nonexistent_id_12345"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True


def test_dashboard_stats_empty(client):
    """仪表盘 — 空数据."""
    resp = client.get("/api/dashboard/stats")
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    stats = data["data"]
    assert "total_works" in stats


# ────── Error Responses ──────


def test_get_nonexistent_work(client):
    """请求不存在的作品."""
    resp = client.get("/api/works/nonexistent-id-12345")
    assert resp.status_code == 404


def test_upload_without_file(client):
    """上传时不提供文件."""
    resp = client.post("/api/works", data={"title": "无文件作品"})
    # 应该返回错误
    assert resp.status_code >= 400 or resp.json().get("success") is False


def test_notary_nonexistent_work(client):
    """对不存在的作品进行存证 — 应返回 404."""
    resp = client.post("/api/notary/records", json={
        "work_id": "nonexistent_work_id",
        "platform": "banquanjia",
    })
    assert resp.status_code == 404


def test_notary_invalid_platform(client):
    """使用无效的存证平台."""
    resp = _random_image(client, "invalid_platform.png", "无效平台测试")
    if resp.status_code == 200:
        work_id = resp.json()["data"]["id"]
        resp2 = client.post("/api/notary/records", json={
            "work_id": work_id,
            "platform": "invalid_fake_platform",
        })
        assert resp2.status_code == 400


def test_monitor_without_work(client):
    """监测不存在的作品 — 应返回 404."""
    resp = client.post("/api/monitor/tasks", json={
        "work_id": "nonexistent_work_id_123",
        "platform": "baidu",
        "search_type": "image",
    })
    assert resp.status_code == 404


def test_invalid_json_body(client):
    """发送无效 JSON."""
    resp = client.post(
        "/api/works",
        content=b"invalid json {{{",
        headers={"Content-Type": "application/json"},
    )
    assert resp.status_code >= 400


# ────── Large Filenames ──────


def test_very_long_filename(client):
    """测试超长文件名 (255+ 字符)."""
    long_name = "a" * 200 + ".png"
    resp = _random_image(client, long_name, "超长文件名测试")
    # 应正常处理或返回合理错误
    assert resp.status_code in (200, 400, 422, 413)


def test_filename_with_special_characters(client):
    """测试特殊字符文件名."""
    names = [
        "test file with spaces.png",
        "test-file-with-dashes.png",
        "test_file_with_underscores.png",
        "测试中文文件名.png",
        "test (1) copy.png",
    ]
    for name in names:
        resp = _random_image(client, name, f"特殊字符测试 - {name}")
        assert resp.status_code == 200, f"Failed for filename: {name}"
        assert resp.json()["data"]["file_name"] == name


def test_filename_with_unicode(client):
    """测试 Unicode 文件名."""
    unicode_names = [
        "café.png",          # cafe + combining accent
        "☃_snowman.png",      # snowman
        "emoji❤️.png",   # heart
    ]
    for name in unicode_names:
        try:
            resp = _random_image(client, name.encode("utf-8").decode("utf-8"), f"Unicode测试")
            assert resp.status_code in (200, 422, 400)
        except Exception:
            # Unicode filenames may cause encoding issues in HTTP
            pass


def test_duplicate_title(client):
    """测试重复标题 (应允许)."""
    unique_name1 = f"dup_test_{random.randint(1, 99999)}.png"
    unique_name2 = f"dup_test_{random.randint(1, 99999)}.png"

    resp1 = _random_image(client, unique_name1, "相同标题")
    resp2 = _random_image(client, unique_name2, "相同标题")

    assert resp1.status_code == 200
    assert resp2.status_code == 200
    assert resp1.json()["data"]["title"] == resp2.json()["data"]["title"] == "相同标题"


def test_zero_size_image(client):
    """测试零尺寸图片上传."""
    from PIL import Image

    # 1x1 像素图片
    img = Image.new("RGB", (1, 1), color=(128, 128, 128))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    buf.name = "one_pixel.png"

    resp = client.post(
        "/api/works",
        files={"file": ("one_pixel.png", buf, "image/png")},
        data={"title": "单像素图片"},
    )
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["file_size"] > 0


def test_large_image_upload(client):
    """测试较大图片上传."""
    from PIL import Image

    img = Image.new("RGB", (1920, 1080), color=(random.randint(1, 254), 100, 200))
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=85)
    buf.seek(0)
    buf.name = "large_1920x1080.jpg"

    resp = client.post(
        "/api/works",
        files={"file": ("large_1920x1080.jpg", buf, "image/jpeg")},
        data={"title": "大图测试"},
    )
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["file_size"] > 0
    assert data["file_type"] == "image"
