<template>
  <div class="video-creator-view">
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
        <span class="stat-label">&#127907; 总视频</span>
        <span class="stat-value">{{ stats.total_videos }}</span>
      </div>
      <div class="stat-item stat-plays">
        <span class="stat-label">&#128065; 播放量</span>
        <span class="stat-value">{{ formatPlays(stats.total_plays) }}</span>
      </div>
      <div class="stat-item stat-scan">
        <span class="stat-label">&#128269; 指纹扫描</span>
        <span class="stat-value">{{ stats.fingerprint_scans }}</span>
      </div>
      <div class="stat-item stat-infringement">
        <span class="stat-label">&#9888;&#65039; 侵权</span>
        <span class="stat-value">{{ stats.infringement_count }}</span>
      </div>
      <div class="stat-item stat-revenue">
        <span class="stat-label">&#128176; 本月收益</span>
        <span class="stat-value">¥{{ stats.monthly_revenue?.toFixed(0) ?? 0 }}</span>
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

    <!-- ========== 视频列表 tab ========== -->
    <div v-if="activeTab === 'list'" class="tab-panel">
      <!-- Filter row -->
      <div class="filter-row">
        <select v-model="filters.fingerprint_status" class="filter-select" @change="loadVideos(1)">
          <option value="">全部状态</option>
          <option value="pending">待扫描</option>
          <option value="processing">扫描中</option>
          <option value="completed">已完成</option>
          <option value="failed">失败</option>
        </select>
        <select v-model="filters.format" class="filter-select" @change="loadVideos(1)">
          <option value="">全部格式</option>
          <option value="mp4">MP4</option>
          <option value="mov">MOV</option>
          <option value="avi">AVI</option>
          <option value="webm">WebM</option>
        </select>
        <input
          v-model="searchKeyword"
          class="filter-input"
          placeholder="搜索视频名..."
          @keyup.enter="loadVideos(1)"
        />
        <button class="btn btn-sm btn-outline" @click="resetFilters">重置</button>
      </div>

      <!-- Video grid -->
      <div v-if="store.videos.length === 0 && !store.loading" class="empty-state">
        <div class="empty-icon">&#127909;</div>
        <p>暂无视频作品</p>
      </div>
      <div v-else class="video-grid">
        <div
          v-for="video in store.videos"
          :key="video.id"
          :class="['video-card', `status-${video.fingerprint_status}`]"
        >
          <!-- Thumbnail -->
          <div class="video-thumb">
            <img
              v-if="video.thumbnail_path"
              :src="video.thumbnail_path"
              :alt="video.title"
              loading="lazy"
            />
            <div v-else class="thumb-placeholder">
              <span>&#127909;</span>
            </div>
            <!-- Duration badge -->
            <span v-if="video.duration_seconds" class="duration-badge">
              {{ formatDuration(video.duration_seconds) }}
            </span>
            <!-- Fingerprint status -->
            <span :class="['fp-badge', `fp-${video.fingerprint_status}`]">
              {{ fpStatusLabel(video.fingerprint_status) }}
            </span>
          </div>
          <!-- Info -->
          <div class="video-info">
            <span class="video-title">{{ video.title }}</span>
            <span class="video-meta">
              {{ video.format ?? '未知' }} · {{ formatFileSize(video.file_size) }}
            </span>
          </div>
          <!-- Actions -->
          <div class="video-actions">
            <button class="btn btn-xs btn-accent" @click="handleScan(video.id)">
              &#128269; 指纹扫描
            </button>
            <button
              v-if="video.match_count && video.match_count > 0"
              class="btn btn-xs btn-danger"
              @click="activeTab = 'fingerprint'; selectedVideoId = video.work_id"
            >
              &#9888;&#65039; {{ video.match_count }} 匹配
            </button>
          </div>
        </div>
      </div>

      <!-- Pagination -->
      <div v-if="store.pagination.total_pages > 1" class="pagination">
        <button
          :disabled="filters.page! <= 1"
          class="btn btn-sm btn-outline"
          @click="loadVideos(filters.page! - 1)"
        >&laquo; 上一页</button>
        <span class="page-info">第 {{ filters.page }} / {{ store.pagination.total_pages }} 页</span>
        <button
          :disabled="filters.page! >= store.pagination.total_pages"
          class="btn btn-sm btn-outline"
          @click="loadVideos(filters.page! + 1)"
        >下一页 &raquo;</button>
      </div>
    </div>

    <!-- ========== 指纹扫描 tab ========== -->
    <div v-if="activeTab === 'fingerprint'" class="tab-panel">
      <div class="fingerprint-panel">
        <h3 class="section-title">视频指纹侵权扫描</h3>

        <!-- Scan target selector -->
        <div class="scan-target">
          <select v-model="selectedVideoId" class="filter-select">
            <option value="" disabled>选择要扫描的视频</option>
            <option v-for="v in store.videos" :key="v.id" :value="v.work_id">
              {{ v.title }}
            </option>
          </select>
          <button
            class="btn btn-primary"
            :disabled="!selectedVideoId || store.fingerprintLoading"
            @click="handleFingerprintScan"
          >
            <span v-if="store.fingerprintLoading" class="spinner-small">加载中...</span>
            <span v-else>&#128269; 发起扫描</span>
          </button>
        </div>

        <!-- Scan result -->
        <div v-if="scanResult" class="scan-result">
          <div class="result-summary">
            <span :class="['result-badge', scanResult.matches_found ? 'result-warning' : 'result-ok']">
              {{ scanResult.matches_found ? `发现 ${scanResult.matches_found} 处匹配` : '未发现侵权' }}
            </span>
            <span v-if="scanResult.frames_extracted" class="result-detail">
              提取 {{ scanResult.frames_extracted }} 帧
            </span>
          </div>
        </div>

        <!-- Match results list -->
        <div v-if="store.matches.length > 0" class="match-list">
          <h4 class="section-title">匹配结果</h4>
          <div class="match-card" v-for="m in store.matches" :key="m.match_id">
            <div class="match-similarity">相似度: {{ m.similarity.toFixed(1) }}%</div>
            <div class="match-detail">
              <span>匹配帧: {{ m.matched_frames }}</span>
              <span>首帧: #{{ m.first_match_frame }}</span>
            </div>
            <a v-if="m.source_url" :href="m.source_url" target="_blank" class="match-link">
              查看来源 &rarr;
            </a>
          </div>
        </div>
      </div>
    </div>

    <!-- ========== 工程包 tab ========== -->
    <div v-if="activeTab === 'package'" class="tab-panel">
      <ProjectPackagePanel />
    </div>

    <!-- ========== 分发 tab ========== -->
    <div v-if="activeTab === 'distribute'" class="tab-panel">
      <div class="distribute-panel">
        <h3 class="section-title">多平台分发</h3>
        <div class="platform-grid">
          <div
            v-for="p in platforms"
            :key="p.key"
            :class="['platform-card', `platform-${p.key}`, { busy: p.loading }]"
          >
            <div class="platform-icon">{{ p.icon }}</div>
            <div class="platform-name">{{ p.name }}</div>
            <div class="platform-status">{{ statusLabel(p.status) }}</div>
            <button
              class="btn btn-sm btn-outline"
              :disabled="p.loading || !selectedVideoId"
              @click="handleDistribute(p.key)"
            >
              {{ p.loading ? '分发中...' : '分发到' + p.name }}
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed } from 'vue'
import { useVideoStore } from '@/stores/useVideoStore'
import type { VideoStats, FingerprintStatus } from '@/types/video'
import ProjectPackagePanel from '@/components/video/ProjectPackagePanel.vue'

