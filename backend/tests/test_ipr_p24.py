"""IP 登记 API 测试 (P2.4 全球覆盖)."""

import io
from sqlalchemy.orm import Session


def test_get_guidelines_all(client):
    """测试获取全局指引 (不指定辖区)."""
    resp = client.get("/api/ipr/guidelines")
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    guidelines = data["data"]["guidelines"]
    # 6 jurisdictions
    assert "cn" in guidelines
    assert "us" in guidelines
    assert "eu" in guidelines
    assert "wipo" in guidelines
    assert "jp" in guidelines
    assert "kr" in guidelines
    assert "disclaimer" in data["data"]


def test_get_guidelines_cn(client):
    """测试获取中国辖区指引."""
    resp = client.get("/api/ipr/guidelines?jurisdiction=cn")
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["jurisdiction"] == "cn"
    assert "copyright" in data["guidelines"]
    assert "trademark" in data["guidelines"]
    assert "design_patent" in data["guidelines"]
    assert data["disclaimer"]


def test_get_guidelines_us(client):
    """测试获取美国辖区指引."""
    resp = client.get("/api/ipr/guidelines?jurisdiction=us")
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["jurisdiction"] == "us"
    assert "copyright" in data["guidelines"]
    # Check copyright details
    us_cr = data["guidelines"]["copyright"]
    assert "U.S. Copyright" in us_cr["title"] or "美国" in us_cr["title"]
    assert us_cr["institution"] == "U.S. Copyright Office (美国版权局)"
    assert "standard_electronic" in us_cr["fee"]
    # Check form types
    assert "CO" in us_cr.get("forms", {})
    assert "VA" in us_cr.get("forms", {})


def test_get_guidelines_eu(client):
    """测试获取欧盟辖区指引 (含 SME Fund)."""
    resp = client.get("/api/ipr/guidelines?jurisdiction=eu")
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["jurisdiction"] == "eu"
    assert "trademark" in data["guidelines"]
    assert "sme_fund" in data["guidelines"]
    # SME Fund eligibility check
    sme = data["guidelines"]["sme_fund"]
    assert "SME Fund" in sme["title"]
    assert sme["eligibility"]["definition"]
    assert len(sme["eligibility"]["requirements"]) > 0
    assert sme["coverage"]["trademark"]["reimbursement_rate"] == "75%"
    # EUIPO trademark details
    eu_tm = data["guidelines"]["trademark"]
    assert "EUIPO" in eu_tm["institution"]
    assert eu_tm["fee"]["basic_1class"] == "€850 (电子申请, 1个类别)"
    assert len(eu_tm["member_countries"]) == 27


def test_get_guidelines_wipo(client):
    """测试获取WIPO辖区指引 (马德里+海牙)."""
    resp = client.get("/api/ipr/guidelines?jurisdiction=wipo")
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["jurisdiction"] == "wipo"
    assert "trademark" in data["guidelines"]
    assert "design_patent" in data["guidelines"]
    # Madrid system
    wipo_tm = data["guidelines"]["trademark"]
    assert "马德里" in wipo_tm["title"]
    assert "CHF 653" in wipo_tm["fee"]["basic"]
    assert len(wipo_tm["fee_examples"]) >= 2
    assert wipo_tm["prerequisites"]
    # Hague system
    wipo_dp = data["guidelines"]["design_patent"]
    assert "海牙" in wipo_dp["title"]
    assert wipo_dp["institution"] == "WIPO (世界知识产权组织)"
    assert wipo_dp["member_count"] == 79


def test_get_guidelines_jp(client):
    """测试获取日本辖区指引."""
    resp = client.get("/api/ipr/guidelines?jurisdiction=jp")
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["jurisdiction"] == "jp"
    jp_tm = data["guidelines"]["trademark"]
    assert "日本" in jp_tm["title"]
    assert "JPO" in jp_tm["institution"]
    assert "日本" in jp_tm.get("note_agent", "")
    # Fee check
    assert "¥12,000" in str(jp_tm["fee"]["application_example_1class"])


