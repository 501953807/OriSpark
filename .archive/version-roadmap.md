# OriStudio 多版本路线图

> **日期**: 2026-06-12 | **基于**: 9角色评估报告(agent-evaluation-report.md)、v3全量设计文档
> **核心决策**: v1聚焦插画师/AIGC艺术家，v2-5每版新增1-2类创作者完整支持
> **协作模式**: 每版本复用5角色Agent协作框架（PM + 业务专家 + 程序员 + 设计师 + 架构师）

---

## 一、版本总览表

| 版本 | 目标创作者 | 核心交付 | 设计 | 实施 | 版本间隔 | 关键风险 |
|------|-----------|---------|------|------|---------|---------|
| **v1** | 插画师/AIGC艺术家 | 全链路: 导入→存证→产品化→分发→收入 | 已完成 | 13-14天 | — | 产品设计器效果深度 |
| **v2** | +摄影师 | RAW解码、选片模式、水印服务、EXIF搜索、图库API | 5天 | 10-12天 | 1周稳定 | rawpy/libraw集成复杂度 |
| **v3** | +短视频/动画 +手工艺人 | 视频项目包、审片协作、物理原件、Etsy API、成本核算 | 4+4天 | 14-18天 | 2周稳定 | 两个差异极大类型并行 |
| **v4** | +音乐人 +文字作者 | ISRC/Split Sheets、章节结构、EPUB导出、抄袭检测 | 4+4天 | 14-18天 | 2周稳定 | 偏离视觉核心最远 |
| **v5** | 全类型+AI增强 | 跨类型智能工作流、移动端、AI生态 | 待定 | 待定 | — | 全类型一致性体验 |

**总计估算**: v1-v4 约 60-75 工作日（不含稳定期），从v1启动到v4上线约 4-5 个月。

### 各版本功能对比矩阵

| 功能域 | v1 (插画师) | v2 (+摄影师) | v3 (+视频+手工) | v4 (+音乐+文字) |
|--------|------------|-------------|----------------|----------------|
| 文件导入 | 图片+基础视频 | +RAW(CR2/NEF/ARW/DNG) | +工程文件(.prproj/.aep/.drp) | +多轨音频/手稿文件 |
| 元数据 | 基础EXIF | +EXIF高级搜索+GPS地图 | +视频元数据+批次信息 | +ISRC+章节标记 |
| 版本管理 | 文件快照 | +XMP sidecar | +视频版本+横竖屏 | +章节修订追踪 |
| 存证 | SHA-256 | 同v1 | +视频指纹(perceptual hash) | +音频指纹(AcoustID) |
| 产品化 | Canvas三层预览 | +水印服务 | +3D打印/按需制造 | +EPUB/PDF排版 |
| 分发 | 社交平台8个 | +图库API(Shutterstock/500px/图虫) | +视频平台(B站/抖音/YouTube) | +音乐平台+写作平台 |
| 变现 | 收入登记+CSV导入 | +数字下载/艺术微喷 | +品牌商单+平台激励 | +版税+权利金拆分 |
| 工作流阶段 | 5阶段 (插画师) | 7阶段 (摄影师) | 6+6阶段 (视频+手工) | 6+5阶段 (音乐+文字) |

---

## 二、v1 - 插画师/AIGC艺术家 (当前版本)

### 2.1 支持范围

**创作者类型**: 插画师、AIGC艺术家
**其他类型**: 基础文件导入可用，专属功能标注"规划中"

### 2.2 核心交付功能清单

**Phase 0 - 合规修复 (3天)**:
- [x] 7项免责声明UI实现
- [x] IP登记合规改造（多分类+置信度+律师审核步骤）
- [x] 创作者类型选择器改造（插画师突出，其他标注"规划中"）

**Phase 1 - 核心能力 (5-6天)**:
- [x] 自动元数据提取（文件名/EXIF自动填充）
- [x] 批量导入文件夹（递归读取+按文件夹创建项目）
- [x] 视频缩略图修正（30%位置关键帧）
- [x] POD渠道管理 + Canvas三层预览
- [x] 收入CSV导入（支付宝/微信/POD平台）

**Phase 2 - UX体验 (4天)**:
- [x] Onboarding 3步向导
- [x] 10场景空状态组件
- [x] 9术语优化（白话+结果式表达）
- [x] 视觉风格轻量调整（温馨/圆角/留白）
- [x] 通用UX组件（WizardStepper/DetailLayout/ListLayout）

**Phase 3 - 文档同步 (1天)**:
- [x] API/模型清单核对
- [x] 模块边界标注

### 2.3 技术关键点

- **Canvas预览**: 默认扁平叠加；Printful Mockup API增强；API不可用时降级
- **POD渠道**: 诚实声明 — 手动上架+URL记录，非API级对接
- **存证**: SHA-256 + 前端友好展示（"已存证 ✅ 日期"）
- **合规**: 尼斯分类多推荐+置信度；CNIPA提交前律师审核不可绕过

### 2.4 5 Agent协作执行节奏

| 角色 | 输入 | 产出 | 工期 |
|------|------|------|------|
| **PM** | 9角色评估报告、P0/P1/P2问题清单 | 任务分配矩阵、进度甘特图、风险登记簿 | 全程 |
| **业务专家** | 插画师真实工作流访谈 | 需求设计v3-final、POD诚实声明策略 | 2天 |
| **程序员** | 现有代码库(49模型/232端点) | 技术可行性报告、代码差距分析、实施路径 | 2天 |
| **设计师** | 插画师UX调研 | UX设计规范、Onboarding/空状态/术语图纸 | 2天 |
| **架构师** | 全部讨论结果 | master-design-v3.md、模块设计更新 | 2天 |

**产出清单**: 需求文档 + UX规范 + 技术评估 + 7模块设计更新(modules-v3/) + 实施计划 + 功能/技术架构图

---

## 三、v2 - 摄影师 (新增完整支持)

### 3.1 核心定位

