# OriStudio 系统设计总纲

> **日期**: 2026-06-25 (全面深化)
> **基于**: 9角色评估报告 + 用户脑暴五点愿景
> **核心定位**: AI 时代的创作者权益保护与商业撮合平台
> **模块设计**: [docs/modules-v3/](modules-v3/) — 7 个模块详细设计

---

## 一、产品定位

### 1.1 一句话描述

OriStudio 是一个在个人电脑上本地运行的 B/S 架构桌面应用，帮助独立创作者完成从**创作前风险预警 → 创作中自动存证 → 创作后自动监测维权 → 商业撮合变现**的全流程闭环。

### 1.2 七大核心能力

```
┌──────────────────────────────────────────────────────────────┐
│                    OriStudio 七大核心能力                       │
│                                                              │
│  ① 创作前 — 侵权风险预警引擎                                   │
│     提示词检测 · LoRA 权属检查 · 商标/Logo 碰撞 · 参考图相似度 │
│                                                              │
│  ② 创作中 — AI 辅助创作过程记录                                │
│     提示词版本追踪 · Seed 值记录 · 迭代参数 · 人工干预点        │
│                                                              │
│  ③ 创作后 — 自动存证 + 全网监测                                │
│     多平台区块链锚定 · C2PA 内容凭证 · 以图搜图 · 视频/音频指纹 │
│                                                              │
│  ④ 维权 — 自动化维权流水线                                     │
│     侵权评分分级 · 证据包自动生成 · 投诉一键提交 · 进展追踪     │
│                                                              │
│  ⑤ 反指控 — 清白证明中心                                       │
│     创作时间线 · 过程证据链 · 独立存证证书 · 反证报告           │
│                                                              │
│  ⑥ 品牌保护 — 商标/Logo 侵权检测                               │
│     CNIPA 商标库对接 · WIPO 马德里查询 · 相似度判定            │
│                                                              │
│  ⑦ 商业撮合 — 创作者·供应商·工厂三方协作                       │
│     产品匹配 · 订单路由 · 收益分账记录 · 合同工具               │
│                                                              │
│  技术特征: AI Agent 编排 + MCP 协议集成 + 第三方权威服务        │
│  核心原则: 不重复造轮子 · 混合 AI 接入 · 平台中立 · 合法合规    │
└──────────────────────────────────────────────────────────────┘
```

### 1.3 核心特性

- **数据主权**：所有数据存储在本地，不上传原始文件
- **不重复造轮子**：通过现有平台 API 实现存证/搜索/发布/商标查询
- **渐进复杂度**：新手只看到基础功能，高级功能可扩展
- **离线优先**：核心功能（哈希计算、本地搜索）无需网络
- **AI Agent 编排**：对外表现为"自动化"，内部使用 Celery + Agent 模式
- **MCP 协议集成**：按需连接外部智能体（Ollama/CNIPA/Google Vision/法律知识库）

### 1.4 v1 聚焦插画师 — 边界定义

**v1 包含（插画师完整支持）**：
- 作品管理：图片格式导入 (PNG/JPG/PSD/TIFF/WebP), 系列/版本管理, AI 创作记录
- 权益保护：SHA-256 哈希, C2PA 内容凭证, 多平台区块链锚定, 时间戳服务, 全网监测, 维权流水线, 清白证明
- IP 登记：著作权/商标/外观设计指引, 尼斯分类多推荐+置信度, 律师审核步骤, 7项免责声明
- 商业撮合：产品设计器, Canvas 叠加预览, POD 渠道管理, 众筹管理, IP 授权管理, 智能匹配
- 内容分发：社交媒体平台 (小红书/站酷/B站/微博/Instagram), AI 文案, 排期发布
- 收入追踪：多渠道收入汇总, 趋势分析, CSV 导入
- 经营管控：合作伙伴管理, 订单管理, 通知中心, 仪表盘

**v1 不包含（标注"规划中"）**：
- 视频工作流：工程文件项目包、视频指纹、Content ID
- 手工工作流：物理原件、原料库存、生产批次、Etsy API
- 摄影工作流：RAW 全流程、选片模式、水印服务、图库 API
- 音乐工作流：ISRC、Split Sheets、发行 API
- 文字工作流：章节层级、EPUB 排版、抄袭检测

---

## 二、创作者类型支持矩阵

