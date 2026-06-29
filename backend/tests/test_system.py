"""P2.6 和 P2.7 — MCP Server + 系统管理深度测试."""

import json


# ─────────────────────────────────────────────────────────────
# P2.6.1-P2.6.4: MCP Server
# ─────────────────────────────────────────────────────────────

def test_mcp_info(client):
    """测试 MCP server 信息端点."""
    resp = client.get("/api/mcp")
    assert resp.status_code == 200
    data = resp.json()
    assert data["protocol"] == "mcp"
    assert data["server"] == "oristudio-pdh-mcp"
    assert isinstance(data["tools"], list)
    assert len(data["tools"]) >= 7
    tool_names = {t["name"] for t in data["tools"]}
    assert "list_products" in tool_names
    assert "get_product" in tool_names
    assert "search_products" in tool_names
    assert "get_product_certificate" in tool_names
    assert "get_verified_mark" in tool_names
    assert "get_revenue_summary" in tool_names
    assert "get_product_feed" in tool_names


def test_mcp_auth_required(client):
    """测试 MCP 需要认证."""
    resp = client.post("/api/mcp", json={
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/list",
    })
    assert resp.status_code == 401


def test_mcp_invalid_key(client):
    """测试无效 API Key."""
    resp = client.post("/api/mcp", json={
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/list",
    }, headers={"Authorization": "Bearer invalid-key"})
    assert resp.status_code == 403


def test_mcp_initialize(client):
    """测试 MCP initialize."""
    resp = client.post("/api/mcp", json={
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "clientInfo": {"name": "test-client", "version": "1.0"},
        },
    }, headers={"Authorization": "Bearer mcp-dev-key-001"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["result"]["protocolVersion"] == "2024-11-05"
    assert "tools" in data["result"]["capabilities"]
    assert data["result"]["serverInfo"]["name"] == "oristudio-pdh-mcp"


def test_mcp_tools_list(client):
    """测试 MCP tools/list."""
    resp = client.post("/api/mcp", json={
        "jsonrpc": "2.0",
        "id": 2,
        "method": "tools/list",
    }, headers={"Authorization": "Bearer mcp-dev-key-001"})
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["result"]["tools"]) >= 7


def test_mcp_tools_call_list_products(client):
    """测试 MCP tools/call list_products."""
    # 先创建几个产品
    for i in range(3):
        client.post("/api/publish/products", json={
            "title": f"MCP测试商品{i}",
            "price": 99.0 + i * 10,
            "category": "mug",
        })

    resp = client.post("/api/mcp", json={
        "jsonrpc": "2.0",
        "id": 3,
        "method": "tools/call",
        "params": {"name": "list_products", "arguments": {}},
    }, headers={"Authorization": "Bearer mcp-dev-key-001"})
    assert resp.status_code == 200
    data = resp.json()
    content = data["result"]["content"][0]["text"]
    result = json.loads(content)
    assert result["total"] >= 3
    assert len(result["products"]) >= 3


def test_mcp_tools_call_get_product(client):
    """测试 MCP tools/call get_product."""
    resp = client.post("/api/publish/products", json={
        "title": "MCP详情测试",
        "price": 188.0,
        "category": "poster",
    })
    product_id = resp.json()["data"]["id"]

    resp = client.post("/api/mcp", json={
        "jsonrpc": "2.0",
        "id": 4,
        "method": "tools/call",
        "params": {"name": "get_product", "arguments": {"product_id": product_id}},
    }, headers={"Authorization": "Bearer mcp-dev-key-001"})
    assert resp.status_code == 200
    data = resp.json()
    content = data["result"]["content"][0]["text"]
    result = json.loads(content)
    assert result["id"] == product_id
    assert result["title"] == "MCP详情测试"
    assert result["price"] == 188.0


