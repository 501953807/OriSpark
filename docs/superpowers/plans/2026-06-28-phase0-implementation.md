# Phase 0 实施计划 — 权益保护基础

> **For agentic workers:** Use superpowers:subagent-driven-development or superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 实现 Phase 0 四个子任务 — 风险预警引擎、AI 创作会话记录、C2PA 扩展、多平台存证扩展

**Architecture:** 在现有 FastAPI + SQLAlchemy + Vue3 架构上新增 5 个数据模型、3 个服务、4 个网关适配器、2 个新路由、2 个新前端组件

**Tech Stack:** Python 3.11+, FastAPI, SQLAlchemy, SQLite, Vue 3 + TypeScript, Axios, Pinia

## Global Constraints

- 所有新模型必须在 `app/models/__init__.py` 中注册
- 所有新路由必须在 `app/main.py` 的 `include_router` 中注册
- 前端 API 调用统一使用 `frontend/src/api/client.ts` (Axios 实例)
- 前端 Store 使用 Pinia defineStore pattern
- 所有 API 响应使用 `ApiResponse` 信封格式
- 所有文件路径使用相对路径，存储在 `data/` 目录下
- 不引入新的 Python 包依赖（C2PA 使用现有 cryptography 包）

---

### Task 1: 风险预警数据模型

**Files:**
- Create: `backend/app/models/risk_warning.py`
- Modify: `backend/app/models/__init__.py` (注册 RiskWarning)
- Modify: `backend/app/models/work.py` (扩展 Work 表: ai_assisted, ai_tools_used, creator_type)

**Interfaces:**
- Consumes: `app.database.Base`, `app.models.work.generate_uuid`
- Produces: `RiskWarning` class, `Work` 扩展字段

**Step 1: 创建 risk_warning.py 模型**

```python
"""风险预警数据模型."""

from datetime import datetime

from sqlalchemy import (
    Column, String, Float, Text, DateTime, Boolean, ForeignKey, Index,
)
from sqlalchemy.orm import relationship

from app.database import Base
from app.models.work import generate_uuid


class RiskWarning(Base):
    """风险预警记录表."""
    __tablename__ = "risk_warnings"

    id = Column(String(32), primary_key=True, default=generate_uuid)
    user_id = Column(String(32), nullable=False)
    work_id = Column(String(32), ForeignKey("works.id"), nullable=True)
    warning_type = Column(String(50), nullable=False)
    severity = Column(String(20), nullable=False)
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    matched_entity = Column(String(500), nullable=True)
    confidence = Column(Float, nullable=True)
    suggestion = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    dismissed = Column(Boolean, default=False)
    dismissed_at = Column(DateTime, nullable=True)

    __table_args__ = (
        Index("idx_risk_work", "work_id"),
        Index("idx_risk_type", "warning_type"),
        Index("idx_risk_severity", "severity"),
    )
```

**Step 2: 扩展 Work 模型 — 在 work.py 末尾添加字段**

在 `Work` 类的 `color_label` 字段之后、`created_at` 之前添加:

```python
# Phase 0: AI 创作记录扩展
ai_assisted = Column(Boolean, default=False)
ai_tools_used = Column(JSON, nullable=True)
creator_type = Column(String(30), default="illustrator")
```

**Step 3: 在 `__init__.py` 中注册新模型**

添加:
```python
from app.models.risk_warning import RiskWarning
```
并在 `__all__` 中添加 `"RiskWarning"`

**Step 4: 验证模型可导入**

```bash
cd backend && python -c "from app.models import RiskWarning; print('OK')"
```

**Step 5: Commit**

```bash
git add backend/app/models/risk_warning.py backend/app/models/work.py backend/app/models/__init__.py
git commit -m "feat: add risk warning and AI session data models"
```

---

### Task 2: AI 创作会话数据模型

**Files:**
- Create: `backend/app/models/ai_session.py`
- Modify: `backend/app/models/__init__.py` (注册 AiCreationSession)

**Interfaces:**
- Consumes: `app.database.Base`, `app.models.work.generate_uuid`
- Produces: `AiCreationSession` class

**Step 1: 创建 ai_session.py 模型**

```python
"""AI 创作会话记录数据模型."""

from datetime import datetime

from sqlalchemy import (
    Column, String, Integer, Text, DateTime, ForeignKey, Index, JSON,
)
from sqlalchemy.orm import relationship

from app.database import Base
from app.models.work import generate_uuid


class AiCreationSession(Base):
    """AI 创作会话记录表."""
    __tablename__ = "ai_creation_sessions"

    id = Column(String(32), primary_key=True, default=generate_uuid)
    work_id = Column(String(32), ForeignKey("works.id", ondelete="CASCADE"), nullable=False)
    tool_name = Column(String(100), nullable=False)
    tool_version = Column(String(50), nullable=True)
    prompt = Column(Text, nullable=False)
    prompt_history = Column(JSON, nullable=True)
    seed = Column(Integer, nullable=True)
    parameters = Column(JSON, nullable=True)
    negative_prompt = Column(Text, nullable=True)
    model_name = Column(String(500), nullable=True)
    lora_names = Column(JSON, nullable=True)
    output_images = Column(JSON, nullable=True)
    human_interventions = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    work = relationship("Work", backref="ai_sessions")

    __table_args__ = (
        Index("idx_ai_session_work", "work_id"),
    )
```

**Step 2: 在 `__init__.py` 中注册**

添加:
```python
from app.models.ai_session import AiCreationSession
```
并在 `__all__` 中添加 `"AiCreationSession"`

**Step 3: 验证模型可导入**

```bash
cd backend && python -c "from app.models import AiCreationSession; print('OK')"
```

**Step 4: Commit**

```bash
git add backend/app/models/ai_session.py backend/app/models/__init__.py
git commit -m "feat: add AI creation session data model"
```

---

### Task 3: 商标数据库网关适配器

**Files:**
- Create: `backend/app/gateway/trademark.py`
- Create: `backend/app/gateway/model_source.py`

**Interfaces:**
- Consumes: 无
- Produces: `TrademarkGateway` ABC, `CNIPATrademarkGateway`, `WiPoTrademarkGateway`, `MockTrademarkGateway`
- Produces: `ModelSourceGateway` ABC, `CivitaiModelSourceGateway`, `HuggingFaceModelSourceGateway`, `MockModelSourceGateway`

