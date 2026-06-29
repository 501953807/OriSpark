# OriStudio Creative Assets Module Redesign - Implementation Plan

## Overview

Seven targeted improvements to the creative assets (works) module. This plan lists exact files, components, data model changes, API additions, UI flows, and the recommended implementation order.

---

## Issue 1: Work-Project Relationship Management

### 1A. Detail Page - "所属项目" Section in Right Sidebar

**File:** `frontend/src/views/WorkDetailView.vue` (lines 76-94, the detail-sidebar div)

**Change:** Insert a new `ProjectInfoCard` between `FileInfoCard` and `StageProgress`.

**New component:** `frontend/src/components/work/ProjectInfoCard.vue`

```vue
<template>
  <div class="project-info-card card">
    <div class="card-header-row">
      <h3>📁 所属项目</h3>
      <button v-if="work?.project?.id" class="btn btn-ghost btn-sm" @click="showChange = true">更换</button>
    </div>
    <div v-if="work?.project?.name" class="project-display">
      <span class="project-name">{{ work.project.name }}</span>
      <span class="project-count">{{ work.project.work_count || 0 }} 个作品</span>
    </div>
    <div v-else class="project-none">未分配项目</div>

    <!-- Change project modal -->
    <div v-if="showChange" class="modal-overlay" @click.self="showChange = false">
      <div class="modal-card">
        <h3>更换项目</h3>
        <select v-model="selectedProject" class="form-input">
          <option :value="null">未分配</option>
          <option v-for="p in projects" :key="p.id" :value="p.id">
            {{ p.name }} ({{ p.work_count || 0 }})
          </option>
        </select>
        <div class="modal-footer">
          <button class="btn btn-secondary" @click="showChange = false">取消</button>
          <button class="btn btn-primary" @click="handleChangeProject">确认</button>
        </div>
      </div>
    </div>
  </div>
</template>
```

**Props:** Same interface as `ProjectDropdown` -- `work` object with `project_id` and `project`.

**Behavior:** Clicking "更换" opens a modal with project list. Selecting a project calls `worksApi.assignProject(workId, projectId)`.

### 1B. List Page - Batch Assign Projects

**File:** `frontend/src/views/WorksView.vue`

**Changes:**
1. Add a multi-select checkbox mode. When user selects multiple works (checkboxes on each card), show a batch toolbar.
2. Batch toolbar contains a project dropdown and "批量分配" button.
3. On submit, call `worksApi.batchEdit(selectedIds, { project_id: selectedProjectId })`.

**Implementation details:**

In `WorksView.vue` toolbar-actions area, add:
```vue
<div v-if="selectedWorks.length" class="batch-toolbar">
  <span>{{ selectedWorks.length }} 已选</span>
  <select v-model="batchProjectId" class="filter-select">
    <option :value="null">-- 分配项目 --</option>
    <option v-for="p in projects" :key="p.id" :value="p.id">{{ p.name }}</option>
  </select>
  <button class="btn btn-primary btn-sm" @click="handleBatchAssign">批量分配</button>
  <button class="btn btn-secondary btn-sm" @click="selectedWorks = []">取消</button>
</div>
```

Each work card gets a checkbox overlay in the top-left corner, only visible when in multi-select mode (triggered by holding Shift or a dedicated "多选" button).

**Store addition** in `useWorkStore`:
```ts
const selectedWorkIds = ref<string[]>([])
function toggleSelect(id: string) {
  const idx = selectedWorkIds.value.indexOf(id)
  if (idx >= 0) selectedWorkIds.value.splice(idx, 1)
  else selectedWorkIds.value.push(id)
}
function clearSelection() { selectedWorkIds.value = [] }
```

### 1C. Folder Import in Import Modal

**File:** `frontend/src/components/common/FileDropZone.vue`

**Change:** Add a "Folder Import" toggle/button below the existing drop zone.

```vue
<div class="folder-import-toggle">
  <button class="btn btn-ghost btn-sm" @click="enableFolderImport = !enableFolderImport">
    {{ enableFolderImport ? '切换为文件导入' : '文件夹导入' }}
  </button>
</div>
```

