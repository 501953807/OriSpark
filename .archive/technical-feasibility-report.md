# OriStudio v3 技术可行性评估报告

> **评估日期**: 2026-06-12 | **评估角色**: 程序员
> **评估方法**: 深度探索 backend/ 和 frontend/ 实际代码，基于真实代码状态给出技术路径

---

## 一、实际代码状态发现

### 1.1 端点统计: 文档145 → 实际231

| 路由文件 | 实际端点数 |
|---------|-----------|
| `system.py` | 50 |
| `supply.py` | 42 |
| `monitor.py` | 31 |
| `ipr.py` | 24 |
| `notary.py` | 18 |
| `works.py` | 18 |
| `publish.py` | 17 |
| `auth.py` | 14 |
| `versions.py` | 8 |
| `batch_works.py` | 6 |
| `dashboard.py` | 2 |
| `websocket_router.py` | 1 |
| **合计** | **231** |

代码比文档多 59% (86 端点)。

### 1.2 模型统计: 文档33表 → 实际49模型类

10个模型文件，49个模型类。关键发现:
- **Order/Partner/OrderPayment** 已在 `supply.py` 中完整实现
- **Campaign/License** 已在 `monetization.py` 中实现
- **RevenueRecord** 已在 `publish.py` 中实现
- 文档严重低估功能范围

### 1.3 前端组件状态

| 组件 | 状态 |
|------|------|
| SupplyView.vue | ✅ 已实现(含dashboard/产品设计器/产品/渠道/众筹/授权/合作伙伴/订单/收入) |
| PublishView.vue | ✅ 已实现(含产品CRUD/AI文案/CSV导出/徽章) |
| WorkDetailView.vue | ✅ 已实现(含预览/EXIF/版本历史/标签) |
| OnboardingView.vue | ⚠️ 仅为幻灯片，需交互式重写 |
| ProductMockup.vue | ❌ 不存在，需全新创建 |
| WatermarkService | ❌ 不存在，需从零开发 |

### 1.4 关键能力状态

| 能力 | 状态 |
|------|------|
| RAW支持 | ❌ ALLOWED_EXTENSIONS 不含 RAW/CR2/NEF/ARW/DNG |
| 视频缩略图 | ⚠️ 当前取首帧，需改为30%位置关键帧 |
| 文件夹导入 | ❌ 不支持递归读取，需新增 |
| Printful网关 | ⚠️ Mock存在，需配置 API Key + 增加 Mockup Generator API |
| Etsy网关 | ❌ 不存在 |
| WebSocket | ✅ 基础存在，需增强 per-user rooms |
| 图像指纹 | ✅ LocalFingerprint 模型已存在 (dHash/pHash/wHash) |
| 视频指纹 | ❌ 需从零开发 |
| 音频指纹 | ❌ 需 pyacoustid + Chromaprint |

---

## 二、14项核心技术可行性评级

| # | 能力 | 评级 | 说明 |
|---|------|------|------|
| 1 | Canvas扁平叠加mockup | ✅ 可做 | 前端Canvas API + PIL，低复杂度 |
| 2 | Printful Mockup API | ⚠️ 需降级 | 需付费计划($24.99/月+)，作为P1增强 |
| 3 | 批量文件夹导入+递归+项目组 | ✅ 可做 | webkitGetAsEntry API + 后端递归 |
| 4 | 后端水印服务 | ✅ 可做 | 需从零开发，~300-500行 Pillow |
| 5 | RAW支持 (rawpy/libraw) | ⚠️ 需降级 | 依赖系统libraw，v2实现 |
| 6 | EXIF高级搜索 | ✅ 可做 | JSON字段 + SQLite JSON操作符 |
| 7 | 大文件处理 | ⚠️ 需降级 | 当前MAX 500MB，需chunked upload + Celery |
| 8 | WebSocket实时通知 | ✅ 可做 | 基础存在，增强 per-user rooms |
| 9 | 尼斯分类多选+置信度 | ✅ 可做 | TF-IDF词频算法 + 预置规则引擎 |
| 10 | Onboarding Wizard | ✅ 可做 | 前端Vue组件，中等复杂度 |
| 11 | 视频指纹 | ⚠️ 需降级 | ffmpeg帧提取 + 图像哈希，v2 |
| 12 | 音频指纹 (AcoustID) | ⚠️ 需降级 | pyacoustid + Chromaprint C库，v2 |
| 13 | Etsy API网关 | ⚠️ 需降级 | OAuth 2.0 + Etsy v3 API，v2 |
| 14 | 移动端响应式 | ✅ 可做 | CSS @media + 底部Tab，2-3周 |