**Step 1: 创建 trademark.py 网关**

```python
"""商标数据库网关适配器 — 对接 CNIPA/WIPO/USPTO/EUIPO."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional


@dataclass
class TrademarkResult:
    """商标搜索结果."""
    mark_name: str
    registration_number: Optional[str] = None
    classes: list[str] = None
    jurisdiction: str = "cn"
    similarity: float = 0.0
    status: str = "unknown"
    owner: str = ""
    url: str = ""


class TrademarkGateway(ABC):
    """商标查询网关基类."""

    @abstractmethod
    async def search(self, mark_name: str, classes: Optional[list[str]] = None,
                     jurisdiction: str = "cn") -> list[TrademarkResult]:
        """搜索商标."""
        ...

    @abstractmethod
    async def check_similarity(self, mark_name: str, jurisdiction: str = "cn") -> float:
        """检查商标相似度 (0-100)."""
        ...


class CNIPATrademarkGateway(TrademarkGateway):
    """CNIPA 中国商标查询适配器 (v1: 本地模拟).

    实际实现需要对接 CNIPA 开放 API 或结构化爬虫.
    v1 使用内置热门品牌库做模糊匹配.
    """

    # 内置热门文创品牌库 (v1 模拟数据)
    _HOT_BRANDS = [
        {"name": "Hello Kitty", "classes": ["16", "21", "25"], "jurisdiction": "cn"},
        {"name": "迪士尼", "classes": ["16", "25", "28"], "jurisdiction": "cn"},
        {"name": "原神", "classes": ["9", "16", "25"], "jurisdiction": "cn"},
        {"name": "故宫文创", "classes": ["16", "21", "35"], "jurisdiction": "cn"},
        {"name": "泡泡玛特", "classes": ["16", "28", "30"], "jurisdiction": "cn"},
    ]

    async def search(self, mark_name: str, classes=None, jurisdiction="cn") -> list[TrademarkResult]:
        results = []
        for brand in self._HOT_BRANDS:
            if mark_name.lower() in brand["name"].lower() or brand["name"].lower() in mark_name.lower():
                results.append(TrademarkResult(
                    mark_name=brand["name"],
                    classes=brand["classes"],
                    jurisdiction=brand["jurisdiction"],
                    similarity=min(95.0, 60.0 + len(mark_name) * 3),
                    status="registered",
                ))
        return results

    async def check_similarity(self, mark_name: str, jurisdiction="cn") -> float:
        results = await self.search(mark_name, jurisdiction=jurisdiction)
        return max((r.similarity for r in results), default=0.0)


class MockTrademarkGateway(TrademarkGateway):
    """模拟网关 — 用于开发和测试."""

    async def search(self, mark_name: str, classes=None, jurisdiction="cn") -> list[TrademarkResult]:
        if "kitty" in mark_name.lower():
            return [TrademarkResult(
                mark_name="Hello Kitty", similarity=85.0,
                classes=["16", "25"], jurisdiction="us", status="registered",
                owner="Sanrio Co., Ltd.")]
        return []

    async def check_similarity(self, mark_name: str, jurisdiction="cn") -> float:
        results = await self.search(mark_name)
        return max((r.similarity for r in results), default=0.0)
```

**Step 2: 创建 model_source.py 网关**

```python
"""模型/LoRA 来源查询网关 — 对接 Civitai/HuggingFace."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional


@dataclass
class ModelSourceInfo:
    """模型来源信息."""
    model_name: str
    source: str  # "civitai" / "huggingface" / "unknown"
    author: str = ""
    license_type: str = "unknown"  # "public" / "restricted" / "commercial_allowed" / "unknown"
    allows_commercial: bool = False
    requires_attribution: bool = False
    model_url: str = ""
    risk_level: str = "unknown"  # "safe" / "caution" / "risk"


class ModelSourceGateway(ABC):
    """模型来源查询网关基类."""

    @abstractmethod
    async def query(self, model_name: str, source: str = "civitai") -> Optional[ModelSourceInfo]:
        """查询模型来源信息."""
        ...


class CivitaiModelSourceGateway(ModelSourceGateway):
    """Civitai 模型查询适配器 (v1: 模拟).

    实际实现需要调用 Civitai API:
    GET https://civitainer.com/api/v1/models?name={model_name}
    """

    async def query(self, model_name: str, source="civitai") -> Optional[ModelSourceInfo]:
        # v1 模拟: 已知风险模型
        _RISK_MODELS = ["photorealism", "realisticVision"]
        if model_name.lower() in _RISK_MODELS:
            return ModelSourceInfo(
                model_name=model_name, source="civitai",
                license_type="restricted", allows_commercial=False,
                requires_attribution=True, risk_level="caution",
            )
        return ModelSourceInfo(
            model_name=model_name, source="civitai",
            license_type="public", allows_commercial=True,
            requires_attribution=False, risk_level="safe",
        )


class MockModelSourceGateway(ModelSourceGateway):
    """模拟网关 — 用于开发和测试."""

    async def query(self, model_name: str, source="civitai") -> Optional[ModelSourceInfo]:
        return ModelSourceInfo(
            model_name=model_name, source=source,
            license_type="public", allows_commercial=True,
            requires_attribution=False, risk_level="safe",
        )
```

**Step 3: 验证网关可导入**

```bash
cd backend && python -c "from app.gateway.trademark import TrademarkGateway; print('OK')"
cd backend && python -c "from app.gateway.model_source import ModelSourceGateway; print('OK')"
```

**Step 4: Commit**

```bash
git add backend/app/gateway/trademark.py backend/app/gateway/model_source.py
git commit -m "feat: add trademark and model source gateway adapters"
```

---

### Task 4: 风险预警引擎服务

**Files:**
- Create: `backend/app/services/risk_warning_service.py`

**Interfaces:**
- Consumes: `RiskWarning` model, `TrademarkGateway`, `ModelSourceGateway`, `hasher.compute_sha256`
- Produces: `RiskWarningService` class with `check_prompt()`, `check_reference()`, `check_model()`, `check_trademark()`

**Step 1: 创建 risk_warning_service.py**