When `enableFolderImport` is true:
- Change the `<input>` to accept `webkitdirectory` attribute (HTML5 directory upload)
- The drop zone text changes to "拖拽文件夹到此处"
- Backend API already supports folder import; frontend just needs the input flag

**File:** `frontend/src/views/WorksView.vue` (import modal, line 163-178)

Pass the `enableFolderImport` flag to `FileDropZone` and append it to FormData:
```ts
fd.append('import_mode', enableFolderImport.value ? 'folder' : 'file')
```

---

## Issue 2: Per-Type Process Stages

### New file: `frontend/src/composables/useWorkStages.ts`

**Current state:** Only `ILLUSTRATION_STAGES` (7 stages) and `GENERIC_STAGES` (5 stages). `getStagesForFileType` maps `'image'` -> illustration, everything else -> generic.

**Changes:** Expand to 6 file types with distinct stage sets.

```ts
export interface StageOption {
  value: string
  label: string
  color: string
}

export const IMAGE_STAGES: StageOption[] = [
  { value: 'inspiration', label: '灵感', color: '#8B5CF6' },
  { value: 'sketch', label: '草图', color: '#EC4896' },
  { value: 'lineart', label: '线稿', color: '#F59E0B' },
  { value: 'coloring', label: '上色', color: '#EF4444' },
  { value: 'detail', label: '细节', color: '#10B981' },
  { value: 'final', label: '终稿', color: '#3B82F6' },
  { value: 'exports', label: '导出', color: '#6366F1' },
]

export const VIDEO_STAGES: StageOption[] = [
  { value: 'script', label: '脚本', color: '#8B5CF6' },
  { value: 'storyboard', label: '分镜', color: '#EC4896' },
  { value: 'roughcut', label: '粗剪', color: '#F59E0B' },
  { value: 'finecut', label: '精剪', color: '#EF4444' },
  { value: 'colorgrade', label: '调色', color: '#10B981' },
  { value: 'final', label: '成片', color: '#3B82F6' },
]

export const AUDIO_STAGES: StageOption[] = [
  { value: 'idea', label: '构思', color: '#8B5CF6' },
  { value: 'arrangement', label: '编曲', color: '#EC4896' },
  { value: 'recording', label: '录音', color: '#F59E0B' },
  { value: 'mixing', label: '混音', color: '#EF4444' },
  { value: 'mastering', label: '母带', color: '#10B981' },
  { value: 'release', label: '发行', color: '#3B82F6' },
]

export const DOCUMENT_STAGES: StageOption[] = [
  { value: 'outline', label: '大纲', color: '#8B5CF6' },
  { value: 'draft', label: '初稿', color: '#EC4896' },
  { value: 'revision', label: '修订', color: '#F59E0B' },
  { value: 'final', label: '定稿', color: '#EF4444' },
  { value: 'formatting', label: '排版', color: '#10B981' },
  { value: 'publish', label: '发布', color: '#3B82F6' },
]

export const DESIGN_STAGES: StageOption[] = [
  { value: 'concept', label: '概念', color: '#8B5CF6' },
  { value: 'modeling', label: '建模', color: '#EC4896' },
  { value: 'texturing', label: '贴图', color: '#F59E0B' },
  { value: 'rigging', label: '绑定', color: '#EF4444' },
  { value: 'animation', label: '动画', color: '#10B981' },
  { value: 'render', label: '渲染', color: '#3B82F6' },
  { value: 'final', label: '成品', color: '#6366F1' },
]

export const CODE_STAGES: StageOption[] = [
  { value: 'design', label: '设计', color: '#8B5CF6' },
  { value: 'prototype', label: '原型', color: '#EC4896' },
  { value: 'develop', label: '开发', color: '#F59E0B' },
  { value: 'test', label: '测试', color: '#EF4444' },
  { value: 'deploy', label: '部署', color: '#10B981' },
  { value: 'maintain', label: '维护', color: '#3B82F6' },
]

// Map file_type -> stages
const STAGE_MAP: Record<string, StageOption[]> = {
  image: IMAGE_STAGES,
  video: VIDEO_STAGES,
  audio: AUDIO_STAGES,
  document: DOCUMENT_STAGES,
  design: DESIGN_STAGES,
  code: CODE_STAGES,
}

export function getStagesForFileType(fileType: string): StageOption[] {
  return STAGE_MAP[fileType] || IMAGE_STAGES // fallback to image/default
}

export function getAllStages(): StageOption[] {
  // Flatten all unique stages across all types (used internally only)
  const seen = new Set<string>()
  const result: StageOption[] = []
  for (const stages of Object.values(STAGE_MAP)) {
    for (const s of stages) {
      if (!seen.has(s.value)) { seen.add(s.value); result.push(s) }
    }
  }
  return result
}

export function getStageColor(stage: string): string {
  for (const stages of Object.values(STAGE_MAP)) {
    const found = stages.find(s => s.value === stage)
    if (found) return found.color
  }
  return '#6B7280'
}

export function getStageIndex(stage: string, fileType: string): number {
  const stages = getStagesForFileType(fileType)
  return stages.findIndex(s => s.value === stage)
}

// Legacy aliases for backward compatibility
export const ILLUSTRATION_STAGES = IMAGE_STAGES
export const GENERIC_STAGES = IMAGE_STAGES // deprecated, kept for compat
```

