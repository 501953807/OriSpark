<template>
  <div class="package-panel">
    <!-- Header -->
    <div class="panel-header">
      <h3 class="panel-title">📥 工程包管理</h3>
      <span class="panel-desc">导出项目素材、时间线和特效配置</span>
    </div>

    <!-- Work selector -->
    <div class="selector-section">
      <label class="form-label">选择项目</label>
      <select v-model="selectedWorkId" class="form-select" :disabled="store.loading">
        <option value="" disabled>-- 请选择项目 --</option>
        <option v-for="v in storeVideos" :key="v.work_id" :value="v.work_id">
          {{ v.title }}
        </option>
      </select>
      <p v-if="storeVideos.length === 0 && !store.loading" class="empty-text">
        暂无项目
      </p>
    </div>

    <!-- Asset list -->
    <div v-if="selectedWorkId" class="assets-section">
      <div class="section-header">
        <h4 class="section-title">项目资产</h4>
      </div>

      <!-- Timeline -->
      <div class="asset-group">
        <div class="group-header">
          <span class="group-icon">🎥</span>
          <span class="group-name">时间线</span>
          <span class="group-count">{{ timelineAssets.length }} 项</span>
        </div>
        <div v-if="timelineAssets.length === 0" class="empty-group">
          尚无时间线数据
        </div>
        <ul v-else class="asset-list">
          <li v-for="asset in timelineAssets" :key="asset.name" class="asset-item">
            <span class="asset-icon">{{ asset.typeIcon }}</span>
            <span class="asset-name">{{ asset.name }}</span>
            <span class="asset-size">{{ asset.size }}</span>
          </li>
        </ul>
      </div>

      <!-- Materials -->
      <div class="asset-group">
        <div class="group-header">
          <span class="group-icon">📷</span>
          <span class="group-name">素材</span>
          <span class="group-count">{{ materialAssets.length }} 项</span>
        </div>
        <div v-if="materialAssets.length === 0" class="empty-group">
          尚无素材数据
        </div>
        <ul v-else class="asset-list">
          <li v-for="asset in materialAssets" :key="asset.name" class="asset-item">
            <span class="asset-icon">{{ asset.typeIcon }}</span>
            <span class="asset-name">{{ asset.name }}</span>
            <span class="asset-size">{{ asset.size }}</span>
          </li>
        </ul>
      </div>

      <!-- Effects -->
      <div class="asset-group">
        <div class="group-header">
          <span class="group-icon">🌴️</span>
          <span class="group-name">特效配置</span>
          <span class="group-count">{{ effectAssets.length }} 项</span>
        </div>
        <div v-if="effectAssets.length === 0" class="empty-group">
          尚无特效数据
        </div>
        <ul v-else class="asset-list">
          <li v-for="asset in effectAssets" :key="asset.name" class="asset-item">
            <span class="asset-icon">{{ asset.typeIcon }}</span>
            <span class="asset-name">{{ asset.name }}</span>
            <span class="asset-size">{{ asset.size }}</span>
          </li>
        </ul>
      </div>
    </div>

    <!-- Export button -->
    <div v-if="selectedWorkId" class="action-section">
      <button
        class="btn btn-primary btn-full"
        :disabled="exporting"
        @click="handleExport"
      >
        <span v-if="exporting" class="spinner"></span>
        {{ exporting ? '导出中...' : '一键导出工程包' }}
      </button>
      <p class="export-hint">将打包所有素材、时间线、特效配置为 zip 文件</p>
    </div>

    <!-- Download history -->
    <div class="history-section">
      <div class="section-header">
        <h4 class="section-title">下载历史</h4>
      </div>
      <div v-if="downloadHistory.length === 0" class="empty-history">
        <span class="empty-icon">🗁</span>
        <p>暂无下载记录</p>
      </div>
      <ul v-else class="history-list">
        <li v-for="(entry, idx) in downloadHistory" :key="idx" class="history-item">
          <span class="history-icon">⬇</span>
          <div class="history-info">
            <span class="history-name">{{ entry.name }}</span>
            <span class="history-meta">{{ entry.date }} · {{ entry.size }}</span>
          </div>
          <button class="btn btn-xs btn-ghost" @click="handleRetry(entry)">
            重新下载
          </button>
        </li>
      </ul>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useVideoStore } from '@/stores/useVideoStore'
import type { VideoWork } from '@/types/video'

interface HistoryEntry {
  name: string
  date: string
  size: string
}

interface AssetItem {
  name: string
  size: string
  typeIcon: string
}

const store = useVideoStore()
const selectedWorkId = ref('')
const exporting = ref(false)

const storeVideos = computed(() => store.videos)

watch(selectedWorkId, async (id) => {
  if (id) await loadAssets(id)
  else {
    timelineAssets.value = []
    materialAssets.value = []
    effectAssets.value = []
  }
})

// ── Asset data (loaded from API when endpoint is ready) ──────────
const timelineAssets = ref<AssetItem[]>([])
const materialAssets = ref<AssetItem[]>([])
const effectAssets = ref<AssetItem[]>([])

