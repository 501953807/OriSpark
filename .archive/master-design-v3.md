# OriStudio v3 系统功能设计总纲

> **基于**: `docs/requirements-v3-final.md` — v1聚焦插画师/AIGC艺术家，其他创作者类型规划中
> **模块设计**: `docs/modules-v3/` — 7个模块，1500+行详细设计
> **设计原则**: 从真实业务出发定义模块，不被历史结构约束
> **最后更新**: 2026-06-12

---

## 一、v1 核心定位

OriStudio v3 **v1 聚焦插画师/AIGC 艺术家**，做深做透完整工作流：作品管理 → 存证确权 → IP登记 → 产品化 → 分发 → 收入追踪。

**诚实声明**: v1 仅深度支持插画师/AIGC 艺术家。摄影师/视频/手工/音乐/文字创作者的基础文件导入功能可用，但专属工作流标注"规划中"。

### 创作者类型支持矩阵

| 创作者类型 | v1 (当前) | v2 (规划) | v3+ (愿景) | 关键缺口 |
|-----------|-----------|-----------|------------|---------|
| **插画师/AIGC艺术家** | 完整支持 | 持续增强 | 持续增强 | — |
| **摄影师** | 基础导入 | 完整支持 | 持续增强 | RAW解码、选片、水印、图库API |
| **短视频/动画** | 基础导入 | 增强导入 | 完整支持 | 工程项目包、视频指纹、商单工作流 |
| **手工艺人** | 基础导入 | 增强导入 | 完整支持 | 物理原件、库存、批次、Etsy API |
| **音乐人** | 基础导入 | 研究阶段 | 完整支持 | ISRC、Split Sheets、发行API |
| **文字作者** | 基础导入 | 研究阶段 | 完整支持 | 章节层级、EPUB排版、抄袭检测 |

### 版本演进路线

```
v1 (当前)          v2 (规划)           v3 (规划)            v4 (愿景)
───────          ────────           ────────            ────────
插画师/AIGC ↓      +摄影师             +短视频/动画         +音乐人
  完整全链路          RAW解码            工程项目包           ISRC/发行
                  EXIF高级搜索          品牌商单工作流        Split Sheets
                  选片模式              视频指纹            专辑管理
                  批量元数据模板         字幕管理            采样授权
                  水印预设              横竖屏版本          +文字作者
                  图库销售                                章节层级
                  数字预设            +手工艺人            EPUB导出
                  艺术微喷            物理原件              权利细分
                  约稿管理            原料库存              电子书/有声书
                  500px/图虫分发       生产批次              KDP/起点对接
                                     质检分级              文本查重
                                     Etsy分发              Spotify/音乐分发
                                     工厂对接              音频指纹
```

**每个版本的创作者扩展**:

| 版本 | 创作者类型 | 核心新增 | 资产中心 | 权利保护 | 商业转化 | 内容分发 | 经营管理 |
|------|-----------|---------|---------|---------|---------|---------|---------|
| **v1** | 插画师/AIGC | 图片全链路 | 完整 | SHA-256存证+以图搜图 | POD+众筹+IP授权 | 8平台+AI文案 | 收入+分析 |
| **v2** | +摄影师(完整) | RAW+选片+水印+图库 | RAW解码/EXIF搜索/选片/水印 | EXIF地图+图库指纹 | 图库销售+预设包+微喷 | 500px/图虫/Shutterstock | 约稿管理 |
| **v3** | +视频/动画+手工艺人 | 工程包/品牌商单/物理原件 | 工程包/字幕/视频指纹/横竖屏 | 视频指纹监测 | 品牌商单/激励/原件/库存/批次/质检 | Etsy API | 工厂对接/质检 |
| **v4** | +音乐人+文字作者 | ISRC/章节/有声书 | 专辑/章节/EPUB导出 | 音频指纹+文本查重 | 发行/Sample/电子书/有声书 | Spotify/音乐/起点/KDP | 发行/有声书管理 |

---

## 二、模块全景

