<template>
  <div class="photographer-view">
    <!-- Loading -->
    <div v-if="store.loading" class="loading-overlay">
      <div class="spinner">加载中...</div>
    </div>

    <!-- Error banner -->
    <div v-if="errorMsg" class="error-banner">
      <span>{{ errorMsg }}</span>
      <button @click="errorMsg = ''">关闭</button>
    </div>

    <!-- Stats bar -->
    <div class="stats-bar">
      <div class="stat-item">
        <span class="stat-label">📷 总作品</span>
        <span class="stat-value">{{ stats.total_variants }}</span>
      </div>
      <div class="stat-item stat-pass">
        <span class="stat-label">✅ 已通过</span>
        <span class="stat-value">{{ stats.pass_count }}</span>
      </div>
      <div class="stat-item stat-shortlist">
        <span class="stat-label">📜 短名单</span>
        <span class="stat-value">{{ stats.shortlist_count }}</span>
      </div>
      <div class="stat-item stat-stock">
        <span class="stat-label">📦 图库上架</span>
        <span class="stat-value">{{ stats.stock_channel_count }}</span>
      </div>
      <div class="stat-item stat-sales">
        <span class="stat-label">💰 本月销售</span>
        <span class="stat-value">¥{{ salesAmount }}</span>
      </div>
    </div>

    <!-- Tab bar -->
    <div class="tab-bar">
      <button
        v-for="tab in tabs"
        :key="tab.key"
        :class="['tab-btn', { active: activeTab === tab.key }]"
        @click="activeTab = tab.key"
      >
        {{ tab.label }}
      </button>
    </div>

    <!-- ========== 选片 tab ========== -->
    <div v-if="activeTab === 'culling'" class="tab-panel">
      <div class="culling-layout">
        <!-- Left: ShotSelector -->
        <div class="culling-main">
          <!-- Filter row -->
          <div class="filter-row">
            <select v-model="shotFilters.shot_status" class="filter-select" @change="loadShots(1)">
              <option value="">全部状态</option>
              <option value="unreviewed">未审核</option>
              <option value="pass">已通过</option>
              <option value="hold">待处理</option>
              <option value="reject">已拒绝</option>
              <option value="shortlist">短名单</option>
            </select>
            <select v-model="shotFilters.camera_model" class="filter-select" @change="loadShots(1)">
              <option value="">全部相机</option>
              <option v-for="cm in cameraModels" :key="cm" :value="cm">{{ cm }}</option>
            </select>
            <input
              v-model="shotSearchKeyword"
              class="filter-input"
              placeholder="搜索作品名..."
              @keyup.enter="loadShots(1)"
            />
            <button class="btn btn-sm btn-outline" @click="resetFilters">重置</button>
          </div>

          <ShotSelector
            :shots="store.shots"
            :loading="store.loading"
            :filter="shotFilters.shot_status"
            @status-change="handleStatusChange"
            @batch-update="handleBatchUpdate"
            @select="(shot: PhotographerShot) => { selectedShot = shot }"
          />

          <!-- Pagination -->
          <div v-if="store.shotPagination.totalPages > 1" class="pagination">
            <button
              :disabled="shotFilters.page! <= 1"
              class="btn btn-sm btn-outline"
              @click="loadShots(shotFilters.page! - 1)"
            >&laquo; 上一页</button>
            <span class="page-info">第 {{ shotFilters.page }} / {{ store.shotPagination.totalPages }} 页</span>
            <button
              :disabled="shotFilters.page! >= store.shotPagination.totalPages"
              class="btn btn-sm btn-outline"
              @click="loadShots(shotFilters.page! + 1)"
            >下一页 &raquo;</button>
          </div>
        </div>

        <!-- Right: sidebar (RawMetadataPanel + StockChannelPanel) -->
        <div class="culling-sidebar">
          <RawMetadataPanel
            v-if="selectedShot"
            :shot="selectedShot"
            @update="handleMetadataUpdate"
          />
          <EmptyState
            v-else
            icon="📷"
            title="选择作品查看详情"
            description="点击左侧作品卡片查看 EXIF 数据和编辑备注。"
          />
        </div>
      </div>
    </div>

    <!-- ========== 图库 tab ========== -->
    <div v-if="activeTab === 'stock'" class="tab-panel">
      <div class="stock-layout">
        <!-- Left: ShotSelector for picking -->
        <div class="stock-left">
          <h3 class="section-title">选择作品</h3>
          <ShotSelector
            :shots="store.shots"
            :loading="store.loading"
            @select="(shot: PhotographerShot) => { selectedShot = shot }"
          />
        </div>
        <!-- Right: channel management -->
        <div class="stock-right">
          <StockChannelPanel
            v-if="selectedShot"
            :shot="selectedShot"
            @channel-added="(shotId, channel) => handleChannelAdded(shotId, channel)"
            @channel-removed="(shotId, channel) => handleChannelRemoved(shotId, channel)"
          />
          <EmptyState
            v-else
            icon="📦"
            title="选择作品管理渠道"
            description="从左侧选择作品，然后在此添加图库销售渠道。"
          />
        </div>
      </div>
    </div>

    <!-- ========== GPS 地图 tab ========== -->
    <div v-if="activeTab === 'gps'" class="tab-panel">
      <GPSMapPanel :shots="store.shots" :loading="store.loading" />
    </div>

    <!-- ========== 统计 tab ========== -->
    <div v-if="activeTab === 'stats'" class="tab-panel">
      <div class="stats-detail-grid">
        <div class="detail-stat-card">
          <div class="detail-stat-value">{{ store.stats?.stats?.unreviewed_count ?? 0 }}</div>
          <div class="detail-stat-label">未审核</div>
        </div>
        <div class="detail-stat-card stat-green">
          <div class="detail-stat-value">{{ store.stats?.stats?.pass_count ?? 0 }}</div>
          <div class="detail-stat-label">已通过</div>
        </div>
        <div class="detail-stat-card stat-orange">
          <div class="detail-stat-value">{{ store.stats?.stats?.hold_count ?? 0 }}</div>
          <div class="detail-stat-label">待处理</div>
        </div>
        <div class="detail-stat-card stat-red">
          <div class="detail-stat-value">{{ store.stats?.stats?.reject_count ?? 0 }}</div>
          <div class="detail-stat-label">已拒绝</div>
        </div>
        <div class="detail-stat-card stat-blue">
          <div class="detail-stat-value">{{ store.stats?.stats?.shortlist_count ?? 0 }}</div>
          <div class="detail-stat-label">短名单</div>
        </div>
        <div class="detail-stat-card stat-purple">
          <div class="detail-stat-value">{{ store.stats?.stats?.raw_file_count ?? 0 }}</div>
          <div class="detail-stat-label">RAW 文件</div>
        </div>
      </div>

      <div v-if="recentActivity.length > 0" class="activity-section">
        <h3 class="section-title">最近活动</h3>
        <ul class="activity-list">
          <li v-for="item in recentActivity" :key="item.id" class="activity-item">
            <span class="activity-name">{{ item.name }}</span>
            <span :class="['activity-status', `badge-${item.shot_status}`]">
              {{ statusLabel(item.shot_status) }}
            </span>
            <span v-if="item.created_at" class="activity-time">{{ formatDate(item.created_at) }}</span>
          </li>
        </ul>
      </div>
    </div>

    <!-- ========== EXIF Overlay modal (deprecated -- sub-components handle this) ========== -->
    <!-- The old inline EXIF overlay has been replaced by RawMetadataPanel and GPSMapPanel sub-components. -->
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { usePhotographerStore } from '@/stores/usePhotographerStore'
import type { PhotographerShot, ShotStats, ShotStatus, ChannelStatus } from '@/types/photographer'
import EmptyState from '@/components/common/EmptyState.vue'
import ShotSelector from '@/components/photographer/ShotSelector.vue'
import RawMetadataPanel from '@/components/photographer/RawMetadataPanel.vue'
import StockChannelPanel from '@/components/photographer/StockChannelPanel.vue'
import GPSMapPanel from '@/components/photographer/GPSMapPanel.vue'

