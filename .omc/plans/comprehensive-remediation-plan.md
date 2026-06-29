---
description: Comprehensive system remediation plan for all unfinished features and bugs
status: pending approval
created: 2026-06-22
updated: 2026-06-22
modules_covered: 01-07
---

# OriStudio 全面修复与功能落实计划

## 背景

用户要求："全面排查系统未完成功能、系统bug都修复，将所有版本，计划的已设计功能全部落实到系统代码。"

经过全面扫描 7 个模块的设计文档、后端代码、前端代码、自动计划和记忆文件，本计划覆盖所有 P0-P4 优先级的未完成功能和已知 bug。

**审查修正记录**: 初版计划中有 5/12 项已实现（视频缩略图 30%、IPRegistration 律师字段、priority→confidence、BusinessView、BusinessChainBar），已移除。Alembic 从 Phase D 提升为 Phase A。

---

## 优先级定义

| 级别 | 含义 | 策略 |
|------|------|------|
| **P0** | 设计文档明确为 v1 但代码中存在缺口 | 立即修复 |
| **P1** | 自动计划/记忆文件中明确标记的 Phase 2-4 任务 | 本轮实施 |
| **P2** | 跨模块标注为 v2 的功能 | 选择性实施核心部分 |
| **P3** | 标注为 v3 的功能 | 仅实施数据库模型 + API 骨架 |
| **P4** | 标注为 v4 的功能 | 记录在案，暂不实施 |

---

## P0: 设计文档明确为 v1 但存在缺口

### P0-1: 文件夹导入 user_id 硬编码

**现状**: `backend/app/routers/works.py` 第 1084/1092/1132 行，`user_id` 硬编码为 `"local"`，有 `# TODO: get from auth` 注释  
**设计**: 文件夹导入应归属到当前登录用户

**修复方案**:
- 文件: `backend/app/routers/works.py`
- 从认证头中提取 `user_id`，替换三处硬编码
- 添加递归深度限制（默认 5 层）
- 添加进度报告机制（返回导入统计：成功/跳过/失败）
- 移除 `# TODO: get from auth` 注释

**验收标准**: 上传文件夹后，所有作品归属到正确用户，项目自动创建

---

### P0-2: 认证中间件统一化 + works.py 零认证修复

**现状**:
- `backend/app/routers/works.py` 全部 18+ 端点**无任何认证检查** — 最大安全缺口
- `backend/app/routers/auth.py` 7 处、`system.py` 9 处重复内联认证检查
- `deps.get_current_user` 存在于 `auth.py:268` 但从未通过 `Depends()` 使用（零匹配）

**修复方案**:
- 文件: `backend/app/deps.py`（扩展现有依赖模块）
- 创建 `get_current_user(authorization: Header(...) = Header(...)) -> User` 统一依赖
- 替换 `auth.py` 和 `system.py` 中的所有内联认证检查
- **关键**: 为 `works.py` 所有端点添加认证保护
- 添加统一的 401/403 错误处理

**验收标准**: 所有端点通过统一依赖获取用户身份；访问作品端点需要有效 token

**风险**: 触及 16+ 端点 Across 4+ 路由器文件。逐个路由器替换，每替换一个验证。

---

### P0-3: Alembic 初始迁移

**现状**: `alembic/versions/` 零迁移文件，数据库 schema 无版本控制  
**风险**: 任何 schema 变更都可能造成数据丢失

**修复方案**:
- 运行 `alembic revision --autogenerate -m "initial schema"` 生成初始迁移
- 验证 `alembic upgrade head` 可干净执行
- 此后每次 schema 变更必须通过 alembic

**验收标准**: `alembic history` 显示迁移链，`alembic upgrade head` 可执行

---

## P1: 自动计划/记忆文件中明确标记的 Phase 2-4 任务

### P1-1: IprView.vue 局部重写

**来源**: `.omc/plans/autopilot-impl.md` Phase 3  
**现状**: `IprView.vue` 存在（82KB），免责声明使用 Modal 而非 Banner  
**修复方案**:
- 文件: `frontend/src/views/IprView.vue`
- 免责声明从 Modal 改为 Banner（页面顶部常驻）
- 管辖区域 Tab 切换
- 指南卡片可折叠
- 新建子组件: `IpTypeSelector.vue`, `JurisdictionGuide.vue`, `SmartAssistant.vue`

