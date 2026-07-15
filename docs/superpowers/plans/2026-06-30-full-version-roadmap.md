# OriStudio v2-v4 全版本功能实施计划

> **Goal:** 完成摄影师(v2)、视频+手工(v3)、音乐+文字(v4)全部创作者类型的完整功能实现
> **Architecture:** 后端已有预留模型(reserved_*.py, 833行)，需实现API路由+业务逻辑；前端需为每类创作者新建视图+组件+store
> **Tech Stack:** Vue 3 + TypeScript + Pinia + Vite (FE), FastAPI + SQLAlchemy + PostgreSQL (BE)

## Global Constraints

- v1 聚焦插画师/AIGC已完成，不得破坏现有功能
- 所有新增代码遵循 immutability 原则，严禁 mutation
- 所有 alert() 替换为 toast，所有 console.log 移除
- 所有 async 函数必须有 try/catch
- 前端文件 <800 行，函数 <50 行
- 后端所有端点必须有对应的前端调用

---

## 版本总览

| 版本 | 新增创作者 | 核心功能 | 预估工作量 |
|------|-----------|---------|-----------|
| **v2** | 摄影师 | RAW导入、选片模式、水印服务、图库API(500px/图虫)、EXIF高级搜索+GPS地图 | ~15天 |
| **v3a** | 短视频/动画 | 工程文件包(.prproj/.aep/.drp)、视频指纹(perceptual hash)、商单工作流、视频平台(B站/抖音/YouTube) | ~12天 |
| **v3b** | 手工艺人 | 物理原件、原料库存、生产批次、质检分级、Etsy API | ~10天 |
| **v4a** | 音乐人 | ISRC、Split Sheets、发行API、专辑管理 | ~8天 |
| **v4b** | 文字作者 | 章节层级、EPUB排版、抄袭检测 | ~8天 |

---

## Phase 1: v2 - 摄影师完整支持

### 1.1 摄影师专属数据层 (后端)
**Files:**
- `backend/app/models/photographer.py` - 新建(从reserved_photographer.py迁移)
- `backend/app/schemas/photographer.py` - 新建
- `backend/app/routers/photographer.py` - 新建
- `backend/app/services/photographer_service.py` - 新建

**功能:**
- RAW文件类型注册 (CR2/NEF/ARW/DNG)
- 摄影师专属过程阶段 (8阶段 vs 插画师6阶段)
- RAW元数据扩展 (相机型号、ISO、光圈、快门、焦距、GPS坐标)
- 选片模式 (Pass/Hold/Reject/Shortlist)
- 图库渠道管理 (500px/图虫/Fotolia/Shutterstock)
- EXIF高级搜索索引

### 1.2 摄影师前端视图
**Files:**
- `frontend/src/views/PhotographerView.vue` - 新建
- `frontend/src/components/photographer/` - 新建目录
  - `ShotSelector.vue` - 选片面板
  - `RawMetadataPanel.vue` - RAW元数据显示
  - `StockChannelPanel.vue` - 图库渠道管理
  - `GPSMapPanel.vue` - GPS拍摄地图
- `frontend/src/stores/usePhotographerStore.ts` - 新建
- `frontend/src/api/photographer.ts` - 新建

### 1.3 水印服务增强 (v2)
**Files:**
- `backend/app/routers/watermark.py` - 扩展现有路由
- `frontend/src/components/photographer/WatermarkPanel.vue` - 新建

**功能:**
- 批量水印生成 (网格/平铺/透明PNG)
- 水印预设管理 (已有WatermarkPresetsView)
- 摄影师专属水印 (EXIF版权信息自动注入)

---

## Phase 2: v3a - 短视频/动画完整支持

### 2.1 视频指纹监测 (后端)
**Files:**
- `backend/app/routers/video_fingerprint.py` - 扩展现有路由
- `backend/app/services/video_fingerprint_service.py` - 新建
- `backend/app/models/video_fingerprint.py` - 扩展现有模型

**功能:**
- perceptual hash (pHash/dHash/aHash) 计算
- 视频帧采样 + 指纹提取
- 模糊匹配 (Hamming distance <= 10)
- 侵权扫描 API (`POST /api/monitor/scan-video-fingerprint`)
- YouTube Content ID 对接 (`POST /api/monitor/content-id/submit`)

### 2.2 视频创作者前端
**Files:**
- `frontend/src/views/VideoCreatorView.vue` - 新建
- `frontend/src/components/video/` - 新建目录
  - `VideoFingerprintPanel.vue` - 视频指纹面板
  - `ProjectPackagePanel.vue` - 工程文件包管理
  - `PlatformDistributionPanel.vue` - 多平台分发(B站/抖音/YouTube)
  - `VideoMonetizationPanel.vue` - 视频变现面板
- `frontend/src/stores/useVideoStore.ts` - 新建
- `frontend/src/api/video.ts` - 新建

### 2.3 商单工作流 (v2，跨创作者类型)
**Files:**
- `backend/app/routers/commission.py` - 扩展现有路由
- `frontend/src/views/CommissionDetailView.vue` - 新建
- `frontend/src/components/commission/` - 新建目录
  - `CommissionKanban.vue` - 看板视图
  - `CommissionTimeline.vue` - 时间线视图
  - `PaymentRecordPanel.vue` - 收款记录
  - `RevisionLogPanel.vue` - 修改记录