v2 的目标是在v1插画师基础上，将摄影师从"基础导入可用"提升到"完整工作流支持"。
摄影师与插画师共享80%基础设施（导入/存储/版本/产品化/分发），差异集中在RAW处理、选片流程、水印和EXIF深度利用。

### 3.2 与v1共享的基础设施 (无需重建)

- 文件导入框架（扩展支持RAW格式）
- SHA-256存证服务
- IP登记工作站（UPL合规已就绪）
- 产品设计器基础（Canvas + 模板）
- 内容分发中心（扩展图库平台）
- 经营管理中心（扩展摄影师收入来源）
- 用户/认证/Onboarding框架

### 3.3 新增交付功能清单

#### 模块1 - 创意资产中心（摄影增强）

| 功能 | 详情 | 优先级 | 工作量 |
|------|------|--------|--------|
| RAW格式解码 | 支持 CR2/NEF/ARW/DNG；rawpy/libraw集成；自动生成预览JPEG | P0 | 2天 |
| 选片(Culling)模式 | 全屏批量浏览、1-3键入选/待定/淘汰、键盘快捷键、过滤视图 | P0 | 2天 |
| 批量元数据模板 | 预设模板(作者/版权/许可证)、批量应用、模板管理CRUD | P0 | 1.5天 |
| XMP Sidecar管理 | .xmp文件读写、RAW关联、元数据同步/冲突处理 | P1 | 1.5天 |
| EXIF高级搜索 | 按镜头型号/光圈/焦距/ISO/快门速度/拍摄日期 | P0 | 2天 |
| GPS地图视图 | 基于EXIF GPS的地图浏览、按地理位置筛选 | P1 | 1天 |
| 摄影师过程阶段 | 拍摄→导入→选片→基础调整→精细调色→局部修饰→导出 | P0 | 1天 |
| 存储策略优化 | 磁盘配额提示、RAW/衍生分离存储、清理建议 | P1 | 1天 |

#### 模块2 - 权利保护中心（摄影增强）

| 功能 | 详情 | 优先级 | 工作量 |
|------|------|--------|--------|
| 批量水印服务 | 后端水印引擎、文字/图片水印、批量处理、平铺模式、差异化强度 | P0 | 2天 |
| 水印预览 | 实时预览、位置/大小/透明度可调 | P1 | 0.5天 |

#### 模块4 - 商业转化引擎（摄影增强）

| 功能 | 详情 | 优先级 | 工作量 |
|------|------|--------|--------|
| 数字下载产品 | 原图/Web尺寸/社交尺寸多规格、定价、许可证选择 | P0 | 1.5天 |
| 艺术微喷产品 | 纸张/尺寸/装裱选项、POD渠道对接(已有框架扩展) | P1 | 1天 |
| 预设/滤镜包 | 预设文件打包、Lightroom/Capture One配置文件管理 | P2 | 1天 |

#### 模块5 - 内容分发中心（摄影增强）

| 功能 | 详情 | 优先级 | 工作量 |
|------|------|--------|--------|
| 图库API对接 | Shutterstock/500px/图虫 至少一个的API适配器 | P0 | 2.5天 |
| 图库发布工作流 | 标题/关键词/类别自动映射、发布状态追踪 | P0 | 1天 |

### 3.4 技术关键点

| 关键点 | 技术方案 | 风险 |
|--------|---------|------|
| RAW解码 | rawpy (libraw Python绑定) + Pillow for JPEG preview | libraw版本兼容性、大文件内存 |
| 选片键盘操作 | 前端全局键盘事件监听、虚拟滚动(万张级性能) | 1000+ RAW预览流畅性 |
| 批量水印 | Pillow后端合成、异步队列(celery/arq)、进度WebSocket推送 | 大量文件并发处理时间 |
| EXIF高级搜索 | SQLite FTS5 + EXIF字段索引 | 查询性能下降(需索引优化) |
| 图库API | 适配器模式(统一接口+平台实现)、OAuth2.0认证 | API变更、速率限制 |
| XMP管理 | python-xmp-toolkit读写 | XMP规范复杂度 |

### 3.5 数据模型扩展

```
v2新增/扩展表:

CreativeAsset:
  + raw_path: String          # RAW文件路径
  + xmp_data: JSON            # XMP元数据快照
  + culling_status: Enum      # pending/picked/rejected
  + lens_model: String        # 镜头型号(扩展EXIF)
  + aperture: Float           # 光圈值
  + focal_length: Float       # 焦距(mm)
  + iso: Integer              # ISO值
  + shutter_speed: String     # 快门速度
  + gps_lat: Float            # GPS纬度
  + gps_lng: Float            # GPS经度

WatermarkTemplate (新表):
  + id, name, type(文字/图片)
  + config: JSON              # 位置/大小/透明度/平铺/强度
  + created_by, created_at, updated_at

MetadataPreset (新表):
  + id, name
  + fields: JSON              # {author, copyright, license, ...}
  + is_default: Boolean

StockPlatformListing (新表):
  + work_id, platform
  + listing_id, status, url
  + submitted_at, approved_at
```

### 3.6 5 Agent协作配置

| 角色 | 具体输入 | 具体产出 | 工期 |
|------|---------|---------|------|
| **PM** | v1完成状态、摄影师评估报告(陈摄影 1.9/10)、P0-P2需求清单 | 摄影师版本任务矩阵、里程碑甘特图、风险登记簿 | 全程 |
| **业务专家** | 摄影师工作流调研(7阶段)、图库平台研究(Shutterstock/500px/图虫) | 摄影师需求设计文档、选片模式业务规则、水印策略、图库对接策略 | 2天 |
| **程序员** | v1代码库、rawpy/libraw文档、图库API文档 | 技术评估报告(RAW解码/EXIF搜索/水印引擎/图库API)、代码差距分析 | 1.5天 |
| **设计师** | 摄影师UX调研、Lightroom/Capture One/Photo Mechanic 竞品分析 | 摄影师UX规范(选片模式交互/EXIF搜索面板/水印预览/GPS地图) | 1天 |
| **架构师** | v1架构文档、全部Agent讨论输出 | 数据模型扩展设计、API端点新增清单、模块设计文档更新(7模块) | 1.5天 |

