<template>
  <div class="recycle-view">
    <!-- 规则说明 -->
    <div class="rv-rules card" style="padding:16px 20px;font-size:.85rem">
      <h3 style="margin:0 0 8px;font-size:.95rem">📋 回收站规则</h3>
      <ul style="margin:0;padding-left:20px;color:var(--muted);line-height:1.8">
        <li>删除的作品会移入回收站，保留 <strong>30 天</strong></li>
        <li>30 天后系统将自动永久删除</li>
        <li>恢复后的作品回到原项目分组，不会丢失任何数据</li>
        <li>永久删除后无法恢复，请谨慎操作</li>
      </ul>
    </div>

    <div class="rv-header">
      <h2>🗑️ 回收站</h2>
      <div class="rv-actions">
        <span class="rv-count">{{ workStore.total }} 个作品</span>
        <button class="btn btn-secondary btn-sm" @click="selectAll" :disabled="!workStore.works.length">全选</button>
        <button v-if="selectedIds.length" class="btn btn-secondary btn-sm" @click="restoreSelected">恢复选中 ({{ selectedIds.length }})</button>
        <button v-if="workStore.works.length" class="btn btn-danger btn-sm" @click="handleEmptyTrash">清空回收站</button>
      </div>
    </div>

    <LoadingSpinner v-if="workStore.loading" text="加载中..." />

    <EmptyState
      v-else-if="workStore.works.length === 0"
      icon="🗑️"
      title="回收站为空"
      description="删除的作品会出现在这里，保留30天"
    />

    <div v-else class="rv-content">
      <!-- Grid view -->
      <div v-if="viewMode === 'grid'" class="works-grid">
        <div
          v-for="work in workStore.works"
          :key="work.id"
          class="work-grid-card card"
          :class="{ 'selected': selectedIds.includes(work.id) }"
        >
          <div class="card-thumb">
            <input type="checkbox" :checked="selectedIds.includes(work.id)" @change="toggleSelect(work.id, $event)" class="rv-checkbox" />
            <LazyImage v-if="work.thumbnail_url" :src="work.thumbnail_url" :alt="work.title" />
            <div v-else class="card-thumb-placeholder">
              <span class="card-thumb-icon">{{ fileTypeEmoji[work.file_type] || '📄' }}</span>
            </div>
            <div class="card-type-badge">{{ work.file_extension.toUpperCase() }}</div>
          </div>
          <div class="card-info">
            <div class="card-title">{{ work.title }}</div>
            <div class="card-date">{{ work.imported_at?.slice(0, 10) }}</div>
          </div>
          <div class="card-actions">
            <button class="btn btn-sm btn-secondary" @click="handleRestore(work)">恢复</button>
            <button class="btn btn-sm btn-danger" @click="handlePermanentDelete(work)">永久删除</button>
          </div>
        </div>
      </div>

      <!-- List view -->
      <div v-else class="works-list-container" ref="listContainerRef">
        <div class="works-list-scroll" :style="{ height: totalListHeight + 'px' }">
          <div class="works-list-content" :style="{ transform: `translateY(${listOffsetY}px)` }">
            <div
              v-for="work in visibleListWorks"
              :key="work.id"
              class="work-list-row"
            >
              <div class="list-thumb">
                <img v-if="work.thumbnail_url" :src="work.thumbnail_url" :alt="work.title" loading="lazy" />
                <span v-else>{{ fileTypeEmoji[work.file_type] || '📄' }}</span>
              </div>
              <div class="list-info">
                <div class="list-title">{{ work.title }}</div>
                <div class="list-meta">
                  {{ work.file_type }} · {{ formatFileSize(work.file_size) }} · {{ work.imported_at?.slice(0, 10) }}
                </div>
              </div>
              <button class="btn btn-sm btn-secondary" @click.stop="handleRestore(work)">恢复</button>
              <button class="btn btn-sm btn-danger" @click.stop="handlePermanentDelete(work)">删除</button>
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
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue'
import { useWorkStore } from '@/stores/useWorkStore'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import LazyImage from '@/components/common/LazyImage.vue'

const workStore = useWorkStore()
const viewMode = ref<'grid' | 'list'>('grid')
const selectedIds = ref<string[]>([])

