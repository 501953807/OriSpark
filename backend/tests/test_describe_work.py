import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

import pytest
from datetime import datetime, timezone

from app.services.describe_work_service import DescribeWorkService
from app.models.work import Work
from app.models.publish import RevenueRecord


@pytest.fixture(autouse=True)
def _cleanup_works(db_session):
    yield
    try:
        from sqlalchemy import text
        db_session.execute(text("DELETE FROM works"))
        db_session.flush()
        db_session.rollback()
    except Exception:
        db_session.rollback()


def test_describe_work_not_found(db_session):
    svc = DescribeWorkService()
    with pytest.raises(ValueError, match="作品不存在"):
        db_session.commit = lambda: None
        import asyncio
        asyncio.run(
            svc.describe_work(db_session, "nonexistent-work-id", {})
        )


def test_describe_work_fallback(db_session):
    work = Work(
        id="test-work-001",
        title="测试作品",
        file_path="/tmp/test.jpg",
        file_name="test.jpg",
        file_size=1024,
        file_type="image",
        file_extension="jpg",
        creator_type="illustrator",
    )
    db_session.add(work)
    db_session.flush()

    svc = DescribeWorkService()
    result = svc._fallback_description(work.title, work.creator_type)

    assert result["title"] == "原创illustrator作品 - 测试作品"
    assert "测试作品" in result["description"]
    assert isinstance(result["specs"], list)
    assert isinstance(result["tags"], list)
    assert "¥" in result["price_range"]


def test_parse_ai_output_basic():
    svc = DescribeWorkService()
    raw = """1. 产品标题：原创插画作品 - 星空

2. 产品描述：
这是一款精心创作的插画作品，展现了独特的星空视角。
适合收藏和装饰。

3. 产品规格：
- 类型：插画
- 格式：数字文件
- 分辨率：4K

4. 推荐标签：
- #原创 #插画 #星空 #设计

5. 参考售价：¥29.9 - ¥79.9"""

    result = svc._parse_result(raw, None, "插画")
    assert "星空" in result["title"]
    assert "插画" in result["description"]
    assert any("分辨率" in s for s in result["specs"])
    assert any("#原创" in t or "原创" in t for t in result["tags"])
    assert "¥" in result["price_range"]


def test_parse_ai_output_empty():
    svc = DescribeWorkService()
    result = svc._parse_result("", None, "音乐")
    assert "未知作品" in result["title"]
    assert "音乐" in result["description"]


def test_parse_ai_output_partial():
    svc = DescribeWorkService()
    raw = "这是一个测试描述，没有完整结构。"
    result = svc._parse_result(raw, None, "测试")
    assert result.get("description") is not None


def test_fallback_english():
    svc = DescribeWorkService()
    result = svc._fallback_description("Test Title", "Photography")
    assert "Photography" in result["title"]
    assert "¥" in result["price_range"]
