# [2] 权益保护中心 — 详细功能设计 v4

> **定位**: AI 时代的创作者权益保护一站式中心。从创作前风险预警 → 创作中 AI 会话记录 → 创作后自动存证 → 全网监测 → 维权流水线 → 清白证明，形成完整权益保护闭环。
> **最后更新**: 2026-06-25 (全面深化: 从"权利保护"升级为"权益保护"，新增 5 大子能力)

---

## 一、模块功能架构

```
[2] 权益保护中心
├── 2.1 创作前 — 侵权风险预警引擎 (新增)
│   ├── 提示词侵权检测 (TF-IDF + 关键词库 + USPTO TESS API)
│   ├── 参考图相似度检测 (pHash/dHash + 百度识图/Google Vision)
│   ├── LoRA/模型权属检查 (Civitai/HuggingFace API)
│   └── 商标/Logo 碰撞 (CNIPA/WIPO/USPTO 官方数据)
│
├── 2.2 创作中 — AI 辅助创作过程记录 (新增)
│   ├── AI 会话自动记录 (prompt + seed + parameters + 输出)
│   ├── 提示词迭代历史追踪
│   ├── 人工干预点记录 (inpainting/重绘/裁剪)
│   └── 创作工具溯源 (Midjourney/StableDiffusion/DALL-E/ComfyUI/Ollama)
│
├── 2.3 创作后 — 自动存证 + 全网监测 (扩展)
│   ├── 多平台区块链锚定 (版权家/蚂蚁链/至信链/Polygon/Ethereum)
│   ├── C2PA 内容凭证嵌入 (v1 实现 — Adobe content-auth SDK)
│   ├── RFC 3161 权威时间戳 (DigiCert TSA)
│   ├── 全网图片监测 (百度识图/Google Vision/TinEye)
│   ├── 电商平台监测 (淘宝/拼多多/闲鱼)
│   ├── 品牌/商标监测 (BrandWatch 扩展)
│   └── 按作品重要度分级调度 (日/3天/月)
│
├── 2.4 维权流水线 — 自动化维权 (全新)
│   ├── 侵权评分分级算法
│   ├── 证据包一键生成 (原始文件+存证+AI会话+C2PA+版本+截图)
│   ├── 投诉模板管理 (DMCA/中国著作权法/各平台规则)
│   ├── 投诉一键提交 (API 直投 / 预填 URL / PDF 材料包)
│   ├── 进展追踪 (状态机 + 提醒 + 统计)
│   └── 维权知识库 (各平台投诉规则)
│
└── 2.5 清白证明中心 (全新)
    ├── 创作时间线还原
    ├── 反证报告自动生成 (PDF)
    ├── 相似作品排除分析
    └── 一键发送给指控方
```

---

## 二、2.1 创作前：侵权风险预警引擎

### 2.1.1 四个检测维度

| 检测维度 | 输入 | 检测逻辑 | 第三方服务 | 实现 |
|---------|------|---------|-----------|------|
| **提示词侵权检测** | AI 生成时的 prompt | TF-IDF + 关键词库匹配：检查是否包含注册商标名、知名 IP 角色名、艺术家风格关键词 | 本地关键词库 + USPTO TESS API (可选) | `risk_warning_service.py` |
| **参考图相似度检测** | 用户上传的参考图/灵感图 | 感知哈希 (pHash/dHash) + 余弦相似度，对比作品库和公开图像索引 | 百度识图 API / Google Vision API | 通过现有 `SearchGateway` 扩展 |
| **LoRA/模型权属检查** | 使用的模型文件名/URL | 查询模型来源数据库，检查是否允许商用、是否署名原作者 | Civitai API / HuggingFace API | `ModelSourceGateway` |
| **商标/Logo 碰撞** | 作品标题/描述/设计中提取的文字 | 对比 CNIPA 商标库 + 自建热门品牌库 | CNIPA 开放查询 / WIPO MADRID / 本地品牌库 | `TrademarkGateway` |

### 2.1.2 数据模型

```sql
-- 新增：风险预警记录表
CREATE TABLE IF NOT EXISTS risk_warnings (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    work_id TEXT REFERENCES works(id),
    warning_type TEXT NOT NULL,  -- 'prompt_risk' / 'reference_similar' / 'lora_rights' / 'trademark_conflict'
    severity TEXT NOT NULL,       -- 'low' / 'medium' / 'high'
    title TEXT NOT NULL,          -- 简短标题: "检测到商标冲突: 'Kitty'"
    description TEXT,             -- 详细说明
    matched_entity TEXT,          -- 匹配到的实体: 商标名/角色名/模型名
    confidence FLOAT,             -- 匹配置信度 0-100
    suggestion TEXT,              -- 系统建议: "建议修改标题为..."
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    dismissed BOOLEAN DEFAULT 0,
    dismissed_at DATETIME
);

CREATE INDEX IF NOT EXISTS idx_risk_work ON risk_warnings(work_id);
CREATE INDEX IF NOT EXISTS idx_risk_type ON risk_warnings(warning_type);
CREATE INDEX IF NOT EXISTS idx_risk_severity ON risk_warnings(severity);
```

