"""存证确权 API 测试."""

import io


def test_get_platforms(client):
    """测试获取存证平台列表."""
    resp = client.get("/api/notary/platforms")
    assert resp.status_code == 200
    platforms = resp.json()["data"]
    assert len(platforms) == 3


def test_notary_record_flow(client):
    """测试完整存证流程：上传 → 存证 → 确认 → 证书."""
    from PIL import Image

    img = Image.new("RGB", (200, 200), color=(255, 50, 50))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    buf.name = "notary_flow_test.png"
    work_resp = client.post(
        "/api/works",
        files={"file": ("notary_flow_test.png", buf, "image/png")},
        data={"title": "存证测试作品"},
    )
    assert work_resp.status_code == 200
    work_id = work_resp.json()["data"]["id"]

    notary_resp = client.post("/api/notary/records", json={
        "work_id": work_id,
        "platform": "banquanjia",
    })
    assert notary_resp.status_code == 200
    record_data = notary_resp.json()["data"]
    assert record_data["platform"] == "banquanjia"
    assert record_data["status"] == "pending"
    assert record_data["fee"] == 3.0

    confirm_resp = client.post(
        f"/api/notary/records/{record_data['id']}/confirm",
        json={"transaction_hash": "0xabc123def456"},
    )
    assert confirm_resp.status_code == 200
    confirmed_data = confirm_resp.json()["data"]
    assert confirmed_data["status"] == "confirmed"

    work_detail = client.get(f"/api/works/{work_id}")
    assert work_detail.json()["data"]["is_verified"] is True


def test_batch_notarize(client):
    """测试批量存证."""
    from PIL import Image
    import random

    work_ids = []
    for i in range(3):
        r, g, b = random.randint(1, 254), random.randint(1, 254), random.randint(1, 254)
        img = Image.new("RGB", (201 + i, 201 + i), color=(r, g, b))
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        buf.seek(0)
        buf.name = f"batch_n_{i}.png"
        resp = client.post(
            "/api/works",
            files={"file": (f"batch_n_{i}.png", buf, "image/png")},
            data={"title": f"批量测试{i}"},
        )
        if resp.status_code == 200:
            work_ids.append(resp.json()["data"]["id"])

    assert len(work_ids) >= 2, f"Only got {len(work_ids)} works, expected >= 2"

    resp = client.post(
        "/api/notary/batch",
        json={"work_ids": work_ids, "platform": "zhixinchain"},
    )
    assert resp.status_code == 200
    result = resp.json()
    assert result["data"]["count"] >= 2
