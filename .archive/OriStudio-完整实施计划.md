# OriStudio v3 完整实施计划 (Stage 2 修订)

> **基于**: Stage 2 全部产出 — PM启动报告、最终需求文档、UX设计规范、代码审计结果
> **核心策略**: v1聚焦插画师/AIGC艺术家，4 Phase从合规修复到文档同步
> **修订日期**: 2026-06-12

---

## 一、实施策略变更

| 维度 | 修订前 | 修订后 |
|------|--------|--------|
| 目标用户 | 6类创作者全覆盖 | **v1 聚焦插画师/AIGC艺术家** |
| Phase 数量 | 6 Phase / 6天 | **4 Phase** / 按实际工作量评估 |
| 实施顺序 | 从模块1→7线性构建 | **P0合规修复最先**，再核心能力，再UX |
| 文件范围 | 所有模块全功能 | 仅实现插画师的完整工作流 |

---

## 二、实施总览

```
Phase 0 ──→ Phase 1 ──→ Phase 2 ──→ Phase 3
合规修复      核心能力      UX体验      文档同步
 (P0)         (P0)         (P1)        (P2)

 3天           5-6天         4天          1天
            ═══════════════════════════════
                  13-14天总计
```

> **注**: 以上为单开发者全时投入的理想估算，实际时间可能受代码质量、测试覆盖、第三方API接入调试等因素影响。

| 阶段 | 定位 | 优先级 | 预估时间 | 依赖 |
|------|------|--------|---------|------|
| Phase 0 | 合规修复 — 法律风险清零 | P0 | 3天 | 无 |
| Phase 1 | 核心能力 — 插画师全链路可用 | P0 | 5-6天 | Phase 0 |
| Phase 2 | UX体验 — 新手友好+视觉优化 + 通用组件 | P1 | 4天 | Phase 1 |
| Phase 3 | 文档同步 — API/模型统计修正 | P2 | 1天 | Phase 1 |

---

## Phase 0: 合规修复 (3天) P0

**目标**: 消除所有法律和业务诚信风险，确保可安全上线。

### 0.1 7项免责声明 UI 实现 (1天)