async function loadAssets(workId: string) {
  // TODO: Replace with videoApi.getProjectPackageAssets(workId) when backend endpoint is ready
  // const res = await videoApi.getProjectPackageAssets(workId)
  // timelineAssets.value = res.data.timeline
  // materialAssets.value = res.data.materials
  // effectAssets.value = res.data.effects
}

// ── Download history ───────────────────────────────────────────
const downloadHistory = ref<HistoryEntry[]>([])

// ── Actions ────────────────────────────────────────────────────
async function handleExport() {
  if (!selectedWorkId.value) {
    ;(window as any)?.$toast?.show('请先选择一个项目', 'warning')
    return
  }

  exporting.value = true
  try {
    // TODO: Call videoApi.exportProjectPackage(selectedWorkId.value) when backend is ready
    ;(window as any)?.$toast?.show('工程包导出功能开发中，请稍后再试', 'info')
  } catch (e: unknown) {
    const msg = e instanceof Error ? e.message : '导出失败'
    ;(window as any)?.$toast?.show(msg, 'error')
  } finally {
    exporting.value = false
  }
}

function handleRetry(entry: HistoryEntry) {
  downloadHistory.value = [entry, ...downloadHistory.value]
  ;(window as any)?.$toast?.show(`已开始重新下载 ${entry.name}`, 'info')
}
</script>

<style scoped>
.package-panel {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

/* ── Panel header ─────────────────────────────────────────────── */
.panel-header {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.panel-title {
  font-size: 1.05rem;
  font-weight: 600;
  color: var(--fg);
  margin: 0;
}

.panel-desc {
  font-size: 0.82rem;
  color: var(--muted);
}

/* ── Selector ─────────────────────────────────────────────────── */
.selector-section,
.action-section {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.form-label {
  display: block;
  font-size: 0.78rem;
  font-weight: 600;
  color: var(--muted);
  text-transform: uppercase;
  letter-spacing: 0.04em;
}

.form-select {
  width: 100%;
  padding: 10px 14px;
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  font-size: 0.9rem;
  background: var(--surface);
  color: var(--fg);
  font-family: inherit;
  transition: border-color 0.2s;
}

.form-select:focus {
  outline: none;
  border-color: var(--accent);
}

.empty-text {
  font-size: 0.84rem;
  color: var(--muted);
  font-style: italic;
}

/* ── Assets section ───────────────────────────────────────────── */
.assets-section {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.section-title {
  font-size: 0.92rem;
  font-weight: 600;
  color: var(--fg);
  margin: 0;
}

.asset-group {
  padding: 14px 16px;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
}

.group-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
  padding-bottom: 8px;
  border-bottom: 1px solid var(--border);
}

.group-icon {
  font-size: 1rem;
}

.group-name {
  font-size: 0.88rem;
  font-weight: 600;
  color: var(--fg);
  flex: 1;
}

.group-count {
  font-size: 0.75rem;
  color: var(--muted);
  background: var(--bg);
  padding: 2px 8px;
  border-radius: 100px;
}

.empty-group {
  font-size: 0.82rem;
  color: var(--muted);
  font-style: italic;
  padding: 8px 0;
}

.asset-list {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.asset-item {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 0.84rem;
  color: var(--fg);
  padding: 4px 0;
}

.asset-icon {
  font-size: 0.78rem;
  color: var(--muted);
  width: 24px;
  text-align: center;
  flex-shrink: 0;
}

.asset-name {
  flex: 1;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.asset-size {
  font-size: 0.78rem;
  color: var(--muted);
  flex-shrink: 0;
}

/* ── Export button ─────────────────────────────────────────────── */
.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 10px 18px;
  border-radius: var(--radius-sm);
  font-size: 0.88rem;
  font-weight: 600;
  cursor: pointer;
  border: 1px solid var(--border);
  background: var(--surface);
  color: var(--fg);
  font-family: inherit;
  transition: background 0.2s, opacity 0.2s;
}

.btn:hover:not(:disabled) {
  background: var(--bg);
}

.btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.btn-full {
  width: 100%;
}

.btn-primary {
  background: var(--accent);
  color: #fff;
  border-color: var(--accent);
}

.btn-primary:hover:not(:disabled) {
  opacity: 0.9;
}

.btn-xs {
  padding: 4px 10px;
  font-size: 0.78rem;
}

.btn-ghost {
  background: transparent;
  border: none;
  color: var(--muted);
}

.export-hint {
  font-size: 0.78rem;
  color: var(--muted);
  text-align: center;
  margin: 0;
}

.spinner {
  display: inline-block;
  width: 14px;
  height: 14px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-top-color: #fff;
  border-radius: 50%;
  animation: spin 0.6s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* ── History section ──────────────────────────────────────────── */
.history-section {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.empty-history {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 24px;
  color: var(--muted);
  gap: 8px;
  background: var(--surface);
  border: 1px dashed var(--border);
  border-radius: var(--radius-sm);
}

.empty-icon {
  font-size: 1.5rem;
}

.history-list {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.history-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 14px;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  font-size: 0.84rem;
}

.history-icon {
  font-size: 1rem;
  color: var(--accent);
}

.history-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
}

.history-name {
  font-weight: 500;
  color: var(--fg);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.history-meta {
  font-size: 0.75rem;
  color: var(--muted);
}
</style>
