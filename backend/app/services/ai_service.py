"""AI 生成服务 — LLM provider abstraction + prompt templates."""

import os
from typing import Optional

import httpx

AI_PROVIDER_DEFAULT = os.getenv("AI_PROVIDER", "openai")
AI_API_BASE_DEFAULT = os.getenv("AI_API_BASE", "https://api.openai.com/v1")
AI_MODEL_DEFAULT = os.getenv("AI_MODEL", "gpt-4o-mini")
AI_TIMEOUT_DEFAULT = int(os.getenv("AI_TIMEOUT", "30"))


class AIService:
    """AI generation service that wraps LLM API calls."""

    def __init__(self, db=None):
        self.db = db

    # ── internal ────────────────────────────────────────────────

    def _is_configured(self) -> bool:
        return bool(os.environ.get("AI_API_KEY", "").strip())

    async def _call_llm(
        self,
        messages: list[dict],
        response_format: dict = None,
    ) -> str:
        """Call the configured LLM provider (OpenAI-compatible API)."""
        api_key = os.environ.get("AI_API_KEY", "").strip()
        api_base = os.environ.get("AI_API_BASE", AI_API_BASE_DEFAULT).strip()
        model = os.environ.get("AI_MODEL", AI_MODEL_DEFAULT)
        timeout = int(os.environ.get("AI_TIMEOUT", AI_TIMEOUT_DEFAULT))

        if not api_key:
            raise RuntimeError("AI_API_KEY is not configured")

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": model,
            "messages": messages,
            "temperature": 0.7,
            "max_tokens": 2048,
        }
        if response_format:
            payload["response_format"] = response_format

        async with httpx.AsyncClient(timeout=timeout) as client:
            resp = await client.post(
                f"{api_base}/chat/completions",
                headers=headers,
                json=payload,
            )
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["message"]["content"].strip()

    # ── public APIs ─────────────────────────────────────────────

    async def auto_tag(self, work_id: str, content: str, file_type: str) -> dict:
        """Generate relevant tags for a work based on content/file metadata."""
        type_labels = {
            "illustration": "插画",
            "photography": "摄影",
            "video": "视频",
            "music": "音乐",
            "writer": "写作",
            "craftsman": "手工艺",
        }
        type_label = type_labels.get(file_type, file_type)

        prompt = (
            "你是专业的内容标签生成器。根据以下作品信息生成 5-10 个精准标签，"
            "标签应涵盖主题、风格、情感、用途等维度。只返回标签列表，用逗号分隔。\n\n"
            f"作品 ID: {work_id}\n"
            f"文件类型: {type_label} ({file_type})\n"
            f"作品内容: {content}\n\n"
            "标签格式示例: 标签1, 标签2, 标签3"
        )

        raw = await self._call_llm([{"role": "user", "content": prompt}])
        tags = [t.strip() for t in raw.replace("，", ",").split(",") if t.strip()]
        tags = tags[:10]
        return {"tags": tags, "confidence": 0.85}

    async def auto_description(
        self, work_id: str, title: str, tags: list[str], file_type: str
    ) -> str:
        """Generate a compelling description for the work."""
        type_labels = {
            "illustration": "插画作品",
            "photography": "摄影作品",
            "video": "视频作品",
            "music": "音乐作品",
            "writer": "文字作品",
            "craftsman": "手工艺品",
        }
        type_label = type_labels.get(file_type, file_type)

        tags_str = "、".join(tags) if tags else "无"

        prompt = (
            "你是专业的文案撰写师。请为以下{type_label}撰写一段吸引人的描述，"
            "100-200字，语言优美、富有感染力。\n\n"
            f"作品标题: {title}\n"
            f"作品标签: {tags_str}\n"
            f"作品类型: {file_type}\n\n"
            "请直接输出描述文本，不要包含标题或其他额外内容。"
        ).format(type_label=type_label)

        return await self._call_llm([{"role": "user", "content": prompt}])

    async def draft_article(self, prompt: str, tone: str = "professional", max_words: int = 2000) -> str:
        """AI-assisted article/book drafting."""
        tone_map = {
            "professional": "专业严谨",
            "casual": "轻松随意",
            "literary": "文艺抒情",
            "humorous": "幽默风趣",
        }
        tone_zh = tone_map.get(tone, "专业严谨")

        prompt_text = (
            f"你是一位专业的文章撰稿人。请使用{tone_zh}的文风"
            f"撰写一篇不超过{max_words}字的文章。\n\n"
            f"写作提示: {prompt}\n\n"
            "请输出完整的文章内容，包含标题和正文。"
        )
        return await self._call_llm([{"role": "user", "content": prompt_text}])

    async def draft_product_description(
        self,
        product_name: str,
        materials: list[str] = None,
        techniques: list[str] = None,
    ) -> str:
        """Generate product description for craftsman sellers."""
        materials_str = "、".join(materials) if materials else "未指定"
        techniques_str = "、".join(techniques) if techniques else "未指定"

        prompt = (
            "你是一位资深的手工艺品销售文案撰写师。"
            "请为以下手工艺品撰写一段精美的产品介绍，150-300字。\n\n"
            f"产品名称: {product_name}\n"
            f"材质: {materials_str}\n"
            f"工艺: {techniques_str}\n\n"
            "要求：突出手工价值、独特性和使用场景。"
        )
        return await self._call_llm([{"role": "user", "content": prompt}])

    async def draft_music_description(
        self, title: str, genre: str, mood: str, bpm: int
    ) -> str:
        """Generate music release description for musician creators."""
        prompt = (
            f"你是一位专业的音乐平台文案撰写师。\n\n"
            f"请为以下音乐作品撰写一段介绍，80-150字。\n\n"
            f"曲目名称: {title}\n"
            f"流派: {genre}\n"
            f"情绪: {mood}\n"
            f"BPM: {bpm}\n\n"
            "要求：描述音乐风格特点、适合场景、情绪氛围。"
        )
        return await self._call_llm([{"role": "user", "content": prompt}])

    async def moderate_content(self, text: str) -> dict:
        """Basic content moderation — delegate to LLM safety check."""
        prompt = (
            "请对以下文本进行安全检查，判断是否包含以下内容：暴力(violence)、色情(pornography)、"
            "仇恨(hate)、政治敏感(political)、广告(advertising)、垃圾(spam)。\n\n"
            "请以 JSON 格式返回结果，不要包含其他文字。\n"
            "格式: {\"safe\": true/false, \"categories\": {\"violence\": false, \"pornography\": false, "
            "\"hate\": false, \"political\": false, \"advertising\": false, \"spam\": false}, "
            "\"reason\": \"如果不安全的原因\"}\n\n"
            f"待检测文本:\n{text}\n"
            "如果文本完全干净，safe 设为 true，reason 设为空字符串。"
        )
        raw = await self._call_llm([{"role": "user", "content": prompt}])

        # Try to parse JSON from LLM response (may wrap in ```json ... ```)
        import json

        cleaned = raw.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.split("```")[1]
            if cleaned.startswith("json"):
                cleaned = cleaned[4:]
            cleaned = cleaned.strip()
            cleaned = cleaned.rstrip("`").strip()

        try:
            result = json.loads(cleaned)
        except json.JSONDecodeError:
            # If parsing fails, assume safe (best-effort)
            result = {"safe": True, "categories": {}, "reason": ""}

        return result

    @staticmethod
    def check_configured() -> dict:
        """Check if AI provider is configured."""
        return {
            "configured": bool(os.environ.get("AI_API_KEY", "").strip()),
            "provider": os.environ.get("AI_PROVIDER", AI_PROVIDER_DEFAULT),
        }
