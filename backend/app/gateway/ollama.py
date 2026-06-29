"""Ollama 本地 LLM 适配器."""

import json
import httpx

from app.config import settings


class OllamaGateway:
    """Ollama 本地 LLM 网关 — 用于 AI 商品描述生成."""

    def __init__(self, base_url: str | None = None):
        self.base_url = base_url or settings.OLLAMA_BASE_URL or "http://localhost:11434"

    async def generate_description(
        self,
        work_title: str,
        work_type: str,
        category: str = "",
        language: str = "zh",
    ) -> str:
        """生成商品描述."""
        prompt = f"""你是一个创意产品描述专家。请为以下作品生成电商商品描述：

作品名称：{work_title}
作品类型：{work_type}
品类：{category or '创意作品'}

请用{language}输出，格式如下：
1. 产品标题（吸引眼球，20字以内）
2. 产品描述（100-150字，突出创意亮点）
3. 产品规格（3-5条）
4. 推荐标签（5-8个）
5. 参考售价建议"""

        try:
            async with httpx.AsyncClient(timeout=60) as client:
                resp = await client.post(
                    f"{self.base_url}/api/generate",
                    json={
                        "model": "qwen2.5:latest",
                        "prompt": prompt,
                        "stream": False,
                    },
                )
                resp.raise_for_status()
                data = resp.json()
                return data.get("response", "")
        except httpx.ConnectError:
            return self._fallback_description(work_title, work_type, language)
        except Exception as e:
            return f"[AI 生成失败: {e}]\n\n{self._fallback_description(work_title, work_type, language)}"

    async def generate_platform_description(
        self,
        system_prompt: str,
        user_prompt: str,
        style: str = "xiaohongshu",
    ) -> str:
        """生成特定平台风格的 AI 商品描述 (P1.6.1).

        Args:
            system_prompt: 平台风格的系统提示词
            user_prompt: 用户产品信息提示词
            style: 平台风格标识
        """
        full_prompt = f"""{system_prompt}

---
{user_prompt}

请直接输出描述内容，不要添加额外的说明或前缀。"""

        try:
            async with httpx.AsyncClient(timeout=60) as client:
                resp = await client.post(
                    f"{self.base_url}/api/generate",
                    json={
                        "model": "qwen2.5:latest",
                        "prompt": full_prompt,
                        "stream": False,
                    },
                )
                resp.raise_for_status()
                data = resp.json()
                result = data.get("response", "").strip()
                if result:
                    return f"[Ollama · {style}] {result}"
                return ""
        except httpx.ConnectError:
            return ""  # 返回空字符串表示需要回退
        except Exception as e:
            return f"[AI 生成失败: {e}]"

    def _fallback_description(self, work_title: str, work_type: str, language: str) -> str:
        """Ollama 不可用时的模板描述."""
        if language == "zh":
            return f"""[本地模板生成]

**产品标题**：原创{work_type}作品 - {work_title}

**产品描述**：
这是一款精心创作的{work_type}作品《{work_title}》，融合了独特的设计理念与精湛的创作技艺。作品展现了创作者的独特视角，适合收藏、装饰或赠送。

**产品规格**：
- 类型：{work_type}
- 格式：数字文件
- 风格：原创设计
- 用途：个人收藏 / 装饰 / 送礼

**推荐标签**：#原创 #创意 #{work_type} #设计 #艺术

**参考售价**：¥19.9 - ¥99.9"""
        return f"""[Template Generated]

**Title**: Original {work_type} — {work_title}

**Description**:
An original {work_type} artwork, crafted with unique vision and creativity. Perfect for collection, decoration, or gifting.

**Tags**: #original #creative #{work_type} #art #design

**Price**: $9.99 - $49.99"""

    async def generate_multilingual(
        self,
        work_title: str,
        work_type: str,
        languages: list[str] = ["zh", "en"],
    ) -> dict[str, str]:
        """多语言商品描述."""
        results = {}
        for lang in languages:
            results[lang] = await self.generate_description(
                work_title, work_type, language=lang,
            )
        return results
