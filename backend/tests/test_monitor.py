"""侵权监测 API 测试."""

import io
import random


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


def test_get_quota(client):
    """测试获取配额信息."""
    resp = client.get("/api/monitor/quota")
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert "baidu" in data
    assert data["baidu"]["daily_limit"] == 100


def test_monitor_scan_flow(client):
    """测试监测流程：上传 → 创建任务 → 扫描 → 标记结果."""
    work_resp = _upload_random_image(client, "monitor_flow.png", "监测测试", (250, 250))
    assert work_resp.status_code == 200
    work_id = work_resp.json()["data"]["id"]

    task_resp = client.post("/api/monitor/tasks", json={
        "work_id": work_id,
        "platform": "baidu",
        "search_type": "image",
    })
    assert task_resp.status_code == 200
    task_data = task_resp.json()["data"]
    assert task_data["platform"] == "baidu"

    scan_resp = client.post(f"/api/monitor/tasks/{task_data['id']}/scan")
    assert scan_resp.status_code == 200

    results_resp = client.get("/api/monitor/results", params={"task_id": task_data["id"]})
    results = results_resp.json()["data"]
    assert len(results) >= 1

    result_id = results[0]["id"]
    update_resp = client.patch(f"/api/monitor/results/{result_id}", json={
        "status": "infringing",
        "action_taken": "generate_complaint",
    })
    assert update_resp.status_code == 200
    assert update_resp.json()["data"]["status"] == "infringing"


def test_batch_scan(client):
    """测试批量扫描."""
    work_ids = []
    for i in range(3):
        resp = _upload_random_image(client, f"batch_scan_{i}.png", f"批量扫描{i}", (260 + i, 260 + i))
        if resp.status_code == 200:
            work_ids.append(resp.json()["data"]["id"])

    assert len(work_ids) >= 2, f"Only got {len(work_ids)} works"

    resp = client.post("/api/monitor/scan", json={
        "work_ids": work_ids[:2],
        "platform": "baidu",
    })
    assert resp.status_code == 200
    assert resp.json()["data"]["works_scanned"] == 2


def test_list_tasks(client):
    """测试获取任务列表."""
    resp = client.get("/api/monitor/tasks")
    assert resp.status_code == 200