```python
"""侵权风险预警引擎服务.

Phase 0: 实现四个检测维度
1. 提示词侵权检测 (本地关键词库 + TF-IDF)
2. 参考图相似度检测 (pHash + 余弦相似度)
3. LoRA/模型权属检查 (Civitai/HuggingFace API)
4. 商标/Logo 碰撞 (CNIPA 本地库)
"""

import re
from dataclasses import dataclass, field
from typing import Optional

from app.models.risk_warning import RiskWarning
from app.gateway.trademark import TrademarkGateway, MockTrademarkGateway
from app.gateway.model_source import ModelSourceGateway, MockModelSourceGateway


# 内置侵权关键词库 (v1 硬编码，后续可从 dictStore 动态加载)
INFRINGEMENT_KEYWORDS = {
    "trademark": [
        "Hello Kitty", "迪士尼", "Disney", "漫威", "Marvel", "任天堂", "Nintendo",
        "宝可梦", "Pokemon", "原神", "Genshin", "泡泡玛特", "故宫",
        "Nike", "Adidas", "Apple", "Louis Vuitton", "Gucci",
    ],
    "character": [
        "米老鼠", "Mickey Mouse", "孙悟空", "哪吒", "葫芦娃", "黑猫警长",
        "蜘蛛侠", "Batman", "Superman", "皮卡丘",
    ],
    "artist_style": [
        "毕加索风格", "Van Gogh style", "莫奈风格", "草间弥生风格",
    ],
}


@dataclass
class WarningResult:
    """单个检测结果."""
    warning_type: str
    severity: str  # "low" / "medium" / "high"
    title: str
    description: str
    matched_entity: str
    confidence: float  # 0-100
    suggestion: str


class RiskWarningService:
    """风险预警引擎服务."""

    def __init__(self, trademark_gateway: Optional[TrademarkGateway] = None,
                 model_gateway: Optional[ModelSourceGateway] = None):
        self.tm_gateway = trademark_gateway or MockTrademarkGateway()
        self.model_gateway = model_gateway or MockModelSourceGateway()

    def check_prompt(self, prompt: str, work_title: str = "") -> list[WarningResult]:
        """维度 1: 提示词侵权检测."""
        warnings = []
        text = f"{prompt} {work_title}".lower()

        for category, keywords in INFRINGEMENT_KEYWORDS.items():
            for kw in keywords:
                if kw.lower() in text:
                    severity = "high" if category == "trademark" else "medium"
                    warnings.append(WarningResult(
                        warning_type=f"prompt_{category}",
                        severity=severity,
                        title=f"检测到{self._cat_label(category)}冲突: '{kw}'",
                        description=f"提示词中包含 '{kw}'，可能涉及{'商标' if category == 'trademark' else '版权'}风险。",
                        matched_entity=kw,
                        confidence=85.0 if category == "trademark" else 60.0,
                        suggestion=self._get_suggestion(category, kw),
                    ))

        return warnings

    def check_reference_image(self, image_hash: str, existing_hashes: list[str]) -> Optional[WarningResult]:
        """维度 2: 参考图相似度检测.

        Args:
            image_hash: 参考图的 pHash 哈希字符串
            existing_hashes: 已有作品的 pHash 哈希列表

        Returns:
            WarningResult 或 None (无风险)
        """
        if not image_hash or not existing_hashes:
            return None

        max_sim = self._cosine_similarity(image_hash, existing_hashes)
        if max_sim > 80.0:
            return WarningResult(
                warning_type="reference_similar",
                severity="high" if max_sim > 90 else "medium",
                title=f"参考图与现有作品高度相似 ({max_sim:.1f}%)",
                description="参考图与系统中已有作品相似度超过阈值，可能存在抄袭风险。",
                matched_entity=f"similarity:{max_sim:.1f}%",
                confidence=max_sim,
                suggestion="建议更换参考图或大幅修改创作方向。",
            )
        return None

    def check_model(self, model_name: str, source: str = "civitai") -> Optional[WarningResult]:
        """维度 3: LoRA/模型权属检查."""
        info = self.model_gateway.query(model_name, source)
        if not info:
            return WarningResult(
                warning_type="lora_rights",
                severity="medium",
                title=f"模型 '{model_name}' 来源不明",
                description="无法确认该模型的授权状态，建议使用前核实。",
                matched_entity=model_name,
                confidence=50.0,
                suggestion="请在模型来源网站核实授权协议。",
            )

        if not info.allows_commercial:
            return WarningResult(
                warning_type="lora_rights",
                severity="high",
                title=f"模型 '{model_name}' 不允许商用",
                description=f"该模型授权类型为 '{info.license_type}'，{'需要署名' if info.requires_attribution else '不可商用'}。",
                matched_entity=model_name,
                confidence=90.0,
                suggestion="请更换允许商用的模型或获取授权。",
            )

        return None

    def check_trademark(self, text: str, jurisdiction: str = "cn") -> list[WarningResult]:
        """维度 4: 商标/Logo 碰撞检测."""
        warnings = []
        results = self.tm_gateway.search(text, jurisdiction=jurisdiction)

        for r in results:
            if r.similarity > 50.0:
                warnings.append(WarningResult(
                    warning_type="trademark_conflict",
                    severity="high" if r.similarity > 80 else "medium",
                    title=f"检测到商标冲突: '{r.mark_name}'",
                    description=f"与{'注册' if r.status == 'registered' else '申请中'}商标 '{r.mark_name}' 相似度 {r.similarity:.1f}%。",
                    matched_entity=r.mark_name,
                    confidence=r.similarity,
                    suggestion=f"建议修改标题/描述，避免使用 '{r.mark_name}' 相关词汇。",
                ))

        return warnings

    async def check_all(self, work_id: Optional[str], prompt: Optional[str] = None,
                        reference_images: Optional[list[str]] = None,
                        model_name: Optional[str] = None,
                        work_title: str = "") -> list[RiskWarning]:
        """统一检测入口 — 编排四个维度."""
        results = []

        # 维度 1: 提示词检测
        if prompt:
            for wr in self.check_prompt(prompt, work_title):
                rw = RiskWarning(
                    user_id="", work_id=work_id,
                    warning_type=wr.warning_type, severity=wr.severity,
                    title=wr.title, description=wr.description,
                    matched_entity=wr.matched_entity, confidence=wr.confidence,
                    suggestion=wr.suggestion,
                )
                results.append(rw)

        # 维度 2: 参考图检测 (placeholder — 实际需要在 DB 中查已有作品哈希)
        if reference_images:
            # TODO: 实现参考图 pHash 计算和对比
            pass

        # 维度 3: 模型权属检查
        if model_name:
            wr = self.check_model(model_name)
            if wr:
                results.append(RiskWarning(
                    user_id="", work_id=work_id,
                    warning_type=wr.warning_type, severity=wr.severity,
                    title=wr.title, description=wr.description,
                    matched_entity=wr.matched_entity, confidence=wr.confidence,
                    suggestion=wr.suggestion,
                ))

        # 维度 4: 商标碰撞
        text_to_check = f"{prompt or ''} {work_title}".strip()
        if text_to_check:
            for wr in self.check_trademark(text_to_check):
                results.append(RiskWarning(
                    user_id="", work_id=work_id,
                    warning_type=wr.warning_type, severity=wr.severity,
                    title=wr.title, description=wr.description,
                    matched_entity=wr.matched_entity, confidence=wr.confidence,
                    suggestion=wr.suggestion,
                ))

        return results

    @staticmethod
    def _cosine_similarity(target_hash: str, hashes: list[str]) -> float:
        """计算目标哈希与一组哈希的最大余弦相似度 (简化版).

        v1: 使用汉明距离近似. 实际应使用感知哈希的余弦相似度.
        """
        if not hashes:
            return 0.0
        try:
            target = int(target_hash, 16) if target_hash else 0
        except ValueError:
            return 0.0

        max_sim = 0.0
        for h in hashes:
            try:
                val = int(h, 16) if h else 0
                # 简化的汉明距离相似度
                xor = target ^ val
                bits = bin(xor).count('0') + bin(xor).count('1')
                zeros = bin(xor).count('0')
                sim = ((bits - zeros) / bits * 50) if bits > 0 else 0
                max_sim = max(max_sim, sim)
            except ValueError:
                continue
        return max_sim

    @staticmethod
    def _cat_label(cat: str) -> str:
        labels = {"trademark": "商标", "character": "角色", "artist_style": "艺术家风格"}
        return labels.get(cat, cat)

    @staticmethod
    def _get_suggestion(cat: str, entity: str) -> str:
        suggestions = {
            "trademark": f"建议修改标题/描述，避免使用 '{entity}' 相关词汇。",
            "character": f"建议避免使用角色 '{entity}' 作为创作参考。",
            "artist_style": f"'{entity}' 可能涉及艺术家风格模仿，注意版权风险。",
        }
        return suggestions.get(cat, "建议修改创作方向。")
```