def test_get_guidelines_kr(client):
    """测试获取韩国辖区指引."""
    resp = client.get("/api/ipr/guidelines?jurisdiction=kr")
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["jurisdiction"] == "kr"
    kr_tm = data["guidelines"]["trademark"]
    assert "韩国" in kr_tm["title"]
    assert "KIPO" in kr_tm["institution"]
    assert "韩国" in kr_tm.get("note_agent", "")


def test_get_guidelines_by_type_cn(client):
    """测试按类型+辖区获取指引."""
    resp = client.get("/api/ipr/guidelines/copyright?jurisdiction=cn")
    assert resp.status_code == 200
    assert "中国著作权" in resp.json()["data"]["title"]

    resp = client.get("/api/ipr/guidelines/trademark?jurisdiction=cn")
    assert resp.status_code == 200
    assert "中国商标" in resp.json()["data"]["title"]


def test_get_guidelines_by_type_us(client):
    """测试按类型获取美国指引."""
    resp = client.get("/api/ipr/guidelines/copyright?jurisdiction=us")
    assert resp.status_code == 200
    assert "U.S. Copyright" in resp.json()["data"]["title"]


def test_get_guidelines_by_type_unsupported(client):
    """测试不支持的辖区/类型组合."""
    resp = client.get("/api/ipr/guidelines/trademark?jurisdiction=xx")
    assert resp.status_code == 404


def test_get_paths_global(client):
    """测试全球IP路径."""
    resp = client.get("/api/ipr/paths")
    assert resp.status_code == 200
    data = resp.json()["data"]
    # Copyright: CN + US
    assert len(data["copyright"]["jurisdictions"]) >= 2
    # Trademark: CN + US + EU + WIPO + JP + KR = 6
    assert len(data["trademark"]["jurisdictions"]) >= 6
    # Design: CN + EU + WIPO = 3
    assert len(data["design_patent"]["jurisdictions"]) >= 3


def test_nice_classes_full(client):
    """测试全45类尼斯分类."""
    resp = client.get("/api/ipr/nice-classes")
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert len(data) == 45
    # Verify specific classes exist
    class_nos = {c["class_no"] for c in data}
    assert 1 in class_nos
    assert 16 in class_nos
    assert 45 in class_nos
    # Check creative relevant count
    creative = [c for c in data if c["is_creative_relevant"]]
    assert len(creative) >= 18


def test_nice_class_detail(client):
    """测试单个尼斯分类详情."""
    resp = client.get("/api/ipr/nice-classes/9/goods")
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["class_no"] == 9
    assert "软件" in data["class_name_zh"] or "科学" in data["class_name_zh"]


def test_fee_calculator_trademark_cn(client):
    """测试费用计算器: 中国商标."""
    resp = client.post("/api/ipr/fee-calculator", json={
        "ip_type": "trademark",
        "jurisdictions": ["cn"],
        "classes": [16, 25, 28],
    })
    assert resp.status_code == 200
    result = resp.json()["data"]
    assert result["summary"]["ip_type"] == "trademark"
    assert result["summary"]["total_fee_cny"] == 900  # 3 * 300
    bd = result["breakdown"][0]
    assert bd["jurisdiction"] == "cn"
    assert bd["currency"] == "CNY"
    assert bd["fee"] == 900
    assert bd["classes_count"] == 3


def test_fee_calculator_trademark_eu(client):
    """测试费用计算器: EUIPO商标."""
    resp = client.post("/api/ipr/fee-calculator", json={
        "ip_type": "trademark",
        "jurisdictions": ["eu"],
        "classes": [16, 25],
    })
    assert resp.status_code == 200
    result = resp.json()["data"]
    bd = result["breakdown"][0]
    assert bd["fee"] == 900  # 850 + 50
    assert bd["currency"] == "EUR"

    # 3 classes
    resp = client.post("/api/ipr/fee-calculator", json={
        "ip_type": "trademark",
        "jurisdictions": ["eu"],
        "classes": [16, 25, 28],
    })
    bd = resp.json()["data"]["breakdown"][0]
    assert bd["fee"] == 1050  # 850 + 50 + 150