**功能:**
- 状态机: 询价→已确认→制作中→交付→已结款
- 里程碑管理 (名称+截止日期+状态)
- 收款记录 (金额+方式+关联里程碑)
- 修改反馈记录 (描述+客户反馈)
- 仪表盘统计 (进行中/待收款/本月收入/平均客单价)
- 日历视图 (截止日+里程碑日)

---

## Phase 3: v3b - 手工艺人完整支持

### 3.1 工厂对接后端
**Files:**
- `backend/app/routers/factory.py` - 扩展现有路由
- `backend/app/services/factory_service.py` - 新建
- `backend/app/models/factory.py` - 扩展现有模型

**功能:**
- RFQ (询价单) CRUD
- 工厂报价对比
- 样品跟踪 (approval_status: pending/approved/rejected)
- 样品照片上传
- 质检报告 (AQL标准)
- 质量统计 (通过率/缺陷趋势/常见缺陷)

### 3.2 手工艺人前端
**Files:**
- `frontend/src/views/CraftsmanView.vue` - 新建
- `frontend/src/components/crafts/` - 新建目录
  - `RFQManager.vue` - 询价单管理
  - `SampleTracker.vue` - 样品跟踪
  - `QualityReportForm.vue` - 质检表单
  - `InventoryPanel.vue` - 原料库存
  - `ProductionBatchPanel.vue` - 生产批次
- `frontend/src/stores/useCraftsStore.ts` - 新建
- `frontend/src/api/factory.ts` - 新建

### 3.3 Etsy API 对接
**Files:**
- `backend/app/services/etsy_service.py` - 新建
- `backend/app/routers/supply.py` - 扩展

**功能:**
- Etsy 店铺授权 (OAuth2)
- 商品同步 (OriStudio → Etsy)
- 订单同步 (Etsy → OriStudio)
- 库存同步

---

## Phase 4: v4a - 音乐人完整支持

### 4.1 音乐后端
**Files:**
- `backend/app/routers/music.py` - 新建
- `backend/app/services/music_service.py` - 新建
- `backend/app/models/music.py` - 从reserved_music.py迁移
- `backend/app/schemas/music.py` - 新建

**功能:**
- ISRC 码生成/管理
- Split Sheets (版权分成协议)
- 专辑管理 (tracks + album metadata)
- 发行API对接 (DistroKid/TuneCore/CD Baby)
- 音频指纹 (AcoustID)

### 4.2 音乐人前端
**Files:**
- `frontend/src/views/MusicianView.vue` - 新建
- `frontend/src/components/music/` - 新建目录
  - `AlbumPanel.vue` - 专辑管理
  - `ISRCManager.vue` - ISRC码管理
  - `SplitSheetPanel.vue` - 分成协议
  - `DistributionPanel.vue` - 发行平台
  - `AudioFingerprintPanel.vue` - 音频指纹
- `frontend/src/stores/useMusicStore.ts` - 新建
- `frontend/src/api/music.ts` - 新建

---

## Phase 5: v4b - 文字作者完整支持

### 5.1 文字后端
**Files:**
- `backend/app/routers/writing.py` - 新建
- `backend/app/services/writing_service.py` - 新建
- `backend/app/models/writing.py` - 从reserved_writing.py迁移
- `backend/app/schemas/writing.py` - 新建

**功能:**
- 章节层级管理 (book → chapters → scenes)
- EPUB 导出 (基于 ebooklib)
- 抄袭检测 (接入 Turnitin/Grammarly API 或自建)
- 文字作品元数据 (字数/类型/标签)

### 5.2 文字作者前端
**Files:**
- `frontend/src/views/WriterView.vue` - 新建
- `frontend/src/components/writing/` - 新建目录
  - `ChapterTree.vue` - 章节树形结构
  - `EPUBExporter.vue` - EPUB导出
  - `PlagiarismChecker.vue` - 抄袭检测
  - `ManuscriptPanel.vue` - 手稿管理
- `frontend/src/stores/useWritingStore.ts` - 新建
- `frontend/src/api/writing.ts` - 新建

---

## Phase 6: 创作者类型系统完善

### 6.1 创作者类型切换
**Files:**
- `frontend/src/stores/useAppStore.ts` - 扩展 (添加 creator_type 状态)
- `frontend/src/components/layout/Sidebar.vue` - 扩展 (根据creator_type显示不同菜单)
- `frontend/src/router/index.ts` - 扩展 (添加新路由)

**功能:**
- 创作者类型选择器 (插画师/摄影师/视频创作者/手工艺人/音乐人/文字作者)
- 动态侧边栏 (根据类型显示不同功能入口)
- Onboarding 向导适配 (每种类型不同的引导流程)

### 6.2 通用功能增强
**Files:**
- `frontend/src/views/WorksView.vue` - 扩展 (按creator_type过滤)
- `frontend/src/api/works.ts` - 扩展 (添加类型专属字段)

---

## 实施顺序建议

1. **Phase 2 (商单工作流)** - 最高优先级，所有创作者类型都需要
2. **Phase 1 (摄影师)** - v2 最早规划，RAW支持需求明确
3. **Phase 2.1 (视频指纹)** - 权益保护中心的v3扩展
4. **Phase 3 (手工艺人)** - v3 第二批
5. **Phase 4 (音乐人)** - v4
6. **Phase 5 (文字作者)** - v4 最后

## 风险点

- 第三方API对接 (Etsy/500px/图虫/DistroKid/Turnitin) 需要申请开发者账号
- 视频指纹和音频指纹计算需要重型依赖 (ffmpeg/acoustid-python)
- EPUB导出需要 ebooklib 依赖
- RAW文件解析需要 libraw 系统库