function toggleSelect(id: string, event: Event) {
  const checked = (event.target as HTMLInputElement).checked
  if (checked) {
    if (!selectedIds.value.includes(id)) selectedIds.value.push(id)
  } else {
    const idx = selectedIds.value.indexOf(id)
    if (idx >= 0) selectedIds.value.splice(idx, 1)
  }
}

function selectAll() {
  selectedIds.value = workStore.works.map(w => w.id)
}

async function restoreSelected() {
  try {
    for (const id of selectedIds.value) {
      await workStore.restoreWork(id)
    }
    selectedIds.value = []
    ;(window as any).$toast?.show('已恢复所选作品', 'success')
  } catch (e: unknown) {
    const msg = e instanceof Error ? e.message : '恢复失败'
    ;(window as any).$toast?.show(msg, 'error')
  }
}

const fileTypeEmoji: Record<string, string> = {
  image: '🖼️', audio: '🎵', video: '🎬',
  document: '📄', design: '🎨', code: '💻',
}

async function handleRestore(work: any) {
  try {
    await workStore.restoreWork(work.id)
    ;(window as any).$toast?.show('作品已恢复', 'success')
  } catch (e: unknown) {
    const msg = e instanceof Error ? e.message : '恢复失败'
    ;(window as any).$toast?.show(msg, 'error')
  }
}

async function handlePermanentDelete(work: any) {
  if (!confirm(`确定永久删除"${work.title}"？此操作不可恢复。`)) return
  try {
    await workStore.permanentDeleteWork(work.id)
    ;(window as any).$toast?.show('作品已永久删除', 'info')
  } catch (e: unknown) {
    const msg = e instanceof Error ? e.message : '删除失败'
    ;(window as any).$toast?.show(msg, 'error')
  }
}

async function handleEmptyTrash() {
  if (!confirm('确定清空回收站？所有被删除的作品将被永久删除，此操作不可恢复。')) return
  try {
    await workStore.emptyTrash()
    ;(window as any).$toast?.show('回收站已清空', 'success')
  } catch (e: unknown) {
    const msg = e instanceof Error ? e.message : '清空失败'
    ;(window as any).$toast?.show(msg, 'error')
  }
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
  workStore.fetchTrashedWorks()
  nextTick(() => {
    if (viewMode.value === 'list') setupListVirtualScroll()
  })
})

onUnmounted(() => {
  listResizeObs?.disconnect()
})
</script>

<style scoped>
.recycle-view { display: flex; flex-direction: column; gap: 16px; }
.rv-header { display: flex; justify-content: space-between; align-items: center; }
.rv-header h2 { margin: 0; font-size: 1.2rem; }
.rv-actions { display: flex; align-items: center; gap: 12px; }
.rv-count { font-size: 0.85rem; color: var(--muted); }

.works-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: 16px;
}
.work-grid-card { overflow: hidden; padding: 0; }
.work-grid-card.selected { outline: 2px solid var(--accent); }
.card-thumb {
  height: 180px; position: relative; overflow: hidden;
  background: oklch(95% 0.003 240);
}
.rv-checkbox {
  position: absolute; top: 8px; left: 8px; z-index: 2;
  width: 18px; height: 18px; cursor: pointer;
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
.card-info { padding: 14px 16px; }
.card-title { font-size: 0.85rem; font-weight: 600; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.card-date { font-size: 0.72rem; color: var(--muted); margin-top: 2px; }
.card-actions {
  padding: 8px 16px;
  display: flex;
  gap: 6px;
  border-top: 1px solid var(--border);
}
.btn-sm { padding: 4px 10px; font-size: 0.75rem; }
.btn-danger { background: #e53e3e; color: #fff; }
.btn-danger:hover { background: #c53030; }

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
  padding: 12px 16px; border-radius: var(--radius-sm);
  transition: background 0.15s;
}
.work-list-row:hover { background: oklch(96% 0.003 240); }
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

.pagination { display: flex; justify-content: center; align-items: center; gap: 16px; margin-top: 8px; }
.pagination button { padding: 8px 16px; border: 1px solid var(--border); border-radius: var(--radius-sm); background: var(--surface); cursor: pointer; font-size: 0.85rem; }
.pagination button:disabled { opacity: 0.4; cursor: default; }
</style>
