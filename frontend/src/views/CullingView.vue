<template>
  <div class="view-page">
    <!-- Filter Bar -->
    <div class="filter-bar">
      <div class="filter-row">
        <div class="filter-group">
          <label>审核状态</label>
          <select v-model="filters.cull_status" class="form-select-sm">
            <option value="">全部</option>
            <option value="pending">待审</option>
            <option value="keep">保留</option>
            <option value="reject">淘汰</option>
          </select>
        </div>
        <div class="filter-group">
          <label>评分</label>
          <select v-model="filters.rating" class="form-select-sm">
            <option value="">全部</option>
            <option value="5">5 星</option>
            <option value="4">4 星</option>
            <option value="3">3 星</option>
            <option value="2">2 星</option>
            <option value="1">1 星</option>
          </select>
        </div>
        <div class="filter-group">
          <label>颜色标签</label>
          <select v-model="filters.color_label" class="form-select-sm">
            <option value="">全部</option>
            <option value="red">红</option>
            <option value="yellow">黄</option>
            <option value="green">绿</option>
            <option value="blue">蓝</option>
          </select>
        </div>
        <div class="filter-group">
          <label>关键词</label>
          <input v-model="filters.keyword" class="form-input-sm" placeholder="搜索..." />
        </div>
        <button class="btn btn-secondary btn-sm" @click="resetFilters">重置</button>
      </div>
    </div>

    <!-- Bulk Action Bar -->
    <div v-if="selectedIds.length > 0" class="bulk-bar">
      <span>已选 {{ selectedIds.length }} 项</span>
      <button class="btn btn-sm btn-secondary" @click="bulkAction('keep', 'keep')">保留选中</button>
      <button class="btn btn-sm btn-secondary" @click="bulkAction('reject', 'reject')">淘汰选中</button>
      <button class="btn btn-sm btn-danger" @click="clearSelection">取消选择</button>
    </div>

    <!-- Thumbnail Grid -->
    <div
      class="thumbnail-grid"
      :class="{ 'keyboard-focus': keyboardActive }"
    >
      <div
        v-for="(work, wi) in filteredWorks"
        :key="work.id"
        class="thumb-card"
        :class="{
          selected: selectedIds.includes(work.id),
          'kb-active': keyboardActiveIndex === wi,
          'cull-keep': work.cull_status === 'keep',
          'cull-reject': work.cull_status === 'reject',
        }"
        @click="toggleSelect(work.id)"
        @mouseenter="hoverId = work.id"
        @mouseleave="hoverId = null"
      >
        <!-- Thumbnail Image -->
        <div class="thumb-img-wrapper">
          <div class="thumb-img" :style="{ backgroundImage: 'url(' + (work.thumbnail || placeholderImg) + ')' }"></div>
          <Transition name="fade">
            <div v-if="hoverId === work.id" class="thumb-hover-overlay">
              <div class="hover-rating">
                <button v-for="s in 5" :key="s" class="star-btn" :class="{ active: s <= hoverRating }" @click.stop="rateWork(work.id, s)">
                  {{ s <= hoverRating ? '★' : '☆' }}
                </button>
              </div>
              <div class="hover-colors">
                <button v-for="c in colorOptions" :key="c" class="color-dot" :class="{ active: hoverColor === c }" @click.stop="setColor(work.id, c)">
                  <span class="dot" :style="{ background: colorMap[c] }"></span>
                </button>
              </div>
              <div class="hover-actions">
                <button class="btn btn-xs btn-green" @click.stop="setCullStatus(work.id, 'keep')">保留</button>
                <button class="btn btn-xs btn-red" @click.stop="setCullStatus(work.id, 'reject')">淘汰</button>
              </div>
            </div>
          </Transition>
          <div v-if="work.cull_status === 'keep'" class="cull-badge keep-badge">保留</div>
          <div v-if="work.cull_status === 'reject'" class="cull-badge reject-badge">淘汰</div>
          <div v-if="work.rating" class="rating-badge">{{ work.rating }} ★</div>
        </div>
        <!-- Info Footer -->
        <div class="thumb-info">
          <span class="thumb-title">{{ work.title }}</span>
          <span v-if="work.color_label" class="color-dot-inline" :style="{ background: colorMap[work.color_label] }"></span>
        </div>
        <!-- Checkbox -->
        <div class="thumb-checkbox" :class="{ checked: selectedIds.includes(work.id) }">
          <span>&#10003;</span>
        </div>
      </div>
    </div>

    <div v-if="filteredWorks.length === 0 && !loading" class="empty-hint">没有找到匹配的作品</div>
    <div v-if="loading" class="empty-hint">加载中...</div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { systemApi } from '@/api/system'