const store = usePhotographerStore()

// ── Active tab ────────────────────────────────────────────────
const tabs = [
  { key: 'culling', label: '📷 选片' },
  { key: 'stock', label: '📦 图库' },
  { key: 'gps', label: '📍 GPS地图' },
  { key: 'stats', label: '📊 统计' },
]
const activeTab = ref<string>('culling')

// ── Error handling ────────────────────────────────────────────
const errorMsg = ref('')

function showError(msg: string) {
  errorMsg.value = msg
  console.error(msg)
}

// ── Selected shot for sub-component panels ───────────────────
const selectedShot = ref<PhotographerShot | null>(null)

// ── Stats ─────────────────────────────────────────────────────
const stats = ref<ShotStats>({
  total_variants: 0,
  pass_count: 0,
  hold_count: 0,
  reject_count: 0,
  shortlist_count: 0,
  unreviewed_count: 0,
  raw_file_count: 0,
  stock_channel_count: 0,
  gps_tracked_count: 0,
})

// Simulated monthly sales (would come from API in production)
const salesAmount = ref('0')

async function loadStats() {
  try {
    const result = await store.fetchStats()
    if (result?.stats) {
      stats.value = result.stats
    }
  } catch (e: unknown) {
    if (e instanceof Error) showError(e.message)
  }
}

