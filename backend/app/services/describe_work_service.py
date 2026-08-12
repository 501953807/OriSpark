"""作品 AI 描述生成服务层."""

import json
import re

from sqlalchemy.orm import Session

from app.gateway.ollama import OllamaGateway
from app.models.work import Work, WorkTag


class DescribeWorkService:
    """作品 AI 描述生成服务."""

    async def describe_work(self, db: Session, work_id: str, options: dict = None) -> dict:
        work = db.query(Work).filter(Work.id == work_id).first()
        if not work:
            raise ValueError(f"作品不存在: {work_id}")

        work_type = work.creator_type or work.file_type or "创意作品"
        category = (work.custom_metadata or {}).get("category", "") if work.custom_metadata else ""
        language = (options or {}).get("language", "zh")

        gateway = OllamaGateway()
        raw_text = await gateway.generate_description(
            work_title=work.title,
            work_type=work_type,
            category=category,
            language=language,
        )

        return self._parse_result(raw_text, work, work_type)

    def _parse_result(self, raw_text: str, work: Work, work_type: str) -> dict:
        title = work.title if work else "未知作品"
        result = self._fallback_description(title, work_type)
        if raw_text and not raw_text.startswith("[AI 生成失败"):
            parsed = self._parse_ai_output(raw_text)
            if parsed:
                result.update(parsed)
        return result

    def _parse_ai_output(self, text: str) -> dict:
        result = {}
        lines = text.strip().split("\n")
        title_lines = []
        desc_lines = []
        spec_lines = []
        tag_lines = []
        price_lines = []
        section = None
        for line in lines:
            stripped = line.strip()
            if "标题" in stripped or "Title" in stripped:
                section = "title"
                m = re.search(r"[：:]\s*(.+)", stripped)
                if m:
                    result["title"] = m.group(1).strip()
                    continue
            elif "描述" in stripped or "Description" in stripped:
                section = "description"
                continue
            elif "规格" in stripped or "Specification" in stripped:
                section = "specs"
                continue
            elif "标签" in stripped or "Tags" in stripped:
                section = "tags"
                continue
            elif "价格" in stripped or "Price" in stripped:
                section = "price"
                continue
            elif stripped.startswith("1.") or stripped.startswith("2.") or stripped.startswith("3.") or stripped.startswith("4.") or stripped.startswith("5."):
                section = None
                continue
            if section == "title" and not result.get("title"):
                m = re.search(r"[：:]\s*(.+)", stripped)
                if m:
                    result["title"] = m.group(1).strip()
            elif section == "description":
                desc_lines.append(stripped)
            elif section == "specs":
                clean = re.sub(r"^[-•*]\s*", "", stripped)
                if clean:
                    spec_lines.append(clean)
            elif section == "tags":
                clean = re.sub(r"^[-•*]\s*", "", stripped)
                if clean:
                    tag_lines.append(clean)
            elif section == "price":
                price_lines.append(stripped)
        if desc_lines:
            result["description"] = "\n".join(desc_lines)[:500]
        if spec_lines:
            result["specs"] = spec_lines[:10]
        if tag_lines:
            tags = []
            for t in tag_lines:
                tags.extend(re.findall(r"#?([^\s#]+)", t))
            result["tags"] = list(dict.fromkeys(tags))[:15]
        if price_lines:
            result["price_range"] = price_lines[-1][:200]
        return result if result else {}

    @staticmethod
    def _fallback_description(title: str, work_type: str) -> dict:
        return {
            "title": f"原创{work_type}作品 - {title}",
            "description": f"这是一款精心创作的{work_type}作品《{title}》，融合了独特的设计理念与精湛的创作技艺。作品展现了创作者的独特视角，适合收藏、装饰或赠送。",
            "specs": [f"类型：{work_type}", "格式：数字文件", "风格：原创设计", "用途：个人收藏 / 装饰 / 送礼"],
            "tags": ["#原创", "#创意", f"#{work_type}", "#设计", "#艺术"],
            "price_range": "¥19.9 - ¥99.9",
        }