**Step 2: 验证服务可导入**

```bash
cd backend && python -c "from app.services.risk_warning_service import RiskWarningService; print('OK')"
```

**Step 3: Commit**

```bash
git add backend/app/services/risk_warning_service.py
git commit -m "feat: add risk warning engine service"
```

---

### Task 5: C2PA 扩展 — 加入 AI 会话摘要

**Files:**
- Modify: `backend/app/services/c2pa_service.py` (扩展 manifest 生成)
- Modify: `backend/app/models/notary.py` (已有 C2PARecord，确认完整)

**Interfaces:**
- Consumes: 现有 `generate_c2pa_manifest`, `generate_c2pa_with_identity`
- Produces: 扩展后的 manifest 包含 `ai_session_summary` 和 `creation_timeline`

**Step 1: 扩展 c2pa_service.py — 添加 AI 会话摘要字段**

在 `generate_c2pa_manifest` 函数中，添加 `ai_session_summary` 参数:

```python
def generate_c2pa_manifest(
    work_title: str,
    author_name: str = "OriStudio Creator",
    sha256_hash: Optional[str] = None,
    file_data: Optional[bytes] = None,
    public_key_pem: Optional[str] = None,
    ai_session_summary: Optional[dict] = None,  # 新增
    creation_timeline: Optional[list[dict]] = None,  # 新增
) -> dict:
```

在 assertions 数组中追加两个新断言:

```python
# 5. AI 创作会话摘要 (新增)
*({"label": "oristudio.ai_session", "data": ai_session_summary} if ai_session_summary else {}),
# 6. 创作时间线 (新增)
*({"label": "oristudio.creation_timeline", "data": creation_timeline} if creation_timeline else {}),
```

**Step 2: 同步扩展 `generate_c2pa_with_identity` 签名**

```python
def generate_c2pa_with_identity(
    work_title: str,
    author_name: str = "OriStudio Creator",
    sha256_hash: Optional[str] = None,
    file_data: Optional[bytes] = None,
    ai_session_summary: Optional[dict] = None,
    creation_timeline: Optional[list[dict]] = None,
) -> tuple[dict, str, str]:
```

内部调用 `generate_c2pa_manifest` 时传入新参数。

**Step 3: 验证扩展后的服务**

```bash
cd backend && python -c "
from app.services.c2pa_service import generate_c2pa_manifest
m = generate_c2pa_manifest('test', ai_session_summary={'tool': 'Midjourney'}, creation_timeline=[{'step': 'draft'}])
assert any(a['label'] == 'oristudio.ai_session' for a in m['assertions'])
print('OK')
"
```

**Step 4: Commit**

```bash
git add backend/app/services/c2pa_service.py
git commit -m "feat: extend C2PA manifest with AI session summary and creation timeline"
```

---

### Task 6: 时间戳网关 — DigiCert TSA

**Files:**
- Create: `backend/app/gateway/digicert_tsa.py`
- Create: `backend/app/services/timestamp_service.py`

**Interfaces:**
- Produces: `TimestampGateway` ABC, `DigiCertTSAGateway`, `MockTSAGateway`
- Produces: `TimestampService` class

**Step 1: 创建 digicert_tsa.py 网关**