def test_fee_calculator_trademark_wipo(client):
    """测试费用计算器: WIPO马德里."""
    resp = client.post("/api/ipr/fee-calculator", json={
        "ip_type": "trademark",
        "jurisdictions": ["wipo"],
        "classes": [16],
        "wipo_designations": ["eu", "us"],
        "is_color": False,
    })
    assert resp.status_code == 200
    result = resp.json()["data"]
    bd = result["breakdown"][0]
    assert bd["currency"] == "CHF"
    assert bd["fee"] == 1950  # 653 + 897 + 400
    # Verify total CNY conversion
    assert result["summary"]["total_fee_cny"] > 0
    assert "disclaimer" in result["summary"]


def test_fee_calculator_multijurisdiction(client):
    """测试费用计算器: 多辖区."""
    resp = client.post("/api/ipr/fee-calculator", json={
        "ip_type": "trademark",
        "jurisdictions": ["cn", "jp", "kr"],
        "classes": [16, 25],
    })
    assert resp.status_code == 200
    result = resp.json()["data"]
    assert len(result["breakdown"]) == 3
    # CN: 2 * 300 = 600 CNY
    # JP: 2 * 12000 = 24000 JPY -> CNY
    # KR: 2 * 56000 = 112000 KRW -> CNY
    assert result["breakdown"][0]["fee"] == 600
    assert result["breakdown"][1]["fee"] == 24000
    assert result["breakdown"][2]["fee"] == 112000
    assert result["summary"]["total_fee_cny"] > 0


def test_fee_calculator_copyright(client):
    """测试费用计算器: 版权."""
    resp = client.post("/api/ipr/fee-calculator", json={
        "ip_type": "copyright",
        "jurisdictions": ["cn", "us"],
    })
    assert resp.status_code == 200
    result = resp.json()["data"]
    assert len(result["breakdown"]) == 2
    assert result["breakdown"][0]["fee"] == 300  # CN copyright
    assert result["breakdown"][1]["fee"] == 45   # US copyright


def test_fee_calculator_design(client):
    """测试费用计算器: 外观设计."""
    resp = client.post("/api/ipr/fee-calculator", json={
        "ip_type": "design_patent",
        "jurisdictions": ["cn"],
    })
    assert resp.status_code == 200
    bd = resp.json()["data"]["breakdown"][0]
    assert bd["fee"] == 500  # CN design

    resp = client.post("/api/ipr/fee-calculator", json={
        "ip_type": "design_patent",
        "jurisdictions": ["eu"],
        "design_count": 3,
    })
    bd = resp.json()["data"]["breakdown"][0]
    assert bd["fee"] == 700  # 350 + 2*175


def test_fee_calculator_wipo_hague(client):
    """测试费用计算器: WIPO海牙外观设计."""
    resp = client.post("/api/ipr/fee-calculator", json={
        "ip_type": "design_patent",
        "jurisdictions": ["wipo"],
        "design_count": 2,
        "wipo_designations": ["eu"],
    })
    assert resp.status_code == 200
    bd = resp.json()["data"]["breakdown"][0]
    assert bd["currency"] == "CHF"
    # 397 + 19 + 17*2 + 67 = 517
    assert bd["fee"] == 517


def test_fee_calculator_disclaimer(client):
    """测试费用计算器返回免责声明."""
    resp = client.post("/api/ipr/fee-calculator", json={
        "ip_type": "trademark",
        "jurisdictions": ["cn"],
        "classes": [16],
    })
    assert resp.status_code == 200
    assert "disclaimer" in resp.json()["data"]["summary"]
    assert "法律建议" in resp.json()["data"]["summary"]["disclaimer"]


def test_fee_calculator_empty_jurisdictions(client):
    """测试空辖区报错."""
    resp = client.post("/api/ipr/fee-calculator", json={
        "ip_type": "trademark",
        "jurisdictions": [],
    })
    assert resp.status_code == 400


def test_templates_list(client):
    """测试获取申请表模板列表."""
    resp = client.get("/api/ipr/templates")
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert len(data) >= 4
    jurisdictions = {t["jurisdiction"] for t in data}
    assert "us" in jurisdictions
    assert "eu" in jurisdictions
    assert "wipo" in jurisdictions
    assert "cn" in jurisdictions


