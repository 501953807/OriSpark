# 音乐人完整支持 (Musician v4a) 实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development to implement task-by-task.
> **Version:** v4a | **Target Creator:** 音乐人

**Goal:** 实现 ISRC 管理、Split Sheets、专辑管理、发行平台对接、音频指纹
**Architecture:** 从 reserved_music.py 迁移模型 + 新建 music 路由 + 全新前端视图
**Tech Stack:** FastAPI + SQLAlchemy (BE), Vue 3 + TypeScript + Pinia (FE)

## Global Constraints

- 所有 alert() 替换为 toast
- 所有 async 函数必须有 try/catch
- 前端文件 <800 行，函数 <50 行
- 严格 immutability

---

## Task 1: 音乐人数据模型

**Files:**
- `backend/app/models/music.py` - 新建(从 reserved_music.py 迁移)
- `backend/app/schemas/music.py` - 新建
- `backend/app/routers/music.py` - 新建

**核心模型:**

```python
# ISRC Registration
class ISRCRegistration(Base):
    __tablename__ = "isrc_registrations"
    id = Column(String, primary_key=True)
    work_id = Column(String, nullable=False, unique=True)
    isrc_code = Column(String(12), unique=True, nullable=False)  # XX-ABC-YY-NNNNN
    title = Column(String(200), nullable=False)
    artist = Column(String(200), nullable=False)
    album = Column(String(200), nullable=True)
    duration_seconds = Column(Integer, nullable=True)
    producer = Column(String(200), nullable=True)
    phonogram_maker = Column(String(200), nullable=True)
    status = Column(String(20), default="pending")  # pending|registered|rejected
    registered_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=current_timestamp)

# Split Sheet (版权分成协议)
class SplitSheet(Base):
    __tablename__ = "split_sheets"
    id = Column(String, primary_key=True)
    song_title = Column(String(200), nullable=False)
    album = Column(String(200), nullable=True)
    isrc = Column(String(12), nullable=True)
    total_splits = Column(Numeric(5, 2), default=100.00)  # 总和应为100%
    status = Column(String(20), default="draft")  # draft|pending_signatures|signed|archived
    created_by = Column(String, nullable=False)
    created_at = Column(DateTime, default=current_timestamp)

class SplitSheetParticipant(Base):
    __tablename__ = "split_sheet_participants"
    id = Column(String, primary_key=True)
    split_sheet_id = Column(String, ForeignKey("split_sheets.id"), nullable=False)
    name = Column(String(200), nullable=False)
    share_percentage = Column(Numeric(5, 2), nullable=False)  # 0-100
    role = Column(String(50))  # composer|lyricist|performer|producer
    signed = Column(Boolean, default=False)
    signed_at = Column(DateTime, nullable=True)
    payout_account = Column(String(200), nullable=True)  # PayPal/bank account

# Album
class Album(Base):
    __tablename__ = "albums"
    id = Column(String, primary_key=True)
    creator_id = Column(String, nullable=False)
    title = Column(String(200), nullable=False)
    album_type = Column(String(20))  # album|ep|single|compilation
    release_date = Column(DateTime, nullable=True)
    label = Column(String(200), nullable=True)
    cover_art_path = Column(String(500), nullable=True)
    total_tracks = Column(Integer, nullable=True)
    genres = Column(JSON, nullable=True)  # ["pop", "rock"]
    status = Column(String(20), default="draft")  # draft|scheduled|released|archived
    created_at = Column(DateTime, default=current_timestamp)

# Distribution Platform
class DistributionPlatform(Base):
    __tablename__ = "distribution_platforms"
    id = Column(String, primary_key=True)
    creator_id = Column(String, nullable=False)
    platform_name = Column(String(100), nullable=False)  # Spotify/Apple Music/DistroKid
    api_key_encrypted = Column(Text, nullable=True)
    status = Column(String(20), default="connected")  # connected/disconnected
    last_sync = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=current_timestamp)

# Streaming Earnings
class StreamingEarning(Base):
    __tablename__ = "streaming_earnings"
    id = Column(String, primary_key=True)
    album_id = Column(String, nullable=True)
    track_isrc = Column(String(12), nullable=True)
    platform = Column(String(100), nullable=False)
    period_start = Column(Date, nullable=False)
    period_end = Column(Date, nullable=False)
    streams = Column(Integer, nullable=False)
    earnings = Column(Numeric(10, 2), nullable=False)
    currency = Column(String(3), default="CNY")
    synced_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=current_timestamp)
```