**产出清单**: 摄影师需求文档 + UX规范(摄影特化) + 技术评估报告 + 模块设计更新(v2标注) + 实施计划(Phase分步) + HTML架构图更新

### 3.7 5 Agent协作执行节奏 (5天设计)

```
Day 1:
  AM: PM启动 → 输出任务矩阵 + 里程碑 + 风险登记簿
  PM: 业务专家 + 程序员 并行调研(工作流 vs 代码库)

Day 2:
  AM: 设计师 UX调研 + 竞品分析
  PM: 业务专家 需求设计初稿 / 程序员 技术评估报告

Day 3:
  AM: 5角色设计评审(PM主持, 需求+UX+技术全面对齐)
  PM: 架构师 汇总 → 数据模型 + API设计初稿

Day 4:
  AM: 架构师 + 程序员 深度技术讨论(RAW解码方案/图库适配器架构)
  PM: 设计师 UX规范定稿; 业务专家 需求最终评审

Day 5:
  AM: 全体最终评审 → 产出清单验收
  PM: PM输出最终报告 + 实施计划确认
```

---

## 四、v3 - 短视频/动画 + 手工艺人

### 4.1 核心定位

v3 是 OriStudio 最关键的一个版本 — 首次同时支持两个差异极大的创作者类型，且两者的数据模型都与视觉基础模型有本质区别。短视频领域需要项目包概念和视频工作流，手工艺领域需要物理原件和制造流程。

### 4.2 与前一版本共享的基础设施

**从v1/v2继承**:
- 文件导入框架（扩展支持视频项目包）
- SHA-256存证（扩展感知哈希）
- IP登记 + 合规框架
- 经营管理基础（扩展商单/成本核算）

**v3新增但为后续版本预铺**:
- 视频指纹基础设施（v4可复用于音频指纹）
- 物理原件-衍生品关系模型（v4可参考用于音乐母带-衍生品）

### 4.3 短视频/动画新增功能清单

#### 模块1 - 创意资产中心（视频增强）

| 功能 | 详情 | 优先级 | 工作量 |
|------|------|--------|--------|
| 工程文件支持 | .prproj/.aep/.drp 项目包概念、素材清单提取、文件关联图 | P0 | 2.5天 |
| 视频指纹 | ffmpeg关键帧提取 + perceptual hashing(pHash/dHash)、重编码不变性 | P0 | 2天 |
| 字幕管理 | .srt/.ass解析与编辑、双语字幕、字幕样式预设、时间轴可视化 | P0 | 2天 |
| 横竖屏版本管理 | 同一视频 16:9/9:16/1:1 不同构图版本关联、裁剪预览 | P1 | 1.5天 |
| 大文件优化 | 分片上传(>500MB)、增量快照策略、存储配额管理 | P0 | 1.5天 |
| 视频过程阶段 | 脚本→分镜→粗剪→精剪→调色→成片 | P0 | 1天 |
| 缩略图策略 | 智能关键帧提取(场景检测)、多帧拼图/GIF预览 | P1 | 1天 |

#### 模块2 - 权利保护中心（视频增强）

| 功能 | 详情 | 优先级 | 工作量 |
|------|------|--------|--------|
| 视频指纹存证 | 基于perceptual hash的视频存证、相似度报告 | P0 | 1.5天 |

#### 模块4 - 商业转化引擎（视频增强）

| 功能 | 详情 | 优先级 | 工作量 |
|------|------|--------|--------|
| 品牌商单工作流 | brief→方案→脚本→制作→反馈→交付→结算 全流程管理 | P0 | 2.5天 |
| 平台激励追踪 | B站/抖音/YouTube创作激励数据抓取/手动导入、收益统计 | P0 | 2天 |
| 周边衍生品管理 | 与POD渠道联动、IP授权衍生品追踪 | P1 | 1天 |

#### 模块5 - 内容分发中心（视频增强）

| 功能 | 详情 | 优先级 | 工作量 |
|------|------|--------|--------|
| 视频平台对接 | B站/抖音/YouTube 创作者后台API对接 | P0 | 2.5天 |
| 审片协作 | Frame.io式时间码标注评论、版本对比、审批流程 | P1 | 2天 |

### 4.4 手工艺人新增功能清单

#### 模块1 - 创意资产中心（手工增强）

| 功能 | 详情 | 优先级 | 工作量 |
|------|------|--------|--------|
| 物理原件实体 | PhysicalItem主实体、照片作为衍生品关联、制作过程记录 | P0 | 2天 |
| 原料库存管理 | 材料种类/存量/单位/保质期/补货阈值/供应商信息 | P0 | 2天 |
| 生产批次管理 | 批次号/投入数量/过程阶段/缺陷率/产出统计/时间追踪 | P0 | 1.5天 |
| 质检分级 | A/B/C级、缺陷照片、根本原因分类、统计面板 | P0 | 1天 |
| 产品摄影工作流 | 白平衡校正/背景去除/多角度拍摄引导/一致灯光检查清单 | P1 | 1.5天 |
| 手工艺阶段 | 设计→备料→制作→质检→拍摄→上架 | P0 | 0.5天 |

#### 模块4 - 商业转化引擎（手工增强）

| 功能 | 详情 | 优先级 | 工作量 |
|------|------|--------|--------|
| 成本核算 | 材料+人工+能耗+包装+物流=单位成本、利润计算器 | P0 | 1.5天 |
| 按需制造 | 陶瓷/木器/布艺/首饰/3D打印 分类模板 | P1 | 1天 |

#### 模块5 - 内容分发中心（手工增强）

| 功能 | 详情 | 优先级 | 工作量 |
|------|------|--------|--------|
| Etsy API网关 | listing/订单/库存/物流/消息 全API适配 | P0 | 3天 |

### 4.5 技术关键点