def test_templates_filter_by_type(client):
    """测试按类型过滤模板."""
    resp = client.get("/api/ipr/templates?ip_type=trademark")
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert len(data) >= 3  # EU + WIPO + CN
    for t in data:
        assert t["ip_type"] == "trademark"


def test_templates_filter_by_jurisdiction(client):
    """测试按辖区过滤模板."""
    resp = client.get("/api/ipr/templates?jurisdiction=eu")
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert len(data) >= 1
    assert data[0]["jurisdiction"] == "eu"


def test_template_detail(client):
    """测试获取单个模板详情."""
    # First list to get an ID
    resp = client.get("/api/ipr/templates")
    templates = resp.json()["data"]
    assert len(templates) > 0
    tid = templates[0]["id"]

    resp = client.get(f"/api/ipr/templates/{tid}")
    assert resp.status_code == 200
    t = resp.json()["data"]
    assert t["id"] == tid
    assert "form_schema" in t
    assert "field_mappings" in t
    assert t["form_schema"]["sections"]


def test_template_not_found(client):
    """测试模板不存在."""
    resp = client.get("/api/ipr/templates/nonexistent123")
    assert resp.status_code == 404


def test_registration_crud(client):
    """测试IP登记记录CRUD."""
    from PIL import Image
    import random

    r, g, b = random.randint(1, 254), random.randint(1, 254), random.randint(1, 254)
    img = Image.new("RGB", (160, 160), color=(r, g, b))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    buf.name = "ipr_test.png"
    work_resp = client.post(
        "/api/works",
        files={"file": ("ipr_test.png", buf, "image/png")},
        data={"title": "IP登记测试", "tags": "插画,IP"},
    )
    assert work_resp.status_code == 200
    work_id = work_resp.json()["data"]["id"]

    # Create
    resp = client.post("/api/ipr/registrations", json={
        "work_id": work_id,
        "ip_type": "trademark",
        "jurisdiction": "cn",
        "official_fee": 300,
        "status": "filed",
        "notes": "测试",
    })
    assert resp.status_code == 200
    reg_id = resp.json()["data"]["id"]

    # List
    resp = client.get("/api/ipr/registrations")
    assert resp.status_code == 200
    records = resp.json()["data"]
    assert len(records) >= 1

    # Get
    resp = client.get(f"/api/ipr/registrations/{reg_id}")
    assert resp.status_code == 200
    assert resp.json()["data"]["ip_type"] == "trademark"
    assert resp.json()["data"]["jurisdiction"] == "cn"

    # Update
    resp = client.patch(f"/api/ipr/registrations/{reg_id}", json={
        "status": "registered", "registration_no": "REG-123",
    })
    assert resp.status_code == 200

    # Delete
    resp = client.delete(f"/api/ipr/registrations/{reg_id}")
    assert resp.status_code == 200


def test_recommend_classes(client):
    """测试类别推荐."""
    resp = client.post("/api/ipr/recommend/classes", json={
        "tags": ["插画", "文创", "角色"],
        "creator_type": "illustrator_product",
    })
    assert resp.status_code == 200
    result = resp.json()["data"]
    assert len(result["recommendations"]) >= 3
    assert result["estimated_total_fee"] > 0


def test_prefill_copyright(client):
    """测试版权预填."""
    from PIL import Image
    import random
    r, g, b = random.randint(1, 254), random.randint(1, 254), random.randint(1, 254)
    img = Image.new("RGB", (160, 160), color=(r, g, b))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    buf.name = "prefill_test.png"
    work_resp = client.post(
        "/api/works",
        files={"file": ("prefill_test.png", buf, "image/png")},
        data={"title": "预填测试作品", "description": "测试预填功能的创作说明文本"},
    )
    assert work_resp.status_code == 200
    work_id = work_resp.json()["data"]["id"]

    resp = client.post("/api/ipr/assistant/prefill", json={
        "work_id": work_id,
        "ip_type": "copyright",
        "jurisdiction": "cn",
    })
    assert resp.status_code == 200
    result = resp.json()["data"]
    assert result["work_title"] == "预填测试作品"
    assert result["completeness"] > 0


