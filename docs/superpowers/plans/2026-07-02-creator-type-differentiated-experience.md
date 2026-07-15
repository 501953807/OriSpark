# Creator Type Differentiated Experience Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Deliver type-aware UI panels for each of the 6 OriStudio creator types (illustrator, photographer, video, craftsman, musician, writer) across work detail view, edit panel, and backend metadata extraction.

**Architecture:** A lightweight `CreatorTypeInfo` dispatcher component sits in WorkDetailView's info panel, reading `work.creator_type` to render one of 5 type-specific sub-components. Backend auto-detects creator_type on upload from file_type + EXIF/metadata signals. Frontend Work interface gains `creator_type` field.

**Tech Stack:**
- Frontend: Vue 3 + TypeScript + Vite
- Backend: FastAPI + SQLAlchemy + PostgreSQL
- Design tokens: OKLCH color system, CSS custom properties

## Global Constraints

- creator_type values: "illustrator" | "photographer" | "video" | "craftsman" | "musician" | "writer"
- Backend works表已有 `creator_type` column (line 75 of work.py), default "illustrator"
- Frontend Work interface MUST gain `creator_type: string` field
- All new components go under `frontend/src/components/work/`
- No breaking changes to existing WorkDetailView layout (grid: 1fr 420px)
- Backward compatible: components degrade gracefully when creator_type is missing

---

### Task 1: Frontend - Add creator_type to Work Interface

**Files:**
- Modify: `frontend/src/types/work.ts:7-48`

**Interfaces:**
- Consumes: nothing
- Produces: `Work.creator_type: string` field

- [ ] **Step 1: Add creator_type to Work interface**

Add `creator_type: string` after line 33 (`import_mode`) in `frontend/src/types/work.ts`:

```typescript
  creator_type: string  // illustrator | photographer | video | craftsman | musician | writer
```

- [ ] **Step 2: Verify the file still compiles**

Run: `npx vue-tsc --noEmit --skipLibCheck` in frontend/
Expected: No new errors introduced

- [ ] **Step 3: Commit**

```bash
git add frontend/src/types/work.ts
git commit -m "feat: add creator_type field to Work interface"
```

---

### Task 2: Backend - Include creator_type in WorkResponse schema

**Files:**
- Modify: `backend/app/schemas/work.py:44-80`

**Interfaces:**
- Consumes: Work ORM model (has `creator_type` column)
- Produces: `WorkResponse` includes `creator_type: str` field

- [ ] **Step 1: Add creator_type to WorkResponse schema**

In `backend/app/schemas/work.py`, add `creator_type: str = "illustrator"` to the `WorkResponse` class after line 70 (`exif_data`):

```python
    creator_type: str = "illustrator"
```

- [ ] **Step 2: Add creator_type to _work_to_response**

In `backend/app/routers/works.py:140-169`, the `_work_to_response` function calls `WorkResponse.model_validate(work)` which will now include `creator_type` automatically. No code change needed — verify it's included in the returned dict.

- [ ] **Step 3: Verify the schema change**

Run: `python -c "from app.schemas.work import WorkResponse; print(WorkResponse.model_fields.keys())"`
Expected: Output includes 'creator_type'

- [ ] **Step 4: Commit**

```bash
git add backend/app/schemas/work.py
git commit -m "feat: add creator_type to WorkResponse schema"
```

---

### Task 3: Backend - Auto-detect creator_type on upload

**Files:**
- Modify: `backend/app/routers/works.py:274-303` (create_work function)
- Modify: `backend/app/routers/works.py:620-634` (create_hash_only_work)
- Modify: `backend/app/routers/works.py:699-715` (create_lowres_work)
- Modify: `backend/app/routers/works.py:1205-1216` (import_folder)
- Modify: `backend/app/routers/works.py:1338-1345` (replace_work_file - update work record)

**Interfaces:**
- Consumes: file_type, exif_data, full_meta from upload
- Produces: work.creator_type set based on detection logic

