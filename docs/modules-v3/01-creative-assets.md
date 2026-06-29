# [1] 创意资产中心 — 详细功能设计 v3

> **定位**: 面向插画师/AIGC艺术家的数字资产统一管理中心。v1深度支持图片格式(插画/AIGC)，其他创作者类型的专属功能标注为"规划中"。
> **最后更新**: 2026-06-12 (Stage 2修订: v1聚焦插画师、自动元数据、批量导入、存证状态优化、缩略图修正)

---

## 一、v1 创作者类型支持声明

| 创作者类型 | v1 支持状态 | 说明 |
|-----------|-----------|------|
| **插画师/AIGC艺术家** | 完整支持 | 图片格式全链路: 导入→元数据→版本→权利→标签→搜索 |
| 摄影师 | 基础导入 | 图片格式可导入，专属工作流(RAW/选片/水印/图库)规划中 |
| 短视频/动画 | 基础导入 | MP4/MOV可导入，工程文件(.prproj/.aep)规划中 |
| 手工艺人 | 基础导入 | 图片格式可导入，物理原件/库存/批次规划中 |
| 音乐人 | 基础导入 | 音频文件可导入，ISRC/Split Sheets规划中 |
| 文字作者 | 基础导入 | 文本文件可导入，章节层级/EPUB规划中 |

---

## 二、支持的文件类型与差异化处理

### 2.1 AI 辅助创作记录 (新增 v1)

**核心设计**: 所有创作者类型的 AI 使用痕迹自动记录，形成不可篡改的创作过程证据链。

| 字段 | 说明 | 来源 |
|------|------|------|
| `works.ai_assisted` | 布尔值：是否 AI 辅助生成 | 用户标记或 API 传入 |
| `works.ai_tools_used` | JSON 数组：`[{"name":"Midjourney v6","version":"6.0","usage":"image_generation"}]` | 用户选择或 API 传入 |

**AI 创作会话记录** (`ai_creation_sessions` 表，详见模块 02)：
- 每个作品可有多条会话记录
- 记录完整：prompt + seed + parameters + 输出 + 人工干预点
- 自动记录：API 调用 AI 时自动写入
- 手动记录：上传 AI 生成图时填写工具名 + prompt

**前端集成 — `AiSessionTimeline.vue`**：
Props: `{ workId: string }`

展示格式：
```
作品《应龙》— AI 创作时间线
├── 2026-06-20 14:30 — Midjourney v6
│   ├── Prompt: "一条中国龙，山海经风格..."
│   ├── Seed: 847261039
│   ├── 输出: 4 张图
│   └── 人工干预: 无
├── 2026-06-20 15:10 — StableDiffusion + ControlNet
│   ├── Prompt: "应龙线稿，精细线条..."
│   ├── LoRA: lineArt_v3.safetensors
│   ├── 人工干预: Inpainting (重绘龙角区域)
│   └── 输出: 1 张图
└── 2026-06-21 09:00 — PS 手动精修
    ├── 工具: Photoshop
    └── 输出: 最终版本
```

### 2.2 v1 完整支持的图片格式

