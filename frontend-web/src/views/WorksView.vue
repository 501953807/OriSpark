<template>
  <div class="works-view">
    <!-- Toolbar -->
    <div class="works-toolbar">
      <SearchBar v-model="searchQuery" @search="handleSearch" />
      <div class="toolbar-actions">
        <select v-model="typeFilter" class="filter-select" @change="handleTypeFilter">
          <option value="">全部类型</option>
          <option value="image">🖼️ 图片</option>
          <option value="audio">🎵 音频</option>
          <option value="video">🎬 视频</option>
          <option value="document">📄 文档</option>
          <option value="design">🎨 设计</option>
          <option value="code">💻 代码</option>
        </select>
        <select v-model="licenseFilter" class="filter-select" @change="handleLicenseFilter">
          <option value="">全部许可证</option>
          <optgroup label="知识共享">
            <option value="CC BY 4.0">CC BY 4.0</option>
            <option value="CC BY-SA 4.0">CC BY-SA 4.0</option>
            <option value="CC BY-NC 4.0">CC BY-NC 4.0</option>
            <option value="CC BY-ND 4.0">CC BY-ND 4.0</option>
            <option value="CC BY-NC-SA 4.0">CC BY-NC-SA 4.0</option>
            <option value="CC BY-NC-ND 4.0">CC BY-NC-ND 4.0</option>
            <option value="CC0 1.0">CC0 1.0</option>
          </optgroup>
          <optgroup label="其他">
            <option value="All Rights Reserved">All Rights Reserved</option>
            <option value="Public Domain">Public Domain</option>
            <option value="Custom">自定义</option>
          </optgroup>
        </select>
        <select v-model="projectFilter" class="filter-select" @change="handleProjectFilter">
          <option value="">📁 全部项目</option>
          <option v-for="p in projects" :key="p.id" :value="p.id">{{ p.name }} ({{ p.work_count || 0 }})</option>
        </select>
        <button class="btn btn-secondary" @click="viewMode = viewMode === 'grid' ? 'list' : 'grid'">
          {{ viewMode === 'grid' ? '📋' : '🔲' }}
        </button>
        <button class="btn btn-primary" @click="showImportModal = true">
          📤 导入作品
        </button>
      </div>
    </div>

    <!-- Floating batch toolbar -->
    <Teleport to="body">
      <div v-if="selectionCount > 0" class="floating-batch-bar">
        <div class="batch-inner">
          <label class="batch-select-all">
            <input type="checkbox" :checked="isPageAllSelected && selectionCount === filteredWorksCount && filteredWorksCount > 0" @change="toggleSelectPage" />
            <span>本页全选</span>
          </label>
          <span class="batch-count">{{ selectionCount }} 已选</span>
          <div class="batch-actions">
            <select v-model="batchProjectId" class="batch-project-select" title="批量分配项目">
              <option :value="null">📁 分配项目</option>
              <option v-for="p in projects" :key="p.id" :value="p.id">{{ p.name }}</option>
            </select>
            <button class="btn btn-secondary btn-sm" @click="handleBatchAssign" :disabled="!batchProjectId">确认分配</button>
            <button class="btn btn-primary btn-sm" @click="showBatchEdit = true">批量编辑</button>
            <button class="btn btn-danger btn-sm" @click="handleBatchDelete">批量删除</button>
            <button class="btn btn-secondary btn-sm" @click="selectAllPage = !selectAllPage">
              {{ selectAllPage ? '取消全选' : '全选本页' }}
            </button>
          </div>
          <button class="batch-dismiss" @click="clearSelection" title="取消选择">&times;</button>
        </div>
      </div>
    </Teleport>

    <!-- Stats bar -->
    <div class="works-stats">
      <span>共 {{ workStore.total }} 个作品</span>
      <span class="works-stats-tags">
        <span v-if="typeFilter" class="filter-chip">{{ typeFilter }} <button @click="typeFilter = ''; handleTypeFilter()">×</button></span>
        <span v-if="licenseFilter" class="filter-chip">{{ licenseFilter }} <button @click="licenseFilter = ''; handleLicenseFilter()">×</button></span>
        <span v-if="projectFilter" class="filter-chip">📁 {{ projects.find(p => p.id === projectFilter)?.name || projectFilter }} <button @click="projectFilter = ''; handleProjectFilter()">×</button></span>
        <span v-if="searchQuery" class="filter-chip">"{{ searchQuery }}" <button @click="searchQuery = ''; handleSearch('')">×</button></span>
      </span>
    </div>

    <!-- Loading -->
    <LoadingSpinner v-if="workStore.loading" text="加载中..." />

    <!-- Empty -->
    <EmptyState
      v-else-if="workStore.works.length === 0"
      icon="🎨"
      title="还没有作品"
      description="导入你的第一个作品开始创作之旅吧"
    >
      <button class="btn btn-primary" style="margin-top:16px" @click="showImportModal = true">📤 导入作品</button>
    </EmptyState>

    <!-- Grid view -->
    <div v-else-if="viewMode === 'grid'" class="works-grid">
      <div
        v-for="work in workStore.works"
        :key="work.id"
        class="work-grid-card card"
        :class="{ selected: selectedIdSet.has(work.id) }"
        @click="!selectedIdSet.has(work.id) && $router.push(`/app/works/${work.id}`)"
      >
        <!-- Selection checkbox -->
        <div class="card-checkbox" @click.stop>
          <input type="checkbox" :checked="selectedIdSet.has(work.id)" @change="toggleSelect(work.id)" />
        </div>
        <div class="card-thumb">
          <LazyImage v-if="work.thumbnail_url" :src="work.thumbnail_url" :alt="work.title" />
          <div v-else class="card-thumb-placeholder">
            <span class="card-thumb-icon">{{ fileTypeEmoji[work.file_type] || '📄' }}</span>
          </div>
          <div class="card-type-badge">{{ work.file_extension.toUpperCase() }}</div>
          <!-- Project badge -->
          <div v-if="work.project?.name" class="card-project-badge">📁 {{ truncate(work.project.name, 6) }}</div>
          <!-- Stage badge -->
          <div v-if="work.current_stage" class="card-stage-badge" :style="{ borderColor: getStageColor(work.current_stage) }">
            {{ getStageLabel(work.current_stage) }}
          </div>
          <div v-if="work.is_verified" class="card-verified">🔒 已存证</div>
          <div v-else class="card-hash-ready">📌 待存证</div>
        </div>
        <div class="card-info">
          <div class="card-title">{{ work.title }}</div>
          <div class="card-date">{{ work.imported_at?.slice(0, 10) }}</div>
        </div>
      </div>
    </div>

    <!-- List view (virtual scroll) -->
    <div v-else class="works-list-container" ref="listContainerRef">
      <div class="works-list-scroll" :style="{ height: totalListHeight + 'px' }">
        <div class="works-list-content" :style="{ transform: `translateY(${listOffsetY}px)` }">
          <div
            v-for="work in visibleListWorks"
            :key="work.id"
            class="work-list-row"
            :class="{ selected: selectedIdSet.has(work.id) }"
            @click="!selectedIdSet.has(work.id) && $router.push(`/app/works/${work.id}`)"
          >
            <!-- Selection checkbox -->
            <div class="list-checkbox" @click.stop>
              <input type="checkbox" :checked="selectedIdSet.has(work.id)" @change="toggleSelect(work.id)" />
            </div>
            <div class="list-thumb">
              <img v-if="work.thumbnail_url" :src="work.thumbnail_url" :alt="work.title" loading="lazy" />
              <span v-else>{{ fileTypeEmoji[work.file_type] || '📄' }}</span>
            </div>
            <div class="list-info">
              <div class="list-title">{{ work.title }}</div>
              <div class="list-meta">
                {{ work.file_type }}
                <span v-if="work.project?.name"> · 📁 {{ work.project.name }}</span>
                <span v-if="work.current_stage"> · {{ getStageLabel(work.current_stage) }}</span>
                · {{ formatFileSize(work.file_size) }}
                · {{ work.imported_at?.slice(0, 10) }}
              </div>
            </div>
            <StatusBadge :status="work.is_verified ? 'confirmed' : 'draft'" :labels="{ confirmed: '已存证', draft: '待存证' }" :variants="{ confirmed: 'success', draft: 'info' }" />
            <div class="list-hash" :title="work.sha256 || ''" v-if="work.is_verified">{{ work.sha256?.slice(0, 8) || '' }}</div>
            <div class="list-hash muted" v-else>—</div>
            <button class="btn-ghost-small" @click.stop="openEdit(work)">✏️</button>
          </div>
        </div>
      </div>
    </div>

    <!-- Pagination -->
    <div v-if="workStore.total > 20" class="pagination">
      <button :disabled="(workStore.filters.page || 1) <= 1" @click="workStore.setPage((workStore.filters.page || 1) - 1)">‹ 上一页</button>
      <span>{{ workStore.filters.page || 1 }} / {{ Math.ceil(workStore.total / (workStore.filters.page_size || 20)) }}</span>
      <button :disabled="(workStore.filters.page || 1) >= Math.ceil(workStore.total / (workStore.filters.page_size || 20))" @click="workStore.setPage((workStore.filters.page || 1) + 1)">下一页 ›</button>
    </div>

    <!-- Import modal -->
    <div v-if="showImportModal" class="modal-overlay" @click.self="showImportModal = false">
      <div class="modal-card animate-scale-in">
        <div class="modal-header">
          <h3>导入作品</h3>
          <button class="modal-close-btn" @click="showImportModal = false">×</button>
        </div>
        <FileDropZone @upload="handleUpload" />
        <div class="import-options">
          <label class="checkbox-label">
            <input type="checkbox" v-model="allowDuplicate" />
            允许重复导入（同文件可添加多次，用于二次/三次导入）
          </label>
        </div>
        <div v-if="uploading" class="uploading-hint">正在导入...</div>
      </div>
    </div>

    <!-- Edit panel (slide-in) -->
    <WorkEditPanel
      :visible="!!editingWork"
      :work="editingWork"
      @close="closeEdit"
      @save="handleSave"
      @delete="handleDelete"
    />

    <!-- Batch edit dialog -->
    <BatchEditDialog
      :visible="showBatchEdit"
      :work-ids="selectedIds"
      @close="showBatchEdit = false"
      @saved="onBatchSaved"
    />

    <!-- Batch delete confirmation -->
    <div v-if="showBatchDeleteConfirm" class="modal-overlay">
      <div class="modal-card animate-scale-in" style="max-width:420px">
        <div class="modal-header">
          <h3>确认批量删除</h3>
          <button class="modal-close-btn" @click="showBatchDeleteConfirm = false">&times;</button>
        </div>
        <p class="delete-confirm-text">
          确定要删除选中的 <strong>{{ selectedIds.length }}</strong> 个作品吗？
          此操作不可恢复，作品将移入回收站。
        </p>
        <div class="modal-footer-actions">
          <button class="btn btn-secondary" @click="showBatchDeleteConfirm = false">取消</button>
          <button class="btn btn-danger" :disabled="batchDeleting" @click="confirmBatchDelete">
            {{ batchDeleting ? '删除中…' : '确认删除' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, nextTick, watch } from 'vue'
import SearchBar from '@/components/common/SearchBar.vue'
import FileDropZone from '@/components/common/FileDropZone.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'
import LazyImage from '@/components/common/LazyImage.vue'
import WorkEditPanel from '@/components/work/WorkEditPanel.vue'
import BatchEditDialog from '@/components/work/BatchEditDialog.vue'
import { useWorkStore } from '@/stores/useWorkStore'
import { worksApi } from '@/api/works'
import { getStageColor, getAllStages } from '@/composables/useWorkStages'
import type { Work } from '@/types/work'

const workStore = useWorkStore()

const searchQuery = ref('')
const typeFilter = ref('')
const licenseFilter = ref('')
const projectFilter = ref('')
const projects = ref<any[]>([])
const viewMode = ref<'grid' | 'list'>('grid')
const showImportModal = ref(false)
const uploading = ref(false)
const allowDuplicate = ref(false)
const editingWork = ref<Work | null>(null)

// Batch selection state
const selectedIds = ref<string[]>([])
const selectAllPage = ref(false)
const showBatchEdit = ref(false)
const showBatchDeleteConfirm = ref(false)
const batchDeleting = ref(false)
const batchProjectId = ref<string | null>(null)

// Whether all items on the current page are selected
const isPageAllSelected = computed(() => {
  if (filteredWorksCount.value === 0) return false
  const pageIds = workStore.works.map(w => w.id)
  return pageIds.every(id => selectedIds.value.includes(id))
})

const allStages = getAllStages()

const fileTypeEmoji: Record<string, string> = {
  image: '🖼️', audio: '🎵', video: '🎬',
  document: '📄', design: '🎨', code: '💻',
}

// Count of works currently displayed (after filters + pagination)
const filteredWorksCount = computed(() => workStore.works.length)

// Which IDs are currently selected
const selectedIdSet = computed(() => new Set(selectedIds.value))

function truncate(str: string, maxLen: number): string {
  return str.length > maxLen ? str.slice(0, maxLen) + '…' : str
}

function getStageLabel(stage: string): string {
  const found = allStages.find(s => s.value === stage)
  return found?.label || stage
}

function handleSearch(val: string) {
  workStore.setFilter('search', val || undefined)
}

function handleTypeFilter() {
  workStore.setFilter('file_type', typeFilter.value || undefined)
}

function handleLicenseFilter() {
  workStore.setFilter('license_type', licenseFilter.value || undefined)
}

function handleProjectFilter() {
  workStore.setFilter('project_id', projectFilter.value || undefined)
}

const selectionCount = computed(() => selectedIds.value.length)

function isSelected(id: string): boolean {
  return selectedIds.value.includes(id)
}

function toggleSelect(id: string) {
  const idx = selectedIds.value.indexOf(id)
  if (idx >= 0) selectedIds.value.splice(idx, 1)
  else selectedIds.value.push(id)
}

function toggleSelectPage() {
  const pageIds = workStore.works.map(w => w.id)
  const allSelected = pageIds.every(id => selectedIds.value.includes(id))
  if (allSelected) {
    selectedIds.value = selectedIds.value.filter(id => !pageIds.includes(id))
  } else {
    for (const id of pageIds) {
      if (!selectedIds.value.includes(id)) {
        selectedIds.value.push(id)
      }
    }
  }
}

function clearSelection() {
  selectedIds.value = []
  selectAllPage.value = false
}

async function handleBatchAssign() {
  if (selectedIds.value.length === 0) return
  try {
    await worksApi.batchEdit(selectedIds.value, { project_id: batchProjectId.value })
    ;(window as any).$toast?.show(`已将 ${selectedIds.value.length} 个作品分配到项目`, 'success')
    clearSelection()
    await workStore.fetchWorks()
  } catch {
    ;(window as any).$toast?.show('批量分配失败', 'error')
  }
}

async function handleBatchDelete() {
  if (selectedIds.value.length === 0) return
  showBatchDeleteConfirm.value = true
}

async function confirmBatchDelete() {
  batchDeleting.value = true
  try {
    await worksApi.batchDelete(selectedIds.value)
    ;(window as any).$toast?.show(
      `${selectedIds.value.length} 个作品已移入回收站`,
      'info',
    )
    clearSelection()
    await workStore.fetchWorks()
  } catch {
    ;(window as any).$toast?.show('批量删除失败', 'error')
  } finally {
    batchDeleting.value = false
    showBatchDeleteConfirm.value = false
  }
}

function onBatchSaved() {
  clearSelection()
}

async function loadProjects() {
  try {
    const res = await worksApi.listProjects()
    projects.value = res.data.data || []
  } catch { projects.value = [] }
}

async function handleUpload(files: File[]) {
  uploading.value = true
  try {
    for (const file of files) {
      const fd = new FormData()
      fd.append('file', file)
      fd.append('title', file.name.replace(/\.[^/.]+$/, ''))
      if (allowDuplicate.value) {
        fd.append('allow_duplicate', 'true')
      }
      await workStore.uploadWork(fd)
    }
    showImportModal.value = false
    allowDuplicate.value = false
    ;(window as any).$toast?.show(`成功导入 ${files.length} 个文件`, 'success')
  } catch {
    ;(window as any).$toast?.show('导入失败', 'error')
  } finally {
    uploading.value = false
  }
}

function openEdit(work: Work) {
  editingWork.value = work
}

function closeEdit() {
  editingWork.value = null
}

async function handleSave(data: any) {
  if (!editingWork.value) return
  const tags = data.tagsStr.split(',').map((t: string) => t.trim()).filter(Boolean)
  await workStore.updateWork(editingWork.value.id, {
    title: data.title,
    description: data.description,
    synopsis: data.synopsis,
    completion_date: data.completion_date,
    current_stage: data.current_stage,
    copyright_year: data.copyright_year,
    license_type: data.license_type,
    tags,
    project_id: data.project_id || null,
    rights: data.rights,
    custom_metadata: data.custom_metadata,
  } as any)
  closeEdit()
  ;(window as any).$toast?.show('作品已更新', 'success')
}

async function handleDelete() {
  if (!editingWork.value) return
  if (!confirm(`确定删除"${editingWork.value.title}"？作品将被移入回收站。`)) return
  await workStore.deleteWork(editingWork.value.id)
  closeEdit()
  ;(window as any).$toast?.show('作品已移入回收站', 'info')
}

function formatFileSize(bytes: number): string {
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
}

// ─── Virtual scroll for list view ───
const LIST_ITEM_HEIGHT = 68
const LIST_OVERSCAN = 8

const listContainerRef = ref<HTMLElement | null>(null)
const listScrollTop = ref(0)
const listContainerHeight = ref(600)

const totalListHeight = computed(() => workStore.works.length * LIST_ITEM_HEIGHT)

const startIndex = computed(() => Math.max(0, Math.floor(listScrollTop.value / LIST_ITEM_HEIGHT) - LIST_OVERSCAN))

const endIndex = computed(() => Math.min(
  workStore.works.length,
  Math.ceil((listScrollTop.value + listContainerHeight.value) / LIST_ITEM_HEIGHT) + LIST_OVERSCAN,
))

const visibleListWorks = computed(() => workStore.works.slice(startIndex.value, endIndex.value))

const listOffsetY = computed(() => startIndex.value * LIST_ITEM_HEIGHT)

let listResizeObs: ResizeObserver | null = null

function onListScroll(event: Event) {
  const target = event.target as HTMLElement
  listScrollTop.value = target.scrollTop
}

function setupListVirtualScroll() {
  const el = listContainerRef.value
  if (!el) return
  listContainerHeight.value = el.clientHeight
  listResizeObs = new ResizeObserver(entries => {
    listContainerHeight.value = entries[0]?.contentRect.height ?? 600
  })
  listResizeObs.observe(el)
}

onMounted(() => {
  workStore.fetchWorks()
  loadProjects()
  nextTick(() => {
    if (viewMode.value === 'list') setupListVirtualScroll()
  })
})

onUnmounted(() => {
  listResizeObs?.disconnect()
})
</script>

<style scoped>
.works-view { display: flex; flex-direction: column; gap: 16px; }
.works-toolbar { display: flex; gap: 12px; align-items: center; }
.works-toolbar > :first-child { flex: 1; }
.toolbar-actions { display: flex; gap: 8px; align-items: center; flex-shrink: 0; }
.filter-select {
  padding: 10px 14px; border: 1px solid var(--border); border-radius: var(--radius);
  background: var(--surface); color: var(--fg); font-size: 0.85rem;
  font-family: var(--font-body); cursor: pointer;
}
.works-stats { font-size: 0.82rem; color: var(--muted); display: flex; gap: 16px; align-items: center; }
.works-stats-tags { display: flex; gap: 6px; flex-wrap: wrap; }
.filter-chip {
  padding: 2px 10px; border-radius: 100px; font-size: 0.75rem;
  background: oklch(56% 0.12 170 / 0.1); color: var(--accent);
  display: flex; align-items: center; gap: 4px;
}
.filter-chip button { background: none; border: none; cursor: pointer; color: var(--accent); font-size: 1rem; }

/* Floating batch bar */
.floating-batch-bar {
  position: fixed; bottom: 24px; left: 50%; transform: translateX(-50%);
  z-index: 10000;
  animation: slideUp 0.25s ease;
}
@keyframes slideUp {
  from { transform: translateX(-50%) translateY(20px); opacity: 0; }
  to { transform: translateX(-50%) translateY(0); opacity: 1; }
}
.batch-inner {
  display: flex; align-items: center; gap: 12px;
  padding: 10px 18px;
  background: oklch(15% 0.02 240 / 0.85);
  backdrop-filter: blur(16px) saturate(180%);
  border: 1px solid oklch(100% 0 0 / 0.12);
  border-radius: 16px;
  color: #fff; font-size: 0.85rem;
  box-shadow: 0 8px 32px oklch(0 0 0 / 0.25);
  white-space: nowrap;
}
.batch-select-all {
  display: flex; align-items: center; gap: 4px; cursor: pointer;
  font-size: 0.78rem; opacity: 0.75; flex-shrink: 0;
}
.batch-select-all input { width: 14px; height: 14px; cursor: pointer; }
.batch-count { font-weight: 700; flex-shrink: 0; }
.batch-actions { display: flex; gap: 6px; align-items: center; }
.batch-project-select {
  padding: 5px 10px; border: 1px solid oklch(100% 0 0 / 0.15);
  border-radius: 8px; background: oklch(100% 0 0 / 0.1);
  color: #fff; font-size: 0.8rem; font-family: var(--font-body);
  cursor: pointer; outline: none;
}
.batch-project-select option { background: #1a1a2e; color: #fff; }
.batch-dismiss {
  background: none; border: none; color: #fff; font-size: 1.2rem;
  cursor: pointer; opacity: 0.5; padding: 0 4px; line-height: 1;
}
.batch-dismiss:hover { opacity: 1; }
.btn-danger { background: #e53e3e; color: #fff; }
.btn-danger:disabled { opacity: 0.5; cursor: not-allowed; }

/* Batch toolbar */
.batch-toolbar {
  display: flex; align-items: center; gap: 10px;
  padding: 10px 14px;
  background: oklch(56% 0.12 170 / 0.08);
  border: 1px solid oklch(56% 0.12 170 / 0.2);
  border-radius: var(--radius-sm);
  font-size: 0.85rem;
}
.batch-toolbar .filter-select { padding: 6px 10px; font-size: 0.82rem; }

.works-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: 16px;
}
.work-grid-card { cursor: pointer; overflow: hidden; padding: 0; position: relative; }
.work-grid-card.selected { outline: 2px solid var(--accent); }
.work-grid-card input[type="checkbox"] { accent-color: var(--accent); }
.card-thumb {
  height: 180px; position: relative; overflow: hidden;
  background: oklch(95% 0.003 240);
}
.card-thumb img { width: 100%; height: 100%; object-fit: cover; }
.card-thumb-placeholder {
  width: 100%; height: 100%; display: flex; align-items: center; justify-content: center;
}
.card-thumb-icon { font-size: 3rem; }
.card-type-badge {
  position: absolute; top: 8px; left: 8px;
  padding: 2px 8px; border-radius: 100px;
  background: oklch(0 0 0 / 0.6); color: #fff;
  font-size: 0.65rem; font-weight: 700;
}
.card-project-badge {
  position: absolute; top: 8px; right: 8px;
  padding: 2px 8px; border-radius: 100px;
  background: oklch(0 0 0 / 0.6); color: #fff;
  font-size: 0.65rem; font-weight: 600;
}
.card-stage-badge {
  position: absolute; bottom: 8px; right: 8px;
  padding: 2px 8px; border-radius: 100px;
  background: oklch(1 1 1 / 0.9); color: var(--fg);
  font-size: 0.65rem; font-weight: 600;
  border: 2px solid;
}
.card-verified {
  position: absolute; bottom: 8px; left: 8px;
  padding: 2px 8px; border-radius: 100px;
  background: oklch(56% 0.12 170 / 0.85); color: #fff;
  font-size: 0.68rem; font-weight: 600;
}
.card-hash-ready {
  position: absolute; bottom: 8px; left: 8px;
  padding: 2px 8px; border-radius: 100px;
  background: oklch(70% 0.15 80 / 0.85); color: #fff;
  font-size: 0.68rem; font-weight: 600;
}
.card-info { padding: 14px 16px; }
.card-title { font-size: 0.85rem; font-weight: 600; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.card-date { font-size: 0.72rem; color: var(--muted); margin-top: 2px; }

/* Multi-select checkbox */
.card-checkbox {
  position: absolute; top: 8px; left: 8px; z-index: 2;
}
.card-checkbox input {
  width: 20px; height: 20px; cursor: pointer;
  accent-color: var(--accent);
}

/* List view */
.works-list-container {
  overflow-y: auto;
  flex: 1;
  min-height: 300px;
}
.works-list-scroll { position: relative; }
.works-list-content {
  position: absolute;
  top: 0; left: 0; right: 0;
}
.work-list-row {
  display: flex; align-items: center; gap: 14px;
  padding: 12px 16px; border-radius: var(--radius-sm); cursor: pointer;
  transition: background 0.15s;
}
.work-list-row:hover { background: oklch(96% 0.003 240); }
.list-checkbox {
  flex-shrink: 0;
}
.list-checkbox input {
  width: 18px; height: 18px; cursor: pointer;
  accent-color: var(--accent);
}
.list-thumb {
  width: 44px; height: 44px; border-radius: var(--radius-sm);
  overflow: hidden; flex-shrink: 0;
  background: oklch(95% 0.003 240);
  display: flex; align-items: center; justify-content: center;
  font-size: 1.4rem;
}
.list-thumb img { width: 100%; height: 100%; object-fit: cover; }
.list-info { flex: 1; min-width: 0; }
.list-title { font-size: 0.88rem; font-weight: 600; }
.list-meta { font-size: 0.72rem; color: var(--muted); }
.list-hash { font-size: 0.68rem; color: var(--muted); font-family: monospace; }
.btn-ghost-small {
  background: none; border: none; cursor: pointer;
  font-size: 1rem; color: var(--muted); padding: 4px 8px;
  border-radius: var(--radius-sm);
}
.btn-ghost-small:hover { background: oklch(0 0 0 / 0.04); }

/* Modal */
.modal-overlay {
  position: fixed; inset: 0; background: oklch(0 0 0 / 0.4);
  backdrop-filter: blur(4px); z-index: 9998;
  display: flex; align-items: center; justify-content: center;
}
.modal-card {
  background: var(--surface); border-radius: var(--radius-xl);
  padding: 28px; max-width: 560px; width: 90%;
  box-shadow: 0 16px 64px oklch(0 0 0 / 0.16);
}
.modal-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 20px; }
.modal-header h3 { margin: 0; font-size: 1.15rem; }
.modal-close-btn { background: none; border: none; cursor: pointer; font-size: 1.4rem; color: var(--muted); }
.uploading-hint { text-align: center; margin-top: 12px; color: var(--accent); font-weight: 600; font-size: 0.88rem; }
.import-options { padding: 12px 0; }
.checkbox-label { display: flex; align-items: center; gap: 8px; font-size: 0.85rem; color: var(--muted); cursor: pointer; }
.checkbox-label input[type="checkbox"] { width: 16px; height: 16px; cursor: pointer; }
.modal-footer-actions { display: flex; justify-content: flex-end; gap: 10px; margin-top: 20px; }
.delete-confirm-text { font-size: 0.92rem; line-height: 1.6; color: var(--fg); }

/* Edit panel */
.edit-overlay { position: fixed; inset: 0; background: oklch(0 0 0 / 0.3); z-index: 9998; }
.edit-panel {
  position: fixed; top: 0; right: 0; bottom: 0;
  width: 420px; max-width: 92vw;
  background: var(--surface); box-shadow: -4px 0 32px oklch(0 0 0 / 0.1);
  display: flex; flex-direction: column;
  overflow-y: auto;
}
.panel-header {
  display: flex; align-items: center; justify-content: space-between;
  padding: 16px 20px; border-bottom: 1px solid var(--border);
  position: sticky; top: 0; background: var(--surface); z-index: 1;
}
.panel-header h3 { margin: 0; font-size: 1.1rem; }
.close-btn { background: none; border: none; font-size: 1.4rem; cursor: pointer; color: var(--muted); }
.panel-body { flex: 1; padding: 20px; overflow-y: auto; display: flex; flex-direction: column; gap: 12px; }
.panel-footer {
  padding: 14px 20px; border-top: 1px solid var(--border);
  display: flex; justify-content: flex-end; gap: 10px;
  position: sticky; bottom: 0; background: var(--surface); z-index: 1;
}
.section-label {
  font-size: 0.72rem; font-weight: 700; text-transform: uppercase;
  letter-spacing: 0.05em; color: var(--accent);
  padding-top: 4px; border-top: 1px solid var(--border);
}
.section-label:first-child { border-top: none; padding-top: 0; }
.form-group { display: flex; flex-direction: column; gap: 4px; }
.form-group label { font-size: 0.8rem; font-weight: 600; color: var(--muted); }
.form-input, .form-textarea {
  padding: 9px 12px; border: 1px solid var(--border); border-radius: var(--radius-sm);
  font-size: 0.88rem; font-family: var(--font-body); color: var(--fg);
  background: var(--surface); outline: none;
}
.form-input:focus, .form-textarea:focus { border-color: var(--accent); box-shadow: 0 0 0 3px oklch(56% 0.12 170 / 0.1); }
.form-textarea { resize: vertical; }
.btn { padding: 9px 18px; border-radius: var(--radius-sm); font-size: 0.85rem; font-weight: 600; cursor: pointer; border: none; font-family: var(--font-body); }
.btn-primary { background: var(--accent); color: #fff; }
.btn-secondary { background: var(--surface); color: var(--fg); border: 1px solid var(--border); }
.btn-danger { background: #e53e3e; color: #fff; }
.btn-sm { padding: 4px 10px; font-size: 0.75rem; }
.animate-slide-right { animation: slideRight 0.2s ease; }
@keyframes slideRight { from { transform: translateX(100%); } to { transform: translateX(0); } }
.checkbox-group { gap: 8px; }
.checkbox-label {
  display: flex; align-items: center; gap: 8px;
  font-size: 0.85rem; cursor: pointer; font-weight: 400; color: var(--fg);
}

.pagination { display: flex; justify-content: center; align-items: center; gap: 16px; margin-top: 8px; }
.pagination button { padding: 8px 16px; border: 1px solid var(--border); border-radius: var(--radius-sm); background: var(--surface); cursor: pointer; font-size: 0.85rem; }
.pagination button:disabled { opacity: 0.4; cursor: default; }

@keyframes scaleIn {
  from { transform: scale(0.95); opacity: 0; }
  to { transform: scale(1); opacity: 1; }
}
.animate-scale-in { animation: scaleIn 0.15s ease; }
</style>