// ── Camera models for filter ──────────────────────────────────
const cameraModels = ref<string[]>([])

function extractCameraModels(shots: PhotographerShot[]) {
  const models = new Set<string>()
  for (const s of shots) {
    if (s.camera_model && s.camera_model.trim()) {
      models.add(s.camera_model)
    }
  }
  cameraModels.value = Array.from(models).sort()
}

// ── Shots & filters ──────────────────────────────────────────
const shotFilters = reactive({
  shot_status: '' as string,
  camera_model: '' as string,
  group_id: '' as string,
  page: 1,
  page_size: 24,
})
const shotSearchKeyword = ref('')
const recentActivity = ref<any[]>([])

async function loadShots(page?: number) {
  if (page !== undefined) shotFilters.page = page

  const filters: any = {}
  if (shotFilters.shot_status) filters.shot_status = shotFilters.shot_status
  if (shotFilters.camera_model) filters.camera_model = shotFilters.camera_model
  if (shotFilters.page) filters.page = shotFilters.page
  if (shotFilters.page_size) filters.page_size = shotFilters.page_size

  try {
    await store.fetchShots(filters, shotFilters.group_id || undefined)
    extractCameraModels(store.shots)
    recentActivity.value = (store.stats?.recent_activity ?? []).slice(0, 20)
  } catch (e: unknown) {
    if (e instanceof Error) showError(e.message)
    store.shots = []
  }
}

function resetFilters() {
  shotFilters.shot_status = ''
  shotFilters.camera_model = ''
  shotFilters.page = 1
  shotSearchKeyword.value = ''
  loadShots()
}

// ── Shot status helpers ───────────────────────────────────────
const STATUS_LABELS: Record<ShotStatus, string> = {
  unreviewed: '☐ 未选',
  pass: '✅ 通过',
  hold: '⏳ 待处',
  reject: '❌ 拒绝',
  shortlist: '📊 短单',
}

function statusLabel(s: ShotStatus): string {
  return STATUS_LABELS[s] ?? s
}

// ── Channel status helpers ────────────────────────────────────
const CHANNEL_LABELS: Record<ChannelStatus, string> = {
  submitted: '⏳ 已提交',
  active: '✅ 上架',
  rejected: '❌ 拒绝',
}

function channelStatusLabel(cs: ChannelStatus): string {
  return CHANNEL_LABELS[cs] ?? cs
}