def test_mcp_tools_call_search_products(client):
    """测试 MCP tools/call search_products."""
    # 创建唯一标题的产品
    client.post("/api/publish/products", json={
        "title": "UniqueSearchTerm42",
        "price": 55.0,
        "category": "sticker",
    })

    resp = client.post("/api/mcp", json={
        "jsonrpc": "2.0",
        "id": 5,
        "method": "tools/call",
        "params": {"name": "search_products", "arguments": {"query": "UniqueSearchTerm42"}},
    }, headers={"Authorization": "Bearer mcp-dev-key-001"})
    assert resp.status_code == 200
    data = resp.json()
    content = data["result"]["content"][0]["text"]
    result = json.loads(content)
    assert result["total"] >= 1
    found = [p for p in result["products"] if "UniqueSearchTerm42" in p["title"]]
    assert len(found) >= 1


def test_mcp_tools_call_get_verified_mark(client):
    """测试 MCP tools/call get_verified_mark."""
    resp = client.post("/api/publish/products", json={
        "title": "MCP徽章测试",
        "price": 66.0,
        "category": "poster",
    })
    product_id = resp.json()["data"]["id"]

    resp = client.post("/api/mcp", json={
        "jsonrpc": "2.0",
        "id": 6,
        "method": "tools/call",
        "params": {"name": "get_verified_mark", "arguments": {"product_id": product_id}},
    }, headers={"Authorization": "Bearer mcp-dev-key-001"})
    assert resp.status_code == 200
    data = resp.json()
    content = data["result"]["content"][0]["text"]
    result = json.loads(content)
    assert "verify_url" in result or "qr_url" in result


def test_mcp_tools_call_revenue_summary(client):
    """测试 MCP tools/call get_revenue_summary."""
    from datetime import date
    client.post("/api/publish/revenue", json={
        "platform": "taobao",
        "amount": 1500.0,
        "date": date.today().isoformat(),
        "order_count": 5,
    })

    resp = client.post("/api/mcp", json={
        "jsonrpc": "2.0",
        "id": 7,
        "method": "tools/call",
        "params": {"name": "get_revenue_summary", "arguments": {"period": "month"}},
    }, headers={"Authorization": "Bearer mcp-dev-key-001"})
    assert resp.status_code == 200
    data = resp.json()
    content = data["result"]["content"][0]["text"]
    result = json.loads(content)
    assert "total_amount" in result
    assert "by_platform" in result
    assert "monthly_trend" in result


def test_mcp_tools_call_get_product_feed(client):
    """测试 MCP tools/call get_product_feed."""
    resp = client.post("/api/mcp", json={
        "jsonrpc": "2.0",
        "id": 8,
        "method": "tools/call",
        "params": {"name": "get_product_feed", "arguments": {"format": "universal"}},
    }, headers={"Authorization": "Bearer mcp-dev-key-001"})
    assert resp.status_code == 200
    data = resp.json()
    content = data["result"]["content"][0]["text"]
    result = json.loads(content)
    assert "products" in result


def test_mcp_wangdiantong_feed(client):
    """测试 MCP 旺店通格式 Feed."""
    resp = client.post("/api/mcp", json={
        "jsonrpc": "2.0",
        "id": 9,
        "method": "tools/call",
        "params": {"name": "get_product_feed", "arguments": {"format": "wangdiantong"}},
    }, headers={"Authorization": "Bearer mcp-dev-key-001"})
    assert resp.status_code == 200
    data = resp.json()
    content = data["result"]["content"][0]["text"]
    result = json.loads(content)
    assert result.get("erp_config", {}).get("format") == "wangdiantong"
    if result.get("products"):
        p = result["products"][0]
        assert "spec_no" in p
        assert "goods_name" in p


