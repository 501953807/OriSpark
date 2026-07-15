# 摄影师完整支持 (Photographer v2) 实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development to implement task-by-task.
> **Version:** v2 | **Target Creator:** 摄影师

**Goal:** 为摄影师类型提供完整的 RAW 工作流、选片模式、图库分发、GPS 地图功能
**Architecture:** 扩展现有 work/work_variant 模型添加摄影师专属字段，新建 photographer 路由和前端视图
**Tech Stack:** FastAPI + SQLAlchemy (BE), Vue 3 + TypeScript + Pinia (FE)

## Global Constraints

- 所有 alert() 替换为 toast
- 所有 async 函数必须有 try/catch
- 前端文件 <800 行，函数 <50 行
- 严格 immutability

---

## Task 1: 摄影师数据模型

**Files:**
- `backend/app/models/photographer.py` - 新建(从 reserved_photographer.py 迁移)
- `backend/app/schemas/photographer.py` - 新建
- `backend/app/routers/photographer.py` - 新建

**摄影师专属字段扩展:**

```python
# 在 work_variants 表中添加摄影师专属字段
class WorkVariant(Base):
    # ... 现有字段 ...
    # 摄影师扩展
    camera_model = Column(String(100), nullable=True)       # 相机型号
    lens = Column(String(200), nullable=True)               # 镜头
    iso = Column(Integer, nullable=True)                    # ISO
    aperture = Column(String(20), nullable=True)            # 光圈 (f/2.8)
    shutter_speed = Column(String(30), nullable=True)       # 快门速度 (1/250s)
    focal_length = Column(String(30), nullable=True)        # 焦距 (50mm)
    gps_latitude = Column(Float, nullable=True)             # GPS 纬度
    gps_longitude = Column(Float, nullable=True)            # GPS 经度
    gps_altitude = Column(Float, nullable=True)             # GPS 海拔
    raw_file_path = Column(String(500), nullable=True)      # RAW 原始文件路径
    shot_status = Column(String(20), default="unreviewed")  # 选片状态: unreviewed|pass|hold|reject|shortlist
    shot_notes = Column(Text, nullable=True)                # 选片备注
    stock_channels = Column(JSON, nullable=True)            # 已投放图库渠道 [{"channel": "500px", "status": "active"}]
```

**摄影师专属过程阶段 (8阶段):**
```
灵感参考 → 拍摄计划 → 素材采集 → 现场拍摄 → 初选 → 后期处理 → 成品交付 → 归档发布
```

**API 端点:**

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/photographer/shots` | 作品列表(含摄影师扩展字段) |
| POST | `/api/photographer/shots/{id}/shot-status` | 更新选片状态 |
| GET | `/api/photographer/exif/search` | EXIF 高级搜索 |
| GET | `/api/photographer/gps/map` | GPS 地图数据 |
| POST | `/api/photographer/stock/channels` | 添加图库渠道 |
| DELETE | `/api/photographer/stock/channels/{channel}` | 移除图库渠道 |
| GET | `/api/photographer/stats` | 摄影师统计 |

- [ ] **Step 1:** 读取 `backend/app/models/reserved_photographer.py` 了解预留结构
- [ ] **Step 2:** 创建 `backend/app/models/photographer.py` 迁移模型
- [ ] **Step 3:** 创建 Alembic 迁移并应用
- [ ] **Step 4:** 创建 `backend/app/schemas/photographer.py` 序列化 schema
- [ ] **Step 5:** 创建 `backend/app/routers/photographer.py` 路由

## Task 2: 摄影师前端 Store + API

**Files:**
- `frontend/src/api/photographer.ts` - 新建
- `frontend/src/stores/usePhotographerStore.ts` - 新建
- `frontend/src/types/photographer.ts` - 新建

**类型定义:**

```typescript
interface PhotographerShot {
  id: string
  work_id: string
  camera_model?: string
  lens?: string
  iso?: number
  aperture?: string
  shutter_speed?: string
  focal_length?: string
  gps_latitude?: number
  gps_longitude?: number
  raw_file_path?: string
  shot_status: 'unreviewed' | 'pass' | 'hold' | 'reject' | 'shortlist'
  shot_notes?: string
  stock_channels?: Array<{channel: string, status: string}>
}

interface PhotoStats {
  total_shots: number
  pass_count: number
  shortlist_count: number
  rejected_count: number
  stock_listings: number
  monthly_sales: number
}
```

**Store 接口:**

```typescript
interface PhotographerStore {
  shots: PhotographerShot[]
  stats: PhotoStats | null
  loading: boolean
  