**验收标准**: IPR 页面有清晰的区域划分，指南可折叠，免责声明常驻顶部

---

### P1-2: SupplyView 去重 — 移除重复的收入/工厂/订单 Tab

**来源**: `.omc/plans/autopilot-impl.md` Phase 2/3  
**现状**: `BusinessView.vue` 已存在（13.9KB，含 5 Tab），但 `SupplyView.vue` 仍有重叠的变现仪表盘 Tab

**修复方案**:
- 文件: `frontend/src/views/SupplyView.vue`
- 移除 Revenue/Factory/Order 相关 Tab（已在 BusinessView 中）
- 保留 Supply 专属 Tab（产品/上架/活动）
- 确保导航路由正确指向 BusinessView

**验收标准**: SupplyView 不再有收入/工厂/订单 Tab，功能在 BusinessView 中可用

---

### P1-3: DashboardView 经营概览增强

**来源**: `.omc/plans/autopilot-impl.md` Phase 2  
**现状**: `DashboardView.vue`（7.8KB）无业务概览卡片

**修复方案**:
- 文件: `frontend/src/views/DashboardView.vue`
- 添加"经营概览"卡片区域
- 显示: 总收入、活跃产品数、进行中活动数、待处理订单数
- 数据来源: 复用现有 API (`/api/supply/dashboard-summary`)

**验收标准**: Dashboard 首页有业务概览数据

---

### P1-4: 前端遗留 .bak 文件清理

**现状**: `frontend/src/views/OnboardingView.vue.bak` 存在

**修复方案**: 删除 .bak 文件

---

## P2: 跨模块标注为 v2 的核心功能

### P2-1: 摄影师 RAW 格式支持

**设计**: `docs/modules-v3/01-creative-assets.md` 12.1.1  
**文件参考**: 模型 `backend/app/models/work.py`，服务 `backend/app/services/work_service.py`

**修复方案**:
- 数据库: 扩展 `works` 表添加 `is_raw_original: bool`, `raw_sidecar_path: str | None`, `raw_processed_variant_id: str | None`
- 后端: 在 `detect_file_type()` 中扩展 RAW 扩展名 (CR2, NEF, ARW, DNG, RW2, ORF, PEF, RAF, X3F)
- 后端: 添加 `import-raw` 端点，自动提取 EXIF
- 前端: 在作品预览中增加 RAW 标识

**验收标准**: 上传 RAW 文件后可正确识别类型并提取 EXIF

---

### P2-2: EXIF 高级搜索

**设计**: `docs/modules-v3/01-creative-assets.md` 12.1.2  
**文件参考**: 路由器 `backend/app/routers/works.py`，前端 `frontend/src/views/WorkListView.vue`

**修复方案**:
- 后端: `/api/works` 接受查询参数: `camera`, `lens`, `iso`, `aperture`, `focal_length`, `shutter_speed`, `date_from`, `date_to`, `gps_lat`, `gps_lon`
- 前端: 在搜索面板中添加 EXIF 筛选器（可折叠）
- 前端: `ExifSearchPanel.vue` 组件

**验收标准**: 可按相机型号/ISO/光圈等条件筛选作品

---

### P2-3: 策展模式 (Culling)

**设计**: `docs/modules-v3/01-creative-assets.md` 12.1.3  
**文件参考**: 模型 `backend/app/models/work.py`

**修复方案**:
- 数据库: 扩展 `works` 表添加 `cull_status: str`, `cull_rating: int`, `color_label: str`
- 后端: 批量策展 API (`POST /api/works/cull-batch`)
- 前端: `CullingView.vue` — 网格视图 + 键盘快捷键 (P/X/H/Z)

**验收标准**: 摄影师可用快捷键快速筛选作品

---

### P2-4: 元数据模板

**设计**: `docs/modules-v3/01-creative-assets.md` 12.1.4  
**文件参考**: 模型 `backend/app/models/work.py`

**修复方案**:
- 数据库: 创建 `metadata_templates` 表 (`id`, `name`, `fields: JSON`, `is_default`, `created_by`)
- 后端: CRUD 端点 + 批量应用模板 (`POST /api/metadata-templates/{id}/apply`)
- 前端: `MetadataTemplateManager.vue`

**验收标准**: 可创建/保存/应用元数据模板到多个作品

---

### P2-5: 水印预设