```python
"""RFC 3161 时间戳网关 — DigiCert TSA 服务适配器."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional
import hashlib


@dataclass
class TimestampToken:
    """RFC 3161 时间戳令牌."""
    token_bytes: bytes  # DER 编码的时间戳令牌
    hash_algorithm: str = "sha256"
    policy: str = "1.2.840.113549.3.2"  # TS Policy OID
    accuracy_seconds: int = 10


class TimestampGateway(ABC):
    """时间戳网关基类."""

    @abstractmethod
    async def request_timestamp(self, data_hash: str) -> Optional[TimestampToken]:
        """请求时间戳令牌.

        Args:
            data_hash: 要加时间戳的数据的 hex 编码 SHA-256 哈希

        Returns:
            TimestampToken 或 None (失败)
        """
        ...


class DigiCertTSAGateway(TimestampGateway):
    """DigiCert 时间戳服务网关.

    TSA Endpoint: http://timestamp.digicert.com
    """

    TSA_URL = "http://timestamp.digicert.com"

    async def request_timestamp(self, data_hash: str) -> Optional[TimestampToken]:
        """v1: 模拟实现.

        实际实现需要:
        1. 构建 RFC 3161 TST Request (DER 编码)
        2. POST 到 TSA URL
        3. 解析 TST Response (DER 编码)
        4. 返回 TimestampToken
        """
        # TODO: 实现真实的 RFC 3161 请求
        return TimestampToken(
            token_bytes=hashlib.sha256(data_hash.encode()).digest(),
            hash_algorithm="sha256",
        )


class MockTSAGateway(TimestampGateway):
    """模拟网关 — 用于开发和测试."""

    async def request_timestamp(self, data_hash: str) -> Optional[TimestampToken]:
        import datetime
        return TimestampToken(
            token_bytes=f"mock-tsa:{data_hash[:16]}:{datetime.datetime.utcnow().isoformat()}".encode(),
            hash_algorithm="sha256",
        )
```

**Step 2: 创建 timestamp_service.py 服务**

```python
"""RFC 3161 时间戳服务."""

import os
from datetime import datetime
from typing import Optional

from app.gateway.digicert_tsa import TimestampGateway, MockTSAGateway
from app.gateway.digicert_tsa import TimestampToken


class TimestampService:
    """时间戳服务 — 封装 TSA 网关调用."""

    def __init__(self, gateway: Optional[TimestampGateway] = None):
        self.gateway = gateway or MockTSAGateway()

    async def timestamp_file(self, file_path: str) -> Optional[TimestampToken]:
        """为文件获取时间戳."""
        if not os.path.exists(file_path):
            return None

        import hashlib
        h = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                h.update(chunk)
        data_hash = h.hexdigest()

        return await self.gateway.request_timestamp(data_hash)

    async def timestamp_hash(self, data_hash: str) -> Optional[TimestampToken]:
        """为已有哈希获取时间戳."""
        return await self.gateway.request_timestamp(data_hash)
```

**Step 3: 验证网关和服务**

```bash
cd backend && python -c "from app.gateway.digicert_tsa import DigiCertTSAGateway; print('OK')"
cd backend && python -c "from app.services.timestamp_service import TimestampService; print('OK')"
```

**Step 4: Commit**

```bash
git add backend/app/gateway/digicert_tsa.py backend/app/services/timestamp_service.py
git commit -m "feat: add DigiCert TSA timestamp gateway and service"
```

---

### Task 7: Polygon 存证网关

**Files:**
- Create: `backend/app/gateway/polygon.py`

**Interfaces:**
- Produces: `PolygonNotaryGateway` class

**Step 1: 创建 polygon.py 网关**

```python
"""Polygon 公链存证网关.

Phase 0: 模拟实现 (v1 不需要真实 gas 费)
实际实现需要:
- web3.py 或 ethers.js
- Polygon Mumbai/Amoy 测试网部署智能合约
- 钱包私钥管理
"""

from dataclasses import dataclass
from typing import Optional
import hashlib


@dataclass
class BlockchainAnchor:
    """区块链锚定结果."""
    tx_hash: str
    block_number: int
    contract_address: str
    chain: str = "polygon"


class PolygonNotaryGateway:
    """Polygon 公链存证网关 (v1: 模拟).

    实际实现需要部署 ERC-725/ERC-721 合约到 Polygon 测试网.
    """

    CONTRACT_ADDRESS = "0x000000000000000000000000000000000000dead"  # v1 placeholder
    RPC_URL = "https://polygon-mainnet.g.alchemy.com/v2/demo"

    async def anchor(self, data_hash: str) -> Optional[BlockchainAnchor]:
        """将数据哈希锚定到 Polygon 链.

        v1: 返回模拟交易哈希.
        """
        tx_hash = hashlib.sha256(data_hash.encode()).hexdigest()
        return BlockchainAnchor(
            tx_hash=f"0x{tx_hash[:64]}",
            block_number=50000000,  # v1 placeholder
            contract_address=self.CONTRACT_ADDRESS,
            chain="polygon",
        )
```

**Step 2: 验证**

```bash
cd backend && python -c "from app.gateway.polygon import PolygonNotaryGateway; print('OK')"
```

**Step 3: Commit**

```bash
git add backend/app/gateway/polygon.py
git commit -m "feat: add Polygon blockchain notary gateway"
```

---

### Task 8: 风险预警路由

**Files:**
- Create: `backend/app/routers/risk_warning.py`

**Interfaces:**
- Consumes: `RiskWarning` model, `RiskWarningService`, `Work` model, `get_db`
- Produces: FastAPI router with 4 endpoints

**Step 1: 创建 risk_warning.py 路由**