| 创作者类型 | v1 (当前) | v2 (规划) | v3+ (愿景) | 实现状态 | 关键缺口 |
|-----------|-----------|-----------|------------|---------|---------|
| **插画师/AIGC艺术家** | ✅ 完整支持 | ✅ 持续增强 | ✅ 持续增强 | ✅ 全链路功能已落地 | — |
| **摄影师** | 🔵 基础支持 | ✅ 完整支持 | ✅ 持续增强 | 🔵 基础数据层就绪 | RAW解码、选片、水印、图库API |
| **短视频/动画** | 🔵 基础支持 | 🔵 增强支持 | ⏳ 完整支持 | 🔵 基础数据层就绪 | 工程文件包、视频指纹、商单工作流 |
| **手工艺人** | 🔵 基础支持 | 🔵 增强支持 | ⏳ 完整支持 | 🔵 基础数据层就绪 | 物理原件、库存、批次、Etsy API |
| **音乐人** | 🔵 基础支持 | 🔬 研究阶段 | ⏳ 完整支持 | 🔵 基础数据层就绪 | ISRC、Split Sheets、发行API |
| **文字作者** | 🔵 基础支持 | 🔬 研究阶段 | ⏳ 完整支持 | 🔵 基础数据层就绪 | 章节层级、EPUB排版、抄袭检测 |

**状态符号**：
- `✅` = 核心工作流完整实现
- `🔵` = 基础数据层已就绪（类型存储/策略配置/平台映射），但专属工作流尚未实现
- `🔬` = 研究阶段，仅有字典定义
- `⏳` = 未来版本规划

---

## 三、版本路线图

```
v1 (当前)          v2 (规划)           v3 (规划)            v4 (愿景)
───────          ────────           ────────            ────────
插画师/AIGC ↓      +摄影师             +短视频/动画         +音乐人
  完整全链路          RAW解码            工程项目包           ISRC/发行
  权益保护闭环        EXIF高级搜索          品牌商单工作流    Split Sheets
  维权流水线          选片模式              视频指纹          专辑管理
  商业撮合            批量元数据模板          字幕管理          采样授权
  通用向导框架          水印预设              横竖屏版本        +文字作者
  风险预警引擎          图库销售                                  章节层级
                                              +手工艺人               EPUB导出
                                            物理原件              权利细分
                                            原料库存              电子书/有声书
                                            生产批次              KDP/起点对接
                                            质检分级              Spotify/音乐分发
                                            Etsy分发              音频指纹
                                            工厂对接
```

### 各版本功能对比

| 功能域 | v1 (插画师) | v2 (+摄影师) | v3 (+视频+手工) | v4 (+音乐+文字) |
|--------|------------|-------------|----------------|----------------|
| 文件导入 | 图片+基础视频 | +RAW(CR2/NEF/ARW/DNG) | +工程文件(.prproj/.aep/.drp) | +多轨音频/手稿文件 |
| 元数据 | 基础EXIF | +EXIF高级搜索+GPS地图 | +视频元数据+批次信息 | +ISRC+章节标记 |
| 存证 | SHA-256+C2PA+TSA | 同v1 | +视频指纹(perceptual hash) | +音频指纹(AcoustID) |
| 风险预警 | 提示词/商标/参考图 | 同v1 | 同v1 | 同v1 |
| 维权 | 图片以图搜图+流水线 | 同v1 | +视频指纹监测 | +音频/文本查重 |
| 产品化 | Canvas三层预览 | +水印服务 | +3D打印/按需制造 | +EPUB/PDF排版 |
| 分发 | 社交平台8个 | +图库API(500px/图虫) | +视频平台(B站/抖音/YouTube) | +音乐平台+写作平台 |
| 变现 | 撮合工具+收入登记 | +数字下载/艺术微喷 | +品牌商单+平台激励 | +版税+权利金拆分 |

### 里程碑

| 里程碑 | 预计时间 | 产出 |
|--------|---------|------|
| M1 - v1 上线 | 第3周 | 插画师全链路完整可用 |
| M2 - v2 上线 | 第7周 | 摄影师完整支持 |
| M3 - v3 上线 | 第13周 | 视频+手工两大类型完整支持 |
| M4 - v4 上线 | 第20周 | 6 类创作者全覆盖 |

**总计**：v1-v4 约 60-75 工作日，从 v1 启动到 v4 上线约 4-5 个月。

---

## 四、模块全景