**Files to update to use new stages:**

1. `frontend/src/components/work/StageProgress.vue` -- no logic change needed (already uses `getStagesForFileType`)
2. `frontend/src/components/work/StageSelector.vue` -- no logic change needed (already uses `getStagesForFileType`)
3. `frontend/src/components/work/MetadataCard.vue` -- update `getStageLabel` to cover all new stage values (lines 49-56)
4. `frontend/src/views/WorksView.vue` -- the "全部阶段" filter dropdown currently shows ALL stages concatenated. Per the requirement, stages should NOT appear in list-level filter. So remove the stage filter dropdown entirely from WorksView toolbar.

**Key decision:** Remove the stage filter select from `WorksView.vue` lines 16-19 and the associated `stageFilter` ref, `allStages`, `getStageLabel`, `handleStageFilter`. Stage management is detail-page only.

---

## Issue 3: Detail Page Timeline Component

### New file: `frontend/src/components/work/StageTimeline.vue`

**Purpose:** Replace the compact `StageProgress` card with a prominent, interactive timeline.

**Placement:** In `WorkDetailView.vue`, replace the `<StageProgress>` card (lines 81-84) with `<StageTimeline :work="work" @stage-change="handleStageChange" />`.

**Component spec:**

```vue
<template>
  <div class="stage-timeline">
    <div class="timeline-header">
      <h3>创作阶段</h3>
      <span class="current-badge" v-if="currentStageIndex >= 0">
        当前: {{ stages[currentStageIndex]?.label }}
      </span>
    </div>

    <!-- Horizontal timeline with clickable nodes -->
    <div class="timeline-track" ref="trackRef">
      <div
        v-for="(stage, i) in stages"
        :key="stage.value"
        class="timeline-node"
        :class="{
          'completed': i < currentStageIndex,
          'current': i === currentStageIndex,
          'future': i > currentStageIndex,
          'disabled': i > currentStageIndex + 1, // can only advance one step at a time
        }"
        @click="handleNodeClick(stage, i)"
      >
        <div class="node-dot" :style="{ '--stage-color': stage.color }">
          <span v-if="i < currentStageIndex" class="check-icon">✓</span>
        </div>
        <div class="node-label">{{ stage.label }}</div>
        <div class="node-tooltip" v-if="showTooltip && hoveredStage === stage.value">
          <div class="tooltip-actions">
            <button v-if="i <= currentStageIndex" @click.stop="advanceTo(i)">设为当前</button>
            <button @click.stop="createSnapshot(stage)">创建快照</button>
            <button @click.stop="editMetadata(stage)">编辑元数据</button>
          </div>
        </div>
      </div>
      <!-- Connectors between nodes -->
      <div
        v-for="i in stages.length - 1"
        :key="'conn-'+i"
        class="node-connector"
        :class="{ 'completed': i <= currentStageIndex }"
        :style="{ '--connector-color': stages[i-1]?.color }"
      />
    </div>

    <!-- Stage detail panel (appears when clicking a node) -->
    <div v-if="selectedStage" class="stage-detail-panel">
      <h4>{{ selectedStage.label }}</h4>
      <div class="detail-fields">
        <label>完成日期</label>
        <input type="date" v-model="detailForm.completionDate" />
        <label>备注</label>
        <textarea v-model="detailForm.notes" rows="2" />
        <label>关联文件</label>
        <input type="file" @change="handleFileUpload" />
      </div>
      <div class="detail-actions">
        <button class="btn btn-primary btn-sm" @click="saveStageDetail">保存</button>
        <button class="btn btn-ghost btn-sm" @click="selectedStage = null">关闭</button>
      </div>
    </div>
  </div>
</template>
```