def test_portfolio(client):
    """测试IP资产组合."""
    resp = client.get("/api/ipr/portfolio")
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert "stats" in data
    assert "renewals" in data
    assert data["total_ips"] >= 0


def test_dashboard(client):
    """测试IP仪表盘."""
    resp = client.get("/api/ipr/dashboard")
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert "total" in data
    assert "by_type" in data


def test_reminders(client):
    """测试到期提醒."""
    resp = client.get("/api/ipr/reminders")
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert "urgent" in data
    assert "upcoming" in data
    assert "future" in data


def test_ipr_disclaimers_in_all_guidelines(client):
    """测试所有辖区指引都含免责声明."""
    for jur in ["cn", "us", "eu", "wipo", "jp", "kr"]:
        resp = client.get(f"/api/ipr/guidelines?jurisdiction={jur}")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert "disclaimer" in data
        assert "不构成法律建议" in data["disclaimer"]


# ─── Gazette monitoring ──────────────────────────────────────────


def test_gazette_cn(client):
    """Test CN trademark gazette info."""
    resp = client.get("/api/ipr/gazette/cn")
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert "CNIPA" in data["institution"]
    assert "商标公告" in data["gazette_name"]
    assert len(data["how_to_monitor"]) > 0


def test_gazette_us(client):
    """Test US trademark gazette info."""
    resp = client.get("/api/ipr/gazette/us")
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert "USPTO" in data["institution"]
    assert "Trademark Official Gazette" in data["gazette_name"]


def test_gazette_eu(client):
    """Test EU trademark gazette info."""
    resp = client.get("/api/ipr/gazette/eu")
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert "EUIPO" in data["institution"]
    assert "EUTM Bulletin" in data["gazette_name"]


def test_gazette_unsupported(client):
    """Test gazette for unsupported jurisdiction returns gracefully."""
    resp = client.get("/api/ipr/gazette/xx")
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert "available_jurisdictions" in data


# ─── Application export (assistant/export) ──────────────────────


def test_export_application_copyright(client):
    """Test exporting copyright application materials."""
    resp = client.post("/api/ipr/assistant/export", json={
        "ip_type": "copyright",
        "jurisdiction": "cn",
        "lawyer_consulted": "A",
    })
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["ip_type"] == "copyright"
    assert data["lawyer_consulted"] == "A"
    assert "checklist" in data


def test_export_trademark(client):
    """Test exporting trademark application materials."""
    resp = client.post("/api/ipr/assistant/export", json={
        "ip_type": "trademark",
        "jurisdiction": "cn",
        "lawyer_consulted": "B",
    })
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["ip_type"] == "trademark"


def test_export_requires_lawyer_consultation(client):
    """Test that export without lawyer consultation is blocked."""
    resp = client.post("/api/ipr/assistant/export", json={
        "ip_type": "copyright",
        "jurisdiction": "cn",
        "lawyer_consulted": "C",
    })
    assert resp.status_code == 403

    resp = client.post("/api/ipr/assistant/export", json={
        "ip_type": "copyright",
        "jurisdiction": "cn",
    })
    assert resp.status_code == 403


# ─── Assistant validate ─────────────────────────────────────────


def test_validate_copyright_complete(client):
    """Test validating a complete copyright application."""
    resp = client.post("/api/ipr/assistant/validate", json={
        "ip_type": "copyright",
        "fields": {
            "作品名称": "Test Work",
            "作品类别": "美术作品",
            "作者姓名": "Test Author",
            "创作完成日期": "2025-01-01",
            "创作说明": "This is a detailed description of the creative process and originality.",
        },
    })
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["valid"] is True


def test_validate_copyright_missing_fields(client):
    """Test validating copyright with missing required fields."""
    resp = client.post("/api/ipr/assistant/validate", json={
        "ip_type": "copyright",
        "fields": {},
    })
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["valid"] is False
    assert len(data["issues"]) > 0