**设计**: `docs/modules-v3/01-creative-assets.md` 12.1.5  
**文件参考**: 后端 `backend/app/services/watermark_service.py`（设计文档标注 v2 范围）

**修复方案**:
- 数据库: 创建 `watermark_presets` 表
- 后端: 水印服务（文本/图片/平铺水印）
- 前端: 水印预览和预设管理

**验收标准**: 可对作品图片批量添加水印

---

### P2-6: 订阅会员系统

**设计**: `docs/modules-v3/04-monetization-engine.md` 16.1  
**文件参考**: 模型 `backend/app/models/supply.py`

**修复方案**:
- 数据库: 创建 `subscription_tiers` 和 `subscription_subscribers` 表
- 后端: Tier CRUD + 订阅/取消订阅 API
- 前端: 订阅管理面板

**验收标准**: 可创建付费订阅层级，用户可订阅/退订

---

### P2-7: 定制委托工作流

**设计**: `docs/modules-v3/04-monetization-engine.md` 16.2 + `06-business-management.md` 11.1  
**文件参考**: 模型 `backend/app/models/supply.py`, `backend/app/models/business.py`

**修复方案**:
- 数据库: 创建 `commission_projects` 表（含里程碑、付款条款）
- 数据库: 创建 `commission_orders` 和 `commission_messages` 表
- 后端: 委托项目 CRUD + 状态机 (Brief→Proposal→Production→Delivery→Settlement)
- 前端: `CommissionKanban.vue`, `CommissionDetail.vue`, `CommissionForm.vue`

**验收标准**: 可创建委托项目，跟踪里程碑和消息

---

### P2-8: 账户安全与通知偏好

**设计**: `docs/modules-v3/07-system-infra.md` 10  
**文件参考**: 前端 `frontend/src/views/SettingsView.vue`

**修复方案**:
- 前端: 在 SettingsView 中添加 `account_security` 分区（密码修改 + 2FA 完善）
- 前端: 添加 `notification_prefs` 分区
- 新建组件: `DisclaimerBanner.vue`, `OnboardingWizard.vue`

**验收标准**: 设置页面有完整的账户安全和通知偏好分区

---

## P3: 标注为 v3 的功能（仅实施模型 + API 骨架）

### P3-1: 视频项目包概念
- 数据库: `project_file_formats` 表 + `works.is_project_package`, `works.project_files`
- 后端: `import-project` 端点骨架
- 前端: 无需立即实现

### P3-2: 字幕管理
- 数据库: `subtitles` 表
- 后端: CRUD 端点骨架
- 前端: 无需立即实现

### P3-3: 视频感知哈希
- 数据库: `works.perceptual_hash`, `works.perceptual_hash_type` + `video_fingerprint_config` + `video_frame_fingerprints`
- 后端: 骨架端点（实际 YouTube Content ID 集成 v3+）
- 前端: 无需立即实现

### P3-4: 宽高比变体管理
- 数据库: `works.aspect_ratio_variants` + `work_variant_groups` 表
- 后端: CRUD 端点骨架

### P3-5: 工厂连接 (RFQ + 样品 + 质检)
- 数据库: `rfq_requests`, `samples`, `quality_reports` 表
- 后端: CRUD 端点骨架
- 前端: 无需立即实现

---

## P4: 标注为 v4 的功能（仅记录在案）

以下功能设计文档中明确标注为 v4，本次不实施，仅记录以便后续追踪：

- 音乐 ISRC/ISWC 元数据
- 专辑/EP/Single 管理
- 分轨权益 (Split Sheets)
- 作家章节结构
- EPUB 导出
- 文学权利细分
- 音频指纹/AcoustID
- 文本抄袭检测
- C2PA 内容凭证
- 音乐发行平台集成
- 写作平台集成

---

## 已知 Bug 修复

### Bug-1: 监控扫描使用 Mock 数据无区分

**现状**: 扫描结果页面显示模拟数据但无明确标记  
**文件参考**: `backend/app/routers/monitor.py` 第 134-137, 217-219, 1093 行

**修复**: 在 UI 上为 mock 结果添加明显标签（"模拟数据" badge），或在设置中明确标注扫描功能当前处于模拟模式

---

### Bug-2: 双产品 Listing 系统共存

**现状**: `/supply/products` (旧 Product) 和 `/supply/listings` (新 DesignListing) 并存  
**文件参考**: `backend/app/models/supply.py`