**文件**: 新建 `frontend/src/components/common/DisclaimerBanner.vue`
- 可复用免责声明组件
- 支持三种展示模式: 全屏Modal / Banner / 底部小字
- Props: disclaimerKey, mode(modal/banner/footer), dismissible
- 首次进入IP登记模块 → 全屏Modal (#1, #2, #3, #7)
- 类别推荐结果 → Banner (#2, #3)
- 侵权监测页面 → Banner (#6)
- AI文案结果 → 底部标注 (#5)
- POD渠道管理 → Banner (#4)

**验证标准**:
- [ ] 首次进入IP登记 → 全屏Modal弹出，必须点击确认才能进入
- [ ] 类别推荐页面 → 黄色Banner显示"仅供参考"
- [ ] 侵权监测页面 → 局限性声明Banner不可折叠

### 0.2 IP登记合规改造 (1.5天)

**后端**: `backend/app/routers/ipr.py`
- POST /api/ipr/recommend/classes 改造: 返回多分类+置信度，最少3条，不可只返回一条
- POST /api/ipr/assistant/export 增强: 触发律师审核步骤前检查

**前端**: `frontend/src/views/IprView.vue`
- 类别推荐结果改为多选+置信度展示
- 新增 CNIPA提交前律师审核步骤组件:
  - 三个选项 (A)已咨询律师 (B)找律师 (C)跳过+二次确认
  - (C)选项触发5项风险确认勾选
  - 记录选择到 registration.lawyer_consulted

**验证标准**:
- [ ] 类别推荐返回至少3条结果，每条有置信度百分比
- [ ] 不可只展示单一推荐
- [ ] CNIPA提交前必须经过律师审核步骤
- [ ] (C)选项触发二次确认，5项全勾选才能继续

### 0.3 创作者类型选择器改造 (0.5天)

**前端**: Onboarding Wizard Step1、设置页面
- 插画师卡片突出(大尺寸+渐变边框+"推荐"徽章)
- 其余5类标注能力状态: "基础导入可用，专属工作流规划中"
- hover Tooltip: "我们正在为[摄影师]优化体验，敬请期待"

**验证标准**:
- [ ] 插画师卡片视觉突出
- [ ] 非插画类型标注"规划中"，hover显示Tooltip
- [ ] 选择非插画类型后可正常使用基础功能(导入/浏览)

---

## Phase 1: 核心能力 (4天) P0

**目标**: 插画师全链路可完整使用 — 导入→存证→产品化→分发→收入。

### 1.1 自动元数据提取 (1天)

**后端**: `backend/app/routers/works.py`

| 元数据字段 | 提取方法 | 实现 |
|-----------|---------|------|
| title | 文件名(去扩展名+格式化) | os.path.splitext |
| completion_date | EXIF DateTimeOriginal → 文件修改时间 | PIL/Pillow EXIF |
| creation_tool | EXIF Software | EXIF标签 Software |
| creation_location | EXIF GPSInfo | EXIF GPS标签 |
| 尺寸/DPI | Pillow | Image.info |
| 视频参数 | ffprobe | subprocess |
| 音频参数 | mutagen | mutagen.File |

- 所有字段自动预填，可编辑，不强制必填
- 导入时不阻塞流程

**验证标准**:
- [ ] 导入PNG → title自动从文件名提取 → completion_date从EXIF提取
- [ ] 所有自动提取的字段可手动编辑
- [ ] 不填任何字段也能成功导入

### 1.2 批量导入文件夹 (1天)

**前端**: `FileDropZone.vue`
- 支持文件夹拖拽 → webkitGetAsEntry 递归读取(深度3层，单次500文件)
- 按文件夹名自动创建Project
- 实时进度: "正在导入 12/47"
- SHA-256去重: 跳过已存在相同哈希的文件

**后端**: `POST /api/works/import-folder`
- 批量接收文件 + auto_create_project标志
- 按文件夹名创建Project
- 子文件夹映射为项目→子系列

**验证标准**:
- [ ] 拖拽文件夹 → 自动递归读取所有图片
- [ ] 按文件夹名创建Project
- [ ] 重复文件被SHA-256去重跳过
- [ ] 进度条实时更新

### 1.3 视频缩略图修正 (0.5天)

**后端**: `backend/app/routers/works.py`
- ffmpeg 提取视频**30%位置关键帧**作为缩略图
- 命令: `ffmpeg -i input.mp4 -vf "thumbnail" -frames:v 1 -ss {duration*0.3} output.jpg`

**验证标准**:
- [ ] 导入视频 → 缩略图为30%位置帧，非首帧全黑
- [ ] 视频时长<3秒时使用中间帧

### 1.4 POD渠道管理 + Canvas三层预览 (1.5天)

**前端**: `ProductMockup.vue` + `SupplyView.vue`

Canvas默认预览 (方案A):
- 产品模板底图 + 设计稿叠加 + 遮罩层
- 拖拽调整位置 / 滚轮缩放 / 颜色切换
- 导出: canvas.toDataURL() → Blob
- UI标注: "平面效果预览，非真实产品照片"

Printful API增强 (方案B):
- 切换按钮: [平面预览] | [AI描述(Ollama)] | [照片级预览(Printful)]
- 现有端点 `POST /api/supply/generate-mockup` 已实现 Ollama AI 文字描述方案(**保留**)
- 新增端点 `POST /api/supply/mockup/printful` 调用 Printful Mockup Generator API
  - 需要 `PRINTFUL_API_KEY` 环境变量
  - 每个颜色变体 = 1次API调用
- API不可用时降级到方案A

POD渠道管理 (原"POD对接"重命名):
- 渠道选择 → 规格展示 → 一键跳转平台 → 手动上架 → 粘贴URL
- Banner标注能力边界: "当前版本不支持自动同步库存/订单/物流"
- 免责声明 #4: POD平台IP条款警告

**后端**: 
- `app/routers/supply.py` 新增 `POST /api/supply/mockup/printful` 端点
- 现有 `POST /api/supply/generate-mockup`(Ollama方案)保留不变
- 需要 `PRINTFUL_API_KEY` 环境变量

**验证标准**:
- [ ] Canvas默认模式下可拖拽/缩放/切换颜色
- [ ] Printful API可用时照片级预览可切换
- [ ] POD渠道管理Tab标注能力边界
- [ ] "POD对接"标签全部改为"POD渠道管理"

---

## Phase 2: UX体验 (3天) P1

**目标**: 新手3分钟进入可用状态，消除术语障碍。

### 2.1 Onboarding 3步向导 (1天)

**新建**: `frontend/src/components/onboarding/OnboardingWizard.vue`

Step1: 创作者类型选择 (插画师突出)
Step2: 导入第一批作品 (文件夹拖拽+跳过)
Step3: 快速上手引导 (3步可视化+开始使用)

**后端**: 新增端点
- POST /api/auth/complete-onboarding — 持久化 creator_type + onboarding_completed

**验证标准**:
- [ ] 首次访问 → 自动弹出Onboarding
- [ ] Step1选择插画师 → 系统自动配置阶段/平台
- [ ] Step2拖入文件夹 → 自动创建项目
- [ ] Step3点击"开始使用" → 进入首页，onboarding_completed=true

### 2.2 空状态设计 (1天)

**新建**: `frontend/src/components/common/EmptyState.vue`
- 10个场景空状态: 空作品库/仪表盘/产品/收入/存证/监测/IP登记/合作伙伴/通知/搜索无结果
- 每个: 图标 + 标题 + 描述 + 主CTA
- 非财务软件风格: 温馨引导，圆角卡片

**验证标准**:
- [ ] 新账号进入每个Tab → 显示对应空状态引导
- [ ] 空仪表盘显示 "开始你的创作之旅"
- [ ] 空产品列表显示 "将IP变成产品"

### 2.3 术语优化 + 存证状态改造 (0.5天)

9个核心术语 Layer 1 替换:
- SHA-256 → "已存证 ✅ 日期"
- EXIF → "图片信息"
- DPI → "清晰度"
- POD → "一键印品"
- C2PA → "AI生成标注"
- WIPO → "国际商标"
- 尼斯分类 → "商标类别推荐"

Tooltip组件: hover展示Layer 2简短解释

**验证标准**:
- [ ] 作品列表/详情页显示"已存证 ✅ 日期"而非原始哈希
- [ ] 9个术语全部替换为白话+结果式表达
- [ ] hover Tooltip正常工作

### 2.4 视觉风格轻量调整 (0.5天)

- 首页: 展示最近作品缩略图而非数据看板
- 色彩: 更大圆角、更暖色调、更大留白
- 非插画类型Tab标注"规划中"

**验证标准**:
- [ ] 首页非空状态显示最近作品
- [ ] 非插画类型的专属功能Tab标注"规划中"

### 2.5 UX通用组件实现 (1天)

**目标**: 实现 UX 规范要求的统一交互模式组件，应用于各模块。

**WizardStepper.vue** (通用向导组件):
- 步骤指示器: 水平步骤条，已完成步骤可点击回退
- 草稿保存: 数据自动存入 Pinia store，支持刷新/关闭后恢复
- 关闭确认: Modal "确认离开？当前设计草稿已自动保存"
- 应用: M3智能助手、M4产品设计器

**DetailLayout.vue** (通用详情页布局):
- 布局: 返回列表 + 操作按钮 + 预览区40% + 信息面板60% + 底栏CTA
- 应用: M1作品详情、M4产品详情、M5发布内容详情

**ListLayout.vue** (通用列表页模板):
- 功能: 搜索栏 + 筛选器 + 视图切换(列表/网格) + 批量操作栏 + 分页 + Skeleton加载 + hover快捷操作
- 应用: M1作品列表、M6收入列表等

**验证标准**:
- [ ] WizardStepper 步骤可回退，草稿刷新后恢复
- [ ] DetailLayout 底栏CTA正确显示
- [ ] ListLayout Skeleton和hover操作正常

---

## Phase 3: 文档同步 (1天) P2

### 3.1 API端点核对与文档修正

- 每个 router 文件与设计文档端点清单一一比对
- 修正所有模块设计文档中的端点数量和路径
- 在 router 文件头部添加对应设计文档引用注释

### 3.2 模型清单核对

- 49个模型类与设计文档的模型清单比对
- 修正所有引用了"33表"的文档

### 3.3 模块边界调整

- 确认每个功能的创作者类型适用范围标注正确
- 非插画类型标签统一为"🔵 规划中"

**验证标准**:
- [ ] 所有文档端点数与代码一致
- [ ] 所有文档模型数与代码一致
- [ ] 每个模块文档标注了v1支持范围

---

## 附录A: 关键文件修改清单

### 后端文件

| 文件 | Phase | 操作 | 说明 |
|------|-------|------|------|
| `app/routers/ipr.py` | P0 | 修改 | 类别推荐多分类+置信度，律师审核步骤 |
| `app/models/ipr.py` | P0 | 修改 | 新增 lawyer_consulted, disclaimer_accepted_at 字段 + DB迁移 |
| `app/routers/works.py` | P1 | 修改 | 自动元数据提取 + 视频缩略图30%位置 + POST /works/import-folder(新建) |
| `app/gateway/printful.py` | P1 | 增强 | generate_mockup() 方法 |
| `app/routers/supply.py` | P1 | 修改 | POD渠道管理端点，CSV导入 |
| `app/schemas/work.py` | P1 | 修改 | 元数据字段自动预填逻辑 |
| `app/schemas/user.py` | P2 | 修改 | creator_type 字段 |
| `app/routers/auth.py` | P2 | 新增 | POST /auth/complete-onboarding |

### 前端文件

| 文件 | Phase | 操作 | 说明 |
|------|-------|------|------|
| `src/components/common/DisclaimerBanner.vue` | P0 | **新建** | 可复用免责声明组件 |
| `src/views/IprView.vue` | P0 | 修改 | 多分类推荐UI+律师审核步骤 |
| `src/views/NotaryView.vue` | P0 | 修改 | 存证状态优化显示 |
| `src/views/MonitorView.vue` | P0 | 修改 | 侵权监测免责Banner |
| `src/components/common/EmptyState.vue` | P2 | **新建** | 10场景空状态组件 |
| `src/components/onboarding/OnboardingWizard.vue` | P2 | **新建** | 3步向导组件 |
| `src/components/supply/ProductMockup.vue` | P1 | **新建** | Canvas三层预览 |
| `src/components/supply/CsvImportWizard.vue` | P1 | **新建** | 收入CSV导入向导 |
| `src/views/SupplyView.vue` | P1 | 修改 | POD渠道管理重命名+空状态 |
| `src/views/WorksView.vue` | P1 | 修改 | 批量导入文件夹+存证状态展示 |
| `src/views/WorkDetailView.vue` | P1 | 修改 | 自动元数据预填+存证状态+底栏CTA |
| `src/components/common/FileDropZone.vue` | P1 | 修改 | 文件夹递归导入 |
| `src/components/common/TermTooltip.vue` | P2 | **新建** | 9术语hover提示 |
| `src/components/common/WizardStepper.vue` | P2 | **新建** | 通用向导步骤指示器+草稿保存+关闭确认 |
| `src/components/common/DetailLayout.vue` | P2 | **新建** | 通用详情页布局(预览40%+信息60%+底栏CTA) |
| `src/components/common/ListLayout.vue` | P2 | **新建** | 通用列表页模板(搜索+筛选+视图切换+Skeleton+hover) |
| `src/views/DashboardView.vue` | P2 | 修改 | 空状态+温馨风格 |
| `src/components/layout/AppSidebar.vue` | P2 | 修改 | 名称更新 |

---

## 附录B: 验证checklist (全Phase完成)

### 合规验证
- [ ] 7项免责声明在各自触发节点正确展示
- [ ] IP登记类别推荐返回多分类+置信度，非单一推荐
- [ ] CNIPA提交前律师审核步骤不可绕过
- [ ] 非插画类型标注"规划中"

### 核心功能验证
- [ ] 导入PNG/PSD → 自动提取元数据 → 不强制手动填写
- [ ] 拖拽文件夹 → 递归导入 → 自动创建项目
- [ ] 存证状态显示"已存证 ✅ 日期"而非原始哈希
- [ ] 视频缩略图为30%位置帧
- [ ] POD渠道管理Tab标注能力边界声明
- [ ] Canvas默认预览可拖拽/缩放/换色
- [ ] Printful Mockup API可切换

### UX验证
- [ ] 首次访问 → Onboarding 3步引导 → 数据持久化
- [ ] 每个空状态Tab显示引导卡片
- [ ] 9个术语Layer 1替换为白话+结果
- [ ] 首页展示作品内容而非空白图表

### 文档验证
- [ ] master-design-v3.md 端点统计=232
- [ ] master-design-v3.md 模型统计=49
- [ ] 每个模块文档标注了v1创作者类型适用范围