**Props:**
- `work: Work` -- the work object
- `fileType: string` -- file type for stage lookup

**Events:**
- `stageChange(stage: StageOption)` -- emitted when user advances to a stage
- `snapshotCreated(stage: StageOption)` -- emitted when user creates a version snapshot from a stage node

**Behavior:**
- Nodes before current are completed (green checkmark)
- Current node pulses
- Next node is clickable (advance to it)
- Future nodes beyond next are dimmed/disabled
- Hovering a node shows tooltip with actions: set as current, create snapshot, edit metadata
- Clicking a node opens the detail panel below the timeline

**Styling:** Full-width component, not confined to sidebar. Should span the main content area width.

### Update WorkDetailView.vue

Replace lines 81-84:
```vue
<!-- OLD -->
<div v-if="work.current_stage" class="sidebar-card card">
  <h3>创作阶段</h3>
  <StageProgress :file-type="work.file_type" :current-stage="work.current_stage" />
</div>

<!-- NEW -->
<StageTimeline :work="work" @stage-change="handleStageAdvance" />
```

Add handler:
```ts
function handleStageAdvance(stage: string) {
  if (!work.value) return
  workStore.updateWork(work.value.id, { current_stage: stage })
  loadWork()
}
```

---

## Issue 4: Archive Tab Removal

**File:** `frontend/src/views/WorksView.vue`

**Changes:**
1. Remove `{ key: 'archived', label: '归档', ... }` from `statusTabs` (line 225)
2. Remove `status: 'archived'` from the `Work` type's status union if it exists (it does -- line 20 of `types/work.ts`)
3. Keep the `archived` status in the data model for backward compatibility (some existing records may have it), but stop exposing it in the UI

**types/work.ts line 20:** Keep `'archived'` in the union type but do not expose in UI. This avoids breaking existing data.

**WorksView.vue statusTabs change:**
```ts
// BEFORE
const statusTabs = ref([
  { key: 'active', label: '活跃', count: undefined },
  { key: 'trashed', label: '回收站', count: undefined },
  { key: 'archived', label: '归档', count: undefined },
])

// AFTER
const statusTabs = ref([
  { key: 'active', label: '活跃', count: undefined as number | undefined },
  { key: 'trashed', label: '回收站', count: undefined as number | undefined },
])
```

---

## Issue 5: Tag Management Entry Point

### New file: `frontend/src/components/work/TagManager.vue`

**Purpose:** Dedicated tag management component for the detail page sidebar.

```vue
<template>
  <div class="tag-manager card">
    <div class="card-header-row">
      <h3>🏷️ 标签管理</h3>
      <button class="btn btn-ghost btn-sm" @click="showAdd = true">+ 新建</button>
    </div>

    <!-- Tag list with counts -->
    <div class="tag-list">
      <div v-for="tagInfo in tagList" :key="tagInfo.tag" class="tag-row">
        <span class="tag-name">{{ tagInfo.tag }}</span>
        <span class="tag-count">{{ tagInfo.work_count }} 个作品</span>
        <div class="tag-actions">
          <button @click="editTag(tagInfo)" title="重命名">✏️</button>
          <button @click="deleteTag(tagInfo)" title="删除">🗑️</button>
        </div>
      </div>
    </div>

    <div v-if="!tagList.length" class="card-empty">暂无标签</div>

    <!-- Add/Edit modal -->
    <div v-if="showAdd || showEdit" class="modal-overlay" @click.self="closeModals">
      <div class="modal-card">
        <h3>{{ showEdit ? '编辑标签' : '新建标签' }}</h3>
        <input v-model="tagForm.name" class="form-input" placeholder="标签名称" />
        <div class="modal-footer">
          <button class="btn btn-secondary" @click="closeModals">取消</button>
          <button class="btn btn-primary" @click="showEdit ? handleEditTag() : handleAddTag()">
            {{ showEdit ? '保存' : '创建' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>
```

