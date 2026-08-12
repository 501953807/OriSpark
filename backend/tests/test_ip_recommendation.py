"""IP Recommendation Service 单元测试."""

import pytest
from unittest.mock import MagicMock, patch

from app.services.ip_recommendation_service import IPRecommendationService


@pytest.fixture
def svc():
    return IPRecommendationService()


class TestRecommendClasses:
    def test_recommend_classes_returns_results(self, svc):
        results = svc.recommend_classes("插画角色设计，时尚服装潮牌，玩具盲盒周边", "trademark")
        assert isinstance(results, list)
        assert len(results) >= 1
        for item in results:
            assert "class_id" in item
            assert "class_name" in item
            assert "confidence" in item
            assert isinstance(item["confidence"], float)
            assert 0 < item["confidence"] <= 1.0

    def test_recommend_classes_high_confidence_for_exact_match(self, svc):
        results = svc.recommend_classes("服装T恤潮牌服饰", "trademark")
        class_25_results = [r for r in results if r["class_id"] == 25]
        assert len(class_25_results) > 0
        assert class_25_results[0]["confidence"] >= 0.4

    def test_recommend_classes_copyright(self, svc):
        results = svc.recommend_classes("动画短片数字艺术作品", "copyright")
        assert isinstance(results, list)
        assert len(results) >= 1

    def test_recommend_classes_empty_description(self, svc):
        results = svc.recommend_classes("", "trademark")
        assert isinstance(results, list)
        assert len(results) >= 1

    def test_recommend_classes_unknown_ip_type(self, svc):
        results = svc.recommend_classes("这是一个测试作品", "unknown_type")
        assert isinstance(results, list)
        assert len(results) >= 1

    def test_recommend_classes_returns_valid_confidence_range(self, svc):
        results = svc.recommend_classes("服装T恤潮牌服饰", "trademark")
        assert isinstance(results, list)
        assert all(0 < r["confidence"] <= 1.0 for r in results)

    def test_recommend_classes_returns_class_id_9_for_software(self, svc):
        results = svc.recommend_classes("人工智能软件AIGC生成应用", "trademark")
        class_9_results = [r for r in results if r["class_id"] == 9]
        assert len(class_9_results) > 0
        assert class_9_results[0]["confidence"] >= 0.4

    def test_recommend_classes_format(self, svc):
        results = svc.recommend_classes("插画设计", "trademark")
        assert len(results) >= 1
        item = results[0]
        assert isinstance(item["class_id"], int)
        assert isinstance(item["class_name"], str)
        assert isinstance(item["class_name_en"], str)
        assert isinstance(item["confidence"], float)
        assert isinstance(item["description"], str)


class TestMaterialList:
    def test_material_list_by_status(self):
        from app.services.ipr_service import _get_material_list_for_status
        result = _get_material_list_for_status("draft", "copyright")
        assert result["status"] == "draft"
        assert result["ip_type"] == "copyright"
        assert isinstance(result["required"], list)
        assert len(result["required"]) > 0
        for item in result["required"]:
            assert "name" in item
            assert "required" in item
            assert "description" in item

    def test_material_list_trademark_submitted(self):
        from app.services.ipr_service import _get_material_list_for_status
        result = _get_material_list_for_status("submitted", "trademark")
        assert result["status"] == "submitted"
        assert result["ip_type"] == "trademark"
        assert len(result["required"]) > 0

    def test_material_list_unknown_ip_type_defaults(self):
        from app.services.ipr_service import _get_material_list_for_status
        result = _get_material_list_for_status("draft", "unknown_type")
        assert result["ip_type"] == "unknown_type"
        assert len(result["required"]) > 0

    def test_material_list_registered_has_certificate(self):
        from app.services.ipr_service import _get_material_list_for_status
        result = _get_material_list_for_status("registered", "copyright")
        names = [item["name"] for item in result["required"]]
        assert any("证书" in name for name in names)