const store = useVideoStore()

// ── Tabs ─────────────────────────────────────────────────────
const tabs = [
  { key: 'list', label: '&#127909; 视频列表' },
  { key: 'fingerprint', label: '&#128269; 指纹扫描' },
  { key: 'package', label: '&#128230; 工程包' },
  { key: 'distribute', label: '&#128233; 分发' },
]
const activeTab = ref<string>('list')

// ── Error handling ──────────────────────────────────────────
const errorMsg = ref('')
function showError(msg: string) {
  errorMsg.value = msg
  console.error(msg)
}

// ── Stats ───────────────────────────────────────────────────
const stats = ref<VideoStats>({
  total_videos: 0,
  total_plays: 0,
  fingerprint_scans: 0,
  infringement_count: 0,
  monthly_revenue: 0,
})

async function loadStats() {
  try {
    const result = await store.fetchStats()
    if (result) {
      stats.value = result
    }
  } catch (e: unknown) {
    if (e instanceof Error) showError(e.message)
  }
}

// ── Videos & filters ────────────────────────────────────────
const filters = reactive({
  fingerprint_status: '' as string | FingerprintStatus,
  format: '' as string,
  page: 1,
  page_size: 24,
})
const searchKeyword = ref('')

async function loadVideos(page?: number) {
  if (page !== undefined) filters.page = page
  const params: Record<string, unknown> = {}
  if (filters.fingerprint_status) params.fingerprint_status = filters.fingerprint_status
  if (filters.format) params.format = filters.format
  if (filters.page) params.page = filters.page
  if (filters.page_size) params.page_size = filters.page_size
  try {
    await store.fetchVideos(params)
  } catch (e: unknown) {
    if (e instanceof Error) showError(e.message)
    store.videos = []
  }
}