def test_mcp_jushuitan_feed(client):
    """测试 MCP 聚水潭格式 Feed."""
    resp = client.post("/api/mcp", json={
        "jsonrpc": "2.0",
        "id": 10,
        "method": "tools/call",
        "params": {"name": "get_product_feed", "arguments": {"format": "jushuitan"}},
    }, headers={"Authorization": "Bearer mcp-dev-key-001"})
    assert resp.status_code == 200
    data = resp.json()
    content = data["result"]["content"][0]["text"]
    result = json.loads(content)
    assert result.get("erp_config", {}).get("format") == "jushuitan"
    if result.get("products"):
        p = result["products"][0]
        assert "sku_id" in p
        assert "name" in p


def test_mcp_notifications_initialized(client):
    """测试 MCP notifications/initialized."""
    resp = client.post("/api/mcp", json={
        "jsonrpc": "2.0",
        "method": "notifications/initialized",
    }, headers={"Authorization": "Bearer mcp-dev-key-001"})
    assert resp.status_code == 200
    assert resp.json().get("result") == {}


# ─────────────────────────────────────────────────────────────
# P2.7.1-P2.7.2: 系统健康监控
# ─────────────────────────────────────────────────────────────

def test_health_dashboard(client):
    """测试系统健康仪表盘."""
    resp = client.get("/api/system/health/dashboard")
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    dashboard = data["data"]
    assert "cpu" in dashboard
    assert "memory" in dashboard
    assert "disk" in dashboard
    assert "services" in dashboard
    assert "database" in dashboard["services"]


def test_service_status(client):
    """测试服务状态."""
    resp = client.get("/api/system/health/services")
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    services = data["data"]
    assert "api_server" in services
    assert "database" in services
    assert "mcp_server" in services


# ─────────────────────────────────────────────────────────────
# P2.7.3-P2.7.4: 备份增强
# ─────────────────────────────────────────────────────────────