// ── Sub-component event handlers ──────────────────────────────
async function handleStatusChange(shotId: string, status: ShotStatus) {
  try {
    await store.updateShotStatus(shotId, status)
    const msgs: Record<ShotStatus, string> = {
      unreviewed: '已标记未选',
      pass: '已通过',
      hold: '已标记待处理',
      reject: '已拒绝',
      shortlist: '已加入短名单',
    }
    ;(window as any).$toast?.show(msgs[status], 'success')
  } catch (e: unknown) {
    const msg = e instanceof Error ? e.message : '操作失败'
    ;(window as any).$toast?.show(msg, 'error')
  }
}

async function handleBatchUpdate(selections: Map<string, ShotStatus>) {
  try {
    const entries = Array.from(selections.entries())
    for (const [id, status] of entries) {
      await store.updateShotStatus(id, status)
    }
    ;(window as any).$toast?.show(`已更新 ${entries.length} 张作品`, 'success')
    selectedShot.value = null
  } catch (e: unknown) {
    const msg = e instanceof Error ? e.message : '批量操作失败'
    ;(window as any).$toast?.show(msg, 'error')
  }
}

async function handleMetadataUpdate(shotId: string, _field: string, value: string) {
  try {
    await store.updateShotStatus(shotId, '', value)
    // Refresh the selected shot in place
    if (selectedShot.value?.id === shotId) {
      const idx = store.shots.findIndex((s) => s.id === shotId)
      if (idx >= 0) {
        selectedShot.value = { ...store.shots[idx], shot_notes: value }
      }
    }
  } catch (e: unknown) {
    const msg = e instanceof Error ? e.message : '保存失败'
    ;(window as any).$toast?.show(msg, 'error')
  }
}

async function handleChannelAdded(shotId: string, channel: string) {
  try {
    await store.addStockChannel(shotId, channel)
    // Refresh selected shot reference
    if (selectedShot.value?.id === shotId) {
      const idx = store.shots.findIndex((s) => s.id === shotId)
      if (idx >= 0) selectedShot.value = store.shots[idx]
    }
    ;(window as any).$toast?.show(`${channel} 已添加`, 'success')
  } catch (e: unknown) {
    const msg = e instanceof Error ? e.message : '添加失败'
    ;(window as any).$toast?.show(msg, 'error')
  }
}

async function handleChannelRemoved(shotId: string, channel: string) {
  try {
    await store.removeStockChannel(shotId, channel)
    if (selectedShot.value?.id === shotId) {
      const idx = store.shots.findIndex((s) => s.id === shotId)
      if (idx >= 0) selectedShot.value = store.shots[idx]
    }
    ;(window as any).$toast?.show(`已移除 ${channel}`, 'info')
  } catch (e: unknown) {
    const msg = e instanceof Error ? e.message : '移除失败'
    ;(window as any).$toast?.show(msg, 'error')
  }
}

// ── Thumbnail URL (fallback only) ─────────────────────────────
function shotThumbnailUrl(_shot: PhotographerShot): string {
  return 'data:image/svg+xml,' + encodeURIComponent(
    '<svg xmlns="http://www.w3.org/2000/svg" width="400" height="300">' +
    '<rect fill="#eee" width="400" height="300"/>' +
    '<text x="50%" y="50%" dominant-baseline="central" text-anchor="middle" fill="#999" font-size="16">暂无缩略图</text>' +
    '</svg>'
  )
}

// ── GPS map data ──────────────────────────────────────────────
const gpsPoints = computed(() => store.gpsMap?.points ?? [])

async function loadGpsMap() {
  if (activeTab.value !== 'gps') return
  try {
    await store.fetchGpsMap()
  } catch (e: unknown) {
    if (e instanceof Error) showError(e.message)
  }
}

// ── Watch tab changes ─────────────────────────────────────────
let tabLoadTimer: ReturnType<typeof setTimeout> | null = null