def test_validate_copyright_bad_date(client):
    """Test validating copyright with invalid date."""
    resp = client.post("/api/ipr/assistant/validate", json={
        "ip_type": "copyright",
        "fields": {
            "作品名称": "Test",
            "作品类别": "美术作品",
            "作者姓名": "Author",
            "创作完成日期": "not-a-date",
            "创作说明": "Short",
        },
    })
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["valid"] is False
    issues = [i for i in data["issues"] if i["field"] == "创作完成日期"]
    assert len(issues) > 0


def test_validate_copyright_future_date(client):
    """Test validating copyright with future completion date."""
    from datetime import date, timedelta
    future = (date.today() + timedelta(days=365)).isoformat()
    resp = client.post("/api/ipr/assistant/validate", json={
        "ip_type": "copyright",
        "fields": {
            "作品名称": "Test",
            "作品类别": "美术作品",
            "作者姓名": "Author",
            "创作完成日期": future,
            "创作说明": "This is a detailed description of the creative process and originality.",
        },
    })
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["valid"] is False


def test_validate_copyright_short_description(client):
    """Test validating copyright with too-short description triggers warning."""
    resp = client.post("/api/ipr/assistant/validate", json={
        "ip_type": "copyright",
        "fields": {
            "作品名称": "Test",
            "作品类别": "美术作品",
            "作者姓名": "Author",
            "创作完成日期": "2025-01-01",
            "创作说明": "Hi",
        },
    })
    assert resp.status_code == 200
    data = resp.json()["data"]
    warnings = [i for i in data["issues"] if i["level"] == "warning"]
    assert len(warnings) > 0


def test_validate_trademark(client):
    """Test validating a trademark application."""
    resp = client.post("/api/ipr/assistant/validate", json={
        "ip_type": "trademark",
        "fields": {
            "商标名称": "MyBrand",
            "申请人名称": "Test Corp",
            "申请人地址": "123 Test St",
            "商品/服务类别": "第16类",
        },
    })
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["valid"] is True


# ─── Assistant generate ─────────────────────────────────────────


def test_generate_copyright_application(client):
    """Test generating a copyright application preview."""
    resp = client.post("/api/ipr/assistant/generate", json={
        "ip_type": "copyright",
        "jurisdiction": "cn",
        "fields": {"作品名称": "Test"},
    })
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["ip_type"] == "copyright"
    assert data["form_title"] == "作品登记申请表"
    assert "disclaimer" in data


def test_generate_trademark_application(client):
    """Test generating a trademark application preview."""
    resp = client.post("/api/ipr/assistant/generate", json={
        "ip_type": "trademark",
        "jurisdiction": "cn",
        "fields": {"商标名称": "MyBrand"},
    })
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["ip_type"] == "trademark"
    assert data["form_title"] == "商标注册申请书"


# ─── Export application package ─────────────────────────────────


def test_export_package(client, db_session: Session):
    """Test exporting IP registration application package."""
    # Create an IP registration first
    resp = client.post("/api/ipr/registrations", json={
        "ip_type": "copyright",
        "jurisdiction": "cn",
        "official_fee": 300,
        "total_cost": 300,
        "status": "filed",
        "notes": "Test export",
    })
    assert resp.status_code == 200
    reg_id = resp.json()["data"]["id"]

    resp = client.post(f"/api/ipr/registrations/{reg_id}/export-package")
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["record_id"] == reg_id
    assert data["ip_type"] == "copyright"
    assert "zip_data_base64" in data
    assert "application_form.txt" in data["package_contents"]


def test_export_package_missing_record(client):
    """Test exporting package for non-existent record."""
    resp = client.post("/api/ipr/registrations/nonexistent/export-package")
    assert resp.status_code == 404


# ─── Recommend strategies ───────────────────────────────────────


def test_recommend_strategies(client):
    """Test getting creator-type recommendation strategies."""
    resp = client.get("/api/ipr/recommend/strategies")
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert isinstance(data, list)
    assert len(data) >= 5
    keys = {s["key"] for s in data}
    assert "illustrator" in keys
    assert "photographer" in keys