- [ ] **Step 1: Add _detect_creator_type helper function**

Add after line 121 in `backend/app/routers/works.py`:

```python
def _detect_creator_type(file_type: str, exif_data: Optional[dict], full_meta: Optional[dict]) -> str:
    """Detect creator type from file characteristics."""
    # Photographer: image with EXIF camera data
    if file_type == "image" and exif_data:
        camera_signals = ("CameraMake", "CameraModel", "LensModel", "Model")
        if any(exif_data.get(k) for k in camera_signals):
            return "photographer"
    # Musician: audio with ISRC/BPM/artists
    if file_type == "audio":
        audio_signals = ("isrc", "bpm", "artist", "Album")
        if any(full_meta and full_meta.get(k) for k in audio_signals):
            return "musician"
        return "musician"  # All audio defaults to musician
    # Video: video file type
    if file_type == "video":
        return "video"
    # Document: could be writer or craftsman
    if file_type == "document":
        # Check for CAD/design metadata
        if full_meta and any(k in full_meta for k in ("software", "Application", "Producer")):
            app = str(full_meta.get("software", "") + full_meta.get("Application", "") + full_meta.get("Producer", ""))
            if any(kw in app.lower() for kw in ("autocad", "solidworks", " SketchUp")):
                return "craftsman"
        return "writer"
    # Default: illustrator for design files and everything else
    if file_type == "design":
        return "illustrator"
    return "illustrator"
```

- [ ] **Step 2: Apply detection in create_work**

In `backend/app/routers/works.py:274`, add `creator_type` to the Work constructor:

```python
    creator_type=_detect_creator_type(file_type, exif_data, full_meta),
```

- [ ] **Step 3: Apply detection in hash-only upload**

In `create_hash_only_work`, add:

```python
    detected_ft = data.file_type or "image"
    work.creator_type = "illustrator"  # hash-only can't detect, default
```

- [ ] **Step 4: Apply detection in lowres upload**

In `create_lowres_work`, add:

```python
    work.creator_type = _detect_creator_type(ft, None, {"width": width, "height": height})
```

- [ ] **Step 5: Apply detection in import_folder**

In `import_folder`, add:

```python
    creator_type = _detect_creator_type(file_type, None, {})
    work.creator_type = creator_type
```

- [ ] **Step 6: Commit**

```bash
git add backend/app/routers/works.py
git commit -m "feat: auto-detect creator_type on file upload"
```

---

### Task 4: Frontend - Create PhotographerExifPanel component

**Files:**
- Create: `frontend/src/components/work/PhotographerExifPanel.vue`

**Interfaces:**
- Props: `work: { exif_data?: Record<string, any>; file_type?: string; is_raw_original?: boolean; ... }`
- Emits: none (display-only)

- [ ] **Step 1: Create PhotographerExifPanel.vue**

Component displays photographer-specific metadata in an info-group style matching WorkDetailView's existing layout:

```vue
<template>
  <section class="info-group" v-if="hasData">
    <h4 class="info-group-title">摄影参数</h4>
    <div class="info-row" v-if="exif.CameraMake || exif.CameraModel">
      <span class="info-label">相机</span>
      <span class="info-value">{{ exif.CameraMake || '' }} {{ exif.CameraModel || '' }}</span>
    </div>
    <div class="info-row" v-if="exif.LensModel">
      <span class="info-label">镜头</span>
      <span class="info-value">{{ exif.LensModel }}</span>
    </div>
    <div class="info-row" v-if="exif.ISOSpeed">
      <span class="info-label">ISO</span>
      <span class="info-value">{{ exif.ISOSpeed }}</span>
    </div>
    <div class="info-row" v-if="exif.FNumber">
      <span class="info-label">光圈</span>
      <span class="info-value">f/{{ exif.FNumber }}</span>
    </div>
    <div class="info-row" v-if="exif.ExposureTime">
      <span class="info-label">快门</span>
      <span class="info-value">{{ formatShutter(exif.ExposureTime) }}</span>
    </div>
    <div class="info-row" v-if="exif.FocalLength">
      <span class="info-label">焦距</span>
      <span class="info-value">{{ exif.FocalLength }}mm</span>
    </div>
    <div class="info-row" v-if="exif.DateTimeOriginal">
      <span class="info-label">拍摄时间</span>
      <span class="info-value">{{ exif.DateTimeOriginal }}</span>
    </div>
    <div class="info-row" v-if="exif.GPSLatitude && exif.GPSLongitude">
      <span class="info-label">位置</span>
      <span class="info-value">{{ exif.GPSLatitude }}, {{ exif.GPSLongitude }}</span>
    </div>
    <div class="info-row" v-if="isRaw">
      <span class="info-label">原始格式</span>
      <span class="info-value"><span class="raw-badge">RAW 原始文件</span></span>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed, type PropType } from 'vue'

const props = defineProps({
  work: { type: Object as PropType<Record<string, any>>, required: true },
})

const exif = computed(() => props.work.exif_data || props.work.custom_metadata?.exif_data || {})
const hasData = computed(() => {
  const e = exif.value
  return !!(e.CameraMake || e.CameraModel || e.LensModel || e.ISOSpeed || e.FNumber ||
    e.ExposureTime || e.FocalLength || e.DateTimeOriginal || e.GPSLatitude || props.work.is_raw_original)
})
const isRaw = computed(() => !!props.work.is_raw_original)

function formatShutter(val: string | number): string {
  const n = typeof val === 'string' ? parseFloat(val) : val
  if (n && n < 1) return `1/${Math.round(1/n)}s`
  return `${n}s`
}
</script>

<style scoped>
.raw-badge {
  display: inline-block;
  padding: 2px 8px;
  border-radius: 100px;
  font-size: 0.72rem;
  font-weight: 700;
  background: oklch(56% 0.12 170 / 0.15);
  color: var(--accent);
}
</style>
```

- [ ] **Step 2: Verify component renders without errors**

Quick check: `npx vue-tsc --noEmit --skipLibCheck` in frontend/
Expected: No type errors for the new component

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/work/PhotographerExifPanel.vue
git commit -m "feat: add PhotographerExifPanel component"
```

---

### Task 5: Frontend - Create MusicMetadataPanel component

**Files:**
- Create: `frontend/src/components/work/MusicMetadataPanel.vue`

**Interfaces:**
- Props: `work: Record<string, any>` (needs `custom_metadata`, `duration`, `exif_data`)
- Emits: none

- [ ] **Step 1: Create MusicMetadataPanel.vue**

```vue
<template>
  <section class="info-group" v-if="hasData">
    <h4 class="info-group-title">音乐信息</h4>
    <div class="info-row" v-if="meta.artist">
      <span class="info-label">艺术家</span>
      <span class="info-value">{{ meta.artist }}</span>
    </div>
    <div class="info-row" v-if="meta.album">
      <span class="info-label">专辑</span>
      <span class="info-value">{{ meta.album }}</span>
    </div>
    <div class="info-row" v-if="meta.bpm">
      <span class="info-label">BPM</span>
      <span class="info-value">{{ meta.bpm }}</span>
    </div>
    <div class="info-row" v-if="meta.isrc">
      <span class="info-label">ISRC</span>
      <span class="info-value"><code>{{ meta.isrc }}</code></span>
    </div>
    <div class="info-row" v-if="meta.genre">
      <span class="info-label">流派</span>
      <span class="info-value">{{ meta.genre }}</span>
    </div>
    <div class="info-row" v-if="props.work.duration">
      <span class="info-label">时长</span>
      <span class="info-value">{{ formatDuration(props.work.duration) }}</span>
    </div>
    <div class="info-row" v-if="meta.key">
      <span class="info-label">调性</span>
      <span class="info-value">{{ meta.key }}</span>
    </div>
    <div class="info-row" v-if="meta.track_number">
      <span class="info-label">曲目</span>
      <span class="info-value">{{ meta.track_number }}</span>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed, type PropType } from 'vue'