**API calls needed:**
- `GET /tags` -- list all tags with counts (may need backend enhancement)
- `POST /tags` -- create tag
- `PATCH /tags/:id` -- rename tag
- `DELETE /tags/:id` -- delete tag
- `GET /works?tag=:tagName` -- used to compute work_count per tag

**Integration in WorkDetailView.vue sidebar:**
Insert `<TagManager :work-id="work.id" />` after `MetadataCard` and before `VersionHistoryCard`.

**Also:** Keep the existing `TagInput` in `WorkEditPanel.vue` for per-work tag editing (they serve different entry points).

---

## Issue 6: Recycle Bin as Standalone Feature

### 6A. New Route

**File:** `frontend/src/router/index.ts`

Add:
```ts
{ path: 'recycle', name: 'recycle', component: () => import('@/views/RecycleBinView.vue') },
```

### 6B. New View

**File:** `frontend/src/views/RecycleBinView.vue`

Extract the trashed-works logic from `WorksView.vue` into a dedicated page. This page shows:
- List/grid view of trashed works
- Restore button per item
- Permanent delete button per item
- "Empty Trash" bulk action
- No status tabs (only trashed works)

**Source:** Reuse the grid/list rendering logic from `WorksView.vue` lines 83-153, but filter to `status: 'trashed'` only. Remove the tab-switching logic.

### 6C. Update Sidebar

**File:** `frontend/src/components/layout/AppSidebar.vue` (line 51-54)

Change:
```vue
<!-- BEFORE -->
<router-link to="/app/works?tab=trash" class="sb-link">
  <span class="sb-icon">🗑️</span>
  <span v-if="!isCollapsed">回收站</span>
</router-link>

<!-- AFTER -->
<router-link to="/app/recycle" class="sb-link">
  <span class="sb-icon">🗑️</span>
  <span v-if="!isCollapsed">回收站</span>
</router-link>
```

### 6D. Update WorksView

**File:** `frontend/src/views/WorksView.vue`

After removing the archive tab (Issue 4), the status tabs become just:
```
活跃 | 回收站
```

But since recycle bin is now standalone, remove the trashed tab entirely:
```ts
const statusTabs = ref([
  { key: 'active', label: '活跃', count: undefined as number | undefined },
])
```

Remove all trashed-specific rendering:
- Delete the `currentStatus === 'trashed'` conditional blocks
- Remove `handleRestore`, `handlePermanentDelete`, `handleEmptyTrash` functions
- Remove the `route.query.tab === 'trash'` initialization logic
- The view now only shows active works (no status tabs at all, or keep a single "全部" label)

**Decision:** With only one tab left, remove the tab bar entirely. Just show active works with the existing toolbar filters.

### 6E. Clean up WorksView route handling

Remove the `route.query.tab === 'trash'` check (lines 230-234).

---

## Issue 7: License Dropdown Redesign

### New file: `frontend/src/components/work/LicenseSelector.vue`

**Purpose:** Grouped license selector with tooltips and auto-rights toggles.

```vue
<template>
  <div class="license-selector">
    <div class="license-group" v-for="group in licenseGroups" :key="group.id">
      <div class="group-header">{{ group.label }}</div>
      <button
        v-for="opt in group.options"
        :key="opt.value"
        class="license-option"
        :class="{ selected: modelValue === opt.value }"
        @click="select(opt)"
        :title="opt.tooltip"
      >
        <span class="license-name">{{ opt.label }}</span>
        <span class="license-icon">{{ opt.icon }}</span>
      </button>
    </div>

    <!-- Rights toggles (auto-populated) -->
    <div v-if="selectedLicense" class="rights-toggles">
      <label class="checkbox-label">
        <input type="checkbox" v-model="form.allow_reproduction" />
        允许复制
      </label>
      <label class="checkbox-label">
        <input type="checkbox" v-model="form.allow_derivatives" />
        允许改编
      </label>
      <label class="checkbox-label">
        <input type="checkbox" v-model="form.allow_commercial" />
        允许商用
      </label>
    </div>
  </div>
</template>
```