### 2.1.3 API 端点

| 方法 | 路径 | 请求体 | 响应 | 说明 |
|------|------|--------|------|------|
| POST | /api/risk-warning/check-prompt | `{prompt, reference_images[]}` | `{warnings: [{type, severity, title, description, matched_entity, confidence, suggestion}]}` | 提示词风险检测 |
| POST | /api/risk-warning/check-reference | `{image_path, work_ids[]?}` | `{similar_works: [{work_id, title, similarity}], external_matches: [{url, similarity}]}` | 参考图相似度检测 |
| GET | /api/risk-warning/model-info | `{model_name, source}` | `{name, author, license, commercial_use_allowed, source_url}` | 查询模型/LoRA 权属信息 |
| POST | /api/risk-warning/check-trademark | `{text, jurisdiction}` | `{conflicts: [{name, class, jurisdiction, confidence, action_url}]}` | 商标碰撞检测 |
| GET | /api/risk-warning/history?work_id=xxx | — | `{warnings: [...]}` | 获取作品的历史预警记录 |
| PATCH | /api/risk-warning/{id}/dismiss | `{}` | `{ok: true}` | 标记预警为已查看 |

### 2.1.4 前端集成

嵌入到作品导入/创建流程的 Step 0（最前面）：

```
作品导入/创建
  → Step 0: 风险预警 (新增)
     - 高风险 (red) → 阻断 + 建议修改
     - 中风险 (yellow) → 警告 + 建议
     - 低风险 → 不显示
  → Step 1: 选作品信息 (原有)
  → ...
```

**组件：`RiskWarningPanel.vue`**

Props: `{ warnings: RiskWarning[] }`
Events: `@dismiss(id)`, `@suggestion-click(suggestion)`

展示规则：
- 每条预警显示 severity 标签 + 标题 + 匹配实体 + 置信度进度条
- 高风险条目附带红色 "建议修改" 按钮
- 中风险条目附带黄色 "了解更多" 按钮
- 所有条目可点击 "我知道了" Dismiss

### 2.1.5 关键词库维护

本地内置关键词库 `backend/app/data/trademark_keywords.json`：

```json
{
  "trademarks": [
    {"name": "Hello Kitty", "class": "28", "jurisdiction": "global", "category": "character"},
    {"name": "Mickey Mouse", "class": "25", "jurisdiction": "global", "category": "character"},
    {"name": "迪士尼", "class": "16,25,28", "jurisdiction": "cn", "category": "character"}
  ],
  "characters": [
    {"name": "孙悟空", "category": "public_domain", "note": "公有领域，可商用"},
    {"name": "哪吒", "category": "public_domain", "note": "公有领域，但特定形象可能受版权保护"}
  ],
  "artists": [
    {"name": "草间弥生", "jurisdiction": "global", "note": "风格不受版权保护，但具体作品受保护"}
  ]
}
```

> **注意**：风格关键词不标记为侵权风险，仅提示"某些艺术家的特定风格可能涉及商业权益"。系统不做法律判断。

---

## 三、2.2 创作中：AI 辅助创作过程记录

### 3.1 核心设计

**所有创作者类型的 AI 使用痕迹自动记录**，形成不可篡改的创作过程证据链。这是 AI 时代版权保护的核心基础设施。

### 3.2 数据模型

```sql
-- 扩展 works 表
ALTER TABLE works ADD COLUMN ai_assisted BOOLEAN DEFAULT 0;
ALTER TABLE works ADD COLUMN ai_tools_used JSON DEFAULT '[]';
-- ai_tools_used: [{"name": "Midjourney v6", "version": "6.0", "usage": "image_generation"}, ...]

-- 新增：AI 创作会话记录表
CREATE TABLE IF NOT EXISTS ai_creation_sessions (
    id TEXT PRIMARY KEY,
    work_id TEXT NOT NULL REFERENCES works(id) ON DELETE CASCADE,
    tool_name TEXT NOT NULL,         -- 'Midjourney' / 'StableDiffusion' / 'DALL-E' / 'ComfyUI' / 'Ollama' / 'Custom'
    tool_version TEXT,
    prompt TEXT NOT NULL,            -- 原始提示词
    prompt_history JSON,             -- 提示词迭代历史
    -- [{"version": 1, "text": "...", "timestamp": "..."}, ...]
    seed INTEGER,                    -- Seed 值
    parameters JSON,                 -- 模型参数
    -- {"steps": 30, "cfg": 7, "sampler": "DPM++ 2M", "width": 1024, "height": 1024}
    negative_prompt TEXT,            -- 反向提示词
    model_name TEXT,                 -- 使用的模型/LoRA 名称
    lora_names JSON,                 -- ["coolStyle_v2.safetensors", ...]
    output_images JSON,              -- ["data/xxx/a1.png", ...]
    human_interventions JSON,        -- [{"type": "inpainting", "step": 5, "description": "重绘面部"}, ...]
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_ai_session_work ON ai_creation_sessions(work_id);
```