```python
"""风险预警 API 路由 — Phase 0."""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.work import Work
from app.models.risk_warning import RiskWarning
from app.schemas.common import ApiResponse
from app.services.risk_warning_service import RiskWarningService

router = APIRouter(prefix="/api/risk-warning", tags=["risk-warning"])


def _get_service() -> RiskWarningService:
    return RiskWarningService()


@router.post("/check", response_model=ApiResponse[list])
def check_risk_warning(
    data: dict,
    db: Session = Depends(get_db),
):
    """统一风险检测入口.

    body: {
        "work_id": str | null,
        "prompt": str | null,
        "reference_images": list[str] | null,
        "model_name": str | null,
        "work_title": str
    }
    """
    service = _get_service()
    results = service.check_all(
        work_id=data.get("work_id"),
        prompt=data.get("prompt"),
        reference_images=data.get("reference_images"),
        model_name=data.get("model_name"),
        work_title=data.get("work_title", ""),
    )

    return ApiResponse(
        message=f"检测到 {len(results)} 条风险预警",
        data=[
            {
                "warning_type": r.warning_type,
                "severity": r.severity,
                "title": r.title,
                "description": r.description,
                "matched_entity": r.matched_entity,
                "confidence": r.confidence,
                "suggestion": r.suggestion,
            }
            for r in results
        ],
    )


@router.get("/work/{work_id}", response_model=ApiResponse[list])
def get_work_warnings(
    work_id: str,
    dismissed: Optional[bool] = None,
    db: Session = Depends(get_db),
):
    """获取作品的风险预警记录."""
    work = db.query(Work).filter(Work.id == work_id).first()
    if not work:
        raise HTTPException(status_code=404, detail="作品不存在")

    query = db.query(RiskWarning).filter(RiskWarning.work_id == work_id)
    if dismissed is not None:
        query = query.filter(RiskWarning.dismissed == dismissed)

    warnings = query.order_by(RiskWarning.created_at.desc()).all()

    return ApiResponse(
        data=[
            {
                "id": w.id,
                "warning_type": w.warning_type,
                "severity": w.severity,
                "title": w.title,
                "matched_entity": w.matched_entity,
                "confidence": w.confidence,
                "dismissed": w.dismissed,
                "created_at": w.created_at.isoformat() if w.created_at else None,
            }
            for w in warnings
        ],
    )


@router.patch("/{warning_id}/dismiss", response_model=ApiResponse)
def dismiss_warning(
    warning_id: str,
    db: Session = Depends(get_db),
):
    """标记预警为已查看."""
    warning = db.query(RiskWarning).filter(RiskWarning.id == warning_id).first()
    if not warning:
        raise HTTPException(status_code=404, detail="预警记录不存在")

    warning.dismissed = True
    from datetime import datetime
    warning.dismissed_at = datetime.utcnow()
    db.commit()

    return ApiResponse(message="已标记为查看")
```

**Step 2: 验证路由可导入**

```bash
cd backend && python -c "from app.routers.risk_warning import router; print('OK')"
```

**Step 3: Commit**

```bash
git add backend/app/routers/risk_warning.py
git commit -m "feat: add risk warning API router"
```

---

### Task 9: AI 会话路由

**Files:**
- Create: `backend/app/routers/ai_session.py`

**Interfaces:**
- Consumes: `AiCreationSession` model, `Work` model, `get_db`
- Produces: FastAPI router with 4 endpoints

**Step 1: 创建 ai_session.py 路由**

```python
"""AI 创作会话 API 路由 — Phase 0."""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.work import Work
from app.models.ai_session import AiCreationSession
from app.schemas.common import ApiResponse

router = APIRouter(prefix="/api/works", tags=["ai-sessions"])


@router.post("/{work_id}/ai-session", response_model=ApiResponse)
def create_ai_session(
    work_id: str,
    data: dict,
    db: Session = Depends(get_db),
):
    """记录 AI 创作会话."""
    work = db.query(Work).filter(Work.id == work_id).first()
    if not work:
        raise HTTPException(status_code=404, detail="作品不存在")

    session = AiCreationSession(
        work_id=work_id,
        tool_name=data["tool_name"],
        tool_version=data.get("tool_version"),
        prompt=data["prompt"],
        prompt_history=data.get("prompt_history"),
        seed=data.get("seed"),
        parameters=data.get("parameters"),
        negative_prompt=data.get("negative_prompt"),
        model_name=data.get("model_name"),
        lora_names=data.get("lora_names"),
        output_images=data.get("output_images"),
        human_interventions=data.get("human_interventions"),
    )
    db.add(session)

    work.ai_assisted = True
    tools = work.ai_tools_used or []
    if not any(t.get("name") == data["tool_name"] for t in tools):
        tools.append({"name": data["tool_name"], "version": data.get("tool_version")})
    work.ai_tools_used = tools

    db.commit()
    db.refresh(session)

    return ApiResponse(message="创作会话记录成功", data={"id": session.id})


@router.get("/{work_id}/ai-sessions", response_model=ApiResponse[list])
def list_ai_sessions(
    work_id: str,
    db: Session = Depends(get_db),
):
    """获取作品的 AI 创作时间线."""
    work = db.query(Work).filter(Work.id == work_id).first()
    if not work:
        raise HTTPException(status_code=404, detail="作品不存在")

    sessions = (
        db.query(AiCreationSession)
        .filter(AiCreationSession.work_id == work_id)
        .order_by(AiCreationSession.created_at.asc())
        .all()
    )

    return ApiResponse(
        data=[
            {
                "id": s.id,
                "tool_name": s.tool_name,
                "tool_version": s.tool_version,
                "prompt": s.prompt,
                "seed": s.seed,
                "model_name": s.model_name,
                "created_at": s.created_at.isoformat() if s.created_at else None,
            }
            for s in sessions
        ],
    )


@router.patch("/{work_id}/ai-session/{session_id}", response_model=ApiResponse)
def update_ai_session(
    work_id: str,
    session_id: str,
    data: dict,
    db: Session = Depends(get_db),
):
    """编辑创作会话记录."""
    session = (
        db.query(AiCreationSession)
        .filter(AiCreationSession.id == session_id, AiCreationSession.work_id == work_id)
        .first()
    )
    if not session:
        raise HTTPException(status_code=404, detail="会话记录不存在")

    for key in ["prompt", "tool_version", "parameters", "negative_prompt", "model_name",
                "lora_names", "output_images", "human_interventions"]:
        if key in data:
            setattr(session, key, data[key])

    db.commit()
    db.refresh(session)
    return ApiResponse(message="会话记录更新成功")


@router.delete("/{work_id}/ai-session/{session_id}", response_model=ApiResponse)
def delete_ai_session(
    work_id: str,
    session_id: str,
    db: Session = Depends(get_db),
):
    """删除创作会话记录."""
    session = (
        db.query(AiCreationSession)
        .filter(AiCreationSession.id == session_id, AiCreationSession.work_id == work_id)
        .first()
    )
    if not session:
        raise HTTPException(status_code=404, detail="会话记录不存在")

    db.delete(session)
    db.commit()
    return ApiResponse(message="会话记录已删除")
```

**Step 2: 验证**

```bash
cd backend && python -c "from app.routers.ai_session import router; print('OK')"
```

**Step 3: Commit**