**License groups data:**

```ts
const licenseGroups = [
  {
    id: 'cc',
    label: '知识共享 (Creative Commons)',
    options: [
      { value: 'CC BY 4.0', label: 'CC BY 4.0', icon: '📢', tooltip: '署名 -- 必须署名原作者，可商用，可修改' },
      { value: 'CC BY-SA 4.0', label: 'CC BY-SA 4.0', icon: '🔄', tooltip: '署名-相同方式共享 -- 衍生作品必须使用相同许可证' },
      { value: 'CC BY-NC 4.0', label: 'CC BY-NC 4.0', icon: '🚫', tooltip: '署名-非商用 -- 不可用于商业用途' },
      { value: 'CC BY-ND 4.0', label: 'CC BY-ND 4.0', icon: '🔒', tooltip: '署名-禁止改编 -- 可商用但不得修改原作' },
      { value: 'CC BY-NC-SA 4.0', label: 'CC BY-NC-SA 4.0', icon: '🚫🔄', tooltip: '署名-非商用-相同方式共享' },
      { value: 'CC BY-NC-ND 4.0', label: 'CC BY-NC-ND 4.0', icon: '🚫🔒', tooltip: '署名-非商用-禁止改编 -- 最限制的知识共享协议' },
      { value: 'CC0 1.0', label: 'CC0 1.0', icon: '🌍', tooltip: '公共领域贡献 -- 放弃所有权利，任何人都可自由使用' },
    ],
  },
  {
    id: 'public',
    label: '公共领域',
    options: [
      { value: 'Public Domain', label: '公共领域', icon: '🏛️', tooltip: '无版权保护，任何人都可自由使用' },
    ],
  },
  {
    id: 'reserved',
    label: '保留所有权利',
    options: [
      { value: 'All Rights Reserved', label: '保留所有权利', icon: '©', tooltip: '默认版权 -- 未经许可不得使用、复制或修改' },
    ],
  },
  {
    id: 'custom',
    label: '自定义',
    options: [
      { value: 'Custom', label: '自定义许可证', icon: '✏️', tooltip: '自定义条款，请在下方填写具体条件' },
    ],
  },
]
```

**Auto-rights logic:**

```ts
function select(opt: LicenseOption) {
  emit('update:modelValue', opt.value)

  // Auto-set rights toggles based on license
  const defaults: Record<string, { reproduction: boolean, derivatives: boolean, commercial: boolean }> = {
    'CC BY 4.0': { reproduction: true, derivatives: true, commercial: true },
    'CC BY-SA 4.0': { reproduction: true, derivatives: true, commercial: true },
    'CC BY-NC 4.0': { reproduction: true, derivatives: true, commercial: false },
    'CC BY-ND 4.0': { reproduction: true, derivatives: false, commercial: true },
    'CC BY-NC-SA 4.0': { reproduction: true, derivatives: true, commercial: false },
    'CC BY-NC-ND 4.0': { reproduction: true, derivatives: false, commercial: false },
    'CC0 1.0': { reproduction: true, derivatives: true, commercial: true },
    'All Rights Reserved': { reproduction: false, derivatives: false, commercial: false },
    'Public Domain': { reproduction: true, derivatives: true, commercial: true },
    'Custom': { reproduction: false, derivatives: false, commercial: false },
  }

  const d = defaults[opt.value]
  if (d) {
    form.allow_reproduction = d.reproduction
    form.allow_derivatives = d.derivatives
    form.allow_commercial = d.commercial
  }
}
```

### Update WorkEditPanel.vue

Replace lines 48-60 (the flat license `<select>`) with:
```vue
<LicenseSelector v-model="form.license_type" @update:modelValue="onLicenseChange" />
```