| 关键点 | 技术方案 | 风险 |
|--------|---------|------|
| 工程文件解析 | Premiere/AE/DaVinci项目文件结构化解析(XML/JSON) | 专有格式版本兼容性 |
| 视频指纹 | pHash/dHash + ffmpeg关键帧提取、帧序列比对 | 长视频计算时间、阈值调优 |
| 字幕编辑器 | 前端WebVTT解析器 + 时间轴可视化组件 | .ass格式兼容性 |
| 品牌商单 | 工作流引擎(状态机)、通知系统扩展 | 流程复杂度(8个状态+) |
| 视频平台API | 各平台OAuth2.0、API适配器模式 | 平台API频繁变更、速率限制 |
| Etsy API | Etsy Open API v3、OAuth1.0a认证 | API限制(5000次/天) |
| 成本核算引擎 | 可配置成本公式、多币种支持 | 业务逻辑复杂度 |

### 4.6 数据模型扩展（核心新增）

```
v3新增/扩展模型:

# === 视频领域 ===

VideoProject (新表):
  + id, title, project_type(prproj/aep/drp)
  + source_file_path, project_file_path
  + aspect_ratios: JSON       # [{ratio: "16:9", version_id: ...}, ...]
  + stages: JSON              # 脚本/分镜/粗剪/精剪/调色/成片状态
  + created_by, created_at, updated_at

VideoVersion (新表):
  + id, video_project_id, version_number
  + aspect_ratio, file_path, duration
  + thumbnail_path, fingerprint_hash

SubtitleTrack (新表):
  + id, video_project_id, language
  + format(srt/ass/vtt), content: JSON
  + style_config: JSON

BrandCampaign (新表):
  + id, title, brand_name
  + status: Enum(brief/proposal/script/production/review/delivery/settlement)
  + brief_doc, proposal_doc, script_doc
  + feedback: JSON[], delivery_files: JSON[]
  + budget, settlement_amount, settlement_date

PlatformEarning (新表):
  + id, platform(bilibili/douyin/youtube)
  + earning_type, amount, currency
  + period_start, period_end
  + raw_data: JSON

VideoReviewComment (新表):
  + id, video_project_id, user_id
  + timecode, content, resolved
  + created_at, replies: JSON[]

# === 手工艺领域 ===

PhysicalItem (新表):
  + id, title, category(ceramic/wood/fabric/jewelry/3dprint/other)
  + description, production_method
  + created_at, updated_at

MaterialInventory (新表):
  + id, name, category, unit
  + current_stock, min_threshold, unit_cost
  + expiry_date, supplier_info

ProductionBatch (新表):
  + id, physical_item_id, batch_number
  + input_quantity, output_quantity, defect_rate
  + stage: Enum(design/prepare/produce/qa/photograph/list)
  + started_at, completed_at

QualityCheck (新表):
  + id, batch_id, grade(A/B/C)
  + defect_photos: JSON[], root_cause
  + inspector_notes

CostBreakdown (新表):
  + id, physical_item_id
  + material_cost, labor_cost, energy_cost
  + packaging_cost, shipping_cost
  + total_unit_cost, suggested_price

EtsyListing (新表):
  + id, physical_item_id
  + etsy_listing_id, etsy_shop_id
  + status, url, price, quantity
  + last_synced_at
```

### 4.7 5 Agent协作配置

**视频Agent组** (前4天):

| 角色 | 输入 | 产出 | 工期 |
|------|------|------|------|
| **PM(视频)** | v2完成状态、视频评估报告(赵一鸣) | 视频任务矩阵 | 全程 |
| **业务专家(视频)** | 视频创作者工作流调研 | 视频需求设计、品牌商单流程设计 | 2天 |
| **程序员(视频)** | v2代码库、ffmpeg/phash文档 | 技术评估(视频指纹/工程文件/审片协作) | 1.5天 |
| **设计师(视频)** | 视频编辑工具竞品(Frame.io/Premiere/CapCut) | 视频UX规范(审片/字幕/横竖屏) | 1天 |
| **架构师(视频)** | 讨论输出 + v2架构 | 视频数据模型+API设计 | 1天 |

**手工Agent组** (同时进行，后4天):

| 角色 | 输入 | 产出 | 工期 |
|------|------|------|------|
| **PM(手工)** | 手工评估报告(周巧手) | 手工艺任务矩阵 | 全程 |
| **业务专家(手工)** | 手工艺人工作流调研、Etsy API研究 | 手工艺需求设计、Etsy对接策略 | 2天 |
| **程序员(手工)** | v2代码库、Etsy API文档 | 技术评估(库存/批次/成本核算/Etsy API) | 1.5天 |
| **设计师(手工)** | Etsy卖家后台竞品、工艺管理工具 | 手工UX规范(库存/批次/质检/成本) | 1天 |
| **架构师(手工)** | 讨论输出 + v2架构 | 手工数据模型+API设计 | 1天 |

**交集第4-5天**: 两组Agent汇总，架构师合并数据模型，PM全量协调。

**产出清单**: 视频需求文档 + 手工需求文档 + 视频UX规范 + 手工UX规范 + 视频技术评估 + 手工技术评估 + 综合数据模型设计 + 7模块设计更新(v3标注) + 实施计划 + HTML架构图更新

### 4.8 5 Agent协作执行节奏 (8天设计)

```
Day 1-2: 两组并行调研
  - 视频组: 业务专家(视频工作流) + 程序员(代码差距) 并行
  - 手工组: 业务专家(Etsy/手工流程) + 程序员(代码差距) 并行
  - 两组PM各自输出任务矩阵

Day 3: 两组并行设计
  - 视频组: 设计师(UX) + 程序员(技术方案)
  - 手工组: 设计师(UX) + 程序员(技术方案)
  - 两组架构师分别开始数据模型设计

Day 4: 两组内部评审 + 跨组对齐
  - AM: 视频组设计评审 / 手工组设计评审
  - PM: 跨组协调 → 识别共享基础设施、避免重复建设
  - 合并数据模型(架构师联合)

Day 5-6: 集成设计
  - 两个架构师联合完成完整数据模型设计
  - PM 输出综合任务矩阵 + 里程碑
  - 设计师 跨类型 UX 一致性审查

Day 7: 实施计划制定
  - PM + 程序员: 分Phase实施策略(先视频还是先手工, 还是并行)
  - 架构师: API端点完整清单

Day 8: 最终评审 + 产出验收
  - AM: 全体评审 → PM最终报告
  - PM: 产出清单验收 + 实施计划确认
```