  fetchShots(filters?: ShotFilters): Promise<void>
  updateShotStatus(shotId: string, status: ShotStatus): Promise<void>
  addStockChannel(shotId: string, channel: string): Promise<void>
  removeStockChannel(shotId: string, channel: string): Promise<void>
  searchByExif(filters: ExifSearchFilters): Promise<PhotographerShot[]>
  fetchStats(): Promise<void>
}
```

- [ ] **Step 1:** 创建 `frontend/src/types/photographer.ts`
- [ ] **Step 2:** 创建 `frontend/src/api/photographer.ts`
- [ ] **Step 3:** 创建 `frontend/src/stores/usePhotographerStore.ts`

## Task 3: 摄影师主视图

**Files:**
- `frontend/src/views/PhotographerView.vue` - 新建

**Layout:**
```
┌─────────────────────────────────────────────┐
│ 摄影师工作台                                │
├─────────────────────────────────────────────┤
│ 📷 总作品: 128  |  ✅ 已通过: 45             │
│ 📋 短名单: 12  |  📦 图库上架: 38           │
│ 💰 本月销售: ¥2,340                         │
├─────────────────────────────────────────────┤
│ [选片] [图库] [GPS地图] [统计]             │
├─────────────────────────────────────────────┤
│                                             │
│  ── 选片视图 ─────────────────────────────  │
│  [缩略图网格]                               │
│  每张图右下角: ☐ 未选 / ✅ 通过 / ❌ 拒绝    │
│  双击图片: 放大查看 EXIF                    │
│                                             │
└─────────────────────────────────────────────┘
```

- [ ] **Step 1:** 创建 PhotographerView.vue 骨架
- [ ] **Step 2:** 实现选片网格视图
- [ ] **Step 3:** 实现 EXIF 悬浮显示
- [ ] **Step 4:** 实现批量选片操作

## Task 4: 摄影师子组件

**Files:**
- `frontend/src/components/photographer/ShotSelector.vue` - 新建
- `frontend/src/components/photographer/RawMetadataPanel.vue` - 新建
- `frontend/src/components/photographer/StockChannelPanel.vue` - 新建
- `frontend/src/components/photographer/GPSMapPanel.vue` - 新建

**ShotSelector.vue:**
Props: `{ shots: PhotographerShot[], loading: boolean }`
Events: `@status-change(shotId, status)`, `@batch-update(statuses: Map<string, ShotStatus>)`
- 缩略图网格 (CSS Grid, responsive)
- 双击放大查看 (Lightbox)
- 悬浮显示 EXIF 信息
- 批量选择工具 (全选/通过/拒绝/短名单)

**RawMetadataPanel.vue:**
Props: `{ shot: PhotographerShot }`
- EXIF 信息展示 (相机/镜头/ISO/光圈/快门/焦距)
- RAW 文件信息
- 编辑备注

**StockChannelPanel.vue:**
Props: `{ shot: PhotographerShot }`
- 已投放渠道列表
- 添加渠道下拉框 (500px/图虫/Fotolia/Shutterstock/Adobe Stock)
- 渠道状态标签 (active/pending/rejected)

**GPSMapPanel.vue:**
Props: `{ shots: PhotographerShot[] }`
- Leaflet 地图集成
- 拍摄点标记
- 点击标记显示作品缩略图 + EXIF

- [ ] **Step 1:** 实现 ShotSelector.vue
- [ ] **Step 2:** 实现 RawMetadataPanel.vue
- [ ] **Step 3:** 实现 StockChannelPanel.vue
- [ ] **Step 4:** 实现 GPSMapPanel.vue (需要安装 leaflet)
- [ ] **Step 5:** 集成到 PhotographerView.vue

## Task 5: 图库 API 对接 (后端)

**Files:**
- `backend/app/services/stock_service.py` - 新建
- `backend/app/routers/photographer.py` - 扩展

**功能:**
- 500px API (OAuth2 + REST)
- 图虫 API (OAuth2 + REST)
- Adobe Stock API (JWT)
- 上传作品 + 元数据
- 同步销售数据

- [ ] **Step 1:** 实现 StockChannel 基类
- [ ] **Step 2:** 实现 500px adapter
- [ ] **Step 3:** 实现 图虫 adapter
- [ ] **Step 4:** 实现 Adobe Stock adapter
- [ ] **Step 5:** 实现销售数据同步定时任务

---

## 测试计划

- [ ] 摄影师数据模型迁移测试
- [ ] EXIF 搜索端点测试
- [ ] 选片状态转换测试
- [ ] ShotSelector 批量操作测试
- [ ] StockChannelPanel 渠道管理测试
- [ ] GPSMapPanel 地图渲染测试