```
┌──────────────────────────────────────────────────────────────┐
│                     OriStudio v3                              │
│                                                              │
│  [1] 创意资产中心    → 作品导入、自动元数据、版本、标签、权利   │
│  [2] 权利保护中心    → 哈希存证、证书、侵权监测、维权           │
│  [3] IP登记工作站    → 多分类推荐+置信度、律师审核步骤、7项免责  │
│  [4] 商业转化引擎    → 产品设计器、Canvas三层预览、POD渠道管理   │
│  [5] 内容分发中心    → 多平台发布、AI文案、排期、影响力         │
│  [6] 经营管理中心    → 收入、合作伙伴、通知、数据分析           │
│  [7] 系统基础设施    → 字典、认证、备份、监控、Onboarding       │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

---

## 三、完整业务链

```
[系统外] 创作完成 (Procreate/PS/Midjourney等)
         │
         ▼ [系统接管]
    [1] 导入作品库(哈希+缩略图+自动元数据)
              │
    ┌─────────┼─────────┐
    ▼         ▼         ▼
   [2]       [4]       [5]
  存证确权   商业转化   内容分发
  SHA-256   IP→产品    多平台推广
  区块链     效果图     AI文案
  证书       POD渠道    影响力追踪
    │         │         │
    └─────────┼─────────┘
              ▼
            [6]
          经营管理
          收入追踪+通知+分析