**修复**: 在后端添加 deprecation 警告日志，旧端点标记 `@deprecated`，前端逐步迁移到 DesignListing

---

### Bug-3: 通知/审计日志 user_id 硬编码

**现状**: 整个通知系统使用 `user_id = "default"`  
**文件参考**: `backend/app/routers/system.py`, `monitor.py`, `notary.py`, `ipr.py`

**修复**: 与 P0-2 统一认证中间件一起修复，所有端点从 JWT 中提取真实 user_id

---

## 实施顺序

```
Phase A (P0 紧急修复):
  1. P0-2: 认证中间件统一化 + works.py 零认证修复
  2. P0-1: 文件夹导入 user_id 修复
  3. P0-3: Alembic 初始迁移

Phase B (P1 UX 修复):
  4. P1-1: IprView 局部重写
  5. P1-2: SupplyView 去重
  6. P1-3: Dashboard 经营概览增强
  7. P1-4: .bak 文件清理

Phase C (P2 v2 核心功能):
  8. P2-1: RAW 格式支持
  9. P2-2: EXIF 高级搜索
  10. P2-3: 策展模式
  11. P2-4: 元数据模板
  12. P2-5: 水印预设
  13. P2-6: 订阅系统
  14. P2-7: 委托工作流
  15. P2-8: 账户安全与通知偏好

Phase D (P3 骨架 + Bug 修复):
  16. P3-1~P3-5: 数据库模型 + API 骨架
  17. Bug-1~Bug-3: Mock 标记、双系统共存、user_id 修复
```

---

## 风险与缓解

| 风险 | 影响 | 缓解 |
|------|------|------|
| **works.py 零认证** | 最大安全缺口，任何人可读写作品 | Phase A 优先修复 |
| 认证中间件统一化触及 16+ 端点 | 大规模回归风险 | 逐个路由器替换，每替换一个验证 |
| Alembic 初始迁移基于当前 schema | 如果当前 DB 有脏数据可能冲突 | 先备份 DB，再生成迁移 |
| 前端组件大量新增 | 编译错误风险 | 逐组件验证，`vue-tsc` 检查 |
| Ollama AI 依赖 | 功能不可用 | 保留模板回退路径 |
| 外部 API 集成 | 需要 API Key | 先用 mock 骨架，留接口 |

---

## 验证方案

1. `vue-tsc --noEmit --skipLibCheck` — 前端编译无错误
2. 后端启动无报错
3. `alembic history` 显示迁移链，`alembic upgrade head` 可执行
4. 每个 P0 功能手动测试（特别是 works.py 认证保护）
5. 每个 P1 功能端到端测试
6. P2+ 功能 API 端点可用（`curl` 测试）
7. 所有 mock 扫描结果有明确标记

---

## ADR (Architecture Decision Records)

### ADR-1: 认证中间件统一化
- **决策**: 创建 `get_current_user` 依赖并通过 `Depends()` 注入
- **驱动因素**: 消除 16+ 端点的重复认证代码，修复 works.py 零认证安全缺口
- **备选考虑**: (a) 使用 FastAPI `Security()` 组合 — 更复杂不必要 (b) 自定义 Middleware — 过度工程
- **为什么选 Depends**: 与 FastAPI 最佳实践一致，易于测试，类型安全
- **后果**: 所有端点行为改变 — 未认证请求从"静默通过"变为"401"

### ADR-2: Alembic 初始迁移
- **决策**: 基于当前 SQLAlchemy 模型生成初始迁移
- **驱动因素**: 数据库 schema 零版本控制，任何变更都有数据丢失风险
- **备选考虑**: (a) 手写迁移 — 耗时且易遗漏 (b) 继续不用迁移 — 不可接受
- **为什么选 autogenerate**: 快速、准确、与模型一致
- **后果**: 此后每次 schema 变更必须通过 alembic

### ADR-3: P2 功能选择性实施
- **决策**: 只实施对 3 种以上创作者类型有用的通用功能
- **驱动因素**: 2.1-2.8 共 8 个 P2 功能，全部实施工作量巨大
- **备选考虑**: (a) 全部实施 — 超出本轮范围 (b) 全部跳过 — 浪费设计投入
- **为什么选选择性**: RAW/EXIF/Culling 对摄影师有用；元数据模板和水印对所有人有用；订阅/委托对商业化有用
- **后果**: 部分 v2 功能推迟到后续迭代
