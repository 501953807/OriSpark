# OriStudio 全面深化设计 — AI 时代的创作者权益保护与商业撮合平台

> **日期**: 2026-06-25
> **基于**: 用户脑暴确认的五点愿景 + 三大强调原则
> **设计优先级**: 权益保护闭环 > 用户体验 > 多创作者底座 > 商业撮合
> **核心原则**: 新设计优先 | 技术先进性 | 不重新造轮子 | 混合 AI 接入 | 自动化优先 | 合法合规 | 平台中立 | AI 渗透一切

---

## 一、重新定义的产品定位

### 1.1 旧定位 vs 新定位

| 维度 | 旧定位 | 新定位 |
|------|--------|--------|
| 一句话描述 | 个人创作者全链路助手工具 | AI 时代的创作者权益保护与商业撮合平台 |
| 核心价值 | 作品管理→存证→IP→变现→分发 | **创作前预防侵权 → 创作中自动存证 → 创作后自动监测维权 → 商业撮合变现** |
| 创作者类型 | v1 聚焦插画师，其他标注"规划中" | **AI 渗透所有类型**：插画/摄影/视频/音乐/手工/文字都在用 AI |
| 商业模式 | POD + 众筹 + IP 授权 | **三方撮合平台**：创作者-供应商-工厂，系统只做工具不碰交易 |
| 技术特征 | 信息化管理系统 | **AI Agent 编排 + 第三方权威服务集成 + 本地 AI 复用** |

### 1.2 新系统七大核心能力

```
┌──────────────────────────────────────────────────────────────┐
│                    OriStudio 新架构                            │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐  │
│  │  能力 1: 创作前 — 侵权风险预警引擎                       │  │
│  │  提示词检测 · LoRA 权属检查 · 商标/Logo 碰撞 · AI 参考图相似度 │
│  └────────────────────────────────────────────────────────┘  │
│  ┌────────────────────────────────────────────────────────┐  │
│  │  能力 2: 创作中 — AI 辅助创作过程记录                    │  │
│  │  提示词版本追踪 · Seed 值记录 · 迭代参数 · 人工干预点 · 自动存证 │
│  └────────────────────────────────────────────────────────┘  │
│  ┌────────────────────────────────────────────────────────┐  │
│  │  能力 3: 创作后 — 自动存证 + 全网监测                    │  │
│  │  多平台区块链锚定 · 以图搜图 · 视频指纹 · 音频指纹 · 文本查重 │
│  └────────────────────────────────────────────────────────┘  │
│  ┌────────────────────────────────────────────────────────┐  │
│  │  能力 4: 维权 — 自动化维权流水线                          │  │
│  │  侵权评分分级 · 证据包自动生成 · 投诉一键提交 · 进展追踪    │
│  └────────────────────────────────────────────────────────┘  │
│  ┌────────────────────────────────────────────────────────┐  │
│  │  能力 5: 反指控 — 清白证明中心                            │  │
│  │  创作时间线 · 过程证据链 · 独立存证证书 · 自动生成反证报告  │
│  └────────────────────────────────────────────────────────┘  │
│  ┌────────────────────────────────────────────────────────┐  │
│  │  能力 6: 品牌保护 — 商标/Logo 侵权检测                    │  │
│  │  CNIPA 商标库对接 · WIPO 马德里查询 · 相似度判定 · 风险预警 │
│  └────────────────────────────────────────────────────────┘  │
│  ┌────────────────────────────────────────────────────────┐  │
│  │  能力 7: 商业撮合 — 创作者·供应商·工厂三方协作            │  │
│  │  产品匹配 · 订单路由 · 收益分账记录 · 合同工具             │
│  └────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────┘
```

---

## 二、支柱一：权益保护闭环（最高优先级 P0）

### 2.1 模块重新命名

原 "[2] 权利保护中心" 更名为 **"[2] 权益保护中心"**，涵盖以下五大子能力：

| 子能力 | 原模块 | 新增/扩展 |
|--------|--------|----------|
| 自动存证 | notary.py (已有) | 扩展：多平台锚定 + C2PA 实现 + 创作过程存证 |
| 全网监测 | monitor.py (已有) | 扩展：视频/音频/文本指纹 + 自动定时扫描 |
| 维权流水线 | evidence_packages (已有表) | **全新**：侵权评分 → 投诉提交 → 进展追踪 |
| 清白证明 | 无 | **全新**：创作过程证据链 + 反证报告生成 |
| 品牌保护 | brand_watches (已有表) | 扩展：对接 CNIPA/WIPO 商标数据库 |

### 2.2 2.1 创作前：侵权风险预警引擎

#### 2.2.1 功能定义

在创作者**开始创作之前**，系统自动检测潜在侵权风险。这不是一个独立功能，而是**嵌入到每个创作者类型的工作流中**。

#### 2.2.2 四个检测维度