```

---

## 四、模块间数据流矩阵

| 数据 | 源 | 消费 | 用途 |
|------|----|------|------|
| work.id, sha256, title, thumbnail, file_path, rights | [1] | [2][4][5] | 存证/产品设计/推广 |
| certificate.id, hash, qr_code | [2] | [4][5] | Verified徽章/发布认证 |
| monitor_results, evidence_package | [2] | [6] | 维权统计 |
| ipr.registration, categories | [3] | [4] | IP授权基础 |
| product.id, mockup, title, price, channel | [4] | [5][6] | 推广素材/收入关联 |
| campaign, license | [4] | [5][6] | 推广/收入 |
| platform_analytics | [5] | [6] | 影响力分析 |
| 全模块聚合 | [1..5] | [6] | 仪表盘 |
| dictionary_items | [7] | [1..6] | 公共枚举/配置 |
| notifications | [7] | [1..6] | 实时通知 |

---

## 五、全局API统计 (以代码实际为准)

| 模块 | 端点数 | 路由文件 |
|------|--------|----------|
| [1] 创意资产中心 | 32 | works.py(18) + batch_works.py(6) + versions.py(8) |
| [2] 权利保护中心 | 49 | notary.py(18) + monitor.py(31) |
| [3] IP登记工作站 | 24 | ipr.py(24) |
| [4] 商业转化引擎 | 42 | supply.py(42) |
| [5] 内容分发中心 | 17 | publish.py(17) |
| [6] 经营管理中心 | 2 | dashboard.py(2) |
| [7] 系统基础设施 | 66 | system.py(50) + auth.py(14) + ws(1) + main(1) |
| **合计** | **232** | 13个路由文件 |

> **注**: 文档此前声称145端点，实际代码含232端点（231 REST + 1 WebSocket）。经营管理中心的收入/合作伙伴/订单/通知端点物理上位于 supply.py(42) 路由中。

---

## 六、全局数据模型统计 (以代码实际为准)

| 模型文件 | 模型数 | 模型类 |
|----------|--------|--------|
| app/models/work.py | 4 | Work, WorkVersion, WorkTag, Project |
| app/models/system.py | 11 | SystemSetting, AuditLog, BackupRecord, DictionaryGroup, DictionaryItem, User, UserLoginHistory, Notification, Plugin, EmailVerification, PasswordReset |
| app/models/supply.py | 6 | Partner, PartnerQualification, Order, OrderPayment, OrderCommunication, Reminder |
| app/models/publish.py | 4 | Product, ProductPublishing, VerifiedMark, RevenueRecord |
| app/models/monitor.py | 4 | MonitorTask, MonitorResult, EvidencePackage, ScanSchedule |
| app/models/monitor_ext.py | 5 | LocalFingerprint, BrandWatch, BrandScanResult, DomainWatch, WhitelistSuggestion |
| app/models/ipr.py | 7 | IPRegistration, TrademarkClass, CopyrightRegistration, TrademarkRegistration, TrademarkMonitoring, ApplicationTemplate, NiceClassification |
| app/models/notary.py | 4 | NotaryRecord, Certificate, C2PARecord, NotaryAuditTrail |
| app/models/monetization.py | 4 | ProductTemplate, MonetizationChannel, Campaign, License |
| **合计** | **49** | 9个模型文件 |

> **注**: 文档此前声称33表，实际代码含49个SQLAlchemy模型类。代码比文档更完整。

---

## 七、与旧版(v2)的核心变化

| v2模块 | v3模块 | 变化 |
|--------|--------|------|
| 作品管理 | 创意资产中心 | 扩大: 全类型文件+完整元数据+权利管理+自动元数据提取+批量导入 |
| 存证确权+侵权监测 | 权利保护中心 | 合并: 存证和维权一体化 |
| IP登记 | IP登记工作站 | 增强: 智能助手+费用计算器+多分类推荐+律师审核步骤 |
| 供应链 | 商业转化引擎 | 彻底重构: IP→产品→效果图→POD渠道管理 |
| 发布变现 | 内容分发中心 | 彻底重构: 社交媒体多平台分发+AI文案 |
| (无) | 经营管理中心 | 新增: 收入/伙伴/通知/分析聚合 |
| 系统管理 | 系统基础设施 | 增强: 字典中心+监控+插件框架+Onboarding |

---

## 八、关键设计决策

1. **v1聚焦插画师** — 非插画类型专属功能标注"规划中"，基础导入可用
2. **POD渠道管理** — 重命名自"POD对接"，明确手动上架+URL记录，诚实声明能力边界
3. **Canvas三层方案** — 默认扁平叠加 / Printful Mockup API增强 / PSD模板规划
4. **UPL合规** — 7项免责声明 + 尼斯多推荐+置信度 + CNIPA律师审核步骤(不可绕过)
5. **文档以代码为准** — 232端点、49模型，文档统计全面更新

---

## 九、技术栈

| 层 | 技术 |
|----|------|
| 前端 | Vue 3 + Vite + TypeScript + Naive UI + Tailwind + Pinia + ECharts + Canvas API |
| 后端 | FastAPI + Uvicorn + SQLAlchemy 2.0 + Celery + WebSocket |
| 数据库 | SQLite WAL (本地) / PostgreSQL (可选迁移) |
| 文件处理 | Pillow(图片) + ffmpeg(视频) + mutagen(音频) |
| AI | Ollama(本地) / OpenAI API(远端) / 模板(fallback) |

---

## 十、设计文档清单

| 编号 | 模块 | 设计文档 | 行数 |
|------|------|----------|------|
| 1 | 创意资产中心 | [01-creative-assets.md](modules-v3/01-creative-assets.md) | 262+ |
| 2 | 权利保护中心 | [02-rights-protection.md](modules-v3/02-rights-protection.md) | 181+ |
| 3 | IP登记工作站 | [03-ip-registration.md](modules-v3/03-ip-registration.md) | 220+ |
| 4 | 商业转化引擎 | [04-monetization-engine.md](modules-v3/04-monetization-engine.md) | 217+ |
| 5 | 内容分发中心 | [05-content-distribution.md](modules-v3/05-content-distribution.md) | 231+ |
| 6 | 经营管理中心 | [06-business-management.md](modules-v3/06-business-management.md) | 158+ |
| 7 | 系统基础设施 | [07-system-infra.md](modules-v3/07-system-infra.md) | 180+ |
| — | 模块索引(v3) | [README.md](modules-v3/README.md) | 56+ |
| — | 模块索引 | [README.md](modules/README.md) | 177+ |

## 十二、预留功能设计索引

> v1系统聚焦插画师/AIGC艺术家。摄影师/视频/手工/音乐/文字创作者在评估报告(`docs/agent-evaluation-report.md`)中提出了大量具体需求。以下为在各模块设计文档中完整设计的预留功能清单。

### 按创作者类型索引

#### 摄影师 (v2) — 共享视觉工作流，增强专业摄影支持

| 功能 | 模块 | 文档章节 | 关键表 | 关键API |
|------|------|---------|--------|---------|
| RAW格式支持 | [1]创意资产 | 12.1.1 | raw_formats, works.raw_sidecar_path | /api/works/import-raw |
| EXIF高级搜索 | [1]创意资产 | 12.1.2 | works.custom_metadata(EXIF索引) | /api/works?camera=&lens=&focal_min=... |
| 选片(Culling)模式 | [1]创意资产 | 12.1.3 | works.cull_status/rating/color_label | /api/works/batch-cull |
| 批量元数据模板 | [1]创意资产 | 12.1.4 | metadata_templates | /api/metadata-templates |
| 水印预设管理 | [1]创意资产 | 12.1.5 | watermark_presets | /api/watermark-presets |
| 图库销售渠道 | [4]商业转化 | 15.1.1 | stock_channels/uploads/sales | /api/stock/channels |
| 数字预设包 | [4]商业转化 | 15.1.2 | digital_downloads | /api/supply/products/digital-preset |
| 艺术微喷产品 | [4]商业转化 | 15.1.3 | fine_art_print_configs | /api/supply/products/{id}/fine-art-config |
| 图库平台分发 | [5]内容分发 | 14.1 | (复用stock_channels) | /api/publish/stock/upload |
| 约稿管理 | [6]经营管理 | 11.1 | commission_projects | /api/commissions |

#### 短视频/动画 (v3) — 独立工程文件工作流

| 功能 | 模块 | 文档章节 | 关键表 | 关键API |
|------|------|---------|--------|---------|
| 工程文件项目包 | [1]创意资产 | 12.2.1 | works.is_project_package/project_files | /api/works/import-project |
| 字幕管理 | [1]创意资产 | 12.2.2 | subtitles | /api/works/{id}/subtitles |
| 视频指纹(pHash) | [1]创意资产 | 12.2.3 | video_fingerprint_config/frame_fingerprints | /api/works/{id}/fingerprint |
| 横竖屏版本 | [1]创意资产 | 12.2.4 | work_variant_groups, works.aspect_ratio_variants | /api/works/{id}/variants |
| 视频指纹监测 | [2]权利保护 | 7.1 | monitor_results(content_type=video_fingerprint) | /api/monitor/scan-video-fingerprint |
| 品牌商单工作流 | [4]商业转化 | 15.2.1 | brand_campaigns/tasks/messages | /api/brand-campaigns |
| 平台激励追踪 | [4]商业转化 | 15.2.2 | platform_earnings/goals | /api/platform-earnings |
| 周边衍生品 | [4]商业转化 | 15.2.3 | (复用POD+产品模型) | (复用现有API) |

#### 手工艺人 (v3) — 物理原件→生产→质检全流程

| 功能 | 模块 | 文档章节 | 关键表 | 关键API |
|------|------|---------|--------|---------|
| 物理原件产品模型 | [4]商业转化 | 15.3.1 | physical_products | /api/physical-products |
| 原料库存管理 | [4]商业转化 | 15.3.2 | materials_inventory | /api/materials |
| 生产批次管理 | [4]商业转化 | 15.3.3 | production_batches | /api/production/batches |
| 质检分级 | [4]商业转化 | 15.3.4 | quality_inspections | /api/production/batches/{id}/inspections |
| Etsy API网关 | [5]内容分发 | 14.2 | etsy_listings/orders | /api/etsy/listings |
| 询价单+样品+质检报告 | [6]经营管理 | 11.2 | rfq_requests/samples/quality_reports | /api/production/rfqs |

#### 音乐人 (v4) — 音频行业独立工作流

| 功能 | 模块 | 文档章节 | 关键表 | 关键API |
|------|------|---------|--------|---------|
| ISRC/ISWC编码 | [1]创意资产 | 12.3.1 | works.custom_metadata(isrc/iswc/upc_ean) | /api/works/{id}/music-metadata |
| 专辑/EP/Single | [1]创意资产 | 12.3.2 | albums/album_tracks | /api/albums |
| Split Sheets | [1]创意资产 | 12.3.3 | work_collaborators | /api/works/{id}/collaborators |
| Master/Publishing权利 | [1]创意资产 | 12.3.4 | works.rights(master/publishing/sync) | /api/works/{id}/rights/music |
| 音频指纹 | [2]权利保护 | 7.2 | works.perceptual_hash(audio_fingerprint) | /api/monitor/generate-audio-fingerprint |
| 音乐发行管理 | [4]商业转化 | 15.4.1 | distribution_releases/distro_platforms | /api/distribution/releases |
| 采样授权 | [4]商业转化 | 15.4.2 | sample_clearances | /api/works/{id}/sample-clearances |
| 音乐平台分发 | [5]内容分发 | 14.3 | (复用distribution_releases) | /api/publish/music-platforms |

#### 文字作者 (v4) — 文本内容独立工作流

| 功能 | 模块 | 文档章节 | 关键表 | 关键API |
|------|------|---------|--------|---------|
| 章节结构 | [1]创意资产 | 12.4.1 | chapters/chapter_comments/revisions | /api/works/{id}/chapters |
| EPUB导出 | [1]创意资产 | 12.4.2 | export_configs, works.export_formats | /api/works/{id}/export |
| 权利细分 | [1]创意资产 | 12.4.3 | works.rights(literary_rights) | /api/works/{id}/rights/literary |
| 文本查重 | [2]权利保护 | 7.3 | monitor_results(content_type=text_plagiarism) | /api/monitor/scan-text |
| 电子书产品 | [4]商业转化 | 15.5.1 | ebook_products | /api/ebooks |
| 有声书制作 | [4]商业转化 | 15.5.2 | audiobook_productions | /api/audiobooks |
| KDP/起点/晋江 | [4]商业转化 | 15.5.3 | (分发Gateway) | /api/publish/writing-platforms |
| 写作平台分发 | [5]内容分发 | 14.4 | (复用ebook_products) | /api/publish/writing/publish |

### 全局预留数据模型汇总

| 创作者类型 | v1预留表数量 | 关键新表 |
|-----------|------------|---------|
| 摄影师 (v2) | 10 | raw_formats, watermark_presets, metadata_templates, stock_channels/uploads/sales, digital_downloads, fine_art_print_configs, commission_projects |
| 视频 (v3) | 8 | project_file_formats, subtitles, video_fingerprint_config, video_frame_fingerprints, work_variant_groups, brand_campaigns/tasks/messages, platform_earnings/goals |
| 手工 (v3) | 9 | physical_products, materials_inventory, production_batches, quality_inspections, etsy_listings/orders, rfq_requests, samples, quality_reports |
| 音乐 (v4) | 8 | albums/album_tracks, work_collaborators, distribution_releases, distro_platforms, sample_clearances |
| 文字 (v4) | 7 | chapters/chapter_comments/chapter_revisions, export_configs, ebook_products, audiobook_productions |
| **合计** | **42** | v1预留42张表供v2-v4版本实施 |

### 预留设计原则

1. **v1数据模型/路由/组件已预留** — 所有表结构在v1中建好，字段带注释"v2/v3/v4激活"
2. **API端点预留查询参数** — 新参数在v1端点中接收但不处理(不报错)
3. **前端组件骨架预留** — 关键按钮/入口/Tab占位，标注"规划中"引导
4. **每个预留功能有完整设计** — 数据模型6要素、API端点、前端组件、v1集成点
5. **版本间正交** — 摄影师v2不影响v3视频功能，可独立并行开发

---

## 十一、相关文档

| 文档 | 路径 | 说明 |
|------|------|------|
| 最终需求文档 | [requirements-v3-final.md](requirements-v3-final.md) | v1聚焦插画师，POD诚实声明，UPL合规 |
| 项目启动报告 | [pm-startup-report.md](pm-startup-report.md) | P0/P1/P2问题清单，任务分配矩阵，8个关键决策点 |
| UX设计规范 | [ux-design-spec.md](ux-design-spec.md) | Onboarding 3步向导，10空状态，9术语优化，移动端适配 |
| 完整实施计划 | [OriStudio-完整实施计划.md](OriStudio-完整实施计划.md) | 4 Phase重规划 |