import { worksApi } from '@/api/works'

interface CullWork {
  id: string
  title: string
  thumbnail: string
  cull_status: '' | 'pending' | 'keep' | 'reject'
  rating: number | null
  color_label: string
}

const filters = ref({
  cull_status: '',
  rating: '',
  color_label: '',
  keyword: '',
})

const works = ref<CullWork[]>([])
const loading = ref(false)
const selectedIds = ref<string[]>([])
const hoverId = ref<string | null>(null)
const hoverRating = ref(0)
const hoverColor = ref('')
const keyboardActive = ref(false)
const keyboardActiveIndex = ref(-1)

const colorMap: Record<string, string> = { red: '#ef4444', yellow: '#eab308', green: '#16a34a', blue: '#3b82f6' }
const colorOptions = ['red', 'yellow', 'green', 'blue']

const filteredWorks = computed(() => {
  let result = works.value
  if (filters.value.cull_status) {
    result = result.filter((w) => w.cull_status === filters.value.cull_status)
  }
  if (filters.value.rating) {
    result = result.filter((w) => w.rating === Number(filters.value.rating))
  }
  if (filters.value.color_label) {
    result = result.filter((w) => w.color_label === filters.value.color_label)
  }
  if (filters.value.keyword) {
    const kw = filters.value.keyword.toLowerCase()
    result = result.filter((w) => w.title.toLowerCase().includes(kw))
  }
  return result
})

const placeholderImg = 'data:image/svg+xml,<svg xmlns=%22http://www.w3.org/2000/svg%22 width=%22400%22 height=%22300%22><rect fill=%22%23eee%22 width=%22400%22 height=%22300%22/><text x=%2250%25%22 y=%2250%25%22 dominant-baseline=%22central%22 text-anchor=%22middle%22 fill=%22%23999%22 font-size=%2216%22>暂无缩略图</text></svg>'

function resetFilters() {
  filters.value = { cull_status: '', rating: '', color_label: '', keyword: '' }
}

function clearSelection() {
  selectedIds.value = []
}

function toggleSelect(id: string) {
  const idx = selectedIds.value.indexOf(id)
  if (idx >= 0) selectedIds.value.splice(idx, 1)
  else selectedIds.value.push(id)
}

async function setCullStatus(workId: string, action: 'keep' | 'reject') {
  try {
    await systemApi.cullWork(workId, action)
    const w = works.value.find((wk) => wk.id === workId)
    if (w) w.cull_status = action
    ;(window as any).$toast?.show(action === 'keep' ? '已标记保留' : '已标记淘汰', 'success')
  } catch (e: any) {
    ;(window as any).$toast?.show(e.response?.data?.detail || '操作失败', 'error')
  }
}

async function rateWork(workId: string, rating: number) {
  hoverRating.value = rating
  try {
    await systemApi.cullWork(workId, 'rate')
    const w = works.value.find((wk) => wk.id === workId)
    if (w) w.rating = rating
  } catch {
    // optimistic update even if API fails
  }
}

async function setColor(workId: string, color: string) {
  hoverColor.value = color
  try {
    await systemApi.cullWork(workId, 'color')
    const w = works.value.find((wk) => wk.id === workId)
    if (w) w.color_label = color
  } catch {
    // optimistic update
  }
}