```
┌──────────────────────────────────────────────────────────────┐
│                     OriStudio 七大模块                         │
│                                                              │
│  [1] 创意资产中心    → 作品导入、自动元数据、版本、标签、AI创作记录 │
│  [2] 权益保护中心    → 风险预警 → 存证(C2PA+区块链+TSA) → 监测 → 维权 → 清白证明 │
│  [3] IP登记工作站    → 多分类推荐+置信度、律师审核步骤、7项免责  │
│  [4] 商业撮合平台    → 四层架构(设计→模板→商品→发布)、智能匹配、分账 │
│  [5] 内容分发中心    → 多平台发布、AI文案、排期、影响力         │
│  [6] 经营管理中心    → 收入、订单、通知、仪表盘聚合             │
│  [7] 系统基础设施    → 字典、认证、备份、监控、审计、插件       │
│                                                              │
│  能力层: AI Agent 编排 (RiskWarning/Enforcement/InnocenceProof)│
│         MCP 协议连接外部智能体 (Ollama/CNIPA/Google Vision)    │
│  生态层: 蚂蚁链/至信链/Polygon | DigiCert TSA | CNIPA/WIPO/USPTO│
│         百度识图/Google Vision/TinEye | Printful/小红书/B站   │
└──────────────────────────────────────────────────────────────┘
```

### 模块间数据流

| 数据 | 源 | 消费 | 用途 |
|------|----|------|------|
| work.id, sha256, title, thumbnail, file_path, rights, ai_assisted | [1] | [2][4][5] | 存证/产品设计/推广 |
| ai_creation_sessions[].prompt, seed, params | [1] | [2] | 创作过程证据链 |
| certificate.id, hash, qr_code, c2pa_manifest | [2] | [4][5] | Verified 徽章/发布认证 |
| monitor_results, evidence_package, enforcement_actions | [2] | [6] | 维权统计 |
| innocence_proofs, similarity_exclusions | [2] | [6] | 反证记录 |
| ipr.registration, categories | [3] | [4] | IP 授权基础 |
| product.id, mockup, title, price, channel | [4] | [5][6] | 推广素材/收入关联 |
| marketplace_orders, revenue_split | [4] | [6] | 撮合订单/分账记录 |
| platform_analytics | [5] | [6] | 影响力分析 |
| 全模块聚合 | [1..5] | [6] | 仪表盘 |
| dictionary_items | [7] | [1..6] | 公共枚举/配置 |
| notifications | [7] | [1..6] | 实时通知 |

---

## 五、API 与数据模型统计

### API 端点（以代码实际为准 — 334+ 端点）

| 模块 | 端点数 | 路由文件 |
|------|--------|----------|
| [1] 创意资产中心 | 61+ | works.py(25) + batch_works.py(7) + versions.py(9) + work_variants.py(10) + subtitle.py(7) + video_fingerprint.py(7) |
| [2] 权益保护中心 | 90+ | notary.py(18) + monitor.py(39) + copyscape.py(9) + **新增: risk_warning(6) + enforcement(8) + innocence_proof(5)** |
| [3] IP 登记工作站 | 24 | ipr.py(24) |
| [4] 商业撮合平台 | 67+ | supply.py(50) + factory.py(9) + commission.py(9) + **新增: marketplace(5+)** |
| [5] 内容分发中心 | 42 | publish.py(26) + playwright_pub.py(7) + subscription.py(7) |
| [6] 经营管理中心 | 2 | dashboard.py(2) |
| [7] 系统基础设施 | 73+ | system.py(54) + auth.py(15) + websocket_router.py(1) |
| **合计** | **334+** | 21+ 个路由文件 |

### 数据模型（102+ 个模型类）