---

## 五、v4 - 音乐人 + 文字作者

### 5.1 核心定位

v4 是 OriStudio 离原始视觉基础最远的版本。音乐人和文字作者的工作流需求与视觉创作者完全不同，需要几乎平行的数据模型。好在v1-v3积累的Agent协作模式、合规框架和基础设施可直接复用。

### 5.2 与前一版本共享的基础设施

**从v1-v3继承**:
- 用户/认证/Onboarding/合规框架（完整复用）
- 存证基础设施（扩展音频指纹）
- 分发中心框架（扩展音乐/写作平台）
- 经营管理基础（扩展版税/权利金）
- IP登记工作站

**v4新增但可预铺的v3能力**:
- 视频指纹→音频指纹 技术路径相似（感知哈希）
- 品牌商单→版税拆分 工作流引擎复用

### 5.3 音乐人新增功能清单

#### 模块1 - 创意资产中心（音乐增强）

| 功能 | 详情 | 优先级 | 工作量 |
|------|------|--------|--------|
| 多轨音频支持 | WAV/FLAC/AIFF/MP3 导入、波形可视化、元数据提取 | P0 | 1.5天 |
| 专辑/EP/Single 概念 | 曲目排序、统一定价、发行日期、封面3000x3000、ISRC关联 | P0 | 2天 |
| 音乐过程阶段 | 灵感→编曲→录音→混音→母带→发行 | P0 | 0.5天 |
| 音频指纹 | AcoustID/Chromaprint 集成、指纹生成与匹配 | P1 | 2天 |
| 合作者管理 | 多作者/表演者/制作人关联、Split Sheets权益分配 | P0 | 1.5天 |

#### 模块2 - 权利保护中心（音乐增强）

| 功能 | 详情 | 优先级 | 工作量 |
|------|------|--------|--------|
| ISRC码管理 | ISRC生成/导入/验证、专辑级+曲目级管理 | P0 | 1.5天 |
| PRO注册追踪 | ASCAP/BMI/PRS/音著协 注册状态追踪 | P1 | 1.5天 |
| Master vs Publishing权利 | 两种权利类型的结构化区分、授权合同模板 | P0 | 1.5天 |
| Sample Clearance追踪 | 采样来源/许可状态/授权范围/到期日期 | P1 | 1天 |

#### 模块4 - 商业转化引擎（音乐增强）

| 功能 | 详情 | 优先级 | 工作量 |
|------|------|--------|--------|
| 机械版税登记 | 版税计算器、发行平台版税报告导入 | P1 | 1.5天 |
| Split Sheets管理 | 合作者权益百分比/角色/支付信息、合同生成 | P0 | 1天 |

#### 模块5 - 内容分发中心（音乐增强）

| 功能 | 详情 | 优先级 | 工作量 |
|------|------|--------|--------|
| 音乐分发平台 | Spotify/QQ音乐/网易云/Apple Music 元数据规范适配 | P0 | 2天 |
| 发行商对接 | DistroKid/TuneCore API 适配、发行状态追踪 | P0 | 2天 |

### 5.4 文字作者新增功能清单

#### 模块1 - 创意资产中心（文字增强）

| 功能 | 详情 | 优先级 | 工作量 |
|------|------|--------|--------|
| 章节层级结构 | 卷→章→节→草稿/设定/反馈/批注 树形组织 | P0 | 2天 |
| 写作过程阶段 | 大纲→初稿→修订→终稿→排版→发布 | P0 | 0.5天 |
| 章节修订跟踪 | 章节级diff、编辑反馈/beta reader意见标注、版本对比 | P0 | 1.5天 |
| 设定/灵感管理 | 角色设定/世界观/情节线 卡片式管理、作品关联 | P2 | 1天 |

#### 模块2 - 权利保护中心（文字增强）

| 功能 | 详情 | 优先级 | 工作量 |
|------|------|--------|--------|
| 抄袭检测 | 文本查重服务接入(Copyscape API/本地算法)、相似度报告 | P0 | 2天 |
| 多维度权利管理 | 翻译权/影视权/连载权/有声书权/游戏改编权、地域/期限/阶梯版税 | P0 | 2天 |

#### 模块4 - 商业转化引擎（文字增强）

| 功能 | 详情 | 优先级 | 工作量 |
|------|------|--------|--------|
| EPUB/PDF排版导出 | Pandoc管道 + 章节合并 + 目录生成 + 封面插入 + 样式定制 | P0 | 2.5天 |

#### 模块5 - 内容分发中心（文字增强）

| 功能 | 详情 | 优先级 | 工作量 |
|------|------|--------|--------|
| 写作平台对接 | 起点/晋江/KDP/微信公众号/知乎 发布元数据适配 | P0 | 2天 |

### 5.5 技术关键点

| 关键点 | 技术方案 | 风险 |
|--------|---------|------|
| 音频指纹 | Chromaprint (AcoustID)、fpcalc二进制分发 | 跨平台fpcalc可用性、速率限制 |
| ISRC管理 | ISRC规范校验、批量生成、唯一性检查 | 国家代码申请流程 |
| Split Sheets | 百分比总和校验、PDF合同生成(ReportLab) | 国际法域差异 |
| 章节diff | diff_match_patch 库、树形合并冲突处理 | 大文本diff性能 |
| 抄袭检测 | Copyscape Premium API + 本地ngram比对降级 | API费用、结果准确度 |
| EPUB导出 | Pandoc + 自定义模板、CSS样式注入 | 中文排版兼容性、图片嵌入 |
| 权利矩阵 | 5维度权利 x N法域 x 期限管理 | 数据模型复杂度 |