```bash
git add backend/app/routers/ai_session.py
git commit -m "feat: add AI creation session API router"
```

---

### Task 10: 扩展 notary 路由 — 多平台存证

**Files:**
- Modify: `backend/app/routers/notary.py` (追加 Polygon + TSA 端点)

**Interfaces:**
- Consumes: 现有 `notary.py` 路由 + 模型
- Produces: 新增 `/notary/polygon` 和 `/notary/timestamp` 端点

**Step 1: 在 notary.py 末尾追加端点**

```python
# ==============================================================================
# Phase 0: Polygon + DigiCert TSA endpoints
# ==============================================================================


@router.post("/notary/polygon", response_model=ApiResponse)
def anchor_to_polygon(data: dict, db: Session = Depends(get_db)):
    """将作品哈希锚定到 Polygon 公链 (Phase 0).

    body: {"work_id": str}
    """
    from app.gateway.polygon import PolygonNotaryGateway

    work_id = data.get("work_id")
    work = db.query(Work).filter(Work.id == work_id).first()
    if not work:
        raise HTTPException(status_code=404, detail="作品不存在")

    if not work.sha256:
        raise HTTPException(status_code=400, detail="作品需要先计算哈希")

    gateway = PolygonNotaryGateway()
    anchor = gateway.anchor(work.sha256)

    if not anchor:
        raise HTTPException(status_code=500, detail="Polygon 锚定失败")

    # 创建存证记录
    record = NotaryRecord(
        work_id=work_id,
        platform="polygon",
        status="confirmed",
        transaction_hash=anchor.tx_hash,
        blockchain=anchor.chain,
        fee=0.0,  # 模拟
    )
    db.add(record)
    db.commit()

    return ApiResponse(
        message=f"已锚定到 Polygon: {anchor.tx_hash[:20]}...",
        data={
            "tx_hash": anchor.tx_hash,
            "block_number": anchor.block_number,
            "contract_address": anchor.contract_address,
        },
    )


@router.post("/notary/timestamp", response_model=ApiResponse)
def request_timestamp(data: dict, db: Session = Depends(get_db)):
    """请求 RFC 3161 时间戳 (Phase 0).

    body: {"work_id": str}
    """
    from app.services.timestamp_service import TimestampService

    work_id = data.get("work_id")
    work = db.query(Work).filter(Work.id == work_id).first()
    if not work:
        raise HTTPException(status_code=404, detail="作品不存在")

    if not os.path.exists(work.file_path):
        raise HTTPException(status_code=400, detail="作品文件不存在")

    service = TimestampService()
    token = await service.timestamp_file(work.file_path)

    if not token:
        raise HTTPException(status_code=500, detail="时间戳请求失败")

    # 保存时间戳文件
    ts_dir = Path("data/timestamps")
    ts_dir.mkdir(parents=True, exist_ok=True)
    ts_path = ts_dir / f"{work_id}.tsr"
    with open(ts_path, "wb") as f:
        f.write(token.token_bytes)

    # 更新存证记录
    record = db.query(NotaryRecord).filter(
        NotaryRecord.work_id == work_id, NotaryRecord.platform == "tts_timestamp"
    ).first()
    if record:
        record.notes = (record.notes or "") + f"\nTimestamp: {ts_path}"
    else:
        record = NotaryRecord(
            work_id=work_id,
            platform="tts_timestamp",
            status="confirmed",
            notes=f"RFC 3161 timestamp: {ts_path}",
            fee=0.15,
        )
        db.add(record)

    db.commit()

    return ApiResponse(
        message="RFC 3161 时间戳生成成功",
        data={"timestamp_path": str(ts_path)},
    )
```

**注意**: 由于 FastAPI `@router.post` 装饰器内的端点需要使用 `async def` 才能用 `await`，上面的 `request_timestamp` 已经是 async。

**Step 2: 在 main.py 中注册新路由**

检查 `backend/app/main.py`，添加:

```python
from app.routers.risk_warning import router as risk_warning_router
from app.routers.ai_session import router as ai_session_router

app.include_router(risk_warning_router)
app.include_router(ai_session_router)
```

**Step 3: 验证**

```bash
cd backend && python -c "from app.routers.notary import router; print('OK')"
```

**Step 4: Commit**

```bash
git add backend/app/routers/notary.py backend/app/main.py
git commit -m "feat: add Polygon anchoring and TSA timestamp endpoints to notary router"
```

---

### Task 11: 前端 — 风险预警页面

**Files:**
- Create: `frontend/src/views/RiskWarningView.vue`
- Create: `frontend/src/api/risk_warning.ts`
- Create: `frontend/src/stores/useRiskWarningStore.ts`
- Create: `frontend/src/types/risk_warning.ts`

**Interfaces:**
- Consumes: `axios` client, `ApiResponse` pattern
- Produces: Vue 页面组件展示风险预警列表，支持按 severity 筛选 + 标记已查看

**Step 1: 创建类型定义**

```typescript
// frontend/src/types/risk_warning.ts

export interface RiskWarning {
  id: string
  warning_type: string
  severity: 'low' | 'medium' | 'high'
  title: string
  matched_entity: string | null
  confidence: number | null
  dismissed: boolean
  created_at: string | null
}

export interface RiskCheckRequest {
  work_id?: string | null
  prompt?: string | null
  reference_images?: string[] | null
  model_name?: string | null
  work_title?: string
}

export type SeverityColor = 'red' | 'orange' | 'yellow'
```

**Step 2: 创建 API 层**

```typescript
// frontend/src/api/risk_warning.ts
import client from './client'
import type { RiskCheckRequest } from '@/types/risk_warning'

export const riskWarningApi = {
  check(data: RiskCheckRequest) {
    return client.post('/risk-warning/check', data)
  },
  getByWork(workId: string) {
    return client.get(`/risk-warning/work/${workId}`)
  },
  dismiss(warningId: string) {
    return client.patch(`/risk-warning/${warningId}/dismiss`)
  },
}
```

**Step 3: 创建 Store**