### Update WorksView.vue License Filter

Replace the flat license dropdown (lines 20-28) with a grouped version. Since `<select>` doesn't support optgroups well in all browsers, use a custom dropdown component `GroupedFilter.vue` or keep the `<select>` but use the grouped `LicenseSelector` as the filter component.

**API client update** in `api/works.ts`: The `license_type` filter parameter already exists and works. No backend changes needed for filtering -- the grouped display is purely frontend.

---

## Implementation Order

### Phase 1: Foundation (stages + types)
1. **`useWorkStages.ts`** -- Rewrite with 6 type-specific stage sets
2. **`MetadataCard.vue`** -- Update `getStageLabel` to cover all new stage values
3. **`StageProgress.vue`**, **`StageSelector.vue`** -- Verify they still work (they use `getStagesForFileType`, no changes needed)

### Phase 2: Detail page enhancements
4. **`ProjectInfoCard.vue`** (new) -- Insert into `WorkDetailView.vue` sidebar
5. **`StageTimeline.vue`** (new) -- Replace `StageProgress` card in `WorkDetailView.vue`
6. **`TagManager.vue`** (new) -- Insert into `WorkDetailView.vue` sidebar
7. **`LicenseSelector.vue`** (new) -- Replace license select in `WorkEditPanel.vue`

### Phase 3: List page changes
8. **`WorksView.vue`** -- Remove archive tab, remove stage filter, remove status tabs entirely, simplify to single-view
9. **`RecycleBinView.vue`** (new) -- Extract trashed-works logic from WorksView
10. **`AppSidebar.vue`** -- Update recycle bin link to `/app/recycle`
11. **`router/index.ts`** -- Add `/app/recycle` route

### Phase 4: Batch operations and import
12. **`useWorkStore.ts`** -- Add `selectedWorkIds` and batch selection methods
13. **`WorksView.vue`** -- Add multi-select checkboxes + batch project assignment toolbar
14. **`FileDropZone.vue`** -- Add folder import toggle (`webkitdirectory`)

### Phase 5: Cleanup
15. **`useWorkStages.ts`** -- Remove `GENERIC_STAGES` export (keep as alias only for backward compat)
16. **`WorksView.vue`** -- Remove `stageFilter`, `allStages`, `getStageLabel`, `handleStageFilter`
17. **`types/work.ts`** -- Keep `archived` in status union for data compat, but it is no longer used in UI

---

## Files Summary

### New files (4)
- `frontend/src/components/work/StageTimeline.vue`
- `frontend/src/components/work/ProjectInfoCard.vue`
- `frontend/src/components/work/TagManager.vue`
- `frontend/src/components/work/LicenseSelector.vue`
- `frontend/src/views/RecycleBinView.vue`

### Modified files (9)
- `frontend/src/composables/useWorkStages.ts` -- Expand stages
- `frontend/src/views/WorkDetailView.vue` -- Insert new components, replace StageProgress
- `frontend/src/views/WorksView.vue` -- Remove archive/trash tabs, remove stage filter, add batch selection
- `frontend/src/components/work/WorkEditPanel.vue` -- Replace license select with LicenseSelector
- `frontend/src/components/work/MetadataCard.vue` -- Expand stage labels
- `frontend/src/components/layout/AppSidebar.vue` -- Update recycle bin link
- `frontend/src/router/index.ts` -- Add recycle route
- `frontend/src/stores/useWorkStore.ts` -- Add batch selection state
- `frontend/src/components/common/FileDropZone.vue` -- Add folder import toggle
- `frontend/src/api/works.ts` -- No changes needed (batch-edit API already exists)

### No changes needed
- `StageProgress.vue` -- Will be replaced by StageTimeline
- `StageSelector.vue` -- Already uses `getStagesForFileType`, works with expanded stages
- `ProjectDropdown.vue` -- Already functional, reused in new ProjectInfoCard
- `TagInput.vue` -- Kept for edit panel; TagManager is a separate entry point
- `VersionHistoryCard.vue` -- Unchanged
- `types/work.ts` -- archived kept in union for backward compat