### 5.6 数据模型扩展（核心新增）

```
v4新增/扩展模型:

# === 音乐领域 ===

Album (新表):
  + id, title, type(single/ep/album)
  + cover_art_path, release_date, total_tracks
  + upc_ean, label, price

Track (新表):
  + id, album_id, track_number, title
  + isrc, duration, audio_file_path
  + lyrics_path, waveform_data: JSON
  + genre, bpm, key

Collaborator (新表):
  + id, track_id, user_id(可选外部)
  + role(composer/lyricist/performer/producer/arranger)
  + split_percentage, payment_info: JSON

MusicRegistration (新表):
  + id, track_id, registration_type(pro/mechanical/soundexchange)
  + organization(ascap/bmi/prs/mcsc/etc.), status, registration_number

SampleClearance (新表):
  + id, track_id, sample_source
  + rights_holder, license_status, cleared_for
  + clearance_doc_path, expiry_date

MusicDistribution (新表):
  + id, track_id/album_id, platform(spotify/qqmusic/netcase/applemusic)
  + distributor(distrokid/tunecore), release_status
  + platform_uri, submitted_at, live_at

# === 文字领域 ===

Manuscript (新表):
  + id, title, type(novel/novella/short_story/serial/webnovel)
  + status(outline/draft/revision/final/layout/published)
  + total_words, target_words

Chapter (新表):
  + id, manuscript_id, volume_number
  + chapter_number, title, word_count
  + status, sort_order

ChapterRevision (新表):
  + id, chapter_id, version_number
  + content, word_count, diff_from_previous
  + revision_notes, reviewer_feedback: JSON[]

StorySetting (新表):
  + id, manuscript_id, type(character/worldbuilding/plotline)
  + title, content: JSON, related_chapters: JSON[]

RightsLicense (新表):
  + id, manuscript_id, right_type(translation/film/serialization/audiobook/game)
  + territory, start_date, end_date
  + royalty_rate, royalty_tier: JSON, licensee_info

PlagiarismCheck (新表):
  + id, chapter_id, check_service
  + similarity_score, matched_sources: JSON[]
  + checked_at
```

### 5.7 5 Agent协作配置

**音乐Agent组** (前4天):

| 角色 | 输入 | 产出 | 工期 |
|------|------|------|------|
| **PM(音乐)** | v3完成状态、音乐评估报告(苏旋律) | 音乐任务矩阵 | 全程 |
| **业务专家(音乐)** | 音乐产业工作流调研、发行平台研究 | 音乐需求设计、ISRC/Split Sheets/PRO注册策略 | 2天 |
| **程序员(音乐)** | v3代码库、AcoustID/DistroKid/TuneCore API文档 | 技术评估(音频指纹/ISRC/发行API) | 1.5天 |
| **设计师(音乐)** | 音乐制作工具竞品(Logic/Cubase/Ableton/DistroKid) | 音乐UX规范(专辑管理/波形/权益分配) | 1天 |
| **架构师(音乐)** | 讨论输出 + v3架构 | 音乐数据模型+API设计 | 1天 |

**文字Agent组** (同时进行，后4天):

| 角色 | 输入 | 产出 | 工期 |
|------|------|------|------|
| **PM(文字)** | 文字评估报告(文墨) | 文字任务矩阵 | 全程 |
| **业务专家(文字)** | 写作行业调研、写作平台研究 | 文字需求设计、权利管理策略 | 2天 |
| **程序员(文字)** | v3代码库、Pandoc/Copyscape文档 | 技术评估(EPUB管道/抄袭检测/章节diff) | 1.5天 |
| **设计师(文字)** | 写作工具竞品(Scrivener/Ulysses/Notion) | 文字UX规范(章节树/写作编辑器/修订对比) | 1天 |
| **架构师(文字)** | 讨论输出 + v3架构 | 文字数据模型+API设计 | 1天 |

**产出清单**: 音乐需求文档 + 文字需求文档 + 音乐UX规范 + 文字UX规范 + 音乐技术评估 + 文字技术评估 + 综合数据模型设计 + 7模块设计更新(v4标注) + 实施计划 + HTML架构图更新

### 5.8 5 Agent协作执行节奏 (8天设计)

与v3相同的两组并行4天+集成4天节奏。

---

## 六、v5 - 全类型 + AI增强 (愿景版)

### 6.1 核心定位

v5 不再新增创作者类型，而是在 v1-v4 完整覆盖的基础上实现两个质的飞跃：
1. **跨类型智能工作流** — 打破创作者类型壁垒，支持跨类型协同
2. **AI深度学习** — 从"工具"进化到"智能伙伴"

### 6.2 方向性功能清单（待后续详细规划）

| 方向 | 功能概念 | 依赖 |
|------|---------|------|
| 跨类型协同 | 多创作者项目（插画师+文字作者合作绘本） | v1+v4 |
| 跨类型协同 | 编辑/经纪人/代理多角色协作面板 | v1-v4全类型 |
| AI学习 | 个人风格学习引擎（历史作品风格提取） | v1-v4作品库 |
| AI学习 | 智能标签/分类/阶段建议（基于行为学习） | v1-v4数据积累 |
| 移动端 | React Native 响应式增强 / PWA | v1-v4 API基础设施 |
| 移动端 | 移动端拍照快速导入+基础选片 | v2 RAW能力 |
| 社区 | 创作者作品集展示页（公开Profile） | v1-v4作品库 |
| 高级分析 | 跨平台数据聚合、收入/流量/粉丝趋势仪表盘 | v1-v4分发数据 |
| 区块链 | 区块链存证增强（可选、非必须） | v1存证体系 |

---

## 七、版本间依赖与升级路径

### 7.1 数据模型扩展策略