function resetFilters() {
  filters.fingerprint_status = ''
  filters.format = ''
  filters.page = 1
  searchKeyword.value = ''
  loadVideos()
}

// ── Fingerprint ─────────────────────────────────────────────
const selectedVideoId = ref('')
const scanResult = ref<any>(null)

async function handleScan(workId: string) {
  try {
    const result = await store.scanFingerprint(workId)
    if (result) {
      scanResult.value = result
      await store.getMatches(workId)
      ;(window as any).$toast?.show('指纹扫描完成', 'success')
    }
  } catch (e: unknown) {
    const msg = e instanceof Error ? e.message : '扫描失败'
    ;(window as any).$toast?.show(msg, 'error')
  }
}

async function handleFingerprintScan() {
  if (!selectedVideoId.value) return
  await handleScan(selectedVideoId.value)
}

// ── Platforms ───────────────────────────────────────────────
interface PlatformState {
  key: string
  name: string
  icon: string
  status: 'idle' | 'uploading' | 'published' | 'failed'
  loading: boolean
}

const platforms = ref<PlatformState[]>([
  { key: 'bilibili', name: 'B站', icon: '&#128235;', status: 'idle', loading: false },
  { key: 'douyin', name: '抖音', icon: '&#127916;', status: 'idle', loading: false },
  { key: 'youtube', name: 'YouTube', icon: '&#9654;', status: 'idle', loading: false },
  { key: 'wechat', name: '视频号', icon: '&#128172;', status: 'idle', loading: false },
])

function statusLabel(s: string): string {
  const labels: Record<string, string> = {
    idle: '未分发',
    uploading: '上传中',
    published: '已发布',
    failed: '失败',
  }
  return labels[s] ?? s
}

async function handleDistribute(platform: string) {
  if (!selectedVideoId.value) {
    ;(window as any).$toast?.show('请先选择一个视频', 'warning')
    return
  }
  const p = platforms.value.find((pp) => pp.key === platform)
  if (!p) return
  p.loading = true
  p.status = 'uploading'
  try {
    const result = await store.distributeToPlatform(selectedVideoId.value, platform, '', '')
    if (result) {
      p.status = result.status
      ;(window as any).$toast?.show(`已分发到 ${p.name}`, 'success')
    } else {
      p.status = 'failed'
      ;(window as any).$toast?.show(`分发到 ${p.name} 失败`, 'error')
    }
  } catch (e: unknown) {
    const msg = e instanceof Error ? e.message : '分发失败'
    p.status = 'failed'
    ;(window as any).$toast?.show(msg, 'error')
  } finally {
    p.loading = false
  }
}

// ── Helpers ─────────────────────────────────────────────────
function formatDuration(seconds: number): string {
  const m = Math.floor(seconds / 60)
  const s = seconds % 60
  return `${m}:${String(s).padStart(2, '0')}`
}

function formatPlays(n: number): string {
  if ((n ?? 0) >= 10000) return `${(n! / 10000).toFixed(1)}万`
  if ((n ?? 0) >= 1000) return `${(n! / 1000).toFixed(1)}K`
  return String(n ?? 0)
}

function formatFileSize(bytes?: number): string {
  if (!bytes) return '-'
  if (bytes >= 1024 * 1024 * 1024) return `${(bytes / (1024 * 1024 * 1024)).toFixed(1)} GB`
  if (bytes >= 1024 * 1024) return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
  return `${(bytes / 1024).toFixed(0)} KB`
}

function fpStatusLabel(status: FingerprintStatus): string {
  const labels: Record<FingerprintStatus, string> = {
    pending: '待扫描',
    processing: '扫描中',
    completed: '已完成',
    failed: '失败',
  }
  return labels[status] ?? status
}

// ── Watch tab changes ───────────────────────────────────────
let tabLoadTimer: ReturnType<typeof setTimeout> | null = null

function handleTabChange() {
  if (tabLoadTimer) clearTimeout(tabLoadTimer)
  tabLoadTimer = setTimeout(() => {
    if (activeTab.value === 'list') {
      loadVideos(1)
    } else if (activeTab.value === 'fingerprint' && selectedVideoId.value) {
      store.getMatches(selectedVideoId.value)
    }
  }, 100)
}

// ── Lifecycle ───────────────────────────────────────────────
onMounted(async () => {
  try {
    await Promise.all([loadStats(), loadVideos(1)])
  } catch (e: unknown) {
    if (e instanceof Error) showError(e.message)
  }
})
</script>