| 模型文件 | 模型数 | 说明 |
|----------|--------|------|
| app/models/work.py | 4 | Work, WorkVersion, WorkTag, Project |
| app/models/work_variant.py | 2 | 横竖屏版本 |
| app/models/system.py | 13 | SystemSetting, AuditLog, User, Notification 等 |
| app/models/supply.py | 6 | Partner, Order, OrderPayment 等 |
| app/models/publish.py | 7 | Product, RevenueRecord 等 |
| app/models/monitor.py | 4 | MonitorTask, MonitorResult 等 |
| app/models/monitor_ext.py | 5 | LocalFingerprint, BrandWatch 等 |
| app/models/ipr.py | 7 | IPRegistration, TrademarkClass 等 |
| app/models/notary.py | 4 | NotaryRecord, Certificate, C2PARecord |
| app/models/monetization.py | 4 | ProductTemplate, Campaign, License |
| app/models/risk_warning.py | **新增** | RiskWarning |
| app/models/enforcement.py | **新增** | EnforcementAction, EnforcementTemplate |
| app/models/innocence_proof.py | **新增** | InnocenceProof, SimilarityExclusion |
| app/models/marketplace.py | **新增** | MarketplaceOrder, FactoryCatalog |
| app/models/ai_session.py | **新增** | AiCreationSession |
| app/models/work_priority.py | **新增** | WorkPriorityScore |
| app/models/subtitle.py | 2 | 字幕管理 |
| app/models/video_fingerprint.py | 2 | 视频指纹 |
| app/models/watermark.py | 1 | 水印模板 |
| app/models/metadata_template.py | 2 | 元数据模板 |
| app/models/commission.py | 3 | 约稿管理 |
| app/models/factory.py | 3 | 工厂对接 |
| app/models/quality_inspection.py | 1 | 质检 |
| app/models/listings.py | 2 | 平台列表 |
| app/models/subscription.py | 2 | 订阅 |
| app/models/reserved_photographer.py | 6 | 摄影师预留 |
| app/models/reserved_video.py | 5 | 视频预留 |
| app/models/reserved_crafts.py | 4 | 手工预留 |
| app/models/reserved_music.py | 6 | 音乐预留 |
| app/models/reserved_writing.py | 7 | 文字预留 |
| **合计** | **102+** | 26+ 个模型文件 |

> **注**：代码已从初始的 232 端点/49 模型持续增长，包含预留表（reserved_*）和新增功能模块。

---

## 六、关键设计决策

1. **v1 聚焦插画师** — 非插画类型专属功能标注"规划中"，基础导入可用
2. **权益保护是核心差异** — 从"存证+监测"升级为"预警→存证→监测→维权→清白证明"完整闭环
3. **C2PA 提升到 v1** — 不再标记为"v1-not-implemented"，使用 Adobe content-auth SDK
4. **AI 渗透所有类型** — AI 不是独立分类，而是所有创作者类型的辅助能力
5. **商业撮合平台定位** — 系统做工具，不碰交易和资金，保持中立
6. **不重复造轮子** — 区块链用蚂蚁链/至信链/Polygon，时间戳用 DigiCert TSA，商标用 CNIPA/WIPO/USPTO
7. **混合 AI 接入** — 核心信任链固定（区块链/商标库），非核心灵活（以图搜图/AI文案可配置）
8. **Gateway ABC 模式** — 所有外部 API 通过抽象基类 + 多实现适配器
9. **文档以代码为准** — 334+ 端点、102+ 模型（持续增长中）

---

## 七、UPL 法律合规需求

### 7 项免责声明（首次启动强制确认）

1. **不构成律师-客户关系** — 使用本软件不建立律师-客户特权关系
2. **不构成法律建议** — IP 登记指引/分类推荐仅供参考
3. **不保证注册成功** — 注册结果取决于官方审查
4. **POD 平台 IP 条款警告** — 上传前请阅读平台服务条款中的知识产权部分
5. **AI 内容标注要求** — 建议按平台规则标注"AI 辅助生成"
6. **侵权监测局限性** — 不能保证发现所有侵权行为
7. **司法管辖区限制** — IP 登记指引仅覆盖主要辖区

### 商标分类推荐

从"系统推荐你注册第 XX 类"改为"以下类别与你的作品可能相关，请与律师确认后选择" — 返回多类可能性 + 置信度

### CNIPA 提交前律师审核步骤（不可绕过）

用户必须选择：(A) 我已咨询律师 (B) 我需要找律师 (C) 我自愿跳过 [二次确认 + 勾选风险声明]

---

## 八、Canvas 效果预览方案

| 方案 | 效果 | v1 |
|------|------|-----|
| **A: Canvas 扁平叠加** | 平面、不真实 | ✅ 默认 |
| **B: Printful Mockup API** | 照片级 | ✅ 增强 P1 |
| **C: 预置 PSD 模板** | 接近照片级 | P2 规划 |

Canvas 阶段明确标注："平面效果预览，非真实产品照片"

---

## 九、设计文档索引

| 文档 | 路径 | 说明 |
|------|------|------|
| 模块详细设计 | [modules-v3/](modules-v3/) | 7 个模块功能设计 |
| UX 设计规范 | [UX.md](UX.md) | Onboarding、空状态、术语、交互规范 |
| 技术架构 | [ARCHITECTURE.md](ARCHITECTURE.md) | 三大架构图 + 可行性评估 + 实施计划 |
| HTML 原型 | [../design/](../design/) | 高保真交互原型 |