```
v1 (插画师)
  ├── CreativeAsset (基础文件模型)
  ├── Work/Version (作品/版本)
  ├── Product/Publishing (产品/分发)
  └── 收入/合作伙伴/通知

v2 (+摄影师) — 扩展 v1 模型，新增组件
  ├── CreativeAsset +raw_path, +xmp_data, +culling_status, +EXIF扩展字段
  ├── +WatermarkTemplate, +MetadataPreset, +StockPlatformListing
  └── 现有表不变，仅扩展字段

v3 (+视频+手工) — 新增独立模型簇
  ├── +VideoProject, +VideoVersion, +SubtitleTrack, +BrandCampaign
  ├── +PlatformEarning, +VideoReviewComment
  ├── +PhysicalItem, +MaterialInventory, +ProductionBatch
  ├── +QualityCheck, +CostBreakdown, +EtsyListing
  └── CreativeAsset 不变（视频项目包独立管理）

v4 (+音乐+文字) — 新增独立模型簇
  ├── +Album, +Track, +Collaborator, +MusicRegistration
  ├── +SampleClearance, +MusicDistribution
  ├── +Manuscript, +Chapter, +ChapterRevision
  ├── +StorySetting, +RightsLicense, +PlagiarismCheck
  └── 先前模型不变
```

### 7.2 向后兼容策略

| 策略 | 细则 |
|------|------|
| **加字段不加表删除** | 扩展现有表只新增可空字段，不断增加必填字段 |
| **独立模型簇** | 新创作者类型的新表完全独立，不污染已有表结构 |
| **API版本化** | `/api/v1/works` → v2新增的RAW/EXIF高级搜索端点用 `/api/v2/works/raw` |
| **前端渐进增强** | 检测用户creator_type → 动态展示对应功能Tab |
| **数据迁移零损失** | 每版本新增 CreatorTypeMixin → 自动关联已有作品到对应类型 |
| **废弃标记** | 功能从"规划中"→"完整支持"时，移除前版本标记但保留数据 |

### 7.3 各版本创作者类型状态矩阵演变

| 创作者类型 | v1 | v2 | v3 | v4 | v5 |
|-----------|-----|-----|-----|-----|-----|
| 插画师/AIGC | 完整 | 完整 | 完整 | 完整 | 完整+AI |
| 摄影师 | 规划中 | **完整** | 完整 | 完整 | 完整+AI |
| 短视频/动画 | 规划中 | 规划中 | **完整** | 完整 | 完整+AI |
| 手工艺人 | 规划中 | 规划中 | **完整** | 完整 | 完整+AI |
| 音乐人 | 规划中 | 规划中 | 规划中 | **完整** | 完整+AI |
| 文字作者 | 规划中 | 规划中 | 规划中 | **完整** | 完整+AI |

### 7.4 模块扩展路径

```
模块1 创意资产中心
  v1: 图片导入+基础版本
  v2: +RAW解码+选片+EXIF高级搜索+GPS地图
  v3: +视频项目包+字幕管理+物理原件+库存/批次
  v4: +专辑/曲目+章节层级+写作编辑器+设定管理
  v5: +AI自动标签/分类/阶段建议

模块2 权利保护中心
  v1: SHA-256存证+侵权监测
  v2: +批量水印服务
  v3: +视频指纹存证
  v4: +ISRC管理+音频指纹+抄袭检测+多维权利矩阵
  v5: +区块链存证增强(可选)

模块3 IP登记工作站
  v1: UPL合规完整(多分类+置信度+律师审核+7项免责)
  v2-v5: 持续合规维护，无明显版本差异

模块4 商业转化引擎
  v1: Canvas三层预览+POD渠道管理
  v2: +数字下载+艺术微喷+预设包
  v3: +品牌商单+成本核算+按需制造+平台激励追踪
  v4: +Split Sheets+版税计算+EPUB/PDF排版
  v5: +AI定价建议+跨类型产品协同

模块5 内容分发中心
  v1: 8个社交平台
  v2: +图库API(Shutterstock/500px/图虫)
  v3: +视频平台(B站/抖音/YouTube)+Etsy API
  v4: +音乐平台(Spotify/QQ音乐/网易云/Apple Music)+写作平台(起点/晋江/KDP)
  v5: +智能发布时间建议+多平台数据聚合

模块6 经营管理中心
  v1: 收入登记+CSV导入
  v2: +图库收入/艺术微喷订单
  v3: +品牌商单结算+平台激励+成本核算
  v4: +版税追踪+权利金拆分+分销收入
  v5: +跨平台收入聚合+AI收入预测

模块7 系统基础设施
  v1-v5: 持续演进，每版本扩展字典、大文件阈值、第三方API配置、监控
```

---

## 八、总时间线

```
2026 Q2-Q3
│
├── v1: 插画师/AIGC 艺术家 ──────────────────────┐
│    ├─ 设计(已完成)                                │
│    ├─ Phase 0 合规修复    3天                     │
│    ├─ Phase 1 核心能力    5-6天                   │
│    ├─ Phase 2 UX体验      4天                     │
│    └─ Phase 3 文档同步    1天                     │
│    设计已完 | 实施 13-14天                         │
│                                                    │
│    ═══════ 1周稳定期 ═══════                      │
│                                                    │
├── v2: +摄影师 ─────────────────────────────────┐  │
│    ├─ 5 Agent 协作设计   5天                    │  │
│    ├─ RAW解码+选片       2天                    │  │
│    ├─ 水印+EXIF搜索      3.5天                  │  │
│    ├─ 元数据模板+XMP      3天                    │  │
│    ├─ 图库API             2.5天                  │  │
│    └─ 测试+文档           1天                    │  │
│    设计 5天 | 实施 10-12天                       │  │
│                                                    │  │
│    ═══════ 1-2周稳定期 ═══════                    │  │
│                                                    │  │
├── v3: +视频/动画 +手工艺人 ────────────────────┐  │  │
│    ├─ 5 Agent x2 设计    8天                    │  │  │
│    ├─ 视频:项目包+指纹    4.5天                  │  │  │
│    ├─ 视频:字幕+商单      4.5天                  │  │  │
│    ├─ 视频:审片+分发      4天                    │  │  │
│    ├─ 手工:原件+库存      3.5天                  │  │  │
│    ├─ 手工:批次+质检      2.5天                  │  │  │
│    ├─ 手工:成本+Etsy      4.5天                  │  │  │
│    ├─ 集成测试            2天                    │  │  │
│    └─ 文档同步            1天                    │  │  │
│    设计 8天 | 实施 14-18天                       │  │  │
│                                                    │  │  │
│    ═══════ 2周稳定期 ═══════                      │  │  │
│                                                    │  │  │
├── v4: +音乐人 +文字作者 ──────────────────────┐  │  │  │
│    ├─ 5 Agent x2 设计    8天                    │  │  │  │
│    ├─ 音乐:专辑+ISRC      3.5天                  │  │  │  │
│    ├─ 音乐:Split+发行     3.5天                  │  │  │  │
│    ├─ 音乐:指纹+PRO       3天                    │  │  │  │
│    ├─ 文字:章节+修订       3.5天                  │  │  │  │
│    ├─ 文字:权利+抄袭       4天                    │  │  │  │
│    ├─ 文字:EPUB+平台       4.5天                  │  │  │  │
│    ├─ 集成测试            2天                    │  │  │  │
│    └─ 文档同步            1天                    │  │  │  │
│    设计 8天 | 实施 14-18天                       │  │  │  │
│                                                    │  │  │  │
│    ═══════ 2周稳定期 ═══════                      │  │  │  │
│                                                    │  │  │  │
└── v5: 全类型+AI增强 ───────────────────────────┘  │  │  │  │
     规划中，待 v1-v4 完成后再定详细方案              │  │  │  │
                                                       │  │  │  │
──────────────────────────────────────────────────────┘──┘──┘──┘
```