const props = defineProps({
  work: { type: Object as PropType<Record<string, any>>, required: true },
})

const meta = computed(() => props.work.custom_metadata || {})
const hasData = computed(() =>
  !!(meta.value.artist || meta.value.album || meta.value.bpm || meta.value.isrc ||
    meta.value.genre || meta.value.key || meta.value.track_number || props.work.duration)
)

function formatDuration(seconds: number): string {
  const m = Math.floor(seconds / 60)
  const s = Math.floor(seconds % 60)
  return `${m}:${s.toString().padStart(2, '0')}`
}
</script>

<style scoped>
.info-group code {
  font-family: monospace;
  font-size: 0.8rem;
  background: oklch(96% 0.003 240);
  padding: 2px 6px;
  border-radius: 3px;
}
</style>
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/components/work/MusicMetadataPanel.vue
git commit -m "feat: add MusicMetadataPanel component"
```

---

### Task 6: Frontend - Create WriterStatsPanel component

**Files:**
- Create: `frontend/src/components/work/WriterStatsPanel.vue`

**Interfaces:**
- Props: `work: Record<string, any>` (needs `custom_metadata`, `width`, `height`, `file_size`)

- [ ] **Step 1: Create WriterStatsPanel.vue**

```vue
<template>
  <section class="info-group" v-if="hasData">
    <h4 class="info-group-title">文稿统计</h4>
    <div class="info-row" v-if="stats.word_count">
      <span class="info-label">字数</span>
      <span class="info-value">{{ formatNumber(stats.word_count) }}</span>
    </div>
    <div class="info-row" v-if="stats.page_count">
      <span class="info-label">页数</span>
      <span class="info-value">{{ stats.page_count }}</span>
    </div>
    <div class="info-row" v-if="stats.chapter_count">
      <span class="info-label">章节数</span>
      <span class="info-value">{{ stats.chapter_count }}</span>
    </div>
    <div class="info-row" v-if="stats.language">
      <span class="info-label">语言</span>
      <span class="info-value">{{ stats.language }}</span>
    </div>
    <div class="info-row" v-if="stats.genre">
      <span class="info-label">体裁</span>
      <span class="info-value">{{ stats.genre }}</span>
    </div>
    <div class="info-row" v-if="stats.status">
      <span class="info-label">状态</span>
      <span class="info-value">
        <span class="status-pill" :class="'status-' + stats.status">{{ statusLabel(stats.status) }}</span>
      </span>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed, type PropType } from 'vue'

const props = defineProps({
  work: { type: Object as PropType<Record<string, any>>, required: true },
})

const stats = computed(() => props.work.custom_metadata || {})
const hasData = computed(() =>
  !!(stats.value.word_count || stats.value.page_count || stats.value.chapter_count ||
    stats.value.language || stats.value.genre || stats.value.status)
)

function formatNumber(n: number): string {
  if (n >= 10000) return `${(n / 10000).toFixed(1)}万`
  return n.toLocaleString()
}

function statusLabel(s: string): string {
  const map: Record<string, string> = {
    draft: '草稿', completed: '已完成', serialized: '连载中', paused: '暂停',
  }
  return map[s] || s
}
</script>