async function bulkAction(status: string, action: string) {
  if (selectedIds.value.length === 0) return
  try {
    await systemApi.batchCull(selectedIds.value, action)
    const w = (window as any).__worksRef
    if (w) {
      for (const id of selectedIds.value) {
        const item = w.find((x: CullWork) => x.id === id)
        if (item) item.cull_status = status
      }
    }
    ;(window as any).$toast?.show(`已批量${action === 'keep' ? '保留' : '淘汰'} ${selectedIds.value.length} 项`, 'success')
    clearSelection()
  } catch (e: any) {
    ;(window as any).$toast?.show(e.response?.data?.detail || '批量操作失败', 'error')
  }
}

// Keyboard navigation
function onKeyDown(e: KeyboardEvent) {
  const items = filteredWorks.value
  if (items.length === 0) return

  if (['ArrowUp', 'ArrowDown', 'ArrowLeft', 'ArrowRight'].includes(e.key)) {
    e.preventDefault()
    keyboardActive.value = true
    let idx = keyboardActiveIndex.value < 0 ? 0 : keyboardActiveIndex.value
    const cols = Math.max(Math.floor(window.innerWidth / 240), 1)
    if (e.key === 'ArrowDown' || e.key === 'ArrowRight') idx = Math.min(idx + 1, items.length - 1)
    if (e.key === 'ArrowUp' || e.key === 'ArrowLeft') idx = Math.max(idx - 1, 0)
    keyboardActiveIndex.value = idx
  }

  if (e.key >= '1' && e.key <= '5') {
    e.preventDefault()
    const current = items[keyboardActiveIndex.value]
    if (current) {
      rateWork(current.id, Number(e.key))
    }
  }

  if (e.key.toLowerCase() === 'a') {
    e.preventDefault()
    const current = items[keyboardActiveIndex.value]
    if (current) setCullStatus(current.id, 'keep')
  }

  if (e.key.toLowerCase() === 'r') {
    e.preventDefault()
    const current = items[keyboardActiveIndex.value]
    if (current) setCullStatus(current.id, 'reject')
  }
}

async function loadWorks() {
  try {
    const res = await worksApi.list({ status: 'active' })
    const items = res.data.data?.items || res.data.data || []
    works.value = (items as any[]).map((w: any) => ({
      id: w.id,
      title: w.title || w.file_name,
      thumbnail: w.thumbnail_url || w.thumbnail_path || '',
      cull_status: w.cull_status || 'pending',
      rating: w.cull_rating ?? null,
      color_label: w.color_label || '',
    })) as CullWork[]
  } catch {
    works.value = []
  }
}

onMounted(async () => {
  loading.value = true
  await loadWorks()
  loading.value = false
  window.addEventListener('keydown', onKeyDown)
})

onUnmounted(() => {
  window.removeEventListener('keydown', onKeyDown)
})
</script>

<style scoped>
.view-page { display: flex; flex-direction: column; gap: 16px; }

/* Filter bar */
.filter-bar { background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius); padding: 16px; }
.filter-row { display: flex; flex-wrap: wrap; gap: 12px; align-items: flex-end; }
.filter-group { display: flex; flex-direction: column; gap: 4px; }
.filter-group label { font-size: 0.75rem; font-weight: 600; color: var(--muted); }
.form-select-sm {
  padding: 7px 12px; border: 1px solid var(--border); border-radius: var(--radius-sm);
  font-size: 0.84rem; background: var(--surface); color: var(--fg); min-width: 130px;
}
.form-input-sm {
  padding: 7px 12px; border: 1px solid var(--border); border-radius: var(--radius-sm);
  font-size: 0.84rem; background: var(--surface); color: var(--fg); min-width: 140px;
}

/* Bulk action bar */
.bulk-bar {
  display: flex; align-items: center; gap: 10px; padding: 10px 16px;
  background: oklch(56% 0.12 170 / 0.06); border: 1px solid var(--accent);
  border-radius: var(--radius); font-size: 0.85rem;
}