| 类型 | 扩展名 | MIME | 元数据提取 | 预览方式 | 过程阶段 |
|------|--------|------|-----------|----------|----------|
| 图片/插画 | PNG/JPG/PSD/TIFF/WebP/SVG | image/* | EXIF(尺寸/DPI/色彩空间/日期/工具/GPS)、图层 | 图片预览+缩放+EXIF面板 | 灵感→草图→线稿→上色→细节→终稿→导出 |

### 2.2 其他格式 (基础导入可用，专属处理规划中)

| 类型 | 扩展名 | v1 处理 | 规划中 |
|------|--------|---------|--------|
| 视频/动画 | MP4/MOV/AVI/WEBM | 基础导入+缩略图+播放 | 工程文件支持、视频指纹、字幕管理、审片协作、横竖屏版本 |
| 音频/音乐 | MP3/WAV/FLAC/AAC | 基础导入+播放 | ISRC码管理、Split Sheets、Master/Publishing区分、Sample Clearance |
| 文档/文字 | TXT/MD/PDF/DOCX | 基础导入+文本预览 | 章节结构、EPUB排版、抄袭检测 |
| 设计/3D | AI/EPS/STL/OBJ/FBX/GLB | 基础导入 | 3D预览 |
| 代码 | PY/JS/TS/HTML/CSS | 基础导入+高亮 | — |

### 2.3 三种导入模式

| 模式 | 说明 | 适用场景 | file_path | 缩略图 | 预览 | SHA-256 |
|------|------|----------|-----------|--------|------|---------|
| 完整导入 | 上传原文件，全功能 | 信任本地系统 | 保存到workspace | 自动生成 | 完全预览 | 是 |
| 低清预览 | 上传缩略图+哈希，不传原文件 | 半公开作品 | NULL | 前端生成低清缩略图 | 低清预览 | 是 |
| 仅哈希 | 不上传文件，仅提取哈希 | 高价值商业作品 | NULL | 显示文件类型图标 | 否 | 是 |

### 2.4 导入流程

```
拖拽文件(支持批量+文件夹) → 前端识别类型 → 计算SHA-256 → 自动提取元数据 → 生成缩略图 → upload → 后端保存 → 返回记录 → 列表刷新
```

后端处理:
- 文件保存: `data/workspace/{uuid前2位}/{uuid}/` 目录
- 缩略图: Pillow生成 → `data/thumbnails/{uuid前2位}/{uuid}_thumb.jpg`
- 视频缩略图: ffmpeg提取 **30%位置关键帧**（非首帧，避免首帧全黑问题）
  - 命令: 先通过 ffprobe 获取时长(`ffprobe -v quiet -show_entries format=duration -of csv=p=0 input.mp4`)，再 `ffmpeg -ss {duration*0.3} -i input.mp4 -vframes 1 -s 400x300 output.jpg`
  - ffprobe 不可用时退化到首帧(现有行为)
  - **实现状态**: 代码中 `work_service.py` 当前取首帧(vframes 1, 无 -ss)，需修改
- 视频元数据: ffprobe提取分辨率/帧率/编码/时长
- 音频元数据: mutagen提取采样率/BPM/时长
- 大文件: >100MB异步Celery任务处理

---

## 三、批量导入文件夹 (新增)

### 3.1 功能设计

- 拖拽文件夹 → 前端 File API `webkitGetAsEntry` 递归读取（深度3层，单次最多500文件）
- 按文件夹名称自动创建 Project/项目组
- 子文件夹层级映射为 项目→子系列 的嵌套结构
- SHA-256 去重: **后端批量计算SHA-256，比对数据库后跳过重复文件**，返回 `{imported: N, skipped_duplicate: M}` 供前端展示
- 批量导入进度: 实时显示"正在导入 12/47" (通过 Task-ID + 轮询或 WebSocket 进度推送)
- API: `POST /api/works/import-folder` **(新建立端点，代码中尚未实现)**

### 3.2 元数据自动提取 (新增)

无需用户手动填写，系统自动抓取:

| 元数据字段 | 自动提取来源 | 提取方法 |
|-----------|-------------|----------|
| title | 文件名(去除扩展名，格式化) | 下划线/连字符→空格，首字母大写 |
| completion_date | EXIF DateTimeOriginal 或 文件修改时间 | PIL/Pillow EXIF读取 |
| creation_tool | EXIF Software 或 文件类型推断 | EXIF标签 Software |
| creation_location | EXIF GPSInfo → GPS坐标+逆地理编码 | EXIF GPS标签 |
| 尺寸/DPI/色彩空间 | EXIF/Pillow | 自动提取 |
| 视频参数 | ffprobe | 分辨率/帧率/编码/时长/比特率 |
| 音频参数 | mutagen | 采样率/BPM/时长/比特率/调性 |

**不强制填写**: 所有自动提取的字段可编辑，所有字段可为空，不阻塞任何流程。

---

## 四、存证状态展示优化

### 当前设计 (不可用)
```
SHA-256: e920814f...  [复制]
```

### 优化后设计
```
已存证 ✅ 2026-06-12 15:43  (hover: "数字指纹已锚定到区块链")
未存证 ⚠️  (点击快速存证)
```

**三层信息策略**:
- **Layer 1 (界面)**: 已存证/未存证 + 日期 — 用户看得懂
- **Layer 2 (hover Tooltip)**: "数字指纹已锚定到区块链" — 简短解释
- **Layer 3 (点击展开)**: 完整SHA-256哈希值 + 存证平台 + 交易哈希 — 技术详情

---

## 五、作品详情页设计

### 5.1 页面布局 (v2 重构 — 两层分离布局)

```
┌─────────────────────────────────────────────────────────────────────┐
│ ← 作品列表               [📥 下载原文件]  [✏️ 编辑作品] [🗑️]        │
├──────────────────────────┬──────────────────────────────────────────┤
│                          │  SECTION A: 作品信息 (全局，始终可见)      │
│   SECTION C:             │  ──────────────────────────────────      │
│   作品预览区              │  标题: 《山海经·应龙》                    │
│   (始终可见)             │  类型: 图片 / PNG / 4500×5400            │
│                        │  大小: 2.7 MB  |  导入: 2026-06-20 14:30  │
│                        │  ──────────────────────────────────      │
│                        │  当前阶段: 终稿 ●  (带颜色边框)            │
│                        │  存证: 已存证 ✅ 2026-06-20                │
│                        │  [🔒 快速存证] [🔍 扫描侵权]              │
│                        │  ──────────────────────────────────      │
│                        │  作者: 山海画师 | 版权: © 2026             │
│                        │  许可: All Rights Reserved                 │
│                        │  工具: Procreate | 地点: 北京              │
│                        │  ──────────────────────────────────      │
│                        │  📁 项目: 山海经系列 (12个作品)            │
│                        │  🏷️ 标签: 山海经 · 应龙 · 水墨            │
│                        │  ──────────────────────────────────      │
│                        │  简介: 山海经系列第三幅...                 │
├──────────────────────────┴──────────────────────────────────────────┤
│                                                                       │
│  SECTION B: 创作过程时间线 (底部)                                     │
│  ─────────────────────────────────────────────────────────            │
│  灵感     草图     线稿     上色     细节     终稿                   │
│  ○──────●──────○──────○──────○──────●                               │
│  ✓      ✓      ✓      ✓      ✓      当前                            │
│                                                                       │
├──────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  SECTION D: 阶段详情面板 (点击阶段后展开)                             │
│  ─────────────────────────────────────────────────────────            │
│  📎 阶段素材 (3个文件)    📝 创作说明    📸 版本历史    🔒 存证记录   │
│  ┌────┬────┬────┐        ┌──────────┐  v3 终稿 ✅ 已存证           │
│  │缩略│缩略│缩略│        │ 终稿确认: │  v2 上色 a1b2c3d4            │
│  │图1 │图2 │图3 │        │ 已完成全部│  v1 草图 f5e6d7c8            │
│  └────┴────┴────┘        │ 准备导出  │  [+ 快照]                    │
│  [+ 上传素材]            └──────────┘                             │
│                                                                       │
└──────────────────────────────────────────────────────────────────────┘
```

**布局原则**:
- **Section A (作品信息)**: 全局信息，始终可见，只读展示。编辑通过头部 "编辑作品" 按钮完成
- **Section B (创作过程)**: 时间线，始终可见。点击阶段节点可展开
- **Section C (作品预览)**: 按文件类型差异化展示，始终可见
- **Section D (阶段详情)**: 仅在选择阶段时显示，包含4个子区块：素材/说明/版本/存证

**关键变化 (vs v1)**:
1. 导入作品后 `current_stage` 自动设为第一阶段（如 `inspiration`），消除"作品没有阶段"的困惑
2. "下载原文件"明确下载原始作品文件，不与阶段混淆
3. "编辑作品"编辑全局元数据 + 当前阶段的创作说明（二合一）
4. 阶段点击后底部面板展示该阶段的素材+说明+版本+存证，不再是分散的静态卡片
5. 所属项目/元数据/标签从独立卡片移到顶部作品信息区统一展示

### 5.2 元数据编辑字段完整清单

| 字段分组 | 字段名 | 类型 | 必填 | 来源 | 对应DB字段 |
|----------|--------|------|------|------|-----------|
| **基础信息** | title | text | 否 | 自动(文件名)/手动 | works.title |
| | synopsis | textarea | 否 | 手动 | works.synopsis(新) |
| | completion_date | date | 否 | 自动(EXIF)/手动 | works.completion_date(新) |
| | creation_tool | text | 否 | 自动(EXIF)/手动 | works.custom_metadata.creation_tool |
| | creation_location | text | 否 | 自动(EXIF GPS)/手动 | works.custom_metadata.creation_location |
| **权利信息** | author_name | text | 否 | 手动 | works.rights.author_name |
| | copyright_year | number | 否 | 手动 | works.rights.copyright_year |
| | license_type | select | 否 | 手动 | works.license_type |
| | attribution_text | text | 否 | 手动 | works.rights.attribution_text |
| **权利开关** | allow_reproduction | toggle | 否 | 手动 | works.rights.allow_reproduction |
| | allow_derivatives | toggle | 否 | 手动 | works.rights.allow_adaptation |
| | allow_commercial | toggle | 否 | 手动 | works.rights.commercial_use |
| **过程管理** | current_stage | select(按类型) | 否 | 手动 | works.current_stage |
| **阶段内容** | stage_notes | textarea | 否 | 手动 | works.custom_metadata.stages[current_stage].notes |
| **归属** | project_id | select | 否 | 手动/自动(文件夹导入) | works.project_id |
| **标签** | tags | tag-input | 否 | 手动+自动 | work_tags.tag |
| **备注** | notes | textarea | 否 | 手动 | works.description |

**许可证选项**: CC BY 4.0 / CC BY-SA 4.0 / CC BY-NC 4.0 / CC BY-NC-ND 4.0 / CC0 1.0 / All Rights Reserved / 自定义

**过程阶段 (插画师)**:
- inspiration(灵感) → sketch(草图) → lineart(线稿) → coloring(上色) → detail(细节) → final(终稿)

**过程阶段 (其他类型 — 规划中)**:
- 视频: script → storyboard → roughcut → finecut → colorgrade → final
- 音频: idea → arrangement → recording → mixing → mastering → release
- 文档: outline → draft → revision → final
- 通用: started → in_progress → completed → abandoned → archived

### 5.3 版本管理

版本历史在作品详情页的**阶段详情面板**中展示（Section D），每个阶段都可以有自己的版本快照。

**创建快照**:
- 保存当前文件+哈希到 work_versions 表
- 自动递增 version_num
- 可填写备注(如"上色完成，准备导出")

**版本列表**:
- 按version_num倒序
- 每行显示: 版本号、阶段标签、创建时间、存证状态、备注
- [回滚]按钮: 下载历史版本文件到本地

**API**:
- POST /api/works/{id}/versions — 创建快照
- GET /api/works/{id}/versions — 版本列表
- POST /api/works/{id}/rollback/{version_id} — 回滚(下载历史文件)

---

## 六、作品列表页

### 6.1 工具栏

```
[🔍 搜索作品名称...]  [类型 ▾] [项目 ▾] [阶段 ▾] [📋] [📤 导入作品]
```

### 6.2 筛选条件

| 筛选项 | 类型 | 说明 | 后端参数 |
|--------|------|------|----------|
| 搜索 | text | 标题/标签/简介模糊 | ?search= |
| 文件类型 | select | 全部/图片/视频/音频/文档/设计/代码 | ?file_type= |
| 项目 | select | 已创建的项目分组 | ?project_id= |
| 过程阶段 | select | 按当前阶段筛选 | ?stage= |
| 许可证 | select | CC/ARR等 | ?license_type= |
| 状态 | select | 活跃/回收站/归档 | ?status= |

### 6.3 视图模式

- 网格视图(默认): 缩略图卡片，hover显示操作按钮
- 列表视图: 详细信息行+虚拟滚动

### 6.4 批量操作

- 批量添加标签: POST /api/works/batch-edit { work_ids, tags, mode: "add" }
- 批量更换标签: mode: "replace"
- 批量移入回收站: POST /api/works/batch-delete
- 批量存证
- 批量导出

---

## 七、项目/系列管理

项目分组用于组织同一系列的作品。是作品的一个筛选维度，不是独立模块。

**功能**:
- 创建/编辑/删除项目，显示作品计数
- 在作品编辑面板中分配给项目
- **文件夹导入时自动创建项目**: 按文件夹名创建Project，子文件夹→子系列
- 在作品列表工具栏中按项目筛选

**API**: GET/POST/PATCH/DELETE /api/projects

---

## 八、回收站

- 30天保留
- 恢复: PATCH /works/{id} { status: "active" }
- 永久删除: DELETE /works/{id}/permanent
- 过期自动清理: Celery Beat

---

## 九、API端点完整清单

| 方法 | 路径 | 说明 | 请求参数 |
|------|------|------|----------|
| GET | /api/works | 作品列表 | ?page=&page_size=&file_type=&project_id=&stage=&license_type=&status=&search=&sort_by=&sort_order= |
| POST | /api/works | 上传作品 | multipart: file+title+description+tags+project_id |
| GET | /api/works/{id} | 作品详情 | |
| PATCH | /api/works/{id} | 更新作品 | body: title/synopsis/rights/license_type/current_stage/project_id/tags/completion_date等 |
| DELETE | /api/works/{id} | 软删除(移入回收站) | |
| POST | /api/works/{id}/restore | 恢复 | |
| DELETE | /api/works/{id}/permanent | 永久删除 | |
| GET | /api/works/{id}/preview | 预览信息(含文本内容) | |
| POST | /api/works/{id}/versions | 创建版本快照 | ?notes= |
| GET | /api/works/{id}/versions | 版本列表 | |
| POST | /api/works/{id}/rollback/{version_id} | 回滚版本 | |
| POST | /api/works/batch-edit | 批量编辑 | body: {work_ids, tags, mode, project_id} |
| POST | /api/works/batch-delete | 批量删除 | body: [work_ids] |
| POST | /api/works/import-folder | 批量导入文件夹(新) | multipart: files[] + auto_create_project |
| POST | /api/works/{id}/ai-session | 记录 AI 创作会话 (新) | body: {tool_name, tool_version, prompt, seed, parameters, negative_prompt, model_name, lora_names, output_images, human_interventions} |
| GET | /api/works/{id}/ai-sessions | 获取 AI 创作时间线 | |
| PATCH | /api/works/{id}/ai-session/{sid} | 编辑会话记录 | |
| DELETE | /api/works/{id}/ai-session/{sid} | 删除会话记录 | |
| GET | /api/tags | 标签列表(含计数) | |
| GET | /api/tags/suggest | 标签联想 | ?query= |
| GET/POST/PATCH/DELETE | /api/projects | 项目CRUD | |

---

## 十、前端实现

### 主要页面

**WorksView.vue**:
- 工具栏: SearchBar + 筛选下拉(type/project/stage) + 视图切换 + 导入按钮
- 统计栏: "共N个作品" + 激活的筛选标签
- 网格视图: WorkCard × N
- 列表视图: VirtualScroll列表行
- 分页: 上一页/下一页
- 导入弹窗: FileDropZone多文件拖拽 + 文件夹拖拽支持
- 空状态: "还没有作品 — 导入第一件作品" 引导卡片

**WorkDetailView.vue**:
- 左侧: 创作阶段时间线 (StageTimeline) — 点击展开查看各阶段素材/说明
- 右侧: 只读信息面板 (点击阶段时显示)
  - 文件信息 (FileInfoStrip, 始终可见)
  - 存证状态 (NotarizationStrip, 始终可见)
  - 所属项目 (ProjectStrip, 只读展示)
  - 元数据 (MetadataStrip, 只读展示)
  - 标签 (TagStrip, 只读展示)
  - 阶段素材 (StageAssetsStrip, 点击阶段后显示)
  - 版本历史 (VersionHistoryStrip, 点击阶段后显示)
- 编辑入口: 头部 "编辑作品" 按钮 → WorkEditPanel 弹窗
- 无阶段选择时右侧显示提示: "点击左侧创作阶段查看详情"

**ProjectsView.vue** (降级): 简单列表 → 点击跳转作品列表(筛选)

### 关键Store

**useWorkStore.ts**:
```
State: works[], currentWork, total, loading, filters
Actions: fetchWorks(), fetchWork(id), uploadWork(fd), updateWork(id,data), deleteWork(id)
         setFilter(key,val), setPage(n), importFolder(files, autoCreateProject)
增强: fetchWorks()后 → appStore.setStats({total_works: total})
```

**useAppStore.ts**:
```
State: workCount, notaryCount, alertCount
Actions: setStats({total_works, total_notarized, infringement_alerts})
Sidebar badge 从 workCount 读取
```

---

### 10.1 缺失前端组件补齐 (v2-v4 预留功能)

#### 10.1.1 摄影师 v2 组件

**RawImportDialog.vue** (v2)
Props: `{ visible: boolean, onComplete: (workId: string) => void }`

```
┌──────────────────────────────────────────────────────┐
│ 📷 RAW 文件导入                                       │
├──────────────────────────────────────────────────────┤
│ [拖拽 RAW 文件到此区域]                               │
│ 支持: CR2 NEF ARW DNG RW2 ORF PEF RAF               │
│                                                      │
│ 处理选项:                                            │
│ ● 自动白平衡  ○ 使用相机预设  ○ 自定义白平衡         │
│ 色彩空间: [sRGB ▼] [AdobeRGB ▼] [ProPhoto RGB ▼]    │
│ 输出格式: [JPEG ▼] [TIFF ▼]                          │
│ 质量: ████████░░ 80%                                 │
│                                                      │
│ [取消]  [导入 3 个 RAW 文件]                         │
└──────────────────────────────────────────────────────┘
```

Events: `@complete(workId)`, `@cancel`, `@progress(percent, current, total)`

**ExifSearchPanel.vue** (v2)
Props: `{ filters: ExifFilters, onChange: (filters) => void }`

```
┌──────────────────────────────────────────────────────┐
│ 🔍 EXIF 高级搜索                                     │
├──────────────────────────────────────────────────────┤
│ 相机: [Canon EOS R5 ________ ▼]                     │
│ 镜头: [24-70mm _________________ ▼]                 │
│ 焦距: [24 ━━━━━●━━━━ 200] mm                        │
│ ISO:  [100 ━━━━━●━━ 6400]                           │
│ 光圈:  [f/1.4 ●━━━━ f/22]                           │
│ 快门:  [1/8000 ●━━━━ 30s]                           │
│ 日期: [2026-01-01] 至 [2026-12-31]                  │
│ GPS: ☑ 仅含GPS数据  半径: [50 km ▼]                 │
│                                                      │
│ [应用筛选] [清除所有]                                 │
└──────────────────────────────────────────────────────┘
```

Events: `@change(filters)`, `@apply`, `@clear`

**GpsMapView.vue** (v2)
Props: `{ works: WorkWithGps[], selectedIds: string[], onSelect: (id) => void }`

- Leaflet/Mapbox 地图展示
- 每张照片一个标记点，hover 显示缩略图+EXIF
- 可圈选区域批量选择

#### 10.1.2 视频 v3 组件

**ProjectPackageView.vue** (v3)
Props: `{ workId: string }`

```
┌──────────────────────────────────────────────────────┐
│ 🎬 工程项目包: 《宣传片_v1.prproj》                    │
├──────────────────────────────────────────────────────┤
│ 左侧: 工程文件树             右侧: 预览区             │
│ ┌──────────────────┐     ┌──────────────────────┐   │
│ │ 📁 clips/        │     │                      │   │
│ │  📄 intro.mp4    │     │   [视频预览播放器]     │   │
│ │  📄 main.mp4     │     │                      │   │
│ │  📄 outro.mp4    │     │  时长: 03:24          │   │
│ │ 📁 audio/        │     │  分辨率: 1920×1080    │   │
│ │  🎵 bgm.wav      │     │                      │   │
│ │ 📁 subtitles/    │     └──────────────────────┘   │
│ │  📄 zh.vtt       │                                │
│ │  📄 en.vtt       │                                │
│ └──────────────────┘                                │
│                                                      │
│ [下载工程包] [关联素材] [导出]                       │
└──────────────────────────────────────────────────────┘
```

**SubtitleManager.vue** (v3)
Props: `{ workId: string }`

- 时间轴编辑器：逐帧调整字幕时间
- 双语言对照编辑
- 导入 SRT/VTT 文件
- 导出 SRT/VTT

**VideoFingerprintPanel.vue** (v3)
Props: `{ workId: string }`

- 视频指纹生成进度
- 已生成的指纹哈希列表
- 匹配结果展示（如有）

#### 10.1.3 音乐 v4 组件

**MusicMetadataForm.vue** (v4)
Props: `{ workId: string, metadata?: MusicMetadata }`

- BPM 可视化编辑器（波形图上标记节拍点）
- 调性选择器（钢琴键可视化）
- ISRC 输入 + 自动校验
- 专辑封面上传 + 裁剪

**AlbumEditor.vue** (v4)
Props: `{ album?: AlbumData, onSave: (album) => void }`

- 拖拽排序曲目列表
- 每首歌显示: 序号 + 标题 + 艺术家 + 时长 + 权利状态
- 批量编辑元数据弹窗

**CollaboratorEditor.vue** (v4)
Props: `{ workId: string, collaborators: Collaborator[] }`

- 贡献者列表 + 份额饼图
- 添加/移除贡献者
- 拖拽调整份额比例

#### 10.1.4 文字 v4 组件

**WritingPublishWizard.vue** (v4)
Props: `{ workId: string }`

Steps:
1. 选择平台 (起点/晋江/KDP/微信公众号)
2. 格式预览 (EPUB/PDF/HTML 预览)
3. 元数据填写 (书名/作者/简介/标签/分类)
4. 确认发布

**PlatformFormatPreview.vue** (v4)
Props: `{ format: string, content: string }`

- 实时预览各平台格式要求
- 格式不符时红色高亮提示

**WritingStatistics.vue** (v4)
Props: `{ workId: string }`

- 写作日历热力图 (类似 GitHub contributions)
- 日/周/月字数趋势折线图
- 章节完成率进度条
- 总字数统计 + 目标设定

#### 10.1.5 其他补齐组件

**WatermarkPresetEditor.vue** (v2)
Props: `{ preset?: WatermarkPreset, onSave: (preset) => void }`

```
┌──────────────────────────────────────────────────────┐
│ 💧 水印预设编辑                                       │
├──────────────────────────────────────────────────────┤
│ 名称: [我的水印 _________]                            │
│ 内容: [© 作者名 2026 ___]                            │
│ 位置: [右下角 ▼] 自定义坐标: X:[10] Y:[10]           │
│ 透明度: ████░░░░░░ 40%                               │
│ 字体: [思源宋体 ▼] 字号: [16]                        │
│ 旋转角度: [0°]                                        │
│                                                      │
│ 预览:                                               │
│ ┌─────────────────────────────┐                     │
│ │   [作品缩略图]              │                     │
│ │                          © 作者名 2026            │
│ └─────────────────────────────┘                     │
│                                                      │
│ [保存预设] [取消]                                    │
└──────────────────────────────────────────────────────┘
```

**WatermarkPresetList.vue** (v2)
Props: `{ presets: WatermarkPreset[], onSelect: (p) => void, onEdit: (p) => void, onDelete: (id) => void }`

- 卡片列表：每张卡片显示预设名称 + 预览缩略图
- 点击卡片选中，悬停显示编辑/删除按钮
- "新建预设" 按钮

**MetadataTemplateManager.vue** (v2)
Props: `{}`

- 模板列表：名称 + 适用类型 + 字段数
- 新建模板按钮 → 弹窗选择要包含的字段
- 批量应用到选定作品

#### 10.1.6 Store 增强

**useAiSessionStore.ts** (新增)
```
State: sessions[], currentWorkId, loading
Actions:
  - fetchSessions(workId): 获取 AI 创作会话列表
  - createSession(workId, data): 记录新会话
  - updateSession(sessionId, data): 编辑会话
  - deleteSession(sessionId): 删除会话
  - exportEvidence(workId): 导出创作时间线证据
```

**useRiskWarningStore.ts** (新增)
```
State: warnings[], workWarningsMap, loading
Actions:
  - checkPrompt(workId, prompt, images): 执行风险检测
  - fetchWarnings(workId): 获取作品预警记录
  - dismissWarning(id): 标记已查看
  - getSuggestions(id): 获取改进建议
```

---

## 十一、与下游模块的数据交互

| 输出数据 | 目标模块 | 用途 |
|----------|---------|------|
| work.id + sha256 + title + thumbnail | [2]权益保护中心 | 存证对象 |
| work.id + file_path + thumbnail | [2]权益保护中心 | 侵权扫描源 |
| ai_creation_sessions[].prompt, seed, params | [2]权益保护中心 | 创作过程证据链 |
| work.id + title + thumbnail + file_path + rights | [4]商业转化引擎 | 产品设计器Step1选稿 |
| work.tags + title | [3]IP登记工作站 | 类别推荐输入 |
| work.rights + author_name | [5]内容分发中心 | 发布署名/水印 |

---

## 十二、预留功能设计 (v2/v3/v4)

> **设计原则**: v1聚焦插画师/AIGC艺术家，其他5类创作者的专属功能在此完整设计。v1阶段预留数据模型/API路由/组件骨架，v2-v4按版本实现具体功能。
> **关联文档**: `docs/agent-evaluation-report.md` 中各角色需求驱动设计。

---

### 12.1 摄影师专属功能 (v2)

#### 12.1.1 RAW格式文件类型定义和导入流程

- **目标版本**: v2 | **目标创作者**: 摄影师
- **定位**: 支持专业摄影RAW格式的完整导入→解码→预览→元数据提取流水线

**数据模型扩展** (v1预留):

```sql
-- works表新增字段
ALTER TABLE works ADD COLUMN raw_sidecar_path VARCHAR(500);  -- XMP sidecar文件路径
ALTER TABLE works ADD COLUMN is_raw_original BOOLEAN DEFAULT FALSE;  -- 是否为RAW原始文件
ALTER TABLE works ADD COLUMN raw_processed_variant_id INTEGER;  -- 关联的处理后变体

-- raw_formats表 (v1预留，v2实现)
CREATE TABLE raw_formats (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    format_name VARCHAR(20) NOT NULL UNIQUE,  -- CR2/NEF/ARW/DNG/RW2/ORF/PEF/RAF
    extension VARCHAR(10) NOT NULL,
    mime_type VARCHAR(50),
    decoder_engine VARCHAR(50),  -- rawpy/libraw/dcraw
    supports_thumbnail BOOLEAN DEFAULT TRUE,
    supports_exif BOOLEAN DEFAULT TRUE,
    supports_preview BOOLEAN DEFAULT TRUE
);

-- 预置种子数据
INSERT INTO raw_formats (format_name, extension, mime_type, decoder_engine) VALUES
('CR2', '.cr2', 'image/x-canon-cr2', 'rawpy'),
('CR3', '.cr3', 'image/x-canon-cr3', 'rawpy'),
('NEF', '.nef', 'image/x-nikon-nef', 'rawpy'),
('ARW', '.arw', 'image/x-sony-arw', 'rawpy'),
('DNG', '.dng', 'image/x-adobe-dng', 'rawpy'),
('RW2', '.rw2', 'image/x-panasonic-rw2', 'rawpy'),
('ORF', '.orf', 'image/x-olympus-orf', 'rawpy'),
('PEF', '.pef', 'image/x-pentax-pef', 'rawpy'),
('RAF', '.raf', 'image/x-fujifilm-raf', 'rawpy');
```

**后端实现方案**:
- 使用 `rawpy` 进行RAW解码: `rawpy.imread(path)` → `raw.postprocess()` → RGB numpy array → PIL Image → JPEG预览缩略图
- libraw 作为备选引擎 (通过 rawpy 内置)
- 解码参数: demosaic_algorithm, use_camera_wb, output_color (sRGB/AdobeRGB)
- 提取完整 EXIF: `rawpy.imread(path)` 可直接读取所有EXIF标签
- 大文件处理: RAW通常25-80MB，异步Celery任务处理

**ALLOWED_EXTENSIONS扩展** (v1代码修改点):

```python
# v1预留，v2激活 — 在 detect_file_type() 中添加
ALLOWED_EXTENSIONS = {
    # ... v1现有类型 ...
    # v2 RAW格式 (当前代码中缺失，需新增)
    'image': {'png','jpg','jpeg','psd','tiff','tif','webp','svg','bmp',
              'cr2','cr3','nef','arw','dng','rw2','orf','pef','raf','xmp'},
}
```

**API端点设计**:

| 方法 | 路径 | 说明 | 版本 |
|------|------|------|------|
| GET | /api/works/raw-formats | 获取支持的RAW格式列表 | v2 |
| POST | /api/works/import-raw | 导入RAW文件 (multipart: file + raw_processor_config) | v2 |
| POST | /api/works/{id}/raw-to-jpeg | RAW→JPEG导出 (body: {quality, resize, color_space}) | v2 |
| GET | /api/works/{id}/raw-preview | 获取RAW预览缩略图 | v2 |
| GET | /api/works/{id}/raw-metadata | 获取完整RAW元数据 | v2 |
| POST | /api/works/{id}/sidecar | 上传/关联XMP sidecar文件 | v2 |

**前端组件**:
- **RawImportDialog.vue** (v2): Props: `{ visible, onComplete }` — RAW文件选择 + 处理选项(色彩空间/白平衡) + 批量导入进度
- **RawPreviewPanel.vue** (v2): Props: `{ workId }` — RAW解码预览 + 元数据面板

**v1集成点**: 
- 文件导入流程中 `detect_file_type()` 扩展点 — 当前RAW落到"other"，v1需预留识别但允许导入（作为二进制文件），v2激活完整RAW流水线
- 作品详情页预览区 — v1对RAW文件显示文件类型图标，v2切换为RAW解码预览

> **标注**: v1数据模型字段(raw_sidecar_path, is_raw_original, raw_processed_variant_id)已预留于works表，raw_formats种子数据预置，detect_file_type()扩展点已标注。完整RAW解码流水线待v2实现。

---

#### 12.1.2 EXIF高级搜索面板

- **目标版本**: v2 | **目标创作者**: 摄影师

**功能说明**: 在作品列表筛选栏增加EXIF维度的高级搜索面板，支持按相机/镜头/焦段/ISO/光圈/快门/拍摄日期范围搜索。

**API端点设计**:

| 方法 | 路径 | 说明 | 查询参数 |
|------|------|------|----------|
| GET | /api/works | 作品列表(增强) | 新增: `?camera=&lens=&focal_min=&focal_max=&iso_min=&iso_max=&aperture_min=&aperture_max=&shutter_min=&shutter_max=&date_from=&date_to=&has_gps=1&gps_lat=&gps_lon=&gps_radius_km=` |

**EXIF搜索参数详细说明**:

| 参数 | 类型 | 说明 | 示例 |
|------|------|------|------|
| camera | string | 相机型号(模糊匹配) | ?camera=Canon+EOS+R5 |
| lens | string | 镜头型号(模糊匹配) | ?lens=24-70mm |
| focal_min | integer | 最小焦距(mm) | ?focal_min=24 |
| focal_max | integer | 最大焦距(mm) | ?focal_max=200 |
| iso_min | integer | 最低ISO | ?iso_min=100 |
| iso_max | integer | 最高ISO | ?iso_max=12800 |
| aperture_min | float | 最小光圈值 | ?aperture_min=1.4 |
| aperture_max | float | 最大光圈值 | ?aperture_max=16 |
| shutter_min | float | 最短快门(秒) | ?shutter_min=1/8000 |
| shutter_max | float | 最长快门(秒) | ?shutter_max=30 |
| date_from | date | 拍摄日期范围起始 | ?date_from=2026-01-01 |
| date_to | date | 拍摄日期范围结束 | ?date_to=2026-06-12 |
| has_gps | boolean | 是否有GPS信息 | ?has_gps=1 |
| gps_lat | float | GPS纬度(用于地图搜索) | ?gps_lat=39.9042 |
| gps_lon | float | GPS经度 | ?gps_lon=116.4074 |
| gps_radius_km | float | 地图搜索半径(km) | ?gps_radius_km=10 |

**后端实现方案** (v2):
- SQLAlchemy filter链: `Work.custom_metadata['exif']['camera'].as_string().ilike('%Canon%')`
- 混合索引: 对custom_metadata中常用EXIF字段建立JSON表达式索引 (SQLite 3.38+ / PostgreSQL GIN)
- 查询优化: 搜索结果缓存(TTL 5分钟)，因为EXIF数据在导入后不变

**地图视图浏览GPS位置**:
- 前端集成: Leaflet/高德地图组件，在地图上标点已导入照片的GPS坐标
- 点击标记→预览该位置拍摄的所有照片
- 聚合显示: 同一区域多张照片聚合为数字气泡

**前端组件**:
- **ExifSearchPanel.vue** (v2): Props: `{ filters, onFilterChange }` — 可折叠高级搜索面板，包含相机/镜头下拉(动态从已有数据中获取选项)、焦段/ISO/光圈范围滑块、日期范围选择器、GPS地图搜索区域
- **GpsMapView.vue** (v2): Props: `{ works[] }` — 地图组件展示照片GPS位置，点击标记预览照片

**v1集成点**:
- 作品列表页 `WorksView.vue` 筛选栏 — v1预留"高级搜索"折叠按钮位置，点击展开ExifSearchPanel
- `/api/works` 端点 — v1预留查询参数接收，default忽略(不报错)，v2激活过滤逻辑

> **标注**: v1 works表的 `custom_metadata` JSON字段已支持存储完整EXIF数据。EXIF搜索参数 `/api/works` 端点已预留(接收但不处理，不报错)。前端WorksView.vue工具栏预留"高级搜索"折叠区。完整搜索面板待v2实现。

---

#### 12.1.3 选片(Culling)模式视图

- **目标版本**: v2 | **目标创作者**: 摄影师

**功能说明**: 全屏浏览模式下快速筛选大量照片，键盘快捷键标记入选(Pick)/淘汰(Reject)/待定(Hold)，支持标记状态的筛选和批量操作。

**数据模型** (works表扩展):

```sql
-- v1 预留字段
ALTER TABLE works ADD COLUMN cull_status VARCHAR(20) DEFAULT 'unreviewed';
-- cull_status 枚举: 'unreviewed'(未选) / 'picked'(入选) / 'rejected'(淘汰) / 'hold'(待定)
ALTER TABLE works ADD COLUMN cull_rating INTEGER DEFAULT 0;  -- 星级评分 0-5
ALTER TABLE works ADD COLUMN color_label VARCHAR(20);  -- 颜色标签(红/黄/绿/蓝/紫)
```

**Culling键盘快捷键** (v2定义):

| 快捷键 | 操作 | 说明 |
|--------|------|------|
| P | Pick(入选) | 标记为入选，自动跳转下一张 |
| X | Reject(淘汰) | 标记为淘汰，自动跳转下一张 |
| H | Hold(待定) | 标记为待定，自动跳转下一张 |
| ←/→ | 上一张/下一张 | 切换照片 |
| 1-5 | 星级评分 | 1-5星标记 |
| F | 全屏切换 | 进入/退出全屏模式 |
| Z | 100%缩放 | 查看照片原始尺寸(RAW解码的完整分辨率) |
| Ctrl+A | 全选 | 批量标记 |
| Tab | 切换信息面板 | 显示/隐藏EXIF面板 |
| 0 | 撤销标记 | 重置为unreviewed |

**API端点设计**:

| 方法 | 路径 | 说明 | 版本 |
|------|------|------|------|
| POST | /api/works/batch-cull | 批量选片操作 | v2 |
| GET | /api/works?cull_status= | 按选片状态筛选 | v2 |
| PATCH | /api/works/{id}/cull-status | 更新单张选片状态 | v2 |

**前端组件**:
- **CullingView.vue** (v2): 全屏选片模式 — 中央大图展示 + 底部缩略图胶片条 + 侧边EXIF信息面板(可收起) + 顶部工具栏(入选/淘汰/待定/评级/筛选状态标签) + 键盘快捷键提示浮层(首次进入时展示)
- **CullingFilmstrip.vue** (v2): Props: `{ works[], currentIndex, cullStatuses, onSelect }` — 底部缩略图胶片条，显示每张照片的缩略图+选片状态图标

**v1集成点**:
- 作品列表页工具栏 — v1预留"选片模式"按钮开关(切换网格视图→全屏选片视图)
- works表 — v1预留cull_status/cull_rating/color_label字段，默认值unreviewed/0/NULL

> **标注**: v1数据模型已预留cull_status/cull_rating/color_label字段。前端WorksView.vue工具栏预留"选片模式"切换按钮。完整Culling模式视图+键盘快捷键系统待v2实现。

---

#### 12.1.4 批量元数据模板

- **目标版本**: v2 | **目标创作者**: 摄影师

**功能说明**: 预设作者/版权/许可证模板，批量应用到选中作品的rights字段。

**数据模型**:

```sql
-- v1预留
CREATE TABLE metadata_templates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    name VARCHAR(100) NOT NULL,  -- 模板名称 e.g., "标准版权模板" "商用授权模板"
    author_name VARCHAR(200),
    copyright_year INTEGER,
    license_type VARCHAR(50),
    attribution_text VARCHAR(500),
    allow_reproduction BOOLEAN DEFAULT TRUE,
    allow_derivatives BOOLEAN DEFAULT FALSE,
    allow_commercial BOOLEAN DEFAULT FALSE,
    custom_rights_text TEXT,  -- 自定义权利声明文本
    is_default BOOLEAN DEFAULT FALSE,  -- 是否为默认模板(导入时自动应用)
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

**API端点设计**:

| 方法 | 路径 | 说明 | 版本 |
|------|------|------|------|
| GET | /api/metadata-templates | 模板列表 | v2 |
| POST | /api/metadata-templates | 创建模板 | v2 |
| PATCH | /api/metadata-templates/{id} | 更新模板 | v2 |
| DELETE | /api/metadata-templates/{id} | 删除模板 | v2 |
| POST | /api/works/batch-apply-template | 批量应用模板 (body: {work_ids[], template_id}) | v2 |
| POST | /api/works/{id}/apply-template | 单个作品应用模板 (body: {template_id}) | v2 |

**前端组件**:
- **MetadataTemplateManager.vue** (v2): Props: `{}` — 模板CRUD管理面板，列表+创建/编辑弹窗，设置默认模板
- **BatchApplyTemplateDialog.vue** (v2): Props: `{ workIds[], visible, onApplied }` — 选择模板→预览将会变更的字段→确认批量应用→结果反馈

**v1集成点**:
- 作品批量操作: 在已有的批量编辑API基础上，v1预留"应用元数据模板"操作入口
- 导入流程: v1预留 metadata_template_id 参数在导入API中，v2导入时自动应用默认模板

> **标注**: v1 metadata_templates表已预留。批量编辑API `/api/works/batch-edit` 已支持rights更新，v2增强为模板应用模式。前端批量操作下拉预留"应用模板"选项。

---

#### 12.1.5 水印预设管理

- **目标版本**: v2 | **目标创作者**: 摄影师

**功能说明**: 预设水印样式(文字水印/图片水印/平铺水印)，批量应用到作品导出，支持差异化强度设置。

**数据模型**:

```sql
-- v1预留
CREATE TABLE watermark_presets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    name VARCHAR(100) NOT NULL,
    watermark_type VARCHAR(20) NOT NULL,  -- 'text' / 'image' / 'tiled'
    text_content VARCHAR(500),  -- 文字水印内容 e.g., "© 陈摄影 2026"
    text_font VARCHAR(50) DEFAULT 'Arial',
    text_size INTEGER DEFAULT 36,
    text_color VARCHAR(20) DEFAULT '#FFFFFF',
    text_opacity FLOAT DEFAULT 0.7,  -- 文字透明度 0.0-1.0
    image_path VARCHAR(500),  -- 图片水印文件路径(logo)
    image_opacity FLOAT DEFAULT 0.5,
    image_scale FLOAT DEFAULT 1.0,  -- 图片缩放比例
    position VARCHAR(20) DEFAULT 'bottom-right',  -- 位置: center/top-left/top-right/bottom-left/bottom-right
    margin_x INTEGER DEFAULT 20,  -- 水平边距(px)
    margin_y INTEGER DEFAULT 20,  -- 垂直边距(px)
    tile_spacing INTEGER DEFAULT 100,  -- 平铺间距(px，仅tiled类型)
    tile_rotate INTEGER DEFAULT 45,  -- 平铺旋转角度(仅tiled类型)
    is_default BOOLEAN DEFAULT FALSE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

**API端点设计**:

| 方法 | 路径 | 说明 | 版本 |
|------|------|------|------|
| GET | /api/watermark-presets | 水印预设列表 | v2 |
| POST | /api/watermark-presets | 创建水印预设 | v2 |
| PATCH | /api/watermark-presets/{id} | 更新水印预设 | v2 |
| DELETE | /api/watermark-presets/{id} | 删除水印预设 | v2 |
| POST | /api/works/batch-watermark | 批量水印 (body: {work_ids[], preset_id, output_format}) | v2 |
| POST | /api/works/{id}/watermark | 单个作品加水印 (body: {preset_id, output_format?}) | v2 |
| GET | /api/works/{id}/watermark-preview | 水印预览(Pillow生成预览图，不保存) | v2 |

**后端实现方案** (v2):
- 使用 Pillow (ImageDraw/ImageFont/ImageFilter) 实现水印叠加
- 文字水印: 计算最佳字号(按图片尺寸比例)，抗锯齿渲染
- 图片水印: logo叠加，支持缩放和透明度
- 平铺水印: 按tile_spacing/tile_rotate矩阵排列
- 批量处理: Celery异步任务，进度推送到WebSocket
- 输出格式: JPEG(带水印)/PNG(保持透明背景)

**前端组件**:
- **WatermarkPresetEditor.vue** (v2): Props: `{ preset?, onSave }` — 水印样式编辑器，实时预览区+文字/图片/平铺切换+参数调整面板
- **WatermarkPresetList.vue** (v2): Props: `{ presets[], onSelect, onEdit, onDelete }` — 水印预设列表+缩略图预览

**v1集成点**:
- 作品批量操作 — v1预留"批量加水印"操作入口
- [5]内容分发中心 — v1发布流程Step4图片处理中预留水印预设选择(当前为手动输入attribution_text)
- watermark_presets表 — v1预留

> **标注**: v1 watermark_presets表已预留。前端批量操作下拉预留"批量加水印"选项。分发中心发布流程Step4预留水印预设选择器。完整后端水印服务(`watermark_service.py`)待v2实现。

---

### 12.2 视频创作者专属功能 (v3)

#### 12.2.1 工程文件项目包概念

- **目标版本**: v3 | **目标创作者**: 短视频/动画

**功能说明**: 视频作品不是单个文件，而是一个项目包(素材+工程文件+调色+字幕+字体)。当前系统一个work=一个文件，需扩展为"作品→项目包→资产文件树"的层级结构。

**数据模型**:

```sql
-- v1预留
ALTER TABLE works ADD COLUMN is_project_package BOOLEAN DEFAULT FALSE;  -- 是否为工程项目包
ALTER TABLE works ADD COLUMN project_files JSON;  -- 项目文件树结构

-- project_files JSON 结构 (v3定义):
-- {
--   "root_path": "/山海经动画/v1/",
--   "total_size_bytes": 524288000,
--   "files": [
--     {"relative_path": "project.prproj", "type": "project_file", "size": 2048000},
--     {"relative_path": "footage/场景1.mp4", "type": "video", "size": 104857600},
--     {"relative_path": "audio/bgm.wav", "type": "audio", "size": 52428800},
--     {"relative_path": "graphics/title.psd", "type": "image", "size": 15728640},
--     {"relative_path": "exports/v1_draft.mp4", "type": "export", "size": 104857600}
--   ]
-- }

-- 工程项目支持的文件格式
CREATE TABLE project_file_formats (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    format_name VARCHAR(50) NOT NULL,  -- Premiere Pro / After Effects / DaVinci Resolve / Final Cut Pro
    extension VARCHAR(10) NOT NULL,  -- .prproj / .aep / .drp / .fcpxml
    software_name VARCHAR(100),
    can_extract_metadata BOOLEAN DEFAULT FALSE,
    can_generate_thumbnail BOOLEAN DEFAULT FALSE
);

INSERT INTO project_file_formats (format_name, extension, software_name) VALUES
('Adobe Premiere Pro', '.prproj', 'Adobe Premiere Pro'),
('Adobe After Effects', '.aep', 'Adobe After Effects'),
('DaVinci Resolve', '.drp', 'DaVinci Resolve'),
('Final Cut Pro', '.fcpxml', 'Final Cut Pro X'),
('Blender', '.blend', 'Blender Foundation');
```

**API端点设计**:

| 方法 | 路径 | 说明 | 版本 |
|------|------|------|------|
| POST | /api/works/import-project | 导入工程文件夹(multipart: files[] + root_path) | v3 |
| GET | /api/works/{id}/project-files | 获取项目包文件树 | v3 |
| GET | /api/works/{id}/project-files/{file_id} | 获取项目包内单个文件 | v3 |
| PATCH | /api/works/{id}/project-files | 更新项目文件树(添加/移除文件) | v3 |

**前端组件**:
- **ProjectPackageView.vue** (v3): Props: `{ workId }` — 文件树组件展示项目包内文件层级 + 各文件类型图标 + 预览区 + 支持上传新文件到项目包
- **ProjectImportWizard.vue** (v3): Props: `{ visible, onComplete }` — 工程文件夹拖拽导入向导 + 自动识别工程文件类型 + 构建文件树

**v1集成点**:
- works表 — v1预留 is_project_package / project_files 字段
- 作品导入流程 — v1预留"导入工程文件夹"选项(与普通文件导入并列)
- 作品详情页预览区 — v1预留项目包→展开文件树的视图切换

> **标注**: v1 works表的 is_project_package / project_files 字段已预留。project_file_formats表已预留。前端导入按钮区域预留"导入工程文件夹"入口。完整项目包工作流待v3实现。

---

#### 12.2.2 字幕管理

- **目标版本**: v3 | **目标创作者**: 短视频/动画

**功能说明**: 管理与视频作品关联的字幕文件(.srt/.ass/.vtt)，支持多语言字幕版本和字幕样式配置。

**数据模型**:

```sql
-- v1预留
CREATE TABLE subtitles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    work_id INTEGER NOT NULL REFERENCES works(id) ON DELETE CASCADE,
    language VARCHAR(10) NOT NULL,  -- ISO 639-1: zh/en/ja/ko
    file_path VARCHAR(500) NOT NULL,  -- 字幕文件存储路径
    subtitle_format VARCHAR(10) NOT NULL,  -- srt/ass/vtt
    style JSON,  -- 字幕样式配置
    -- style JSON结构:
    -- {
    --   "font_family": "Source Han Sans",
    --   "font_size": 48,
    --   "font_color": "#FFFFFF",
    --   "outline_color": "#000000",
    --   "outline_width": 2,
    --   "background_color": "rgba(0,0,0,0.5)",
    --   "position": "bottom",  -- bottom/top/center
    --   "alignment": "center"  -- left/center/right
    -- }
    is_primary BOOLEAN DEFAULT FALSE,  -- 是否为主要字幕
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_subtitles_work_id ON subtitles(work_id);
```

**API端点设计**:

| 方法 | 路径 | 说明 | 版本 |
|------|------|------|------|
| GET | /api/works/{id}/subtitles | 作品字幕列表 | v3 |
| POST | /api/works/{id}/subtitles | 上传字幕文件(multipart: file + language + format + style) | v3 |
| PATCH | /api/works/{id}/subtitles/{sub_id} | 更新字幕(文本/样式) | v3 |
| DELETE | /api/works/{id}/subtitles/{sub_id} | 删除字幕 | v3 |
| GET | /api/works/{id}/subtitles/{sub_id}/download | 下载字幕文件 | v3 |

**前端组件**:
- **SubtitleManager.vue** (v3): Props: `{ workId }` — 字幕列表(按语言分组) + 上传/替换/删除 + 字幕文本编辑器(内联编辑器阅读和修改.srt内容) + 样式可视化编辑器
- **SubtitlePreview.vue** (v3): Props: `{ workId, subtitleId }` — 视频播放器叠加字幕预览效果

**v1集成点**:
- 作品详情页 — v1预留"字幕管理"Tab(视频类型时显示)
- subtitles表 — v1预留

> **标注**: v1 subtitles表已预留。作品详情页对视频类型内容预留"字幕管理"区域。完整字幕管理功能待v3实现。

---

#### 12.2.3 视频指纹 (Perceptual Hash)

- **目标版本**: v3 | **目标创作者**: 短视频/动画

**功能说明**: 基于视频帧的感知哈希(perceptual hash)而非SHA-256。视频重编码后SHA-256变化但视觉内容不变，感知哈希可识别重编码版本。这是评估报告中赵一鸣指出的核心缺失。

**数据模型**:

```sql
-- v1预留
ALTER TABLE works ADD COLUMN perceptual_hash VARCHAR(128);  -- 视频/图像感知哈希
ALTER TABLE works ADD COLUMN perceptual_hash_type VARCHAR(50);  -- 'video_frames' / 'image_phash' / 'audio_fingerprint'

-- 视频帧指纹采样配置
CREATE TABLE video_fingerprint_config (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    work_id INTEGER NOT NULL REFERENCES works(id) ON DELETE CASCADE,
    sample_count INTEGER DEFAULT 10,  -- 采样帧数
    sample_positions JSON,  -- 采样时间点: [0.1, 0.2, 0.3, ...] (按视频时长比例)
    hash_algorithm VARCHAR(50) DEFAULT 'phash',  -- phash/dhash/ahash/whash
    hash_size INTEGER DEFAULT 16,  -- 哈希尺寸
    fingerprinted_at DATETIME,
    is_current BOOLEAN DEFAULT TRUE
);

-- 帧级指纹存储
CREATE TABLE video_frame_fingerprints (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    fingerprint_config_id INTEGER NOT NULL REFERENCES video_fingerprint_config(id) ON DELETE CASCADE,
    frame_index INTEGER NOT NULL,  -- 采样位置/帧索引
    time_position FLOAT NOT NULL,  -- 时间位置(秒)
    frame_hash VARCHAR(128) NOT NULL,  -- 该帧的感知哈希
    UNIQUE(fingerprint_config_id, frame_index)
);
```

**实现方案** (v3):
- ffmpeg提取关键帧: `ffmpeg -i input.mp4 -vf "fps=1/10" frame_%04d.jpg` (每10秒一帧)
- Python imagehash库计算帧级pHash: `imagehash.phash(Image.open(frame))`
- 组合指纹: 按时间序排列的帧哈希数组 → 作为视频感知哈希
- 相似度匹配: 使用汉明距离(Hamming distance)比较两段视频的感知哈希
- 对接YouTube Content ID: 需合作伙伴资格 + API提交(Digital Fingerprint API)
- 对接国内的灵创/维权骑士等第三方监测平台

**API端点设计**:

| 方法 | 路径 | 说明 | 版本 |
|------|------|------|------|
| POST | /api/works/{id}/fingerprint | 生成视频感知指纹 | v3 |
| GET | /api/works/{id}/fingerprint | 获取已生成的指纹信息 | v3 |
| POST | /api/monitor/scan-video-fingerprint | 以视频指纹发起侵权扫描 | v3 |
| GET | /api/monitor/video-matches | 视频指纹匹配结果(?hamming_threshold=10) | v3 |

**前端组件**:
- **VideoFingerprintPanel.vue** (v3): Props: `{ workId }` — 指纹生成状态 + 采样帧预览网格 + 哈希详情 + 重新生成按钮
- **VideoMatchResult.vue** (v3): Props: `{ matchResults[] }` — 视频匹配结果列表 + 汉明距离指示器 + 相似帧对比视图

**v1集成点**:
- works表 — v1预留 perceptual_hash / perceptual_hash_type 字段
- [2]权利保护中心 — 侵权扫描扩展点: v2图片以图搜图 → v3视频帧指纹匹配
- video_fingerprint_config / video_frame_fingerprints表 — v1预留

> **标注**: v1 works表已预留perceptual_hash/perceptual_hash_type字段。指纹相关表已预留。完整视频指纹生成+匹配系统待v3实现。

---

#### 12.2.4 横竖屏版本管理

- **目标版本**: v3 | **目标创作者**: 短视频/动画

**功能说明**: 同一视频内容的16:9/9:16/1:1不同构图版本作为版本分组关联，而非独立作品。

**数据模型**:

```sql
-- v1预留
ALTER TABLE works ADD COLUMN aspect_ratio_variants JSON;
-- aspect_ratio_variants JSON 结构:
-- {
--   "primary": "16:9",
--   "variants": [
--     {"work_id": 234, "aspect_ratio": "9:16", "crop_mode": "center", "created_from": "ffmpeg_crop"},
--     {"work_id": 235, "aspect_ratio": "1:1", "crop_mode": "center", "created_from": "ffmpeg_crop"}
--   ]
-- }

-- 版本组关联表
CREATE TABLE work_variant_groups (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    master_work_id INTEGER NOT NULL REFERENCES works(id),
    variant_work_id INTEGER NOT NULL REFERENCES works(id),
    variant_type VARCHAR(20) NOT NULL,  -- 'aspect_ratio' / 'resolution' / 'format' / 'duration'
    variant_value VARCHAR(50),  -- '9:16' / '4K' / '1080p' / 'shorts'
    UNIQUE(master_work_id, variant_work_id, variant_type)
);
```

**API端点设计**:

| 方法 | 路径 | 说明 | 版本 |
|------|------|------|------|
| POST | /api/works/{id}/variants | 创建变体版本 (body: {aspect_ratio, crop_mode}) | v3 |
| GET | /api/works/{id}/variants | 获取所有变体版本 | v3 |
| PATCH | /api/works/{id}/variants/reorder | 调整变体排序 | v3 |
| DELETE | /api/works/{id}/variants/{variant_id} | 删除变体版本 | v3 |

**前端组件**:
- **VariantGroupView.vue** (v3): Props: `{ workId }` — 主版本+变体网格展示 + 每个变体的尺寸标签 + 创建新变体按钮(选择目标比例→ffmpeg后端裁切)
- **AspectRatioBadge.vue** (v3): Props: `{ ratio }` — 横竖屏尺寸标签(16:9横/9:16竖/1:1方)

**v1集成点**:
- works表 — v1预留 aspect_ratio_variants 字段
- work_variant_groups表 — v1预留
- 作品列表卡片 — v1预留变体数量角标(如 "主作品 +2变体")

> **标注**: v1 works表的 aspect_ratio_variants 字段已预留。work_variant_groups表已预留。作品列表卡片预留变体数量角标。横竖屏变体管理待v3实现。

---

### 12.3 音乐创作者专属功能 (v4)

#### 12.3.1 ISRC/ISWC字段

- **目标版本**: v4 | **目标创作者**: 音乐人

**功能说明**: ISRC (International Standard Recording Code) 是音乐发行的必须标识码，无ISRC的音频文件会被DistroKid等平台拒绝。ISWC (International Standard Musical Work Code) 用于标识作曲/作词作品。

**数据模型** (works.custom_metadata扩展):

```json
// works.custom_metadata 音乐专属扩展字段 (v1预留JSON路径，v4填充)
{
  "isrc": "CN-A09-26-00001",    // ISRC录音编码 (12位字母数字)
  "iswc": "T-123.456.789-0",    // ISWC作曲编码
  "ipn": null,                   // IPN (International Performer Number, 可选)
  "isni": null,                  // ISNI (International Standard Name Identifier, 可选)
  "upc_ean": "0123456789012",   // UPC/EAN条形码(发行用)
  "recording_location": "北京百花录音棚",
  "recording_date": "2026-03-15",
  "recording_engineer": "张三",
  "mastering_engineer": "李四",
  "tempo_bpm": 120,
  "key_signature": "C# minor",  // 调性
  "time_signature": "4/4",
  "genre": "电子/实验",
  "sub_genre": "Ambient Techno"
}
```

**API端点设计**:

| 方法 | 路径 | 说明 | 版本 |
|------|------|------|------|
| PATCH | /api/works/{id}/music-metadata | 更新音乐元数据 (body: {isrc, iswc, upc_ean, ...}) | v4 |
| GET | /api/works/{id}/music-metadata | 获取音乐元数据 | v4 |
| POST | /api/works/validate-isrc | 校验ISRC格式 (body: {isrc}) | v4 |
| POST | /api/works/lookup-isrc | ISRC查重（检查是否被重复注册） | v4 |

**前端组件**:
- **MusicMetadataForm.vue** (v4): Props: `{ workId, metadata? }` — 音乐元数据编辑表单，ISRC/ISWC/UPC/录音信息/调性/BPM等字段
- **IsrcValidator.vue** (v4): Props: `{ isrc }` — ISRC实时格式校验+提示

**v1集成点**:
- works.custom_metadata — v1 JSON字段已预留所有音乐专属路径
- 作品详情页元数据编辑面板 — v1预留按文件类型切换表单区域(音频类型显示MusicMetadataForm)

> **标注**: v1 works.custom_metadata JSON已预留ISRC/ISWC/UPC_EAN等字段路径。作品详情页元数据表单预留音频类型专属区域。完整ISRC校验+发行集成交付v4实现。

---

#### 12.3.2 专辑/EP/Single概念

- **目标版本**: v4 | **目标创作者**: 音乐人

**功能说明**: 音乐作品需要专辑/EP/Single的层级概念，包含曲目排序、统一封面(3000x3000规范)、发行日期管理。

**数据模型**:

```sql
-- v1预留
CREATE TABLE albums (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    title VARCHAR(200) NOT NULL,
    album_type VARCHAR(20) NOT NULL,  -- 'album'(专辑) / 'ep'(EP) / 'single'(单曲)
    release_date DATE,
    cover_art_path VARCHAR(500),  -- 封面3000×3000px规范
    genre VARCHAR(100),
    label VARCHAR(200),  -- 厂牌
    upc_ean VARCHAR(20),  -- 条形码
    description TEXT,
    total_tracks INTEGER DEFAULT 0,  -- 曲目数
    total_duration_seconds FLOAT,  -- 总时长
    status VARCHAR(20) DEFAULT 'draft',  -- draft/released/archived
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 曲目排序关联表
CREATE TABLE album_tracks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    album_id INTEGER NOT NULL REFERENCES albums(id) ON DELETE CASCADE,
    work_id INTEGER NOT NULL REFERENCES works(id),
    track_number INTEGER NOT NULL,  -- 曲目序号 1,2,3...
    disc_number INTEGER DEFAULT 1,  -- CD盘号(多CD专辑)
    is_bonus_track BOOLEAN DEFAULT FALSE,  -- 是否为附赠曲目
    UNIQUE(album_id, work_id)
);

CREATE INDEX idx_album_tracks_album ON album_tracks(album_id);
CREATE INDEX idx_album_tracks_work ON album_tracks(work_id);
```

**API端点设计**:

| 方法 | 路径 | 说明 | 版本 |
|------|------|------|------|
| GET | /api/albums | 专辑列表 (?album_type=&status=) | v4 |
| POST | /api/albums | 创建专辑 | v4 |
| GET | /api/albums/{id} | 专辑详情(含曲目列表) | v4 |
| PATCH | /api/albums/{id} | 更新专辑信息 | v4 |
| DELETE | /api/albums/{id} | 删除专辑 | v4 |
| POST | /api/albums/{id}/tracks | 添加曲目 (body: {work_id, track_number}) | v4 |
| PATCH | /api/albums/{id}/tracks/reorder | 曲目排序 (body: [{track_id, new_position}]) | v4 |
| DELETE | /api/albums/{id}/tracks/{track_id} | 移除曲目 | v4 |

**前端组件**:
- **AlbumEditor.vue** (v4): Props: `{ album?, onSave }` — 专辑创建/编辑表单 + 曲目拖拽排序列表 + 封面预览(3000x3000规范提醒)
- **AlbumCard.vue** (v4): Props: `{ album }` — 专辑卡片展示(封面+标题+类型+曲目数+时长)
- **TrackOrderEditor.vue** (v4): Props: `{ tracks[], onReorder }` — 拖拽排序组件

**v1集成点**:
- albums / album_tracks表 — v1预留
- 作品详情页右侧关联面板 — v1预留"所属专辑"显示区域
- 项目(Project)管理 — v1可降级使用Project替代专辑(v1过渡方案)

> **标注**: v1 albums / album_tracks表已预留。作品编辑面板预留"所属专辑"关联入口。完整专辑/EP/Single管理待v4实现。

---

#### 12.3.3 Split Sheets (合作者权益分配)

- **目标版本**: v4 | **目标创作者**: 音乐人

**功能说明**: 音乐行业标准的合作者权益分配表，记录每个参与者的角色和权益百分比。当前系统只有单个author_name字段，完全无法满足多合作者场景。

**数据模型**:

```sql
-- v1预留
CREATE TABLE work_collaborators (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    work_id INTEGER NOT NULL REFERENCES works(id) ON DELETE CASCADE,
    user_id INTEGER,  -- 系统内用户(可为NULL表示外部合作者)
    name VARCHAR(200) NOT NULL,  -- 合作者姓名
    role VARCHAR(50) NOT NULL,  -- 角色: composer/lyricist/producer/arranger/mixer/performer/featured_artist
    role_detail VARCHAR(200),  -- 角色补充说明 e.g., "主歌作曲"
    percentage FLOAT NOT NULL,  -- 权益百分比 e.g., 50.0
    ipi_number VARCHAR(50),  -- IPI/CAE号(PRO系统标识)
    pro_affiliation VARCHAR(100),  -- 所属PRO: ASCAP/BMI/PRS/MCSC等
    publisher_name VARCHAR(200),  -- 出版公司
    publisher_percentage FLOAT DEFAULT 0.0,  -- 出版方份额
    writer_percentage FLOAT DEFAULT 0.0,  -- 词曲方份额
    contract_reference VARCHAR(500),  -- 合同编号/链接
    signature_status VARCHAR(20) DEFAULT 'unsigned',  -- unsigned/signed/disputed
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_work_collaborators_work ON work_collaborators(work_id);
```

**验证规则**:
- 所有合作者 percentage 总和必须等于 100%
- publisher_percentage + writer_percentage 应当匹配各自份额

**API端点设计**:

| 方法 | 路径 | 说明 | 版本 |
|------|------|------|------|
| GET | /api/works/{id}/collaborators | 合作者列表 | v4 |
| POST | /api/works/{id}/collaborators | 添加合作者 (body: {name, role, percentage, ...}) | v4 |
| PATCH | /api/works/{id}/collaborators/{collab_id} | 更新合作者信息 | v4 |
| DELETE | /api/works/{id}/collaborators/{collab_id} | 移除合作者 | v4 |
| GET | /api/works/{id}/split-sheet | 生成Split Sheet文档(PDF) | v4 |
| POST | /api/works/{id}/collaborators/validate | 校验分配比例(总和=100%) | v4 |

**前端组件**:
- **CollaboratorEditor.vue** (v4): Props: `{ workId, collaborators[] }` — 合作者列表 + 添加/编辑弹窗 + 百分比饼图可视化 + 总百分比校验(红色警告!=100%)
- **SplitSheetGenerator.vue** (v4): Props: `{ workId }` — Split Sheet PDF生成 + 预览 + 下载/发送

**v1集成点**:
- work_collaborators表 — v1预留
- 作品详情页 — v1预留"合作者"关联面板(替代当前单一author_name展示)
- works.author_name — v1保留为主创作者/主署名，collaborators承载详细分配

> **标注**: v1 work_collaborators表已预留。作品详情页预留多合作者显示区域。Split Sheet PDF生成待v4实现。

---

#### 12.3.4 Master vs Publishing权利区分

- **目标版本**: v4 | **目标创作者**: 音乐人

**功能说明**: 音乐行业最基础的法律区分——Master Rights(录音母带权利)和Publishing Rights(词曲版权)。当前系统用单个rights JSON覆盖所有，无法区分。

**数据模型** (works.rights JSON扩展):

```json
// works.rights — v1预留JSON结构，v4扩展为以下完整结构
{
  // === v1 现有字段 (保留) ===
  "author_name": "苏旋律",
  "copyright_year": 2026,
  "license_type": "all_rights_reserved",
  "attribution_text": "© 苏旋律 2026",
  "allow_reproduction": false,
  "allow_adaptation": false,
  "commercial_use": false,

  // === v4 Master Rights (录音母带权利) ===
  "master_rights": {
    "owner": "苏旋律",           // 母带权利持有人
    "owner_share": 100.0,        // 母带份额
    "label_share": 0.0,          // 厂牌份额
    "is_master_owned": true,     // 是否持有母带权利
    "master_license_terms": null // 母带授权条款
  },

  // === v4 Publishing Rights (词曲版权) ===
  "publishing_rights": {
    "publisher": "独立出版",     // 出版方
    "publisher_share": 0.0,      // 出版方份额
    "writer_share": 100.0,       // 词曲方份额
    "pro_registration": {        // PRO注册信息
      "organization": "ASCAP",
      "work_id": null,
      "registration_date": null,
      "status": "unregistered"
    }
  },

  // === v4 Sync Rights (同步授权) ===
  "sync_rights": {
    "available_for_sync": false,
    "sync_agency": null,
    "one_stop": false,  // 是否为one-stop(母带+词曲统一管理)
    "restrictions": []
  },

  // === v4 Derived Rights (衍生权利) ===
  "derived_rights": {
    "remix_ok": false,
    "sample_ok": false,
    "karaoke_ok": false,
    "lyric_translation_ok": true
  }
}
```

**API端点设计**:

| 方法 | 路径 | 说明 | 版本 |
|------|------|------|------|
| PATCH | /api/works/{id}/rights/music | 更新音乐权利配置 (body: master_rights, publishing_rights, sync_rights) | v4 |
| GET | /api/works/{id}/rights/music | 获取完整音乐权利信息 | v4 |

**前端组件**:
- **MusicRightsPanel.vue** (v4): Props: `{ workId, rights }` — Master/Publishing/Sync分页面板 + 可视化份额饼图 + 法律术语简单解释Tooltip

**v1集成点**:
- works.rights JSON — v1已预留完整JSON结构路径，v4填充
- 作品详情页权利信息区 — v1预留"权利详情"展开面板(音频类型显示MusicRightsPanel)

> **标注**: v1 works.rights JSON已预留 master_rights / publishing_rights / sync_rights / derived_rights 完整路径。前端权利面板预留音频类型专属展开区域。完整音乐权利管理待v4实现。

---

### 12.4 文字创作者专属功能 (v4)

#### 12.4.1 章节结构

- **目标版本**: v4 | **目标创作者**: 文字作者

**功能说明**: 文字作品需要卷→章→内容+草稿+设定+批注的层级结构。当前系统"一个work就是一个文件"完全不符合写作工作流。

**数据模型**:

```sql
-- v1预留
CREATE TABLE chapters (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    work_id INTEGER NOT NULL REFERENCES works(id) ON DELETE CASCADE,
    volume_number INTEGER DEFAULT 1,  -- 卷号
    chapter_number INTEGER NOT NULL,  -- 章节序号
    title VARCHAR(500) NOT NULL,  -- 章节标题
    content TEXT,  -- 章节正文(纯文本)
    content_html TEXT,  -- 章节正文(HTML，富文本)
    word_count INTEGER DEFAULT 0,  -- 字数
    status VARCHAR(20) DEFAULT 'draft',  -- draft/revised/final/locked
    notes TEXT,  -- 作者备注(创作笔记/设定)
    revision_count INTEGER DEFAULT 0,  -- 修改次数
    last_revision_at DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(work_id, volume_number, chapter_number)
);

-- 章节级评论/批注 (Beta Reader / 编辑反馈)
CREATE TABLE chapter_comments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    chapter_id INTEGER NOT NULL REFERENCES chapters(id) ON DELETE CASCADE,
    user_id INTEGER,
    commenter_name VARCHAR(100),
    comment_text TEXT NOT NULL,
    comment_type VARCHAR(20) DEFAULT 'feedback',  -- feedback/suggestion/correction/note
    line_start INTEGER,  -- 批注起始行号
    line_end INTEGER,    -- 批注结束行号
    is_resolved BOOLEAN DEFAULT FALSE,
    resolved_at DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 章节级版本快照(轻量级，不同于全文件work_versions)
CREATE TABLE chapter_revisions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    chapter_id INTEGER NOT NULL REFERENCES chapters(id) ON DELETE CASCADE,
    revision_number INTEGER NOT NULL,
    content_snapshot TEXT,  -- 该版本的正文副本
    word_count INTEGER,
    change_summary VARCHAR(500),  -- 修改摘要 e.g., "第三章重写对白, 增加环境描写"
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_chapters_work ON chapters(work_id);
CREATE INDEX idx_chapter_comments_chapter ON chapter_comments(chapter_id);
CREATE INDEX idx_chapter_revisions_chapter ON chapter_revisions(chapter_id);
```

**API端点设计**:

| 方法 | 路径 | 说明 | 版本 |
|------|------|------|------|
| GET | /api/works/{id}/chapters | 章节列表(按卷/章排序) | v4 |
| POST | /api/works/{id}/chapters | 创建章节 | v4 |
| GET | /api/works/{id}/chapters/{chapter_id} | 章节详情(含正文) | v4 |
| PATCH | /api/works/{id}/chapters/{chapter_id} | 编辑章节(正文/标题/状态) | v4 |
| DELETE | /api/works/{id}/chapters/{chapter_id} | 删除章节 | v4 |
| POST | /api/works/{id}/chapters/reorder | 重新排序章节 | v4 |
| GET | /api/works/{id}/chapters/{chapter_id}/comments | 章节评论/批注 | v4 |
| POST | /api/works/{id}/chapters/{chapter_id}/comments | 添加批注 | v4 |
| GET | /api/works/{id}/chapters/{chapter_id}/revisions | 章节修订历史 | v4 |
| POST | /api/works/{id}/chapters/{chapter_id}/revisions | 创建章节快照 | v4 |
| GET | /api/works/{id}/statistics | 作品统计(总字数/章节数/完成率等) | v4 |

**前端组件**:
- **ChapterTree.vue** (v4): Props: `{ workId }` — 左侧章节树(卷→章层级) + 拖拽排序 + 右键菜单(新建/重命名/删除/锁定)
- **ChapterEditor.vue** (v4): Props: `{ chapter }` — 富文本编辑器(Quill/TipTap) + 字数实时统计 + 状态选择 + 自动保存
- **ChapterComments.vue** (v4): Props: `{ chapterId }` — 侧边批注面板 + Beta Reader反馈管理 + 已解决/未解决筛选
- **WritingStatistics.vue** (v4): Props: `{ workId }` — 写作统计仪表盘: 总字数/日字数趋势/完成率/写作日历热力图

**v1集成点**:
- chapters / chapter_comments / chapter_revisions 表 — v1预留
- 作品详情页 — v1预留按文件类型切换详情视图(对于text/markdown类型，显示ChapterTree视图替代5.1节的单一预览区)
- works.version (全文件快照) — v1保留，v4与chapter_revisions共存(全文件快照用于里程碑，章节修订用于日常编辑)

> **标注**: v1 chapters/chapter_comments/chapter_revisions 三张表已预留。作品详情页预留文字类型→章节树视图切换。完整章节编辑系统待v4实现。

---

#### 12.4.2 EPUB导出

- **目标版本**: v4 | **目标创作者**: 文字作者

**功能说明**: 将作品的章节结构导出为完整EPUB电子书，包含封面/目录/章节合并/元数据嵌入。

**数据模型** (works表扩展):

```sql
-- v1预留
ALTER TABLE works ADD COLUMN export_formats JSON;
-- export_formats JSON 结构:
-- {
--   "available": ["epub", "pdf", "mobi", "html", "docx"],
--   "epub": {
--     "last_exported": "2026-06-12T15:43:00Z",
--     "file_path": "data/exports/ab/cd/abc123.epub",
--     "file_size": 2048000,
--     "cover_image_path": "data/exports/ab/cd/abc123_cover.jpg",
--     "toc_generated": true
--   },
--   "pdf": { ... }
-- }

-- EPUB导出配置
CREATE TABLE export_configs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    work_id INTEGER NOT NULL REFERENCES works(id) ON DELETE CASCADE,
    format VARCHAR(10) NOT NULL,  -- epub/pdf/mobi/docx
    cover_path VARCHAR(500),  -- 封面图片路径
    title_page_text TEXT,  -- 扉页内容
    include_toc BOOLEAN DEFAULT TRUE,  -- 包含目录
    include_copyright_page BOOLEAN DEFAULT TRUE,  -- 包含版权页
    font_embedding TEXT,  -- 嵌入字体列表
    page_size VARCHAR(20) DEFAULT 'A5',  -- PDF纸张尺寸
    margin_mm INTEGER DEFAULT 20,  -- PDF页边距
    chapter_title_style VARCHAR(50) DEFAULT 'h1',  -- 章节标题样式
    custom_css TEXT,  -- 自定义样式
    metadata_overrides JSON,  -- 元数据覆盖
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

**导出管道 (Pandoc)**:
- 章节合并: SQL查询按chapter_number排序拼接 → 格式化为Markdown
- Pandoc转换: `pandoc input.md -o output.epub --toc --metadata title="..." --metadata author="..."`
- 封面处理: Pillow生成封面图+嵌入epub
- 元数据嵌入: Dublin Core/EPUB3 metadata
- 输出格式: EPUB (.epub) / PDF (通过LaTeX/Pandoc) / MOBI (通过kindlegen) / DOCX / HTML

**API端点设计**:

| 方法 | 路径 | 说明 | 版本 |
|------|------|------|------|
| POST | /api/works/{id}/export-config | 创建导出配置 | v4 |
| GET | /api/works/{id}/export-config | 获取导出配置列表 | v4 |
| POST | /api/works/{id}/export | 执行导出 (body: {format, config_id}) | v4 |
| GET | /api/works/{id}/export-status | 导出任务状态(异步) | v4 |
| GET | /api/works/{id}/exports/{export_id}/download | 下载导出文件 | v4 |
| GET | /api/works/{id}/exports | 导出历史列表 | v4 |

**前端组件**:
- **ExportWizard.vue** (v4): Props: `{ workId }` — 导出向导: 选格式→配置封面→预览→导出→下载
- **ExportHistory.vue** (v4): Props: `{ workId }` — 导出历史列表+下载+重新导出

**v1集成点**:
- works.export_formats JSON — v1预留
- export_configs表 — v1预留
- 作品详情页操作按钮区 — v1预留"导出"按钮(文字类型时显示)

> **标注**: v1 works表的 export_formats 字段已预留。export_configs表已预留。作品详情页预留文字类型"导出"入口。完整EPUB/PDF导出管道待v4实现。

---

#### 12.4.3 权利细分

- **目标版本**: v4 | **目标创作者**: 文字作者

**功能说明**: 文字作品的权利远不止一个license_type下拉框。翻译权、影视改编权、连载权、有声书权、游戏改编权需要独立管理。

**数据模型** (works.rights JSON扩展):

```json
// works.rights — v1预留JSON结构，v4扩展
{
  // ... v1现有字段保留 ...

  // === v4 文字作品权利细分 ===
  "literary_rights": {
    "translation_ok": false,        // 翻译权
    "film_ok": false,               // 影视改编权
    "serial_ok": false,             // 连载权
    "audiobook_ok": false,          // 有声书权
    "game_ok": false,               // 游戏改编权
    "stage_ok": false,              // 舞台剧改编权
    "comic_ok": false,              // 漫画改编权
    "merchandise_ok": false,        // 周边衍生品权
    "territory": "worldwide",       // 授权地域: worldwide/china/asia/europe/north_america/custom
    "territory_detail": null,       // 自定义地域说明
    "royalty_rate_ebook": 0.0,      // 电子书版税率
    "royalty_rate_print": 0.0,      // 纸质书版税率
    "royalty_rate_audio": 0.0,      // 有声书版税率
    "royalty_rate_adaptation": 0.0,  // 改编版税率
    "exclusive_until": null,        // 独家授权截止日期
    "rights_holder_note": null      // 权利持有人备注
  }
}
```

**API端点设计**:

| 方法 | 路径 | 说明 | 版本 |
|------|------|------|------|
| PATCH | /api/works/{id}/rights/literary | 更新文字作品权利配置 | v4 |
| GET | /api/works/{id}/rights/literary | 获取文字作品完整权利 | v4 |

**前端组件**:
- **LiteraryRightsPanel.vue** (v4): Props: `{ workId, rights }` — 权利细分面板: 各改编权toggle + 地域选择器(世界地图/列表) + 版税率滑块 + 独家期限日期选择器

**v1集成点**:
- works.rights JSON — v1已预留 literary_rights 完整JSON路径
- 作品详情页权利信息区 — v1预留文字类型→权利细分展开面板

> **标注**: v1 works.rights JSON已预留literary_rights完整路径结构。前端权利面板预留文字类型专属展开区域。完整文字权利管理待v4实现。