### 3.3 自动记录策略

| 场景 | 自动记录内容 | 用户操作 |
|------|-------------|---------|
| 通过 API 调用 AI 生成 | prompt + seed + parameters + 输出自动记录 | 无需操作 |
| 本地 Ollama/ComfyUI 生成 | 通过 webhook 或 API 回调记录 | 需配置 webhook |
| 手动上传 AI 生成图 | 询问"是否 AI 生成？" → 填写工具名 + prompt | 一次性填写 |
| 迭代修改（Vary Region/Inpainting） | 记录每次修改的 prompt 变化 + 修改区域 | 自动记录 |

### 3.4 API 端点

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | /api/works/{id}/ai-session | 记录 AI 创作会话 |
| GET | /api/works/{id}/ai-sessions | 获取作品的 AI 创作时间线 |
| PATCH | /api/works/{id}/ai-session/{sid} | 编辑会话记录 |
| DELETE | /api/works/{id}/ai-session/{sid} | 删除会话记录 |

### 3.5 前端组件

**`AiSessionTimeline.vue`** — AI 创作时间线展示

Props: `{ workId: string }`

```
作品《应龙》— AI 创作时间线
├── 2026-06-20 14:30 — Midjourney v6
│   ├── Prompt: "一条中国龙，山海经风格..."
│   ├── Seed: 847261039
│   ├── 输出: 4 张图
│   └── 人工干预: 无
│
├── 2026-06-20 15:10 — StableDiffusion + ControlNet
│   ├── Prompt: "应龙线稿，精细线条..."
│   ├── LoRA: lineArt_v3.safetensors
│   ├── 人工干预: Inpainting (重绘龙角区域)
│   └── 输出: 1 张图
│
└── 2026-06-21 09:00 — PS 手动精修
    ├── 工具: Photoshop
    ├── 人工干预: 色彩调整 + 细节增强
    └── 输出: 最终版本
```

---

## 四、2.3 创作后：自动存证 + 全网监测

### 4.1 多平台存证增强

**现有能力**：notary.py 已支持版权家、蚂蚁链、至信链。

**新增能力**：

| 存证维度 | 现有 | 新增 | 说明 |
|---------|------|------|------|
| SHA-256 哈希 | ✅ | 保留 | 基础文件指纹 |
| 区块链锚定 | ✅ (蚂蚁链/至信链) | 扩展：Polygon/Ethereum | 增加国际认可的公链 |
| C2PA 内容凭证 | ❌ → **v1 实现** | 嵌入 Content Credentials 到文件元数据 | Adobe content-auth Python SDK |
| 创作过程存证 | ❌ → **v1 实现** | ai_creation_sessions 自动上链 | 会话摘要哈希锚定到区块链 |
| 权威时间戳 | ❌ → **v1 实现** | 对接 RFC 3161 TTS 服务机构 | DigiCert TSA，约 $0.15/次 |