---

## 三、文档 vs 代码差距报告

| 发现项 | 文档 | 实际 | 差距 | 影响 |
|--------|------|------|------|------|
| API端点 | 145 | 231 | +86 (59%) | 严重低估 |
| 模型类 | 33表 | 49模型 | +16 (48%) | 严重低估 |
| 水印服务 | 声称存在 | 不存在 | 缺失 | 全新开发 |
| ProductMockup | 声称Canvas | 组件不存在 | 缺失 | 全新开发 |
| OnboardingView | 声称完整 | 仅为幻灯片 | 功能不足 | 需重写 |
| Printful网关 | 列P2.5.1 | Mock已存在 | 接近可用 | 配置API Key即可 |
| dict_seed.py | 声称35KB | 597行(~35KB) | 准确 | — |
| 产品品类 | 声称60+ | 60+确认 | 准确 | — |

---

## 四、Phase实现路径建议

### Phase 0: 合规修复 (P0, 3天)
- 7项免责声明组件: DisclaimerBanner.vue + 首次启动强制确认 + 各模块关键操作前提示
- IP登记合规: 尼斯分类多推荐API改造 + CNIPA律师审核步骤(前端disabled+后端403)
- 创作者类型选择器: 诚实标注支持状态
- DB迁移: lawyer_consulted, disclaimer_accepted_at 字段

### Phase 1: 核心能力 (P0, 5-6天)
- 自动元数据提取: EXIF→completion_date/creation_tool, 文件名→title
- 批量文件夹导入: POST /api/works/import-folder (递归+去重+自动项目)
- 视频缩略图: ffmpeg 30%位置关键帧
- POD渠道管理: Printful产品目录API + 创建草稿 + URL记录
- Canvas效果预览: ProductMockup.vue 新建 (Canvas叠加+拖拽+缩放+颜色)
- 产品设计器: 7步向导增强(规格校验+定价计算)

### Phase 2: UX体验 (P1, 4天)
- Onboarding Wizard 3步引导
- 10个空状态引导组件
- 9个术语全局替换
- WizardStepper/DetailLayout/ListLayout 通用组件
- 收入CSV导入
- 确认Modal + Toast通知系统

### Phase 3: 文档同步 (P2, 1天)
- API统计/模型统计修正
- 模块边界调整
- 功能适用范围标注

---

## 五、关键风险

| 风险 | 影响 | 缓解 |
|------|------|------|
| Printful API breaking change | 效果预览降级 | Canvas方案作为fallback |
| rawpy/Libraw系统依赖 | RAW支持延迟 | v2实现 |
| 49模型/231端点的测试覆盖 | 回归风险 | 按模块逐步补测试 |
| 大文件存储空间 | 硬盘满 | 磁盘配额+阈值告警 |

---

## 六、关键文件索引

| 文件 | 角色 | 重要性 |
|------|------|--------|
| `backend/app/models/__init__.py` | 模型注册(33 exports) | 🔴 模型事实来源 |
| `backend/app/models/base.py` | Alembic注册(49 imports) | 🔴 迁移事实来源 |
| `backend/app/services/work_service.py` | detect_file_type/EXIF/缩略图 | 🔴 需增强RAW |
| `backend/app/services/seed_data.py` | 60+品类/14平台 | 🟡 种子数据 |
| `backend/app/routers/works.py` | 18端点 | 🔴 作品管理 |
| `backend/app/routers/supply.py` | 42端点 | 🔴 供应链API |
| `backend/app/routers/publish.py` | 17端点 | 🟡 发布管线 |
| `backend/app/gateway/printful.py` | Printful网关(mock) | 🟡 需配置API Key |
| `frontend/src/views/SupplyView.vue` | 供应链仪表盘 | 🔴 最复杂前端视图 |
| `frontend/src/views/OnboardingView.vue` | 基础幻灯片 | 🟡 需交互式重写 |
| `frontend/src/views/WorkDetailView.vue` | 作品详情 | 🔴 作品详情页 |