/* Thumbnail grid */
.thumbnail-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: 16px;
}
.thumb-card {
  border: 2px solid transparent; border-radius: var(--radius); overflow: hidden;
  cursor: pointer; transition: border-color 0.2s, box-shadow 0.2s;
  position: relative;
}
.thumb-card:hover { box-shadow: 0 4px 16px oklch(0 0 0 / 0.08); }
.thumb-card.selected { border-color: var(--accent); }
.thumb-card.kb-active { border-color: var(--accent2); box-shadow: 0 0 0 3px oklch(62% 0.16 280 / 0.15); }
.thumb-card.cull-keep { border-left: 4px solid #16a34a; }
.thumb-card.cull-reject { border-left: 4px solid #ef4444; }

.thumb-img-wrapper { position: relative; width: 100%; padding-top: 75%; overflow: hidden; }
.thumb-img {
  position: absolute; inset: 0; background-size: cover; background-position: center;
  background-color: var(--border); transition: transform 0.3s;
}
.thumb-card:hover .thumb-img { transform: scale(1.03); }

/* Hover overlay */
.thumb-hover-overlay {
  position: absolute; inset: 0;
  background: oklch(0 0 0 / 0.7); backdrop-filter: blur(2px);
  display: flex; flex-direction: column; align-items: center; justify-content: center;
  gap: 10px; padding: 16px;
}
.hover-rating { display: flex; gap: 4px; }
.star-btn {
  background: none; border: none; font-size: 1.5rem; cursor: pointer;
  color: oklch(50% 0.15 55); transition: color 0.15s;
}
.star-btn.active { color: #eab308; }
.hover-colors { display: flex; gap: 8px; }
.color-dot {
  background: none; border: 2px solid transparent; border-radius: 50%;
  cursor: pointer; padding: 4px; width: 36px; height: 36px;
  display: flex; align-items: center; justify-content: center;
}
.color-dot.active { border-color: #fff; }
.dot { width: 16px; height: 16px; border-radius: 50%; display: block; }
.hover-actions { display: flex; gap: 8px; }

/* Badges */
.cull-badge {
  position: absolute; top: 8px; left: 8px;
  font-size: 0.72rem; font-weight: 700; padding: 2px 8px;
  border-radius: 10px; z-index: 2;
}
.keep-badge { background: #16a34a; color: #fff; }
.reject-badge { background: #ef4444; color: #fff; }
.rating-badge {
  position: absolute; top: 8px; right: 8px;
  font-size: 0.78rem; font-weight: 700; color: #eab308;
  text-shadow: 0 1px 3px oklch(0 0 0 / 0.5); z-index: 2;
}

/* Thumb info footer */
.thumb-info {
  padding: 8px 12px; display: flex; align-items: center; gap: 8px;
  font-size: 0.82rem; border-top: 1px solid var(--border); background: var(--surface);
}
.thumb-title { flex: 1; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.color-dot-inline { width: 10px; height: 10px; border-radius: 50%; display: inline-block; flex-shrink: 0; }

/* Checkbox */
.thumb-checkbox {
  position: absolute; top: 8px; left: 8px; z-index: 3;
  width: 20px; height: 20px; border-radius: 4px;
  border: 2px solid rgba(255,255,255,0.6);
  background: oklch(0 0 0 / 0.3);
  display: flex; align-items: center; justify-content: center;
  color: #fff; font-size: 0.7rem;
}
.thumb-checkbox.checked { background: var(--accent); border-color: var(--accent); }

.btn-sm { padding: 6px 14px; font-size: 0.82rem; }
.btn-xs { padding: 4px 10px; font-size: 0.75rem; }
.btn-green { background: #16a34a; color: #fff; border: none; }
.btn-red { background: #ef4444; color: #fff; border: none; }

.empty-hint { text-align: center; padding: 48px 24px; color: var(--muted); font-size: 0.9rem; }

/* Fade transition */
.fade-enter-active, .fade-leave-active { transition: opacity 0.15s ease; }
.fade-enter-from, .fade-leave-to { opacity: 0; }

@media (max-width: 768px) {
  .thumbnail-grid { grid-template-columns: repeat(auto-fill, minmax(150px, 1fr)); gap: 10px; }
  .filter-row { flex-direction: column; align-items: stretch; }
  .form-select-sm, .form-input-sm { min-width: 100%; }
}
</style>