function handleTabChange() {
  if (tabLoadTimer) clearTimeout(tabLoadTimer)
  tabLoadTimer = setTimeout(() => {
    if (activeTab.value === 'culling') {
      loadShots(1)
    } else if (activeTab.value === 'gps') {
      loadGpsMap()
    } else if (activeTab.value === 'stats') {
      if (!store.stats) loadStats()
      else recentActivity.value = (store.stats.recent_activity ?? []).slice(0, 20)
    }
  }, 100)
}

// Watch activeTab
// We use a simple approach: reload when entering the tab
// Since we can't watch inlined reactive props easily, we call loadShots on mounted

// ── Date formatting ───────────────────────────────────────────
function formatDate(iso: string): string {
  const d = new Date(iso)
  if (isNaN(d.getTime())) return iso
  const pad = (n: number) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`
}

// ── Mount ─────────────────────────────────────────────────────
onMounted(async () => {
  try {
    await Promise.all([loadStats(), loadShots(1)])
  } catch (e: unknown) {
    if (e instanceof Error) showError(e.message)
  }
})
</script>

<style scoped>
/* ── Layout ────────────────────────────────────────────────── */
.photographer-view {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.loading-overlay {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 48px;
  color: var(--muted);
  font-size: 0.9rem;
}

.spinner {
  display: inline-flex;
  align-items: center;
  gap: 8px;
}

.error-banner {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  background: oklch(65% 0.18 20);
  color: #fff;
  border-radius: var(--radius);
  font-size: 0.88rem;
}

.error-banner button {
  background: none;
  border: none;
  color: #fff;
  cursor: pointer;
  font-size: 1.1rem;
  opacity: 0.8;
}

/* ── Stats bar ─────────────────────────────────────────────── */
.stats-bar {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 16px;
}

.stat-item {
  display: flex;
  align-items: baseline;
  gap: 6px;
  padding: 8px 14px;
  background: var(--bg);
  border-radius: var(--radius-sm);
  flex: 1;
  min-width: 160px;
}

.stat-label {
  font-size: 0.82rem;
  color: var(--muted);
  white-space: nowrap;
}

.stat-value {
  font-size: 1.25rem;
  font-weight: 700;
  color: var(--fg);
  font-family: var(--font-display);
}

.stat-pass .stat-value { color: #16a34a; }
.stat-shortlist .stat-value { color: #2563eb; }
.stat-stock .stat-value { color: #9333ea; }
.stat-sales .stat-value { color: #ea580c; }

/* ── Tab bar ───────────────────────────────────────────────── */
.tab-bar {
  display: flex;
  gap: 4px;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 6px;
}

.tab-btn {
  flex: 1;
  padding: 10px 16px;
  border: none;
  border-radius: calc(var(--radius) - 6px);
  background: transparent;
  font-size: 0.9rem;
  font-weight: 600;
  color: var(--muted);
  cursor: pointer;
  transition: background 0.2s, color 0.2s;
  font-family: inherit;
}

.tab-btn:hover {
  color: var(--fg);
  background: var(--bg);
}

.tab-btn.active {
  background: var(--accent);
  color: #fff;
}

.tab-panel {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

/* ── Filter row ────────────────────────────────────────────── */
.filter-row {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  align-items: flex-end;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 12px 16px;
}

.filter-select,
.filter-input {
  padding: 7px 12px;
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  font-size: 0.84rem;
  background: var(--surface);
  color: var(--fg);
  font-family: inherit;
  min-width: 140px;
}

.filter-input {
  min-width: 200px;
}

/* ── Shot grid ─────────────────────────────────────────────── */
.shot-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
}

@media (max-width: 1200px) {
  .shot-grid { grid-template-columns: repeat(3, 1fr); }
}

@media (max-width: 900px) {
  .shot-grid { grid-template-columns: repeat(2, 1fr); }
}

@media (max-width: 600px) {
  .shot-grid { grid-template-columns: 1fr; }
}

/* ── Shot card ─────────────────────────────────────────────── */
.shot-card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  overflow: hidden;
  transition: box-shadow 0.2s, border-color 0.2s;
  cursor: pointer;
}

.shot-card:hover {
  box-shadow: 0 4px 16px oklch(0 0 0 / 0.08);
}

.shot-card.status-pass { border-left: 4px solid #16a34a; }
.shot-card.status-reject { border-left: 4px solid #ef4444; }
.shot-card.status-shortlist { border-left: 4px solid #2563eb; }
.shot-card.status-hold { border-left: 4px solid #ea580c; }

.shot-thumb {
  position: relative;
  width: 100%;
  padding-top: 66.67%;
  overflow: hidden;
  background: var(--bg);
}

.shot-thumb img {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: transform 0.3s;
}

.shot-card:hover .shot-thumb img {
  transform: scale(1.03);
}

.status-badge {
  position: absolute;
  bottom: 8px;
  right: 8px;
  font-size: 0.7rem;
  font-weight: 700;
  padding: 2px 8px;
  border-radius: 10px;
  z-index: 2;
  text-shadow: 0 1px 2px oklch(0 0 0 / 0.4);
}

.badge-unreviewed { background: oklch(50% 0.02 240); color: #fff; }
.badge-pass { background: #16a34a; color: #fff; }
.badge-hold { background: #ea580c; color: #fff; }
.badge-reject { background: #ef4444; color: #fff; }
.badge-shortlist { background: #2563eb; color: #fff; }

.shot-info {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  font-size: 0.82rem;
  border-top: 1px solid var(--border);
  background: var(--surface);
}

.shot-name {
  flex: 1;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  color: var(--fg);
}

.shot-dims {
  color: var(--muted);
  font-size: 0.75rem;
  flex-shrink: 0;
}

.shot-actions {
  display: flex;
  gap: 6px;
  padding: 8px 12px;
  border-top: 1px solid var(--border);
  background: var(--bg);
}

/* ── Buttons ───────────────────────────────────────────────── */
.btn {
  padding: 8px 16px;
  border-radius: var(--radius-sm);
  font-size: 0.84rem;
  cursor: pointer;
  border: 1px solid var(--border);
  background: var(--surface);
  color: var(--fg);
  font-family: inherit;
  transition: background 0.2s;
}

.btn:hover { background: var(--bg); }

.btn-sm { padding: 6px 14px; font-size: 0.82rem; }
.btn-xs { padding: 4px 10px; font-size: 0.75rem; }

.btn-outline {
  background: transparent;
  border-color: var(--muted);
}

.btn-outline:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.btn-green {
  background: #16a34a;
  color: #fff;
  border-color: #16a34a;
}

.btn-orange {
  background: #ea580c;
  color: #fff;
  border-color: #ea580c;
}

.btn-red {
  background: #ef4444;
  color: #fff;
  border-color: #ef4444;
}

/* ── Pagination ────────────────────────────────────────────── */
.pagination {
  display: flex;
  align-items: center;
  gap: 12px;
  justify-content: center;
  padding: 12px;
}

.page-info {
  font-size: 0.84rem;
  color: var(--muted);
}

/* ── GPS map ───────────────────────────────────────────────── */
.gps-map-placeholder {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.gps-summary {
  padding: 12px 16px;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  font-size: 0.9rem;
  color: var(--fg);
}

.gps-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 12px;
}

.gps-point-card {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
}

.gps-point-icon {
  font-size: 1.5rem;
  flex-shrink: 0;
}

.gps-point-name {
  font-size: 0.88rem;
  font-weight: 600;
  color: var(--fg);
}

.gps-point-coords {
  font-size: 0.78rem;
  color: var(--muted);
}

/* ── Stats detail ──────────────────────────────────────────── */
.stats-detail-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
  gap: 12px;
}

.detail-stat-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  padding: 20px 16px;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
}

.detail-stat-value {
  font-size: 1.5rem;
  font-weight: 700;
  color: var(--fg);
  font-family: var(--font-display);
}

.detail-stat-label {
  font-size: 0.8rem;
  color: var(--muted);
}

.stat-green .detail-stat-value { color: #16a34a; }
.stat-orange .detail-stat-value { color: #ea580c; }
.stat-red .detail-stat-value { color: #ef4444; }
.stat-blue .detail-stat-value { color: #2563eb; }
.stat-purple .detail-stat-value { color: #9333ea; }

.activity-section { margin-top: 8px; }
.section-title {
  font-size: 0.92rem;
  font-weight: 600;
  color: var(--fg);
  margin-bottom: 12px;
}

.activity-list {
  list-style: none;
  padding: 0;
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.activity-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 16px;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  font-size: 0.85rem;
}

.activity-name { flex: 1; color: var(--fg); }
.activity-time { color: var(--muted); font-size: 0.78rem; }

/* ── EXIF overlay ──────────────────────────────────────────── */
.exif-overlay {
  position: fixed;
  inset: 0;
  background: oklch(0 0 0 / 0.65);
  backdrop-filter: blur(4px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.exif-modal {
  background: var(--surface);
  border-radius: var(--radius-lg);
  max-width: 860px;
  width: 90%;
  max-height: 90vh;
  overflow-y: auto;
  position: relative;
  box-shadow: 0 8px 32px oklch(0 0 0 / 0.3);
}

.exif-close {
  position: absolute;
  top: 12px;
  right: 12px;
  width: 32px;
  height: 32px;
  border: none;
  border-radius: 50%;
  background: var(--bg);
  color: var(--fg);
  font-size: 1.2rem;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1;
}

.exif-close:hover { background: var(--border); }

.exif-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 20px;
  border-bottom: 1px solid var(--border);
}

.exif-name {
  font-size: 1rem;
  font-weight: 600;
  color: var(--fg);
}

.exif-dims {
  font-size: 0.84rem;
  color: var(--muted);
}

.exif-body {
  display: flex;
  gap: 24px;
  padding: 20px;
}

.exif-image {
  flex: 1;
  min-width: 0;
}

.exif-image img {
  width: 100%;
  border-radius: var(--radius);
  object-fit: cover;
  background: var(--bg);
}

.exif-data {
  flex: 1;
  min-width: 0;
}

.exif-section-title {
  font-size: 0.84rem;
  font-weight: 600;
  color: var(--muted);
  margin: 12px 0 8px;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.exif-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.84rem;
}

.exif-table td {
  padding: 4px 0;
  vertical-align: top;
}

.exif-table tr td:first-child {
  width: 80px;
  color: var(--muted);
  font-weight: 500;
}

.exif-table tr td:last-child {
  color: var(--fg);
}

.channel-list {
  list-style: none;
  padding: 0;
  margin: 0;
}

.channel-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 4px 0;
}

.channel-name { flex: 1; color: var(--fg); font-size: 0.84rem; }

.channel-status {
  font-size: 0.72rem;
  padding: 2px 8px;
  border-radius: 8px;
  font-weight: 600;
}

.channel-status.status-submitted { background: oklch(50% 0.02 240 / 0.2); color: var(--fg); }
.channel-status.status-active { background: #16a34a; color: #fff; }
.channel-status.status-rejected { background: #ef4444; color: #fff; }

.exif-meta {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
  margin-top: 16px;
  padding-top: 12px;
  border-top: 1px solid var(--border);
}

.meta-row {
  display: flex;
  justify-content: space-between;
  font-size: 0.82rem;
  color: var(--muted);
}

.meta-row span:last-child { color: var(--fg); font-weight: 500; }

/* ── Sub-component layouts ───────────────────────────────────── */
.culling-layout,
.stock-layout {
  display: grid;
  grid-template-columns: 1fr 340px;
  gap: 16px;
}

.stock-layout .stock-left {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.culling-sidebar,
.stock-right {
  display: flex;
  flex-direction: column;
  gap: 0;
}

/* ── Responsive ──────────────────────────────────────────────── */
@media (max-width: 1024px) {
  .culling-layout,
  .stock-layout {
    grid-template-columns: 1fr;
  }
  .stats-bar {
    flex-direction: column;
  }
  .stat-item {
    min-width: unset;
  }
}
</style>