**C2PA 实现方案**（不重新造轮子）：
- 使用 [Adobe's content-auth](https://github.com/adobe/content-auth) Python SDK
- manifest 自动生成：包含作品元数据 + SHA-256 + AI 创作会话摘要 + 时间戳
- 嵌入到 JPEG/PNG 的 XMP 元数据块中

**时间戳服务对接**：
- 首选：[DigiCert Timestamp Service](https://www.digicert.com/code-signing/tsa.htm) (RFC 3161)
- 备选：[GlobalSign TSA](https://www.globalsign.com/en/timestamp-service)

### 4.2 全网监测增强

**现有能力**：monitor.py 已支持百度识图、Google Vision。

**扩展维度**：

| 监测维度 | v1 现状 | v1 新增 | 第三方服务 |
|---------|---------|---------|-----------|
| 图片以图搜图 | ✅ 百度/Google | 扩展：TinEye API | TinEye (付费，准确率最高) |
| 电商平台监测 | 预留 | **v1 实现** | 百度识图 + 爬虫 |
| 品牌/商标监测 | BrandWatch (已有) | 扩展：CNIPA/WIPO 商标库对比 | TrademarkGateway |
| 视频指纹监测 | 预留 | v1 预留数据结构，v3 实现 | 灵创/维权骑士 API |
| 音频指纹监测 | 无 | v1 预留，v4 实现 | AcoustID API |

**自动监测调度增强**：
- 现有：Celery Beat 每周扫描一次
- 新增：**按作品重要度分级调度**

```sql
-- 新增：作品重要度评分表
CREATE TABLE IF NOT EXISTS work_priority_scores (
    id TEXT PRIMARY KEY,
    work_id TEXT NOT NULL UNIQUE REFERENCES works(id),
    score INTEGER NOT NULL,           -- 0-100
    has_notary BOOLEAN DEFAULT 0,     -- +30 已存证
    has_ipr BOOLEAN DEFAULT 0,        -- +25 有IP登记
    has_certificate BOOLEAN DEFAULT 0, -- +20 有证书
    monetization_count INTEGER DEFAULT 0, -- +5 * 变现产品数 (max +25)
    scan_frequency TEXT NOT NULL,     -- 'daily' / 'every_3_days' / 'monthly' / 'manual'
    calculated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

调度规则：
| 分数区间 | 重要度 | 扫描频率 | 说明 |
|---------|--------|---------|------|
| 75-100 | 高 | 每日 | 已存证 + 有 IP 登记 + 有变现产品 |
| 50-74 | 中 | 每 3 天 | 已存证或有 IP 登记 |
| 25-49 | 低 | 每月 | 仅有存证 |
| 0-24 | 极低 | 手动 | 未存证作品 |

### 4.3 数据模型扩展

```sql
-- 扩展 notary_records 表
ALTER TABLE notary_records ADD COLUMN blockchain_type TEXT DEFAULT 'antchain';
-- 'antchain' / 'zhixinchain' / 'polygon' / 'ethereum' / 'tts_timestamp'
ALTER TABLE notary_records ADD COLUMN c2pa_manifest_path TEXT;
ALTER TABLE notary_records ADD COLUMN timestamp_token_path TEXT;

-- 扩展 EvidencePackage 表 (monitor.py 已有，需增加)
-- ALTER TABLE evidence_packages ADD COLUMN blockchain_anchor TEXT;
-- ALTER TABLE evidence_packages ADD COLUMN updated_at DATETIME;

-- 扩展 monitor_results 表
-- ALTER TABLE monitor_results ADD COLUMN enforcement_status TEXT DEFAULT 'pending_review';
-- 'pending_review' / 'confirmed' / 'evidence_gathered' / 'complaint_filed' / 'resolved_takedown' / 'resolved_disputed' / 'ignored' / 'whitelisted'
```

### 4.4 前端组件

**`MonitoringTab.vue`** — 监测操作区

```
侵权监测
├── 作品选择: [下拉多选，按重要度排序高→低]
├── 扫描引擎: [百度识图 ✓] [Google Vision ✓] [TinEye ○ 需配置]
├── 扫描频率: [按重要度自动] [自定义]
├── [开始扫描]
│
├── 监测结果列表:
│   ┌─────────────────────────────────────────────┐
│   │ [92%] https://taobao.com/item/xxx            │
│   │ 发现: 2026-06-24 10:30  重要度: ★★★★★       │
│   │ [确认侵权] [标记误报] [加入白名单]            │
│   └─────────────────────────────────────────────┘
│   ┌─────────────────────────────────────────────┐
│   │ [85%] https://reddit.com/r/xxx              │
│   │ 发现: 2026-06-24 10:30  重要度: ★★★☆☆       │
│   │ [确认侵权] [标记误报] [加入白名单]            │
│   └─────────────────────────────────────────────┘
│
└── 定时扫描配置:
    [每周自动扫描] [开启/关闭]
    下次扫描: 2026-06-28
```

---

## 五、2.4 维权流水线（全新核心模块）

### 5.1 维权流水线状态机

```
pending_review (待审核)
  → confirmed (确认侵权) ──▶ evidence_gathering (证据收集)
                              │
                              ├──▶ complaint_filed (投诉已提交)
                              │       │
                              │       └──▶ resolved (已解决)
                              │              ├── takedown (已下架)
                              │              └── disputed (被申诉)
                              │
                              ├──▶ lawyer_letter_sent (律师函已发)
                              │       │
                              │       └──▶ responding (对方回应)
                              │               ├── settled (已和解)
                              │               └── litigation (诉讼)
                              │
                              └──▶ escalated (升级处理)
                                      │
                                      └──▶ external_lawyer (委托外部律师)
```

### 5.2 数据模型

```sql
-- 新增：维权行动记录表
CREATE TABLE IF NOT EXISTS enforcement_actions (
    id TEXT PRIMARY KEY,
    monitor_result_id TEXT NOT NULL REFERENCES monitor_results(id),
    action_type TEXT NOT NULL,  -- 'platform_complaint' / 'dmca_notice' / 'lawyer_letter' / 'litigation'
    platform TEXT NOT NULL,      -- 侵权发生平台: 'taobao' / 'instagram' / 'redbubble' / 'custom'
    status TEXT NOT NULL,        -- 'draft' / 'sent' / 'responding' / 'resolved' / 'escalated'
    complaint_text TEXT,         -- 投诉函/DMCA 通知正文
    template_used TEXT,          -- 使用的模板: 'dmca_us' / 'copyright_cn' / 'custom'
    sent_at DATETIME,
    response_text TEXT,          -- 对方回复内容
    resolved_at DATETIME,
    resolution_type TEXT,        -- 'takedown' / 'settlement' / 'dismissed' / 'litigation_started'
    compensation_amount FLOAT,   -- 赔偿金额
    notes TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 新增：维权知识库表（存储各平台投诉规则和模板）
CREATE TABLE IF NOT EXISTS enforcement_templates (
    id TEXT PRIMARY KEY,
    platform TEXT NOT NULL,       -- 'taobao' / 'instagram' / 'google' / 'generic'
    jurisdiction TEXT NOT NULL,   -- 'cn' / 'us' / 'eu' / 'global'
    action_type TEXT NOT NULL,    -- 'dmca' / 'copyright' / 'trademark' / 'design_right'
    title TEXT NOT NULL,          -- 模板标题
    body_template TEXT NOT NULL,  -- 带 {{placeholders}} 的模板正文
    required_evidence JSON,       -- ["certificate", "original_file", "timestamp", "ai_session"]
    filing_url TEXT,              -- 投诉提交URL
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 种子数据
INSERT OR IGNORE INTO enforcement_templates VALUES
('tpl_dmca_us', 'us', 'dmca', 'DMCA Takedown Notice (US)',
 'Under Section 512(c) of the DMCA... {{work_title}}... {{copyright_notice}}...',
 '["certificate", "original_file"]',
 'https://www.google.com/forms/surveillance', '2026-06-25'),
('tpl_copyright_cn', 'cn', 'copyright', '著作权投诉模板 (中国)',
 '依据《中华人民共和国著作权法》... {{work_title}}... {{author_name}}...',
 '["certificate", "original_file", "ai_session"]',
 '', '2026-06-25'),
('tpl_instagram_meta', 'global', 'copyright', 'Instagram/Meta Copyright Report',
 'I am the copyright owner... {{work_title}}... {{infringing_url}}...',
 '["certificate", "original_file"]',
 'https://www.facebook.com/help/contact/260749600974958', '2026-06-25');
```

### 5.3 证据包自动生成

现有 `EvidencePackage` 表已存在，需增强为自动收集：

**自动收集的证据清单**：

| 证据类型 | 来源 | 说明 |
|---------|------|------|
| 原始文件 | `works.file_path` | 上传的原始作品 |
| SHA-256 哈希 | `works.sha256` | 文件指纹 |
| 存证证书 | `notary_records` + `certificates` | 区块链存证回执 + PDF 证书 |
| C2PA manifest | `c2pa_records.manifest_json` | 内容凭证 |
| 创作时间线 | `ai_creation_sessions` | 完整 AI 创作会话记录 |
| 版本历史 | `work_versions` | 所有版本快照 |
| 侵权页面截图 | `monitor_results.screenshot_path` | Playwright 抓取的侵权页面 |
| 侵权 URL 取证 | 新增: `enforcement_evidence.url_proof` | 区块链存证的 URL 快照 |
| 存证时间对比 | `notary_records.created_at` | 证明存证时间早于侵权发现时间 |

**证据包生成服务** (`backend/app/services/enforcement_service.py`)：

```python
class EnforcementService:
    async def build_evidence_package(self, monitor_result_id: str) -> EvidencePackage:
        """一键构建完整维权证据包"""
        result = await self._get_monitor_result(monitor_result_id)
        work = await self._get_work(result.work_id)

        evidence = {
            "original_file": work.file_path,
            "sha256": work.sha256,
            "notary_records": await self._get_notary_records(work.id),
            "c2pa_manifest": await self._get_c2pa(work.id),
            "ai_sessions": await self._get_ai_sessions(work.id),
            "versions": await self._get_versions(work.id),
            "infringement_screenshots": [result.screenshot_path],
            "infringement_url_proof": await self._blockchain_url_proof(result.matched_url),
            "timeline": self._build_timeline(work, result),
        }

        # 生成 ZIP + 区块链存证证据包本身
        zip_path = await self._generate_zip(evidence)
        pkg_hash = await self._anchor_to_blockchain(zip_path)

        return EvidencePackage(
            work_id=work.id,
            related_result_ids=[monitor_result_id],
            package_path=zip_path,
            package_type="enforcement",
            blockchain_anchor=pkg_hash,
        )
```

### 5.4 投诉一键提交

| 平台类型 | 提交方式 | 实现 |
|---------|---------|------|
| 有官方投诉通道的平台 | 自动生成投诉函 + 打开投诉页面（预填） | 构造 URL 带参数打开 |
| 支持 API 投诉的平台 | 通过 API 直接提交 | Gateway 适配器 |
| 仅支持手动投诉的平台 | 生成完整投诉材料包（PDF + ZIP） | 用户手动提交 |

### 5.5 维权统计数据

| 指标 | 计算方式 | 展示位置 |
|------|---------|---------|
| 维权成功率 | resolved / total_actions | Dashboard 仪表盘 |
| 平均处理时长 | avg(resolved_at - sent_at) | 维权详情页 |
| 各平台投诉效率 | group_by(platform) | 维权统计页 |

### 5.6 API 端点

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /api/enforcement/actions | 维权行动列表 |
| POST | /api/enforcement/actions | 创建维权行动 |
| POST | /api/enforcement/{mr_id}/build-evidence | 构建证据包 |
| POST | /api/enforcement/{mr_id}/file-complaint | 提交投诉 |
| GET | /api/enforcement/{ea_id}/status | 查询投诉状态 |
| PATCH | /api/enforcement/{ea_id}/update-status | 手动更新状态 |
| GET | /api/enforcement/templates | 获取投诉模板列表 |
| GET | /api/enforcement/stats | 维权统计数据 |

### 5.7 前端组件

**`EnforcementView.vue`** — 维权管理中心

```
维权管理中心
├── 维权行动列表:
│   ┌──────────────────────────────────────────────┐
│   │ [taobao.com] 应龙T恤侵权案                     │
│   │ 状态: 🟢 已解决(下架)  处理时长: 3天           │
│   │ 模板: 中国著作权法投诉  提交: 2026-06-20       │
│   │ [查看详情] [查看证据包]                        │
│   └──────────────────────────────────────────────┘
│
├── 维权向导 (4步):
│   步骤1: 确认侵权 → 步骤2: 构建证据包 → 步骤3: 选择投诉模板 → 步骤4: 提交并追踪
│
└── 维权统计:
    总行动: 12 | 成功率: 83% | 平均处理: 5.2天 | 本月新增: 3
```

**`EnforcementWizard.vue`** — 维权向导组件

Props: `{ monitorResultId: string }`

Steps:
1. **确认侵权** — 展示侵权对比图 + 相似度 + 操作按钮
2. **构建证据包** — 自动收集所有证据，展示清单 + 进度
3. **选择投诉模板** — 按平台推荐模板 + 预览投诉函
4. **提交并追踪** — 提交方式选择 + 成功提示 + 追踪入口

---

## 六、2.5 清白证明中心（全新模块）

### 6.1 场景定义

当创作者**被他人指控侵权时**（如收到律师函、平台投诉），系统自动准备反驳证据：

```
收到侵权指控
  → 系统自动分析指控内容（谁、什么作品、什么权利）
  → 自动构建清白证据包：
     1. 我的创作时间线（证明我先创作的）
     2. 我的 AI 创作会话记录（证明独立创作过程）
     3. 我的存证证书（证明创作时间早于对方）
     4. 我的提示词和参数（证明独立构思）
     5. 相似作品排除报告（AI 比对：与指控作品相似度 < X%）
  → 生成专业 PDF 反证报告
  → 可选：通过系统直接发送给指控方
```

### 6.2 数据模型

```sql
-- 新增：清白证明请求表
CREATE TABLE IF NOT EXISTS innocence_proofs (
    id TEXT PRIMARY KEY,
    work_id TEXT NOT NULL REFERENCES works(id),
    triggered_by TEXT NOT NULL,  -- 'user_requested' / 'incoming_complaint' / 'automated'
    complaint_summary TEXT,      -- 指控摘要（从 incoming DMCA/律师函提取）
    complaint_complainant TEXT,   -- 指控方名称
    complaint_date DATETIME,
    evidence_bundle_path TEXT,    -- 生成的证据包路径
    report_pdf_path TEXT,         -- 反证报告 PDF 路径
    blockchain_anchor TEXT,       -- 证据包区块链存证
    status TEXT NOT NULL,         -- 'building' / 'ready' / 'sent' / 'resolved'
    sent_at DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 新增：相似作品排除报告
CREATE TABLE IF NOT EXISTS similarity_exclusions (
    id TEXT PRIMARY KEY,
    innocence_proof_id TEXT REFERENCES innocence_proofs(id),
    compared_work_id TEXT NOT NULL,  -- 被指控相似的对方作品
    similarity_score FLOAT,           -- 相似度 (越低越好)
    hash_comparison JSON,             -- SHA-256 对比
    perceptual_comparison JSON,       -- 感知哈希对比
    conclusion TEXT,                  -- "独立创作，相似度低于阈值"
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

### 6.3 API 端点

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | /api/innocence-proof/build | 构建清白证据包 |
| GET | /api/innocence-proof/{id} | 获取清白证明状态 |
| GET | /api/innocence-proof/{id}/download | 下载反证报告 |
| POST | /api/innocence-proof/{id}/send | 发送给指控方 |
| POST | /api/innocence-proof/auto-on-complaint | 自动触发（接入侵权监测结果） |

### 6.4 前端组件

**`InnocenceProofView.vue`** — 清白证明中心

```
清白证明中心
├── 收到指控通知:
│   "2026-06-24 收到来自 XXX 公司的 DMCA 投诉，指控作品《应龙》侵权"
│   [立即构建反证] [稍后处理]
│
├── 反证构建进度:
│   ████████████░░░░ 60% — 正在收集创作会话记录...
│
├── 反证报告预览:
│   ┌─────────────────────────────────────┐
│   │ 反证报告: 《应龙》独立创作证明         │
│   │                                     │
│   │ 一、创作时间线                       │
│   │   2026-06-20 14:30 首次生成          │
│   │   2026-06-20 15:10 ControlNet 精修   │
│   │   2026-06-21 09:00 PS 手动精修       │
│   │                                     │
│   │ 二、存证证书                         │
│   │   版权家 DCI: 已存证 2026-06-20      │
│   │   蚂蚁链: 已锚定 2026-06-20          │
│   │                                     │
│   │ 三、相似作品排除                     │
│   │   与指控作品相似度: 12.3% (低于阈值) │
│   │   结论: 独立创作                     │
│   └─────────────────────────────────────┘
│   [下载报告] [发送给指控方]
```

**`InnocenceWizard.vue`** — 被指控应对向导 (5步)

Steps:
1. **分析指控** — 解析 DMCA/律师函内容
2. **收集证据** — 自动聚合创作时间线 + 存证 + AI 会话
3. **相似排除** — 与指控作品做相似度比对
4. **审核报告** — 预览反证报告，可手动补充
5. **发送** — 选择发送方式（系统发送 / 手动下载）

---

## 七、模块命名变更

原 **"[2] 权利保护中心"** 更名为 **"[2] 权益保护中心"**，涵盖以下五大子能力：

| 子能力 | 原模块 | 新增/扩展 |
|--------|--------|----------|
| 自动存证 | notary.py (已有) | 扩展：多平台锚定 + C2PA 实现 + 创作过程存证 |
| 全网监测 | monitor.py (已有) | 扩展：电商平台 + TinEye + 按重要度调度 |
| 维权流水线 | evidence_packages (已有表) | **全新**：侵权评分 → 证据包 → 投诉提交 → 进展追踪 |
| 清白证明 | 无 | **全新**：创作过程证据链 + 反证报告生成 |
| 品牌保护 | brand_watches (已有表) | 扩展：对接 CNIPA/WIPO 商标数据库 |

---

## 八、上下游数据流

| 输入数据 | 来源 | 用途 |
|----------|------|------|
| work.id, sha256, title, thumbnail, file_path, ai_assisted, ai_tools_used | [1]创意资产中心 | 存证 + 扫描源 + 创作证据链 |
| ai_creation_sessions[] | [1]创意资产中心 | 维权/清白证明证据 |
| certificate.id, hash, qr_code, c2pa_manifest | [2]自身 | Verified 徽章 |

| 输出数据 | 目标 | 用途 |
|----------|------|------|
| certificate.id, hash, proof_url | [4]商业撮合 / [5]内容分发 | Verified 徽章 |
| evidence_package (侵权证据包) | [6]经营管理中心 | 维权记录 |
| enforcement_actions[] | [6]经营管理中心 | 维权统计 |
| innocence_proofs[] | [6]经营管理中心 | 反证记录 |
| monitor_results[] | [6]经营管理中心 | 安全仪表盘 |

---

## 九、前端组件清单

| 组件 | 路径 | Props | 说明 |
|------|------|-------|------|
| `NotaryView.vue` | views/ | — | 存证 Tab（原有，扩展 C2PA/TSA 选项） |
| `MonitoringTab.vue` | views/ | — | 监测 Tab（原有，扩展电商/TinEye/重要度调度） |
| `RiskWarningPanel.vue` | components/ | `{ warnings: RiskWarning[] }` | 风险预警面板（新增） |
| `AiSessionTimeline.vue` | components/ | `{ workId: string }` | AI 创作时间线（新增） |
| `EnforcementView.vue` | views/ | — | 维权管理中心（全新页面） |
| `EnforcementWizard.vue` | components/wizard/ | `{ monitorResultId: string }` | 维权向导 4 步（新增） |
| `InnocenceProofView.vue` | views/ | — | 清白证明中心（全新页面） |
| `InnocenceWizard.vue` | components/wizard/ | `{ workId: string }` | 被指控应对向导 5 步（新增） |
| `EvidencePackageViewer.vue` | components/ | `{ packageId: string }` | 证据包查看器（新增） |

### 补充前端组件规格

**EvidencePackageViewer.vue** — 证据包查看器

Props: `{ packageId: string }`

```
┌────────────────────────────────────────────────────────┐
│ 📦 证据包: EP-20260624-001                              │
├────────────────────────────────────────────────────────┤
│ 作品: 《应龙》                                           │
│ 类型: 侵权证据包                                        │
│ 生成时间: 2026-06-24 14:30                              │
│ 区块链存证: 已锚定 ✅                                   │
│                                                        │
│ 证据清单:                                               │
│ ┌────────────────────────────────────────────────────┐ │
│ │ ✅ 原始文件 (应龙_final.png) 2.7 MB                │ │
│ │ ✅ SHA-256 哈希 (e920814f...)                      │ │
│ │ ✅ 存证证书 (版权家 + 蚂蚁链)                       │ │
│ │ ✅ C2PA manifest (content-auth)                    │ │
│ │ ✅ AI 创作会话 (3 条记录)                           │ │
│ │ ✅ 版本历史 (v1/v2/v3 终稿)                        │ │
│ │ ✅ 侵权页面截图 (taobao.com/item/xxx)              │ │
│ │ ✅ URL 区块链存证                                  │ │
│ └────────────────────────────────────────────────────┘ │
│                                                        │
│ [下载 ZIP] [查看区块链存证] [添加到维权行动]            │
└────────────────────────────────────────────────────────┘
```

Events: `@add-to-enforcement(packageId)`, `@download`, `@view-blockchain`

---

## 十、新增服务与网关

### 10.1 新增 Service

| 文件 | 职责 |
|------|------|
| `services/risk_warning_service.py` | 侵权风险预警引擎 |
| `services/enforcement_service.py` | 维权流水线服务 |
| `services/innocence_proof_service.py` | 清白证明生成服务 |
| `services/c2pa_service.py` | C2PA 内容凭证生成 |
| `services/timestamp_service.py` | RFC 3161 时间戳服务 |
| `services/similarity_service.py` | 相似作品排除分析 |

### 10.2 新增 Gateway

| 文件 | 继承基类 | 职责 |
|------|---------|------|
| `gateway/trademark.py` | ABC | 商标数据库查询 (CNIPA/WIPO/USPTO/EUIPO) |
| `gateway/model_source.py` | ABC | 模型/LoRA 来源查询 (Civitai/HuggingFace) |
| `gateway/tineye.py` | `SearchGateway` | TinEye 以图搜图 |
| `gateway/digicert_tsa.py` | `NotaryGateway` | DigiCert 时间戳服务 |

### 10.3 AI Agent 编排

| Agent | 监听事件 | 编排逻辑 |
|-------|---------|---------|
| `RiskWarningAgent` | works 创建/更新 | 提示词检测 → 参考图检测 → LoRA 检查 → 商标碰撞 → 输出 RiskWarning |
| `EnforcementAgent` | monitor_results 状态变更为 confirmed | 构建证据包 → 选择投诉模板 → 提交投诉 → 追踪状态 |
| `InnocenceProofAgent` | incoming_complaint 事件 | 收集创作证据 → 生成排除报告 → 生成 PDF 反证报告 |

---

## 十一、API 端点汇总

| 模块 | 端点数 | 路由文件 |
|------|--------|----------|
| 存证确权 | 18 | notary.py |
| 侵权监测 | 39 | monitor.py |
| 风险预警 | **6** (新增) | risk_warning.py |
| 维权流水线 | **8** (新增) | enforcement.py |
| 清白证明 | **5** (新增) | innocence_proof.py |
| 品牌监测 | 9 | copyscape.py |
| **合计** | **85** | 6 个路由文件 |

---

## 十二、免责声明（必须在监测页面醒目展示）

> **侵权监测局限性声明** — 黄色警告框，不可折叠:
> "本监测功能基于公开搜索引擎的以图搜图能力（百度识图/Google Vision/TinEye），存在以下局限：
> 1. 不能保证发现所有侵权行为 — 搜索结果受搜索引擎索引范围和算法限制
> 2. 搜索结果需人工审核判断是否构成侵权 — 系统不自动做出侵权认定
> 3. 相似度分数仅为参考 — 高相似度不必然等于侵权，低相似度不必然等于不侵权
> 4. 本功能提供侵权线索发现辅助，不提供法律判断。"

---

## 十三、预留功能设计 (v2/v3/v4)

### 13.1 视频指纹 (v3)

**目标创作者**: 短视频/动画
**技术实现**: ffmpeg 提取关键帧 → imagehash 计算感知哈希 → 汉明距离匹配

API:
| 方法 | 路径 | 说明 | 版本 |
|------|------|------|------|
| POST | /api/monitor/scan-video-fingerprint | 以视频指纹发起侵权扫描 | v3 |
| GET | /api/monitor/video-matches | 视频指纹匹配结果列表 | v3 |
| POST | /api/monitor/content-id/submit | 提交到 YouTube Content ID | v3 |

### 13.2 音频指纹 (v4)

**目标创作者**: 音乐人
**技术实现**: Chromaprint 生成指纹 → AcoustID/Shazam 查询

API:
| 方法 | 路径 | 说明 | 版本 |
|------|------|------|------|
| POST | /api/monitor/generate-audio-fingerprint | 生成音频指纹 | v4 |
| POST | /api/monitor/scan-audio-fingerprint | 发起音频指纹扫描 | v4 |
| GET | /api/monitor/audio-matches | 音频匹配结果列表 | v4 |

### 13.3 文本查重 (v4)

**目标创作者**: 文字作者
**技术实现**: TF-IDF + 第三方 API (百度/阿里云/Turnitin)

API:
| 方法 | 路径 | 说明 | 版本 |
|------|------|------|------|
| POST | /api/monitor/scan-text | 发起文本查重 | v4 |
| GET | /api/monitor/text-matches | 文本匹配结果列表 | v4 |

---

## 十四、C2PA 诚实边界说明（已更新）

**旧设计**（v1-not-implemented）：C2PA 因实现复杂度和虚假安全感问题被推迟。

**新设计**（v1 实现）：
- 使用 Adobe content-auth Python SDK，不重新造轮子
- manifest 自动生成：作品元数据 + SHA-256 + AI 创作会话摘要 + 时间戳
- 嵌入到 JPEG/PNG 的 XMP 元数据块中
- UI 中明确标注: **"C2PA 为技术标识标准，不等同于法律版权证明。法律保护请使用存证确权功能。"**
- 不对"C2PA 能防止侵权"做任何暗示