- [ ] **Step 1:** 读取 `backend/app/models/reserved_music.py`
- [ ] **Step 2:** 创建 `backend/app/models/music.py`
- [ ] **Step 3:** Alembic 迁移并应用
- [ ] **Step 4:** 创建 schemas
- [ ] **Step 5:** 创建 music.py 路由

**API 端点:**

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/music/isrc` | ISRC 码列表 |
| POST | `/api/music/isrc/register` | 申请 ISRC 码 |
| GET | `/api/music/split-sheets` | Split Sheets 列表 |
| POST | `/api/music/split-sheets` | 创建 Split Sheet |
| PATCH | `/api/music/split-sheets/{id}/sign` | 签署 Split Sheet |
| GET | `/api/music/albums` | 专辑列表 |
| POST | `/api/music/albums` | 创建专辑 |
| POST | `/api/music/albums/{id}/tracks` | 添加音轨 |
| GET | `/api/music/distribution/platforms` | 发行平台列表 |
| POST | `/api/music/distribution/upload` | 上传作品到发行平台 |
| GET | `/api/music/earnings` | 流媒体收益汇总 |
| POST | `/api/music/audio-fingerprint` | 音频指纹 (AcoustID) |

## Task 2: 音乐人前端

**Files:**
- `frontend/src/views/MusicianView.vue` - 新建
- `frontend/src/components/music/` - 新建目录
- `frontend/src/stores/useMusicStore.ts` - 新建
- `frontend/src/api/music.ts` - 新建

**音乐人专属过程阶段:**
```
作曲 → 编曲 → 录音 → 混音 → 母带 → ISRC登记 → 发行 → 收益追踪
```

**Layout:**
```
┌─────────────────────────────────────────────┐
│ 音乐人工作台                                  │
├─────────────────────────────────────────────┤
│ 🎵 专辑: 3  |  🎶 音轨: 24                   │
│ 📻 发行平台: 5  |  💰 本月流媒体: ¥1,200     │
├─────────────────────────────────────────────┤
│ [专辑] [ISRC] [Split Sheets] [发行] [收益]  │
├─────────────────────────────────────────────┤
│                                             │
│  ── 专辑列表 ──────────────────────────────  │
│  [专辑封面卡片网格]                           │
│  标题 | 类型 | 音轨数 | 发行状态 | 收益      │
│                                             │
└─────────────────────────────────────────────┘
```

- [ ] **Step 1:** 创建 MusicianView.vue 骨架
- [ ] **Step 2:** 创建 useMusicStore.ts
- [ ] **Step 3:** 创建 api/music.ts
- [ ] **Step 4:** 创建类型定义 frontend/src/types/music.ts

## Task 3: 音乐人子组件

**Files:**
- `frontend/src/components/music/AlbumPanel.vue` - 新建
- `frontend/src/components/music/ISRCManager.vue` - 新建
- `frontend/src/components/music/SplitSheetPanel.vue` - 新建
- `frontend/src/components/music/DistributionPanel.vue` - 新建
- `frontend/src/components/music/EarningsPanel.vue` - 新建

**AlbumPanel.vue:**
- 专辑创建/编辑表单
- 音轨列表 (拖拽排序)
- 封面上传
- 发行状态跟踪

**ISRCManager.vue:**
- ISRC 码列表
- 申请新 ISRC 码
- ISRC 批量分配

**SplitSheetPanel.vue:**
- 创建 Split Sheet
- 添加参与者 (姓名/角色/分成比例)
- 在线签署流程
- 分成比例自动校验 (总和=100%)

**DistributionPanel.vue:**
- 发行平台连接管理 (Spotify/Apple Music/DistroKid)
- 上传作品到各平台
- 发行状态跟踪

**EarningsPanel.vue:**
- 各平台收益汇总
- 月度/年度趋势图
- 分成计算 (基于 Split Sheet)

- [ ] **Step 1:** 实现 AlbumPanel.vue
- [ ] **Step 2:** 实现 ISRCManager.vue
- [ ] **Step 3:** 实现 SplitSheetPanel.vue
- [ ] **Step 4:** 实现 DistributionPanel.vue
- [ ] **Step 5:** 实现 EarningsPanel.vue

---

## 测试计划

- [ ] ISRC 码生成和验证测试
- [ ] Split Sheet 分成比例校验测试
- [ ] 专辑音轨排序测试
- [ ] 发行平台上传流程测试
- [ ] 收益汇总计算测试