### 里程碑摘要

| 里程碑 | 预计时间 | 产出 |
|--------|---------|------|
| M1 - v1上线 | 第3周 | 插画师全链路完整可用 |
| M2 - v2上线 | 第7周 | 摄影师完整支持，首类非插画师用户可迁移 |
| M3 - v3上线 | 第13周 | 视频+手工两大差异类型完整支持，数据模型重大扩展 |
| M4 - v4上线 | 第20周 | 6类创作者全覆盖 |
| M5 - v5启动 | 第22周 | 跨类型智能+AI深度学习规划 |

**总时间**: v1启动到v4上线约 20-22 周（约5个月），v5在v4稳定后规划。

---

## 九、风险与缓解

| 风险 | 严重度 | 缓解措施 |
|------|--------|---------|
| v3两个差异极大类型并行导致质量分散 | 高 | v3设计期两组Agent独立但定期跨组对齐；实施时优先一个类型再另一个 |
| 每版本新增类型导致API/UI膨胀 | 中 | 统一适配器模式、类型检测动态展示功能Tab |
| 第三方API依赖（图库/Etsy/音乐平台） | 高 | 每个API适配器设降级策略(手动模式)、定期API兼容性检查 |
| 大文件处理（RAW 50MB+/视频 GB级） | 中 | 分片上传、差异快照、存储配额提示 |
| 测试覆盖随版本增加而稀释 | 中 | 每版本强制80%+覆盖率、核心路径E2E必测 |
| 5 Agent协作在v3/v4中沟通成本指数增长 | 中 | 固定协作节奏、设计文档为单一事实源、PM为最终协调人 |
| 非视觉类型(v4音乐/文字)UX偏离核心设计语言 | 中 | 设计师跨组一致性审查、统一Design Token |
| 法律合规(新类型新法域) | 中 | v1合规框架每版本review一次 |

---

## 十、附录：各版本Agent协作模板

### A. 5角色分工速查表

| 角色 | 核心职责 | 关键产出 | 每版本工期 |
|------|---------|---------|-----------|
| **PM** | 总体规划、任务分配、进度监督、质量把关、最终输出 | 任务矩阵、里程碑甘特图、风险登记簿、最终报告 | 全设计期 |
| **业务专家** | 该类型创作者真实工作流调研、业务实现方式研究 | 需求设计文档、业务规则定义、平台对接策略 | 2天 |
| **程序员** | 技术可行性评估、代码差距分析、实现路径 | 技术评估报告、代码差距清单、实施建议 | 1.5天 |
| **设计师** | 专属UX设计、交互流程、空状态、术语优化 | UX设计规范、交互原型、术语对照表 | 1天 |
| **架构师** | 汇总讨论结果、更新全部设计文档 | 数据模型设计、API端点清单、模块设计更新 | 1-1.5天 |

### B. 每版本标准产出清单

```
版本产出包:
  ├── requirements-v{version}-{type}.md        # 需求文档
  ├── ux-spec-v{version}-{type}.md             # UX规范
  ├── technical-assessment-v{version}-{type}.md # 技术评估
  ├── modules-v{version}/                       # 模块设计更新
  │   ├── 01-creative-assets.md
  │   ├── 02-rights-protection.md
  │   ├── 03-ip-registration.md
  │   ├── 04-monetization-engine.md
  │   ├── 05-content-distribution.md
  │   ├── 06-business-management.md
  │   └── 07-system-infra.md
  ├── implementation-plan-v{version}.md         # 实施计划
  ├── architecture-diagram-v{version}.html      # HTML架构图
  └── master-design-v{version}.md               # 设计总纲更新
```

### C. Agent设计期日常节奏

```
09:00 - PM 每日站会 (15min)：进度同步、阻塞识别、优先级调整
09:15 - 各角色独立工作
12:00 - 午餐
13:30 - 交叉评审（业务↔程序、设计↔架构）
15:00 - 各角色独立工作
17:00 - PM 日终汇总 (30min)：当日产出上传、风险更新、次计划确认
```

---

> **本文档基于**: `docs/agent-evaluation-report.md` (9角色评估)、`docs/master-design-v3.md` (系统总纲)、`docs/OriStudio-完整实施计划.md` (v1实施计划)、`docs/modules-v3/` (7模块设计)、`docs/requirements-v3-full.md` (6类创作者完整需求分析)
>
> **下一步**: 本文档经评审确认后，作为v2-v5各版本启动的纲领性文件。