| 检测维度 | 输入 | 检测逻辑 | 第三方服务 | 实现方式 |
|---------|------|---------|-----------|---------|
| **提示词侵权检测** | AI 生成时的 prompt | TF-IDF + 关键词库匹配：检查是否包含注册商标名、知名 IP 角色名、艺术家风格关键词 | 本地关键词库 + USPTO TESS API (可选) | 后端服务 `risk_warning_service.py` |
| **参考图相似度检测** | 用户上传的参考图/灵感图 | 感知哈希 (pHash/dHash) + 余弦相似度，对比作品库和公开图像索引 | 百度识图 API / Google Vision API | 通过现有 SearchGateway 扩展 |
| **LoRA/模型权属检查** | 使用的模型文件名/URL | 查询模型来源数据库，检查是否允许商用、是否署名原作者 | Civitai API / HuggingFace API | Gateway 适配器 `ModelSourceGateway` |
| **商标/Logo 碰撞** | 作品标题/描述/设计中提取的文字 | 对比 CNIPA 商标库 + 自建热门品牌库 | CNIPA 开放查询 / WIPO MADRID / 本地品牌库 | Gateway 适配器 `TrademarkGateway` |

#### 2.2.3 数据模型

```sql
-- 新增：风险预警记录表
CREATE TABLE risk_warnings (
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

CREATE INDEX idx_risk_work ON risk_warnings(work_id);
CREATE INDEX idx_risk_type ON risk_warnings(warning_type);
CREATE INDEX idx_risk_severity ON risk_warnings(severity);
```

#### 2.2.4 API 端点

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | /api/risk-warning/check-prompt | 提示词风险检测 (body: {prompt, reference_images[]}) |
| POST | /api/risk-warning/check-reference | 参考图相似度检测 (body: {image_path}) |
| GET | /api/risk-warning/model-info | 查询模型/LoRA 权属信息 (body: {model_name, source}) |
| POST | /api/risk-warning/check-trademark | 商标碰撞检测 (body: {text, jurisdiction}) |
| GET | /api/risk-warning/history | 获取作品的历史预警记录 |
| PATCH | /api/risk-warning/{id}/dismiss | 标记预警为已查看 |

#### 2.2.5 前端集成

嵌入到作品导入/创建流程的 Step 0（最前面）：

```
作品导入/创建
  → Step 0: 风险预警 (新增)
     - 如果检测到高风险 → 红色阻断 + 建议
     - 如果检测到中风险 → 黄色警告 + 建议
     - 如果低风险 → 不显示
  → Step 1: 选作品信息 (原有)
  → ...
```

组件：`RiskWarningPanel.vue`

### 2.3 2.2 创作中：AI 辅助创作过程记录

#### 2.3.1 核心设计

**所有创作者类型的 AI 使用痕迹自动记录**，形成不可篡改的创作过程证据链。这是 AI 时代版权保护的核心基础设施。

#### 2.3.2 数据模型

```sql
-- 扩展 works 表，新增 AI 创作记录字段
ALTER TABLE works ADD COLUMN ai_assisted BOOLEAN DEFAULT 0;
ALTER TABLE works ADD COLUMN ai_tools_used JSON;
-- ai_tools_used: [{"name": "Midjourney v6", "version": "6.0", "usage": "image_generation"}, ...]

-- 新增：AI 创作会话记录表
CREATE TABLE ai_creation_sessions (
    id TEXT PRIMARY KEY,
    work_id TEXT NOT NULL REFERENCES works(id) ON DELETE CASCADE,
    tool_name TEXT NOT NULL,         -- 'Midjourney' / 'StableDiffusion' / 'DALL-E' / 'Custom'
    tool_version TEXT,
    prompt TEXT NOT NULL,            -- 原始提示词
    prompt_history JSON,             -- 提示词迭代历史: [{"version": 1, "text": "...", "timestamp": "..."}, ...]
    seed INTEGER,                    -- Seed 值
    parameters JSON,                 -- 模型参数: {steps: 30, cfg: 7, sampler: 'DPM++ 2M', ...}
    negative_prompt TEXT,            -- 反向提示词
    model_name TEXT,                 -- 使用的模型/LoRA 名称
    lora_names JSON,                 -- 使用的 LoRA: ["coolStyle_v2.safetensors", ...]
    output_images JSON,              -- 输出图片路径: ["data/xxx/a1.png", ...]
    human_interventions JSON,        -- 人工干预点: [{"type": "inpainting", "step": 5, "description": "重绘面部"}, ...]
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_ai_session_work ON ai_creation_sessions(work_id);
```

#### 2.3.3 自动记录策略

| 场景 | 自动记录内容 | 用户操作 |
|------|-------------|---------|
| 通过 API 调用 AI 生成 | prompt + seed + parameters + 输出自动记录 | 无需操作 |
| 本地 Ollama/ComfyUI 生成 | 通过 ComfyUI webhook 或 API 回调记录 | 需配置 webhook |
| 手动上传 AI 生成图 | 询问"是否 AI 生成？" → 填写工具名 + prompt | 一次性填写 |
| 迭代修改（如 Midjourney Vary Region） | 记录每次修改的 prompt 变化 + 修改区域 | 自动记录 |

#### 2.3.4 API 端点

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | /api/works/{id}/ai-session | 记录 AI 创作会话 |
| GET | /api/works/{id}/ai-sessions | 获取作品的 AI 创作时间线 |
| PATCH | /api/works/{id}/ai-session/{sid} | 编辑会话记录 |
| DELETE | /api/works/{id}/ai-session/{sid} | 删除会话记录 |

### 2.4 2.3 创作后：自动存证 + 全网监测

#### 2.4.1 多平台存证增强

**现有能力**：notary.py 已支持版权家、蚂蚁链、至信链。

**新增能力**：