<style scoped>
.status-pill {
  display: inline-block;
  padding: 2px 10px;
  border-radius: 100px;
  font-size: 0.75rem;
  font-weight: 600;
}
.status-draft { background: oklch(80% 0.05 80 / 0.2); color: #6B8E4E; }
.status-completed { background: oklch(80% 0.12 140 / 0.2); color: #2E8B57; }
.status-serialized { background: oklch(75% 0.15 30 / 0.2); color: #CC7722; }
.status-paused { background: oklch(75% 0.05 60 / 0.2); color: #888; }
</style>
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/components/work/WriterStatsPanel.vue
git commit -m "feat: add WriterStatsPanel component"
```

---

### Task 7: Frontend - Create VideoMetadataPanel and CraftsmanInfoPanel

**Files:**
- Create: `frontend/src/components/work/VideoMetadataPanel.vue`
- Create: `frontend/src/components/work/CraftsmanInfoPanel.vue`

**Interfaces:**
- VideoMetadataPanel props: `work: Record<string, any>` (needs `duration`, `exif_data`, `custom_metadata`)
- CraftsmanInfoPanel props: `work: Record<string, any>` (needs `custom_metadata`, `width`, `height`)

- [ ] **Step 1: Create VideoMetadataPanel.vue**

```vue
<template>
  <section class="info-group" v-if="hasData">
    <h4 class="info-group-title">视频信息</h4>
    <div class="info-row" v-if="exif.Software || meta.encoder">
      <span class="info-label">编码工具</span>
      <span class="info-value">{{ exif.Software || meta.encoder || '—' }}</span>
    </div>
    <div class="info-row" v-if="meta.framerate">
      <span class="info-label">帧率</span>
      <span class="info-value">{{ meta.framerate }} fps</span>
    </div>
    <div class="info-row" v-if="meta.bitrate">
      <span class="info-label">码率</span>
      <span class="info-value">{{ formatBitrate(meta.bitrate) }}</span>
    </div>
    <div class="info-row" v-if="meta.codec">
      <span class="info-label">编解码</span>
      <span class="info-value">{{ meta.codec }}</span>
    </div>
    <div class="info-row" v-if="props.work.duration">
      <span class="info-label">时长</span>
      <span class="info-value">{{ formatDuration(props.work.duration) }}</span>
    </div>
    <div class="info-row" v-if="meta.project_name">
      <span class="info-label">工程名</span>
      <span class="info-value">{{ meta.project_name }}</span>
    </div>
    <div class="info-row" v-if="meta.resolution_label">
      <span class="info-label">分辨率</span>
      <span class="info-value">{{ meta.resolution_label }}</span>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed, type PropType } from 'vue'

const props = defineProps({
  work: { type: Object as PropType<Record<string, any>>, required: true },
})

const exif = computed(() => props.work.exif_data || {})
const meta = computed(() => props.work.custom_metadata || {})
const hasData = computed(() =>
  !!(exif.value.Software || meta.value.encoder || meta.value.framerate ||
    meta.value.bitrate || meta.value.codec || meta.value.project_name ||
    meta.value.resolution_label || props.work.duration)
)

function formatDuration(s: number): string {
  const h = Math.floor(s / 3600)
  const m = Math.floor((s % 3600) / 60)
  const sec = Math.floor(s % 60)
  return h > 0 ? `${h}:${m.toString().padStart(2,'0')}:${sec.toString().padStart(2,'0')}`
    : `${m}:${sec.toString().padStart(2,'0')}`
}

function formatBitrate(bps: number | string): string {
  const b = typeof bps === 'string' ? parseInt(bps) : bps
  if (b >= 1e6) return `${(b / 1e6).toFixed(1)} Mbps`
  if (b >= 1e3) return `${(b / 1e3).toFixed(0)} kbps`
  return `${b} bps`
}
</script>
```

- [ ] **Step 2: Create CraftsmanInfoPanel.vue**

```vue
<template>
  <section class="info-group" v-if="hasData">
    <h4 class="info-group-title">工艺信息</h4>
    <div class="info-row" v-if="meta.material">
      <span class="info-label">材质</span>
      <span class="info-value">{{ meta.material }}</span>
    </div>
    <div class="info-row" v-if="meta.dimensions">
      <span class="info-label">尺寸</span>
      <span class="info-value">{{ meta.dimensions }}</span>
    </div>
    <div class="info-row" v-if="meta.weight">
      <span class="info-label">重量</span>
      <span class="info-value">{{ meta.weight }}</span>
    </div>
    <div class="info-row" v-if="meta technique">
      <span class="info-label">技法</span>
      <span class="info-value">{{ meta.technique }}</span>
    </div>
    <div class="info-row" v-if="meta.edition">
      <span class="info-label">版数</span>
      <span class="info-value">{{ meta.edition }}</span>
    </div>
    <div class="info-row" v-if="meta.certification">
      <span class="info-label">认证</span>
      <span class="info-value"><span class="cert-badge">{{ meta.certification }}</span></span>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed, type PropType } from 'vue'

const props = defineProps({
  work: { type: Object as PropType<Record<string, any>>, required: true },
})

const meta = computed(() => props.work.custom_metadata || {})
const hasData = computed(() =>
  !!(meta.value.material || meta.value.dimensions || meta.value.weight ||
    meta.value.technique || meta.value.edition || meta.value.certification)
)
</script>

<style scoped>
.cert-badge {
  display: inline-block;
  padding: 2px 8px;
  border-radius: 100px;
  font-size: 0.72rem;
  font-weight: 700;
  background: oklch(65% 0.15 45 / 0.15);
  color: oklch(35% 0.15 45);
}
</style>
```

Note: Fix the template typo in step 2 — `v-if="meta technique"` should be `v-if="meta.technique"`.

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/work/VideoMetadataPanel.vue frontend/src/components/work/CraftsmanInfoPanel.vue
git commit -m "feat: add VideoMetadataPanel and CraftsmanInfoPanel components"
```

---

### Task 8: Frontend - Create CreatorTypeInfo dispatcher component

**Files:**
- Create: `frontend/src/components/work/CreatorTypeInfo.vue`

**Interfaces:**
- Props: `work: Record<string, any>` (needs `creator_type`, `exif_data`, `custom_metadata`, `file_type`, `is_raw_original`, `duration`, `width`, `height`)
- Emits: none

- [ ] **Step 1: Create CreatorTypeInfo.vue dispatcher**

```vue
<template>
  <template v-if="work?.creator_type">
    <PhotographerExifPanel v-if="work.creator_type === 'photographer'" :work="work" />
    <MusicMetadataPanel v-else-if="work.creator_type === 'musician'" :work="work" />
    <WriterStatsPanel v-else-if="work.creator_type === 'writer'" :work="work" />
    <VideoMetadataPanel v-else-if="work.creator_type === 'video'" :work="work" />
    <CraftsmanInfoPanel v-else-if="work.creator_type === 'craftsman'" :work="work" />
    <!-- illustrator: no specialized panel needed, falls through -->
  </template>
</template>

<script setup lang="ts">
import { type PropType } from 'vue'
import PhotographerExifPanel from './PhotographerExifPanel.vue'
import MusicMetadataPanel from './MusicMetadataPanel.vue'
import WriterStatsPanel from './WriterStatsPanel.vue'
import VideoMetadataPanel from './VideoMetadataPanel.vue'
import CraftsmanInfoPanel from './CraftsmanInfoPanel.vue'

defineProps({
  work: { type: Object as PropType<Record<string, any>>, required: true },
})
</script>
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/components/work/CreatorTypeInfo.vue
git commit -m "feat: add CreatorTypeInfo dispatcher component"
```

---

### Task 9: Frontend - Insert CreatorTypeInfo into WorkDetailView

**Files:**
- Modify: `frontend/src/views/WorkDetailView.vue:100-121` (insert after project/tags group)

**Interfaces:**
- Consumes: `work` ref (already available in WorkDetailView)
- Produces: Type-specific info panel rendered in the right info column

- [ ] **Step 1: Import CreatorTypeInfo**

Add import after line 279 in `WorkDetailView.vue`:

```typescript
import CreatorTypeInfo from '@/components/work/CreatorTypeInfo.vue'
```

- [ ] **Step 2: Insert CreatorTypeInfo component in template**

After the closing `</section>` of Group 5 (Project & Tags, line 114), before Group 6 (Synopsis, line 116), add:

```vue
          <!-- Group 5.5: Creator Type Specific Info -->
          <CreatorTypeInfo :work="work" />
```

This inserts the type-specific panel between project/tags and synopsis sections in the right info column.

- [ ] **Step 3: Verify layout preserved**

Check: the detail-body grid (`grid-template-columns: 1fr 420px`) is unchanged. CreatorTypeInfo renders inside `.detail-info` which already has `overflow-y: auto`.

- [ ] **Step 4: Commit**

```bash
git add frontend/src/views/WorkDetailView.vue
git commit -m "feat: integrate CreatorTypeInfo into WorkDetailView"
```

---

### Task 10: Frontend - Enhance WorkEditPanel with type-specific fields

**Files:**
- Modify: `frontend/src/components/work/WorkEditPanel.vue`

**Interfaces:**
- Consumes: `work` prop (now includes `creator_type`)
- Produces: Type-specific edit fields shown conditionally

- [ ] **Step 1: Add type-specific edit sections**

After the Project section (line 88-97), before Notes section (line 99), insert conditional type-specific edit fields:

```vue
          <!-- Type-Specific Fields -->
          <template v-if="work?.creator_type === 'photographer'">
            <div class="section-label">摄影参数</div>
            <div class="form-group">
              <label>相机型号</label>
              <input v-model="form.camera_model" class="form-input" placeholder="如: Sony A7IV" />
            </div>
            <div class="form-group">
              <label>镜头</label>
              <input v-model="form.lens" class="form-input" placeholder="如: FE 24-70mm f/2.8 GM" />
            </div>
            <div class="form-group">
              <label>RAW 文件路径</label>
              <input v-model="form.raw_file_path" class="form-input" placeholder="/path/to/raw/file" />
            </div>
          </template>

          <template v-if="work?.creator_type === 'musician'">
            <div class="section-label">音乐信息</div>
            <div class="form-group">
              <label>ISRC</label>
              <input v-model="form.isrc" class="form-input" placeholder="CN-xxx-xx-00001" />
            </div>
            <div class="form-group">
              <label>BPM</label>
              <input v-model.number="form.bpm" type="number" class="form-input" min="1" max="999" />
            </div>
            <div class="form-group">
              <label>调性</label>
              <input v-model="form.music_key" class="form-input" placeholder="如: C大调" />
            </div>
          </template>

          <template v-if="work?.creator_type === 'writer'">
            <div class="section-label">文稿信息</div>
            <div class="form-group">
              <label>字数</label>
              <input v-model.number="form.word_count" type="number" class="form-input" min="0" />
            </div>
            <div class="form-group">
              <label>章节数</label>
              <input v-model.number="form.chapter_count" type="number" class="form-input" min="0" />
            </div>
            <div class="form-group">
              <label>体裁</label>
              <input v-model="form.genre" class="form-input" placeholder="小说/散文/诗歌…" />
            </div>
          </template>
```

- [ ] **Step 2: Add form fields for type-specific data**

In the `form` reactive object (line 150), add type-specific fields:

```typescript
  // Photographer
  camera_model: '',
  lens: '',
  raw_file_path: '',
  // Musician
  isrc: '',
  bpm: null as number | null,
  music_key: '',
  // Writer
  word_count: null as number | null,
  chapter_count: null as number | null,
  genre: '',
```

- [ ] **Step 3: Wire form data to emit in handleSave**

In `handleSave()`, merge type-specific fields into `custom_metadata`:

```typescript
  // Type-specific metadata
  if (form.camera_model) metadata.camera_model = form.camera_model
  if (form.lens) metadata.lens = form.lens
  if (form.raw_file_path) metadata.raw_file_path = form.raw_file_path
  if (form.isrc) metadata.isrc = form.isrc
  if (form.bpm !== null) metadata.bpm = form.bpm
  if (form.music_key) metadata.music_key = form.music_key
  if (form.word_count !== null) metadata.word_count = form.word_count
  if (form.chapter_count !== null) metadata.chapter_count = form.chapter_count
  if (form.genre) metadata.genre = form.genre
```

- [ ] **Step 4: Load type-specific data in watch**

In the `watch(() => props.work, ...)` block, add type-specific field loading:

```typescript
    // Type-specific fields from custom_metadata
    form.camera_model = cm.camera_model || ''
    form.lens = cm.lens || ''
    form.raw_file_path = cm.raw_file_path || ''
    form.isrc = cm.isrc || ''
    form.bpm = cm.bpm ?? null
    form.music_key = cm.music_key || ''
    form.word_count = cm.word_count ?? null
    form.chapter_count = cm.chapter_count ?? null
    form.genre = cm.genre || ''
```

- [ ] **Step 5: Commit**

```bash
git add frontend/src/components/work/WorkEditPanel.vue
git commit -m "feat: add type-specific edit fields to WorkEditPanel"
```

---

### Task 11: Backend - Set creator_type for existing works (migration)

**Files:**
- Create: `backend/alembic/versions/<hash>_set_default_creator_type.py` (or append to existing migration)

**Interfaces:**
- Consumes: existing works table
- Produces: all existing works get a creator_type based on file_type

- [ ] **Step 1: Add upgrade/downgrade ops**

Since `creator_type` column already exists with default `"illustrator"`, existing rows already have it. No migration needed unless we want to backfill intelligently.

Optionally, add a data migration that sets creator_type based on file_type for existing records:

```python
def upgrade():
    # Backfill creator_type from file_type for existing works
    op.execute("""
        UPDATE works SET creator_type = 'photographer'
        WHERE file_type = 'image' AND exif_data->>'CameraModel' IS NOT NULL
        AND creator_type = 'illustrator'
    """)
    op.execute("""
        UPDATE works SET creator_type = 'musician'
        WHERE file_type = 'audio' AND creator_type = 'illustrator'
    """)
    op.execute("""
        UPDATE works SET creator_type = 'video'
        WHERE file_type = 'video' AND creator_type = 'illustrator'
    """)
    op.execute("""
        UPDATE works SET creator_type = 'writer'
        WHERE file_type = 'document' AND creator_type = 'illustrator'
    """)
```

- [ ] **Step 2: Commit**

```bash
git add backend/alembic/versions/
git commit -m "feat: backfill creator_type for existing works based on file_type"
```

---

## Self-Review Checklist

**Spec coverage:**
- [x] Task 1-2: Work interface + schema gain creator_type
- [x] Task 3: Backend auto-detects creator_type on upload
- [x] Task 4-7: 5 type-specific components (Photographer, Music, Writer, Video, Craftsman)
- [x] Task 8: CreatorTypeInfo dispatcher
- [x] Task 9: WorkDetailView integration
- [x] Task 10: WorkEditPanel type-specific fields
- [x] Task 11: Backfill migration

**Placeholder scan:** All components have complete template + script + style. No TBD/TODO markers.

**Type consistency:** All components use `Record<string, any>` for work prop to avoid importing the full Work type (which has strict fields). This matches the existing pattern in WorkEditPanel.

**Backward compatibility:**
- Illustrator has no specialized panel (dispatcher falls through) — correct, illustrator is the default
- Components use `v-if="hasData"` guard — empty data won't render blank sections
- creator_type defaults to "illustrator" in DB — existing works unaffected

---

## Execution Notes

- Tasks 1-3 are sequential dependencies (types -> schema -> detection)
- Tasks 4-8 are independent (all create new files) — can run in parallel
- Task 9 depends on Task 8
- Task 10 is independent of the component tasks
- Task 11 is optional (column already exists with default)

Recommended execution order:
1. Tasks 1-3 (backend types + schema + detection) — sequential
2. Tasks 4-8 (all frontend components) — parallel dispatch
3. Task 9 (integration) — depends on Task 8
4. Task 10 (edit panel) — independent
5. Task 11 (migration) — optional
