"""Notary Comparison Service 单元测试."""

import pytest


class TestNotaryComparisonService:
    """NotaryComparisonService 测试."""

    def test_get_platforms_returns_all(self):
        from app.services.notary_comparison_service import NotaryComparisonService

        svc = NotaryComparisonService()
        platforms = svc.get_platforms()
        assert len(platforms) >= 3

        keys = {p.key for p in platforms}
        assert "banquanjia" in keys
        assert "antchain" in keys
        assert "zhixinchain" in keys

    def test_get_platform_by_key(self):
        from app.services.notary_comparison_service import NotaryComparisonService

        svc = NotaryComparisonService()
        info = svc.get_platform("antchain")
        assert info is not None
        assert info.key == "antchain"
        assert info.fee_per_record == 0.5
        assert info.legal_level == "commercial"

    def test_get_nonexistent_platform(self):
        from app.services.notary_comparison_service import NotaryComparisonService

        svc = NotaryComparisonService()
        assert svc.get_platform("nonexistent") is None

    def test_has_platform(self):
        from app.services.notary_comparison_service import NotaryComparisonService

        svc = NotaryComparisonService()
        assert svc.has_platform("antchain") is True
        assert svc.has_platform("zhixinchain") is True
        assert svc.has_platform("nonexistent") is False

    def test_comparison_returns_sorted_by_fee(self):
        from app.services.notary_comparison_service import NotaryComparisonService

        svc = NotaryComparisonService()
        platforms, best_key, reasons = svc.compare(
            work_count=1,
            work_type="image",
            budget=10.0,
            legal_level="commercial",
            priority="cost",
        )
        assert len(platforms) >= 3
        assert platforms[0].estimated_total <= platforms[-1].estimated_total
        assert best_key in ("antchain", "zhixinchain", "banquanjia")


class TestAntChainGateway:
    """AntChainGateway 适配器测试."""

    def test_get_platform_name(self):
        from app.gateway.antchain import AntChainGateway

        gw = AntChainGateway()
        assert gw.get_platform_name() == "蚂蚁链 (AntChain)"

    def test_get_legal_level(self):
        from app.gateway.antchain import AntChainGateway

        gw = AntChainGateway()
        assert gw.get_legal_level() == "commercial"

    def test_get_fee(self):
        from app.gateway.antchain import AntChainGateway

        gw = AntChainGateway()
        assert gw.get_fee() == 0.5

    @pytest.mark.asyncio
    async def test_submit_evidence_no_api_key(self):
        from app.gateway.antchain import AntChainGateway

        gw = AntChainGateway()
        result = await gw.submit_evidence("abc123", {"type": "image"})
        assert result.success is True
        assert result.record_id is not None

    @pytest.mark.asyncio
    async def test_check_status_no_api_key(self):
        from app.gateway.antchain import AntChainGateway

        gw = AntChainGateway()
        status = await gw.check_status("some_record_id")
        assert status == "confirmed"


class TestZhixinChainGateway:
    """ZhixinChainGateway 适配器测试."""

    def test_get_platform_name(self):
        from app.gateway.zhixinchain import ZhixinChainGateway

        gw = ZhixinChainGateway()
        assert gw.get_platform_name() == "至信链 (ZhixinChain)"

    def test_get_legal_level(self):
        from app.gateway.zhixinchain import ZhixinChainGateway

        gw = ZhixinChainGateway()
        assert gw.get_legal_level() == "judicial"

    def test_get_fee(self):
        from app.gateway.zhixinchain import ZhixinChainGateway

        gw = ZhixinChainGateway()
        assert gw.get_fee() == 1.0

    @pytest.mark.asyncio
    async def test_submit_evidence_no_api_key(self):
        from app.gateway.zhixinchain import ZhixinChainGateway

        gw = ZhixinChainGateway()
        result = await gw.submit_evidence("abc123", {"type": "image"})
        assert result.success is True
        assert result.record_id is not None

    @pytest.mark.asyncio
    async def test_check_status_no_api_key(self):
        from app.gateway.zhixinchain import ZhixinChainGateway

        gw = ZhixinChainGateway()
        status = await gw.check_status("some_record_id")
        assert status == "confirmed"


class TestBanquanjiaGateway:
    """BanquanjiaGateway 适配器测试."""

    def test_get_platform_name(self):
        from app.gateway.banquanjia import BanquanjiaGateway

        gw = BanquanjiaGateway()
        assert gw.get_platform_name() == "版权家 (DCI)"

    def test_get_legal_level(self):
        from app.gateway.banquanjia import BanquanjiaGateway

        gw = BanquanjiaGateway()
        assert gw.get_legal_level() == "national"

    def test_get_fee(self):
        from app.gateway.banquanjia import BanquanjiaGateway

        gw = BanquanjiaGateway()
        assert gw.get_fee() == 3.0


class TestNotaryComparisonServiceHTTP:
    """对比服务 HTTP 端点测试."""

    def test_get_platforms_endpoint(self, client):
        resp = client.get("/api/notary/platforms")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert isinstance(data, list)
        assert len(data) >= 3
        keys = {p["key"] for p in data}
        assert "antchain" in keys
        assert "zhixinchain" in keys
        assert "banquanjia" in keys

    def test_compare_endpoint(self, client):
        resp = client.get(
            "/api/notary/compare",
            params={
                "work_count": 5,
                "work_type": "image",
                "budget": 20.0,
                "legal_level": "commercial",
                "priority": "cost",
            },
        )
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert "platforms" in data
        assert "recommended" in data
        assert "reasons" in data
        assert len(data["platforms"]) >= 3