def test_encrypted_backup(client):
    """测试加密备份."""
    resp = client.post("/api/system/backup", params={
        "include_files": False,
        "encrypted": True,
        "incremental": False,
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["data"]["encrypted"] is True


def test_backup_schedule(client):
    """测试定时备份配置."""
    resp = client.post("/api/system/backup/schedule", params={
        "cron_expr": "0 3 * * *",
        "encrypted": True,
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "0 3 * * *" in data["data"]["cron"]


def test_get_backup_schedule(client):
    """测试获取定时备份配置."""
    resp = client.get("/api/system/backup/schedule")
    assert resp.status_code == 200
    data = resp.json()
    assert "cron" in data["data"]


def test_backup_list(client):
    """测试备份列表."""
    # 确保有备份
    client.post("/api/system/backup", params={"include_files": False})

    resp = client.get("/api/system/backups")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data["data"], list)


def test_restore_backup(client):
    """测试恢复备份."""
    # 先创建备份 (使用查询参数)
    backup_resp = client.post("/api/system/backup", params={
        "include_files": False,
        "encrypted": False,
    })
    assert backup_resp.status_code == 200
    backup_id = backup_resp.json()["data"]["backup_id"]

    resp = client.post("/api/system/restore", params={"backup_id": backup_id})
    assert resp.status_code == 200
    assert "恢复" in resp.json()["message"]


def test_delete_backup(client):
    """测试删除备份."""
    backup_resp = client.post("/api/system/backup", params={"include_files": False})
    backup_id = backup_resp.json()["data"]["backup_id"]

    resp = client.delete(f"/api/system/backups/{backup_id}")
    assert resp.status_code == 200


# ─────────────────────────────────────────────────────────────
# P2.7.5: Email SMTP 通知渠道
# ─────────────────────────────────────────────────────────────

def test_email_test_without_config(client):
    """测试邮件通知 (未配置 SMTP)."""
    resp = client.post("/api/system/notification/email/test", params={
        "recipient": "test@example.com",
    })
    # 未配置 SMTP 应返回 400
    assert resp.status_code == 400
    assert "SMTP" in resp.json()["detail"]


# ─────────────────────────────────────────────────────────────
# P2.7.8: 插件框架
# ─────────────────────────────────────────────────────────────

def test_register_plugin(client):
    """测试注册插件."""
    resp = client.post("/api/system/plugins", json={
        "name": "test-plugin",
        "display_name": "测试插件",
        "version": "1.0.0",
        "description": "A test plugin",
        "hooks": ["on_startup", "on_product_create"],
        "config": {"max_items": 100},
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "已注册" in data["message"]
    assert data["data"]["id"]


def test_list_plugins(client):
    """测试列出插件."""
    # 确保存在
    client.post("/api/system/plugins", json={
        "name": f"list-plugin-{id(client)}",
        "display_name": "列表测试",
    })

    resp = client.get("/api/system/plugins")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data["data"], list)


def test_enable_disable_plugin(client):
    """测试启用/禁用插件."""
    resp = client.post("/api/system/plugins", json={
        "name": "toggle-plugin",
        "display_name": "开关测试",
        "enabled": True,
    })
    plugin_id = resp.json()["data"]["id"]

    # 禁用
    resp = client.patch(f"/api/system/plugins/{plugin_id}", json={"enabled": False})
    assert resp.status_code == 200

    # 重新启用
    resp = client.patch(f"/api/system/plugins/{plugin_id}", json={"enabled": True})
    assert resp.status_code == 200


def test_delete_plugin(client):
    """测试删除插件."""
    resp = client.post("/api/system/plugins", json={
        "name": "delete-plugin",
        "display_name": "删除测试",
    })
    plugin_id = resp.json()["data"]["id"]

    resp = client.delete(f"/api/system/plugins/{plugin_id}")
    assert resp.status_code == 200


# ─────────────────────────────────────────────────────────────
# P2.7.11: 邮箱验证
# ─────────────────────────────────────────────────────────────

def test_send_verification_email(client):
    """测试发送验证码."""
    resp = client.post("/api/system/email/verify/send", params={
        "email": "verify@example.com",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True


def test_confirm_verification_invalid(client):
    """测试无效验证码."""
    resp = client.post("/api/system/email/verify/confirm", params={
        "email": "verify@example.com",
        "code": "000000",
    })
    assert resp.status_code == 400


# ─────────────────────────────────────────────────────────────
# P2.7.12: 密码重置
# ─────────────────────────────────────────────────────────────

def test_request_password_reset(client):
    """测试请求密码重置."""
    resp = client.post("/api/system/password/reset/request", params={
        "email": "reset@example.com",
    })
    assert resp.status_code == 200


# ─────────────────────────────────────────────────────────────
# P2.7.13: 密码强度检测
# ─────────────────────────────────────────────────────────────

def test_check_password_strength_weak(client):
    """测试弱密码."""
    resp = client.post("/api/system/password/check-strength", params={
        "password": "123",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["data"]["level"] == "weak"
    assert data["data"]["score"] < 50


def test_check_password_strength_strong(client):
    """测试强密码."""
    resp = client.post("/api/system/password/check-strength", params={
        "password": "MyStr0ng!Pass#2026",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["data"]["level"] == "strong"
    assert data["data"]["score"] >= 80


# ─────────────────────────────────────────────────────────────
# P2.7.14: 数据导出
# ─────────────────────────────────────────────────────────────

def test_export_all_json(client):
    """测试 JSON 格式导出."""
    resp = client.get("/api/system/export/all", params={"format": "json"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert "works" in data["data"]
    assert "products" in data["data"]


def test_export_all_csv(client):
    """测试 CSV 格式导出."""
    resp = client.get("/api/system/export/all", params={"format": "csv"})
    assert resp.status_code == 200
    data = resp.json()
    assert "csv_content" in data["data"]


# ─────────────────────────────────────────────────────────────
# P2.7.15: 危险区
# ─────────────────────────────────────────────────────────────

def test_clear_data_without_confirmation(client):
    """测试未确认清除."""
    resp = client.post("/api/system/danger/clear-data", params={
        "confirmation": "no",
    })
    assert resp.status_code == 400