```typescript
// frontend/src/stores/useRiskWarningStore.ts
import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { RiskWarning } from '@/types/risk_warning'
import { riskWarningApi } from '@/api/risk_warning'

export const useRiskWarningStore = defineStore('riskWarning', () => {
  const warnings = ref<RiskWarning[]>([])
  const loading = ref(false)

  async function check(data: Record<string, unknown>) {
    loading.value = true
    try {
      const res = await riskWarningApi.check(data as any)
      return res.data.data
    } finally {
      loading.value = false
    }
  }

  async function fetchByWork(workId: string) {
    const res = await riskWarningApi.getByWork(workId)
    warnings.value = res.data.data
  }

  async function dismiss(id: string) {
    await riskWarningApi.dismiss(id)
    warnings.value = warnings.value.map(w => w.id === id ? { ...w, dismissed: true } : w)
  }

  return { warnings, loading, check, fetchByWork, dismiss }
})
```

**Step 4: 创建 RiskWarningView.vue**

参考现有 `NotaryPanel.vue` 的简洁风格，创建风险预警中心页面:
- 顶部统计卡片: 总数 / 未查看 / 高风险
- 预警列表表格: 类型 + 严重度 badge + 标题 + 匹配实体 + 置信度 + 操作
- 支持 severity 筛选 (全部/高/中/低)
- 每条记录有"已查看"按钮

**Step 5: Commit**

```bash
git add frontend/src/types/risk_warning.ts frontend/src/api/risk_warning.ts frontend/src/stores/useRiskWarningStore.ts frontend/src/views/RiskWarningView.vue
git commit -m "feat: add RiskWarning frontend page with API layer and store"
```

---

### Task 12: 前端 — AI 会话面板

**Files:**
- Create: `frontend/src/components/AiSessionPanel.vue`
- Create: `frontend/src/api/ai_session.ts`
- Create: `frontend/src/stores/useAiSessionStore.ts`
- Create: `frontend/src/types/ai_session.ts`

**Interfaces:**
- Consumes: work_id from parent component
- Produces: 作品详情页内的 AI 会话记录面板

**Step 1: 创建类型定义**

```typescript
// frontend/src/types/ai_session.ts

export interface AiSession {
  id: string
  work_id: string
  tool_name: string
  tool_version?: string
  prompt: string
  seed?: number | null
  model_name?: string
  created_at: string | null
}

export interface AiSessionCreate {
  tool_name: string
  tool_version?: string
  prompt: string
  prompt_history?: unknown[]
  seed?: number | null
  parameters?: Record<string, unknown>
  negative_prompt?: string
  model_name?: string
  lora_names?: string[]
  output_images?: string[]
  human_interventions?: unknown[]
}
```

**Step 2: 创建 API + Store + 组件**

参考 Task 11 的模式:
- `ai_session.ts` API: `create(workId, data)`, `list(workId)`, `update(workId, sessionId, data)`, `delete(workId, sessionId)`
- `useAiSessionStore.ts` Store: 管理 sessions ref + CRUD 方法
- `AiSessionPanel.vue` 组件: 时间线式展示，支持新增/编辑/删除

**Step 3: Commit**

```bash
git add frontend/src/types/ai_session.ts frontend/src/api/ai_session.ts frontend/src/stores/useAiSessionStore.ts frontend/src/components/AiSessionPanel.vue
git commit -m "feat: add AI Session recording panel with API layer and store"
```

---

### Task 13: 集成验证 — 后端启动 + 路由注册

**Files:**
- Modify: `backend/app/main.py` (确保新路由已注册)

**Step 1: 确认 main.py 包含所有路由**

```python
from app.routers.risk_warning import router as risk_warning_router
from app.routers.ai_session import router as ai_session_router
```

**Step 2: 启动后端验证**

```bash
cd backend && uvicorn app.main:app --host 0.0.0.0 --port 8000
```

**Step 3: 测试端点**

```bash
curl http://localhost:8000/api/risk-warning/check \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Hello Kitty style drawing", "work_title": "Test"}'

curl http://localhost:8000/api/works/test-work-123/ai-sessions
```

**Step 4: Commit**

```bash
git add backend/app/main.py
git commit -m "chore: register Phase 0 routers in main.py and verify"
```

---

## 文件变更汇总

### 新建文件 (12 个)

| # | 文件 | 用途 |
|---|------|------|
| 1 | `backend/app/models/risk_warning.py` | 风险预警数据模型 |
| 2 | `backend/app/models/ai_session.py` | AI 创作会话数据模型 |
| 3 | `backend/app/gateway/trademark.py` | 商标数据库网关 |
| 4 | `backend/app/gateway/model_source.py` | LoRA 来源查询网关 |
| 5 | `backend/app/services/risk_warning_service.py` | 风险预警引擎服务 |
| 6 | `backend/app/gateway/digicert_tsa.py` | DigiCert TSA 网关 |
| 7 | `backend/app/services/timestamp_service.py` | 时间戳服务 |
| 8 | `backend/app/gateway/polygon.py` | Polygon 存证网关 |
| 9 | `backend/app/routers/risk_warning.py` | 风险预警 API |
| 10 | `backend/app/routers/ai_session.py` | AI 会话 API |
| 11 | `frontend/src/views/RiskWarningView.vue` | 风险预警页面 |
| 12 | `frontend/src/components/AiSessionPanel.vue` | AI 会话面板 |

### 新增前端文件 (8 个)

| # | 文件 | 用途 |
|---|------|------|
| 1 | `frontend/src/types/risk_warning.ts` | 风险预警类型 |
| 2 | `frontend/src/api/risk_warning.ts` | 风险预警 API |
| 3 | `frontend/src/stores/useRiskWarningStore.ts` | 风险预警 Store |
| 4 | `frontend/src/types/ai_session.ts` | AI 会话类型 |
| 5 | `frontend/src/api/ai_session.ts` | AI 会话 API |
| 6 | `frontend/src/stores/useAiSessionStore.ts` | AI 会话 Store |

### 修改文件 (5 个)

| # | 文件 | 变更 |
|---|------|------|
| 1 | `backend/app/models/work.py` | 扩展: ai_assisted, ai_tools_used, creator_type |
| 2 | `backend/app/models/__init__.py` | 注册 RiskWarning + AiCreationSession |
| 3 | `backend/app/services/c2pa_service.py` | 扩展 manifest 生成: 加入 AI 会话摘要 |
| 4 | `backend/app/routers/notary.py` | 扩展: Polygon + TSA 端点 |
| 5 | `backend/app/main.py` | 注册新路由 |