<style scoped>
/* ── Layout ────────────────────────────────────────────────── */
.video-creator-view {
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

.spinner-small {
  font-size: 0.82rem;
  color: var(--muted);
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
  min-width: 140px;
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

.stat-plays .stat-value { color: #2563eb; }
.stat-scan .stat-value { color: #9333ea; }
.stat-infringement .stat-value { color: #ef4444; }
.stat-revenue .stat-value { color: #ea580c; }

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

/* ── Video grid ────────────────────────────────────────────── */
.video-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
  gap: 16px;
}

.video-card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  overflow: hidden;
  transition: box-shadow 0.2s, border-color 0.2s;
}

.video-card:hover {
  box-shadow: 0 4px 16px oklch(0 0 0 / 0.08);
}

.video-card.status-completed { border-top: 3px solid #16a34a; }
.video-card.status-pending { border-top: 3px solid #94a3b8; }
.video-card.status-processing { border-top: 3px solid #2563eb; }
.video-card.status-failed { border-top: 3px solid #ef4444; }

.video-thumb {
  position: relative;
  width: 100%;
  padding-top: 56.25%;
  background: var(--bg);
  overflow: hidden;
}

.video-thumb img {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.thumb-placeholder {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 2.5rem;
  color: var(--muted);
}

.duration-badge {
  position: absolute;
  bottom: 8px;
  right: 8px;
  font-size: 0.72rem;
  font-weight: 600;
  padding: 2px 8px;
  border-radius: 4px;
  background: oklch(0 0 0 / 0.7);
  color: #fff;
}

.fp-badge {
  position: absolute;
  top: 8px;
  right: 8px;
  font-size: 0.68rem;
  font-weight: 600;
  padding: 2px 8px;
  border-radius: 10px;
  color: #fff;
}

.fp-pending { background: #94a3b8; }
.fp-processing { background: #2563eb; }
.fp-completed { background: #16a34a; }
.fp-failed { background: #ef4444; }

.video-info {
  padding: 10px 12px;
  border-top: 1px solid var(--border);
}

.video-title {
  display: block;
  font-size: 0.88rem;
  font-weight: 600;
  color: var(--fg);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.video-meta {
  display: block;
  font-size: 0.78rem;
  color: var(--muted);
  margin-top: 2px;
}

.video-actions {
  display: flex;
  gap: 8px;
  padding: 10px 12px;
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

.btn-primary {
  background: var(--accent);
  color: #fff;
  border-color: var(--accent);
}

.btn-primary:hover {
  opacity: 0.9;
}

.btn-accent {
  background: var(--accent);
  color: #fff;
  border-color: var(--accent);
}

.btn-danger {
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

/* ── Empty state ───────────────────────────────────────────── */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 64px 24px;
  color: var(--muted);
  font-size: 0.95rem;
}

.empty-icon {
  font-size: 3rem;
  margin-bottom: 12px;
}

.hint {
  font-size: 0.8rem;
  margin-top: 8px;
  opacity: 0.7;
}

/* ── Fingerprint panel ─────────────────────────────────────── */
.fingerprint-panel {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.scan-target {
  display: flex;
  gap: 12px;
  align-items: center;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 12px 16px;
}

.scan-target .filter-select {
  flex: 1;
  min-width: unset;
}

.result-summary {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 16px;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
}

.result-badge {
  font-size: 0.92rem;
  font-weight: 600;
}

.result-ok { color: #16a34a; }
.result-warning { color: #ea580c; }

.result-detail {
  font-size: 0.84rem;
  color: var(--muted);
}

.match-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.match-card {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 12px 16px;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
}

.match-similarity {
  font-weight: 700;
  font-size: 0.92rem;
  color: #ef4444;
  min-width: 100px;
}

.match-detail {
  display: flex;
  gap: 16px;
  font-size: 0.82rem;
  color: var(--muted);
}

.match-link {
  margin-left: auto;
  font-size: 0.84rem;
  color: var(--accent);
  text-decoration: none;
}

.match-link:hover { text-decoration: underline; }

/* ── Section titles ────────────────────────────────────────── */
.section-title {
  font-size: 0.92rem;
  font-weight: 600;
  color: var(--fg);
  margin: 0;
}

.panel-desc {
  font-size: 0.88rem;
  color: var(--muted);
  margin: 0 0 8px;
}

/* ── Package panel ─────────────────────────────────────────── */
.package-panel {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

/* ── Distribute panel ──────────────────────────────────────── */
.distribute-panel {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.platform-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: 16px;
}

.platform-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  padding: 24px 16px;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  text-align: center;
}

.platform-card.busy {
  opacity: 0.6;
  pointer-events: none;
}

.platform-icon {
  font-size: 2.5rem;
}

.platform-name {
  font-size: 0.92rem;
  font-weight: 600;
  color: var(--fg);
}

.platform-status {
  font-size: 0.82rem;
  color: var(--muted);
}

/* ── Responsive ─────────────────────────────────────────────── */
@media (max-width: 1024px) {
  .stats-bar {
    flex-direction: column;
  }
  .stat-item {
    min-width: unset;
  }
}
</style>