| 存证维度 | 现有 | 新增 | 说明 |
|---------|------|------|------|
| SHA-256 哈希 | ✅ | 保留 | 基础文件指纹 |
| 区块链锚定 | ✅ (蚂蚁链/至信链) | 扩展：Polygon/Ethereum | 增加国际认可的公链 |
| C2PA 内容凭证 | ❌ | **v1 实现** | 嵌入 Content Credentials 到文件元数据 |
| 创作过程存证 | ❌ | **v1 实现** | ai_creation_sessions 自动上链 |
| 权威时间戳 | ❌ | **v1 实现** | 对接 RFC 3161 TTS 服务机构 |

**C2PA 实现方案（不重新造轮子）**：
- 使用 [C2PA-RS](https://github.com/contentauth/c2pa-rs) 编译为 Python binding，或通过 subprocess 调用 c2pa-tool
- 或使用 [Adobe's content-auth](https://github.com/adobe/content-auth) Python SDK
- manifest 自动生成：包含作品元数据 + SHA-256 + AI 创作会话摘要 + 时间戳
- 嵌入到 JPEG/PNG 的 XMP 元数据块中

**时间戳服务对接**：
- 首选：[DigiCert Timestamp Service](https://www.digicert.com/code-signing/tsa.htm) (RFC 3161)
- 备选：[GlobalSign TSA](https://www.globalsign.com/en/timestamp-service)
- 费用：约 $0.15/次，远低于区块链存证

#### 2.4.2 全网监测增强

**现有能力**：monitor.py 已支持百度识图、Google Vision。

**扩展维度**：

| 监测维度 | v1 现状 | v1 新增 | 第三方服务 |
|---------|---------|---------|-----------|
| 图片以图搜图 | ✅ 百度/Google | 扩展：TinEye API | TinEye (付费，准确率最高) |
| 视频指纹监测 | 预留 | **v1 预留数据结构，v3 实现** | 灵创/维权骑士 API |
| 音频指纹监测 | 无 | **v1 预留，v4 实现** | AcoustID API |
| 文本相似度 | 无 | **v1 预留，v4 实现** | 百度内容审核 API |
| 电商平台监测 | 预留 (brand_watches) | **v1 实现淘宝/拼多多/闲鱼** | 百度识图 + 爬虫 |
| 社交媒体监测 | 无 | **v1 预留** | Twitter/Instagram API |

**自动监测调度增强**：
- 现有：Celery Beat 每周扫描一次
- 新增：**按作品重要度分级调度**
  - 高重要度（已存证+有IP登记）：每日扫描
  - 中重要度（已存证）：每3天扫描
  - 低重要度（未存证）：每月扫描或手动
- priority_score 字段已存在于 MonitorTask 表，需实现评分算法

#### 2.4.3 数据模型扩展

```sql
-- 扩展 notary_records 表
ALTER TABLE notary_records ADD COLUMN blockchain_type TEXT DEFAULT 'antchain';
-- 'antchain' / 'zhixinchain' / 'polygon' / 'ethereum' / 'tts_timestamp'
ALTER TABLE notary_records ADD COLUMN c2pa_manifest_path TEXT;
ALTER TABLE notary_records ADD COLUMN timestamp_token_path TEXT;

-- 新增：作品重要度评分表
CREATE TABLE work_priority_scores (
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

### 2.5 2.4 维权流水线（全新核心模块）

这是整个权益保护闭环中最关键的增量——**发现侵权后的一站式维权处理**。

#### 2.5.1 维权流水线状态机

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

#### 2.5.2 数据模型

```sql
-- 扩展现有 monitor_results 表，增加维权流程字段
-- monitor_results.status 扩展:
-- 'pending_review' / 'confirmed' / 'evidence_gathered' / 'complaint_filed' / 'resolved_takedown' / 'resolved_disputed' / 'ignored' / 'whitelisted'

-- 新增：维权行动记录表
CREATE TABLE enforcement_actions (
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
CREATE TABLE enforcement_templates (
    id TEXT PRIMARY KEY,
    platform TEXT NOT NULL,       -- 'taobao' / 'instagram' / 'google' / 'generic'
    jurisdiction TEXT NOT NULL,   -- 'cn' / 'us' / 'eu' / 'global'
    action_type TEXT NOT NULL,    -- 'dmca' / 'copyright' / 'trademark' / 'design_right'
    title TEXT NOT NULL,          -- 模板标题
    body_template TEXT NOT NULL,  -- 带 {{placeholders}} 的模板正文
    required_evidence JSON,       -- 需要的证据清单: ["certificate", "original_file", "timestamp"]
    filing_url TEXT,              -- 投诉提交URL
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 种子数据：预置主流平台投诉模板
INSERT INTO enforcement_templates VALUES
('tpl_dmca_us', 'us', 'dmca', 'DMCA Takedown Notice (US)',
 'Under Section 512(c) of the DMCA... {{work_title}}... {{copyright_notice}}...',
 '["certificate", "original_file"]',
 'https://www.google.com/forms/surveillance', '2026-06-25'),
('tpl_copyright_cn', 'cn', 'copyright', '著作权投诉模板 (中国)',
 '依据《中华人民共和国著作权法》... {{work_title}}... {{author_name}}...',
 '["certificate", "original_file", "ai_session"]',
 '', '2026-06-25');
```

#### 2.5.3 证据包自动生成（增强版）

现有 `EvidencePackage` 表已存在，需增强：

**自动收集的证据清单**：

| 证据类型 | 来源 | 说明 |
|---------|------|------|
| 原始文件 | works.file_path | 上传的原始作品 |
| SHA-256 哈希 | works.sha256 | 文件指纹 |
| 存证证书 | notary_records + certificates | 区块链存证回执 + PDF 证书 |
| C2PA manifest | c2pa_records.manifest_json | 内容凭证 |
| 创作时间线 | ai_creation_sessions | 完整 AI 创作会话记录 |
| 版本历史 | work_versions | 所有版本快照 |
| 侵权页面截图 | monitor_results.screenshot_path | Playwright 抓取的侵权页面 |
| 侵权 URL 取证 | 新增: enforcement_evidence.url_proof | 区块链存证的 URL 快照 |
| 存证时间对比 | notary_records.created_at | 证明存证时间早于侵权发现时间 |

**证据包生成服务**：

```python
# backend/app/services/enforcement_service.py

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

#### 2.5.4 投诉一键提交

**核心设计**：针对不同平台提供不同的投诉提交方式：

| 平台类型 | 提交方式 | 实现 |
|---------|---------|------|
| 有官方投诉通道的平台 | 自动生成投诉函 + 打开投诉页面（预填） | 构造 URL 带参数打开 |
| 支持 API 投诉的平台 | 通过 API 直接提交 | Gateway 适配器 |
| 仅支持手动投诉的平台 | 生成完整投诉材料包（PDF + ZIP） | 用户手动提交 |

**预填投诉 URL 示例**：
- Google: `https://forms.google.com/dmca?work=xxx`
- Instagram (Meta): 通过 Meta Copyright Portal
- 淘宝: 通过 Alipay 知识产权平台
- Redbubble/Society6: 站内 DMCA 表单 + 预填好表单内容

#### 2.5.5 进展追踪

| 功能 | 说明 |
|------|------|
| 投诉状态轮询 | 对支持 API 的平台，定期查询投诉状态 |
| 人工标记 | 用户对不支持 API 的平台，手动标记"已处理"/"未处理" |
| 提醒通知 | 投诉后 7 天无回应 → 提醒跟进；对方申诉 → 通知创作者 |
| 统计数据 | 维权成功率、平均处理时长、各平台投诉效率 |

#### 2.5.6 API 端点

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

### 2.6 2.5 清白证明中心（全新模块）

#### 2.6.1 场景定义

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

#### 2.6.2 数据模型

```sql
-- 新增：清白证明请求表
CREATE TABLE innocence_proofs (
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
CREATE TABLE similarity_exclusions (
    id TEXT PRIMARY KEY,
    innocence_proof_id TEXT REFERENCES innocence_proofs(id),
    compared_work_id TEXT NOT NULL,  -- 被指控相似的对方作品
    similarity_score FLOAT,           -- 相似度 (越低越好)
    hash_comparison JSON,             -- SHA-256 对比
    perceptual_comparison JSON,       -- 感知哈希对比
    conclusion TEXT,                  -- 结论: "独立创作，相似度低于阈值"
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

#### 2.6.3 API 端点

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | /api/innocence-proof/build | 构建清白证据包 |
| GET | /api/innocence-proof/{id} | 获取清白证明状态 |
| GET | /api/innocence-proof/{id}/download | 下载反证报告 |
| POST | /api/innocence-proof/{id}/send | 发送给指控方 |
| POST | /api/innocence-proof/auto-on-complaint | 自动触发（接入侵权监测结果） |

### 2.7 2.6 品牌保护：商标/Logo 侵权检测

#### 2.7.1 双向保护设计

系统不仅要帮创作者**防止被别人侵权**，还要帮创作者**避免无意中侵犯别人的商标**：

| 方向 | 场景 | 系统行为 |
|------|------|---------|
| 正向保护 | 别人用了我的作品 | 监测 + 维权流水线 |
| 反向保护 | 我用了我不该用的商标/Logo | 创作前风险预警（2.2 节） |
| 品牌监控 | 有人假冒我的品牌 | BrandWatch 扩展 + 电商平台监测 |

#### 2.7.2 商标数据库对接

**不重新造轮子**，对接权威官方数据源：

| 数据源 | 覆盖范围 | 对接方式 | 费用 |
|--------|---------|---------|------|
| **CNIPA 中国商标网** | 中国 | 开放数据查询 API（如有）或结构化爬虫 | 免费 |
| **WIPO MADRID** | 国际 | Madrid Monitor API | 免费 |
| **USPTO TESS** | 美国 | TESS API | 免费 |
| **EUIPO eSearch** | 欧盟 | eSearch Plus API | 免费 |
| **自建热门品牌库** | 全球 | 维护文创领域常见品牌列表 | 免费 |

**TrademarkGateway 适配器设计**：

```python
# backend/app/gateway/trademark.py

class TrademarkGateway(ABC):
    @abstractmethod
    async def search(self, mark_name: str, classes: list[str], jurisdiction: str) -> list[TrademarkResult]:
        """搜索商标"""
        ...

    @abstractmethod
    async def check_logo_similarity(self, logo_image_path: str, jurisdiction: str) -> list[TrademarkResult]:
        """Logo 图像相似度搜索"""
        ...

class CNIPATrademarkGateway(TrademarkGateway):
    """CNIPA 商标查询适配器"""
    ...

class WiPoTrademarkGateway(TrademarkGateway):
    """WIPO MADRID 适配器"""
    ...
```

#### 2.7.3 数据模型

```sql
-- 扩展现有 brand_watches 表
-- brand_watches 已有: brand_name, keywords, platforms, is_active

-- 新增：商标监测记录
CREATE TABLE trademark_monitor_logs (
    id TEXT PRIMARY KEY,
    brand_watch_id TEXT REFERENCES brand_watches(id),
    search_query TEXT NOT NULL,
    results_count INTEGER DEFAULT 0,
    new_matches JSON,  -- [{"url": "...", "similarity": 85, "title": "..."}, ...]
    scanned_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

---

## 三、支柱二：用户体验全面优化（P1）

### 3.1 向导式交互框架

所有复杂流程统一为向导式步骤，系统在每个步骤中**自动处理技术细节，用户只需确认**。

#### 3.1.1 通用向导组件

```
frontend/src/components/wizard/
├── WizardStepper.vue        # 步骤指示器（已有，复用）
├── WizardFrame.vue          # 向导容器（新增）
│   Props: { steps: Step[], autoSave: boolean, onCancel: fn }
│   功能: 步骤导航 + 草稿自动保存(Pinia) + 关闭确认 + 进度持久化
├── WizardStore.ts           # 向导状态管理（新增）
│   - 当前步骤、已完成步骤、草稿数据
│   - localStorage + Pinia 双持久化
│   - 页面刷新后可恢复
```

#### 3.1.2 关键向导场景

| 向导名称 | 触发入口 | 步骤数 | 说明 |
|---------|---------|--------|------|
| **快速存证向导** | 作品详情页 | 3步 | 选平台→确认→查看证书 |
| **侵权处理向导** | 监测结果列表 | 4步 | 确认侵权→构建证据→选择投诉→提交追踪 |
| **IP 登记向导** | IP 登记模块 | 5步 | (已有，保持不变) |
| **产品设计器向导** | 商业转化 | 7步 | (已有，保持不变) |
| **被指控应对向导** | 收到指控通知 | 5步 | 分析指控→构建反证→审核→发送 |
| **新创作者 Onboarding** | 首次登录 | 3步 | (已有，保持不变) |

### 3.2 智能通知系统

| 事件 | 通知方式 | 时机 |
|------|---------|------|
| 发现疑似侵权 | 站内通知 + WebSocket | 实时 |
| 侵权投诉已提交 | 站内通知 | 实时 |
| 投诉被受理/拒绝 | 邮件 + 站内通知 | 平台回调 |
| 作品存证完成 | 站内通知 | 实时 |
| 商标预警 | 站内通知 | 创作时 |
| 维权进展更新 | 站内通知 | 状态变更时 |

### 3.3 空状态和引导优化

在权益保护相关的空状态中加入引导：

| 场景 | 标题 | CTA |
|------|------|-----|
| 无存证作品 | "你的作品还没有存证" | "选择作品快速存证" |
| 无监测结果 | "暂无侵权监测结果" | "启动首次扫描" |
| 无维权记录 | "还没有维权记录" | "了解维权流程" |
| 无风险预警 | "创作前请先检测风险" | "导入作品并开始创作" |

---

## 四、支柱三：多创作者类型统一底座（P2）

### 4.1 设计原则

**AI 是渗透性能力，不是独立模块**。每种创作者类型的工作流中，AI 辅助记录、风险预警、智能监测自然嵌入。

### 4.2 创作者类型统一框架

```
CreatorType (创作者类型)
  ├── 基础属性 (所有类型共有)
  │   ├── 作品导入
  │   ├── AI 创作记录
  │   ├── 存证
  │   ├── 监测
  │   └── 维权
  │
  └── 专属能力 (按类型激活)
      ├── 插画师/AIGC (v1 完整)
      │   ├── 图片格式全支持
      │   ├── EXIF 元数据
      │   ├── 版本管理 (灵感→草图→线稿→上色→细节→终稿)
      │   └── Canvas Mockup 预览
      │
      ├── 摄影师 (v2)
      │   ├── RAW 解码 (rawpy)
      │   ├── EXIF 高级搜索
      │   ├── 选片模式 (Culling)
      │   ├── 水印预设
      │   └── 图库销售
      │
      ├── 视频创作者 (v3)
      │   ├── 工程文件项目包
      │   ├── 字幕管理
      │   ├── 视频指纹
      │   └── 横竖屏版本
      │
      ├── 音乐人 (v4)
      │   ├── ISRC/ISWC 管理
      │   ├── 专辑/EP/Single
      │   ├── Split Sheets (合作者分配)
      │   ├── Master vs Publishing 权利
      │   └── 音频指纹
      │
      ├── 手工艺人 (v3)
      │   ├── 物理原件管理
      │   ├── 原料库存
      │   ├── 生产批次
      │   └── 质检分级
      │
      └── 文字作者 (v4)
          ├── 章节结构
          ├── EPUB 导出
          ├── 权利细分
          └── 文本查重
```

### 4.3 数据模型扩展

```sql
-- works 表已预留 perceptual_hash / perceptual_hash_type
-- 需新增 creator_type 字段以支持类型化工作流

ALTER TABLE works ADD COLUMN creator_type TEXT DEFAULT 'illustrator';
-- 'illustrator' / 'photographer' / 'videographer' / 'musician' / 'craftsman' / 'writer'

-- 扩展 custom_metadata 的通用 AI 字段路径
-- {
--   "ai_assisted": true,
--   "ai_tools": [...],
--   "exif": {...},          -- 摄影师
--   "music": {...},         -- 音乐人 (ISRC 等)
--   "video": {...},         -- 视频 (工程文件)
--   "literary": {...}       -- 文字 (章节)
-- }
```

---

## 五、支柱四：商业撮合平台（P3）

### 5.1 平台定位重申

**系统不做交易、不碰钱、不当中间商**。系统提供工具，让三方高效协作：

```
创作者 (Design)         系统工具平台           供应商/工厂 (Make)
    │                       │                      │
    │  1. 上传设计稿          │                      │
    │  2. 选择可承接的工厂    │  智能匹配引擎         │
    │  3. 发起询价            │──── 推荐 ──────────▶ │
    │                       │                      │
    │◀── 4. 工厂报价          │                      │
    │  5. 下单                │  订单管理工具          │
    │──────────────────────▶ │──────── 转发 ────────▶ │
    │                       │                      │
    │                       │  进度追踪工具           │
    │◀══════════ 5. 交付产品 ══│                      │
    │                       │                      │
    │  6. 收益分账记录        │  分账记录工具          │  供应商集采/分销
    │──────────────────────▶ │──────── 记录 ────────▶ │
```

### 5.2 新增/调整的数据模型

```sql
-- 扩展现有 partners 表，明确三方角色
-- partners.type 扩展值:
-- 'manufacturer' (工厂) / 'supplier' (供应商/经销商/众筹者) / 'pod_platform' (POD平台) / 'fulfillment' (履约服务商)

-- 新增：撮合订单表（区别于现有 Order 表，用于三方协作）
CREATE TABLE marketplace_orders (
    id TEXT PRIMARY KEY,
    creator_id TEXT NOT NULL,              -- 创作者
    supplier_id TEXT,                      -- 供应商 (可为空，工厂直连创作者时无需供应商)
    factory_id TEXT NOT NULL,              -- 工厂
    listing_id TEXT REFERENCES design_listings(id),  -- 关联商品
    order_type TEXT NOT NULL,              -- 'custom_mfg' / 'crowdfunding_fulfillment' / 'bulk_purchase' / 'drop_ship'
    quantity INTEGER NOT NULL,
    unit_price FLOAT,
    total_amount FLOAT,
    status TEXT NOT NULL,                  -- 'quoted' / 'confirmed' / 'in_production' / 'shipped' / 'delivered' / 'disputed'
    quote_details JSON,                    -- 工厂报价详情
    contract_path TEXT,                    -- 合同文件
    revenue_split JSON,                    -- 分账: {"creator": 60, "supplier": 20, "factory": 20}
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 新增：工厂能力目录
CREATE TABLE factory_catalogs (
    id TEXT PRIMARY KEY,
    partner_id TEXT NOT NULL REFERENCES partners(id),
    category TEXT NOT NULL,                -- 品类: 'textile' / 'paper' / 'ceramic' / ...
    products JSON,                         -- 可生产的产品列表
    min_order_quantity INTEGER,            -- 最小起订量
    lead_time_days INTEGER,                -- 交付周期
    price_tiers JSON,                      -- 阶梯报价: [{"qty_min": 1, "price": 45}, ...]
    certifications JSON,                   -- 资质认证
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

### 5.3 智能匹配引擎

**匹配逻辑**：根据设计稿的品类和需求，自动推荐合适的工厂和供应商：

```python
# backend/app/services/matching_service.py

class MatchingService:
    def match_factory(self, listing: DesignListing, quantity: int) -> list[FactoryMatch]:
        """
        匹配工厂: 基于品类 + 数量 + 材质要求
        返回排序后的工厂列表，按综合评分排序:
          - 价格匹配度 (40%)
          - 交期匹配度 (30%)
          - 历史合作评分 (20%)
          - 资质匹配度 (10%)
        """
        ...

    def match_supplier(self, listing: DesignListing) -> list[SupplierMatch]:
        """
        匹配供应商: 基于产品类型和变现路径
        优先匹配有该品类众筹经验或分销渠道的供应商
        """
        ...
```

### 5.4 现有 supply.py 模块的调整

| 现有实体 | 调整 |
|---------|------|
| Partner | type 字段增加 'supplier' 和 'fulfillment' 值；增加 rating/历史合作数据 |
| Order | 增加 marketplace_order_id FK，区分"传统供应链订单"和"撮合订单" |
| campaigns | 增加 supplier_id FK，标注供应商参与的众筹 |
| 新增 | MarketplaceOrder + FactoryCatalog |

---

## 六、AI Agent 架构设计

### 6.1 AI 能力接入策略

| 原则 | 说明 |
|------|------|
| **核心链路固定** | 存证区块链、IP 登记、商标查询使用权威固定接口，不可随意更换 |
| **非核心灵活** | 侵权检测、AI 文案、定价建议可配置切换 |
| **本地优先** | 检测到本机有 Ollama/Claude 等则优先使用，其次云端 API |
| **不重新造轮子** | 使用现有第三方 API，系统只做编排和自动化 |

### 6.2 固定接入（不可更换）

| 能力 | 默认接入 | 备选 | 说明 |
|------|---------|------|------|
| 区块链存证 | 蚂蚁链 + 版权家 | Polygon | 国内司法认可 |
| 国际存证 | Polygon | Ethereum | 国际认可 |
| 时间戳 | DigiCert TSA | GlobalSign | RFC 3161 |
| IP 登记 | CNIPA 官方 | — | 唯一来源 |
| 商标查询 | CNIPA + WIPO + USPTO | EUIPO | 权威数据源 |

### 6.3 灵活接入（用户可配置）

| 能力 | 默认 | 备选 | 配置位置 |
|------|------|------|---------|
| 以图搜图 | 百度识图 + Google Vision | TinEye | 设置 → 监测引擎 |
| AI 文案 | 主流大模型 API | 本地 Ollama | 设置 → AI 引擎 |
| 风险预警关键词库 | 本地内置 | + USPTO TESS API | 自动 |
| 视频指纹 | 本地 imagehash | 灵创 API | 设置 → 监测引擎 |

### 6.4 AI Agent 编排层

系统内部使用 AI Agent 编排各步骤，对外表现为"自动化"：

```
EnforcementAgent (维权 Agent)
  ├── 监听: monitor_results 状态变更 (confirmed)
  ├── 决策: 评估侵权严重度 → 选择维权策略
  ├── 编排:
  │   ├── 调用 EvidenceService 构建证据包
  │   ├── 调用 TemplateService 选择投诉模板
  │   ├── 调用 TrademarkGateway 验证权利基础
  │   └── 调用 NotificationService 通知创作者
  └── 执行: 提交投诉 → 追踪状态 → 升级处理

RiskWarningAgent (风险预警 Agent)
  ├── 监听: works 创建/更新事件
  ├── 编排:
  │   ├── 调用 PromptScanner 检测提示词风险
  │   ├── 调用 ReferenceScanner 检测参考图相似度
  │   ├── 调用 ModelSourceGateway 检查 LoRA 权属
  │   └── 调用 TrademarkGateway 检测商标碰撞
  └── 输出: 生成 RiskWarning 记录

InnocenceProofAgent (清白证明 Agent)
  ├── 监听: 用户触发 or incoming_complaint 事件
  ├── 编排:
  │   ├── 调用 EvidenceService 收集创作证据链
  │   ├── 调用 SimilarityService 生成排除报告
  │   └── 调用 ReportGenerator 生成 PDF
  └── 输出: InnocenceProof 记录
```

### 6.5 MCP 协议集成

**通过 MCP 连接外部智能体**，不重复造轮子：

| 用途 | 连接的 MCP 服务 | 说明 |
|------|----------------|------|
| 本地 AI 推理 | Ollama MCP Server | 调用本地大模型做文本分析和分类 |
| 商标查询 | CNIPA MCP Adapter (自建) | 结构化查询 CNIPA 商标数据库 |
| 法律条文检索 | 外部法律知识库 MCP | 查询相关法律法规，辅助生成合规投诉函 |
| 图像分析 | Google Vision MCP | 以图搜图和图像分析 |

---

## 七、模块边界调整

### 7.1 新旧模块对照

| 旧模块名 | 新模块名 | 变化 |
|---------|---------|------|
| [1] 创意资产中心 | **[1] 创意资产中心** | 不变，增加 AI 创作记录 |
| [2] 权利保护中心 | **[2] 权益保护中心** | 更名，新增维权流水线、清白证明、品牌保护 |
| [3] IP 登记工作站 | **[3] IP 登记工作站** | 不变，增加商标查询联动 |
| [4] 商业转化引擎 | **[4] 商业撮合平台** | 更名，从"变现工具"变为"三方协作工具" |
| [5] 内容分发中心 | **[5] 内容分发中心** | 不变 |
| [6] 经营管理中心 | **[6] 经营管理中心** | 不变，增加维权统计 |
| [7] 系统基础设施 | **[7] 系统基础设施** | 新增风险预警、AI Agent 编排层 |

### 7.2 新增文件清单

| 文件 | 用途 |
|------|------|
| `backend/app/services/risk_warning_service.py` | 侵权风险预警引擎 |
| `backend/app/services/enforcement_service.py` | 维权流水线服务 |
| `backend/app/services/innocence_proof_service.py` | 清白证明生成服务 |
| `backend/app/services/matching_service.py` | 商业匹配引擎 |
| `backend/app/services/c2pa_service.py` | C2PA 内容凭证生成 |
| `backend/app/services/timestamp_service.py` | RFC 3161 时间戳服务 |
| `backend/app/services/similarity_service.py` | 相似作品排除分析 |
| `backend/app/gateway/trademark.py` | 商标数据库网关适配器 |
| `backend/app/gateway/model_source.py` | 模型/LoRA 来源查询网关 |
| `backend/app/gateway/tineye.py` | TinEye 以图搜图网关 |
| `backend/app/gateway/digicert_tsa.py` | DigiCert 时间戳网关 |
| `backend/app/models/risk_warning.py` | 风险预警数据模型 |
| `backend/app/models/enforcement.py` | 维权行动数据模型 |
| `backend/app/models/innocence_proof.py` | 清白证明数据模型 |
| `backend/app/models/marketplace.py` | 商业撮合数据模型 |
| `backend/app/models/ai_session.py` | AI 创作会话数据模型 |
| `backend/app/models/enforcement_template.py` | 投诉模板数据模型 |
| `backend/app/models/work_priority.py` | 作品重要度评分 |
| `frontend/src/views/RiskWarningView.vue` | 风险预警页面 |
| `frontend/src/views/EnforcementView.vue` | 维权管理中心 |
| `frontend/src/views/InnocenceProofView.vue` | 清白证明中心 |
| `frontend/src/views/MarketplaceView.vue` | 商业撮合工作台 |
| `frontend/src/components/wizard/WizardFrame.vue` | 通用向导容器 |
| `frontend/src/components/wizard/EnforcementWizard.vue` | 维权向导 |
| `frontend/src/components/wizard/InnocenceWizard.vue` | 被指控应对向导 |
| `frontend/src/stores/useWizardStore.ts` | 向导状态管理 |
| `frontend/src/stores/useEnforcementStore.ts` | 维权状态管理 |

### 7.3 需重构的现有文件

| 文件 | 变更 |
|------|------|
| `backend/app/models/notary.py` | 扩展: 增加 c2pa_manifest_path, timestamp_token_path, blockchain_type |
| `backend/app/models/monitor.py` | 扩展: monitor_results 增加维权状态字段; 增强 EvidencePackage |
| `backend/app/models/monitor_ext.py` | 扩展: brand_watches 增加商标关联 |
| `backend/app/models/supply.py` | 扩展: partners.type 增加 supplier/fulfillment; 新增 marketplace_orders |
| `backend/app/models/work.py` | 扩展: 增加 ai_assisted, ai_tools_used, creator_type |
| `backend/app/routers/notary.py` | 扩展: C2PA 生成 + 时间戳服务 |
| `backend/app/routers/monitor.py` | 扩展: 维权流水线 + 作品重要度评分 |
| `backend/app/routers/supply.py` | 扩展: 商业撮合 API |
| `backend/app/gateway/base.py` | 扩展: 新增 NotaryGateway 新方法 (c2pa/timestamp) |
| `backend/app/gateway/baidu_vision.py` | 扩展: 增加电商监测能力 |
| `backend/app/gateway/zhixinchain.py` | 扩展: 增加 URL 取证能力 |

---

## 八、实施路线图（按优先级）

### Phase 0: 权益保护基础 (P0, 5-7天)

| 任务 | 文件 | 说明 |
|------|------|------|
| 风险预警引擎 | risk_warning_service.py + gateway/trademark.py | 提示词检测 + 商标碰撞 |
| AI 创作会话记录 | ai_session.py + works 扩展 | 记录 prompt/seed/参数 |
| C2PA 内容凭证 | c2pa_service.py + notary.py 扩展 | 嵌入 Content Credentials |
| 多平台存证扩展 | gateway/digicert_tsa.py + polygon | 增加 Polygon + 时间戳 |

### Phase 1: 维权流水线 (P0, 7-10天)

| 任务 | 文件 | 说明 |
|------|------|------|
| 证据包自动生成 | enforcement_service.py | 一键构建完整证据 |
| 投诉模板 + 一键提交 | enforcement.py + templates | 预置主流平台模板 |
| 维权行动追踪 | enforcement_actions 表 + API | 状态机 + 进展追踪 |
| 清白证明中心 | innocence_proof_service.py | 反证报告自动生成 |

### Phase 2: 用户体验优化 (P1, 4-5天)

| 任务 | 文件 | 说明 |
|------|------|------|
| 通用向导容器 | WizardFrame.vue + WizardStore.ts | 所有复杂流程统一 |
| 维权向导 | EnforcementWizard.vue | 4步引导完成维权 |
| 被指控应对向导 | InnocenceWizard.vue | 5步引导完成反证 |
| 智能通知增强 | WebSocket + 通知模板 | 维权进展实时通知 |

### Phase 3: 商业撮合 (P2, 5-7天)

| 任务 | 文件 | 说明 |
|------|------|------|
| 撮合数据模型 | marketplace.py | 三方协作表结构 |
| 智能匹配引擎 | matching_service.py | 工厂/供应商推荐 |
| 商业撮合工作台 | MarketplaceView.vue | 三方协作 UI |

### Phase 4: 多创作者扩展 (P2, 按版本)

| 版本 | 内容 |
|------|------|
| v2 | 摄影师: RAW + EXIF搜索 + 选片 + 水印 |
| v3 | 视频: 工程包 + 字幕 + 视频指纹 |
| v3 | 手工: 原料库存 + 生产批次 + 质检 |
| v4 | 音乐: ISRC + 专辑 + Split Sheets + 音频指纹 |
| v4 | 文字: 章节 + EPUB + 文本查重 |

---

## 九、关键技术决策

| 决策 | 选择 | 理由 |
|------|------|------|
| 区块链存证 | 蚂蚁链+至信链(国内) + Polygon(国际) | 国内司法认可 + 国际通用 |
| C2PA 实现 | Adobe content-auth Python SDK | 不重新造轮子，官方 SDK |
| 时间戳 | DigiCert TSA (RFC 3161) | 行业标准，全球认可 |
| 商标查询 | CNIPA + WIPO + USPTO 官方数据 | 权威数据源，不自建 |
| 以图搜图 | 百度+Google(默认) + TinEye(可选) | 免费额度够用，TinEye 精度最高 |
| AI 推理 | 本地 Ollama 优先 + 云端 API 备选 | 隐私 + 成本 + 可用性 |
| Agent 编排 | 内部 Python 服务 + Celery | 不引入外部 Agent 框架，保持轻量 |
| MCP 集成 | 按需接入外部 MCP 服务 | 仅在需要连接外部智能体时使用 |
| 维权模板 | 预置 DMCA + 中国著作权法模板 | 覆盖主流场景，用户可自定义 |
| 撮合平台 | 纯工具模式，不碰资金 | 符合"平台中立"定位，合规风险最低 |
