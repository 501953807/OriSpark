<template>
  <div class="fingerprint-panel">
    <!-- Header -->
    <div class="panel-header">
      <h3 class="panel-title">&#128270; 视频指纹侵权扫描</h3>
      <span class="panel-desc">选择视频发起扫描，自动比对全网侵权内容</span>
    </div>

    <!-- Video selector -->
    <div class="selector-section">
      <label class="form-label">选择视频作品</label>
      <select v-model="selectedWorkId" class="form-select" :disabled="store.loading">
        <option value="" disabled>-- 请选择作品 --</option>
        <option v-for="v in storeVideos" :key="v.work_id" :value="v.work_id">
          {{ v.title }}
          <template v-if="v.duration_seconds"> ({{ Math.round(v.duration_seconds / 60) }}分)</template>
        </option>
      </select>
      <p v-if="storeVideos.length === 0 && !store.loading" class="empty-text">
        暂无视频作品
      </p>
    </div>

    <!-- Scan button -->
    <div class="action-section">
      <button
        class="btn btn-primary btn-full"
        :disabled="!selectedWorkId || store.fingerprintLoading"
        @click="handleScan"
      >
        <span v-if="store.fingerprintLoading" class="spinner"></span>
        {{ store.fingerprintLoading ? '扫描中...' : '发起指纹扫描' }}
      </button>
    </div>

    <!-- Scan result summary -->
    <div v-if="fingerprintResult" class="result-summary">
      <div class="summary-card">
        <div class="summary-item">
          <span class="summary-label">提取帧数</span>
          <span class="summary-value">{{ fingerprintResult.frames_extracted ?? 0 }}</span>
        </div>
        <div class="summary-item">
          <span class="summary-label">匹配数</span>
          <span class="summary-value highlight">{{ fingerprintResult.matches_found ?? 0 }}</span>
        </div>
        <div class="summary-item">
          <span class="summary-label">状态</span>
          <span class="summary-value">{{ STATUS_LABELS[fingerprintResult.status] || fingerprintResult.status }}</span>
        </div>
      </div>
    </div>

    <!-- Matches list -->
    <div v-if="matches.length > 0" class="matches-section">
      <div class="section-header">
        <h4 class="section-title">&#128270; 匹配结果 ({{ matches.length }})</h4>
        <button class="btn btn-xs btn-ghost" @click="sortOrder = sortOrder === 'desc' ? 'asc' : 'desc'">
          排序: {{ sortOrder === 'desc' ? '降序' : '升序' }}
        </button>
      </div>
      <div class="matches-list">
        <div
          v-for="match in sortedMatches"
          :key="match.match_id"
          class="match-item"
          :class="{ risk: match.similarity >= 80 }"
        >
          <div class="match-similarity">
            <span class="similarity-bar" :style="{ width: match.similarity + '%' }"
                 :class="similarityColorClass(match.similarity)"></span>
            <span class="similarity-value" :class="similarityTextColorClass(match.similarity)">
              {{ match.similarity.toFixed(1) }}%
            </span>
          </div>
          <div class="match-meta">
            <span>匹配帧: {{ match.matched_frames }}</span>
            <span>首帧位置: #{{ match.first_match_frame }}</span>
          </div>
          <a
            v-if="match.source_url"
            :href="match.source_url"
            target="_blank"
            rel="noopener"
            class="match-source"
          >
            查看来源 &rarr;
          </a>
          <span v-else class="match-source muted">来源未记录</span>
        </div>
      </div>
    </div>

    <!-- No matches state -->
    <div v-if="fingerprintResult && matches.length === 0 && !store.fingerprintLoading" class="no-matches">
      <span class="no-match-icon">&#128994;</span>
      <p>未发现匹配的侵权内容</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useVideoStore } from '@/stores/useVideoStore'
import type { VideoWork, VideoMatchResult } from '@/types/video'

const store = useVideoStore()
const selectedWorkId = ref('')
const sortOrder = ref<'desc' | 'asc'>('desc')

const storeVideos = computed<VideoWork[]>(() => store.videos)

const matches = computed<VideoMatchResult[]>(() => store.matches)

const fingerprintResult = computed(() => {
  const m = store.matches
  const last = m[0]
  if (!last) return null
  return {
    video_id: last.match_id,
    status: 'completed',
    frames_extracted: 0,
    matches_found: m.length,
  }
})

const sortedMatches = computed(() => {
  const sorted = [...matches.value].sort((a, b) =>
    sortOrder.value === 'desc' ? b.similarity - a.similarity : a.similarity - b.similarity
  )
  return sorted
})

function similarityColorClass(similarity: number): string {
  if (similarity >= 90) return 'high-risk'
  if (similarity >= 70) return 'med-risk'
  return 'low-risk'
}

function similarityTextColorClass(similarity: number): string {
  if (similarity >= 90) return 'text-danger'
  if (similarity >= 70) return 'text-warning'
  return 'text-safe'
}

const STATUS_LABELS: Record<string, string> = {
  pending: '待处理',
  processing: '处理中',
  completed: '已完成',
  failed: '失败',
}

async function handleScan() {
  if (!selectedWorkId.value) {
    ;(window as any)?.$toast?.show('请选择一个视频作品', 'warning')
    return
  }

  try {
    // Start fingerprint scan
    const result = await store.scanFingerprint(selectedWorkId.value)

    if (!result) {
      ;(window as any)?.$toast?.show('指纹扫描失败', 'error')
      return
    }

    // Fetch matches
    const matchResults = await store.getMatches(selectedWorkId.value)

    if (matchResults.length > 0) {
      ;(window as any)?.$toast?.show(`扫描完成，发现 ${matchResults.length} 条侵权匹配`, 'info')
    } else {
      ;(window as any)?.$toast?.show('扫描完成，未发现侵权内容', 'success')
    }
  } catch (e: unknown) {
    const msg = e instanceof Error ? e.message : '扫描失败'
    ;(window as any)?.$toast?.show(msg, 'error')
  }
}
</script>

<style scoped>
.fingerprint-panel {
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

/* ── Buttons ──────────────────────────────────────────────────── */
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

/* ── Result summary ───────────────────────────────────────────── */
.result-summary {
  padding: 12px 0;
}

.summary-card {
  display: flex;
  gap: 20px;
  padding: 16px;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
}

.summary-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
  flex: 1;
}

.summary-label {
  font-size: 0.72rem;
  color: var(--muted);
  text-transform: uppercase;
  letter-spacing: 0.04em;
}

.summary-value {
  font-size: 1.2rem;
  font-weight: 700;
  color: var(--fg);
}

.summary-value.highlight {
  color: var(--accent);
}

/* ── Matches section ──────────────────────────────────────────── */
.matches-section {
  display: flex;
  flex-direction: column;
  gap: 12px;
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

.matches-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.match-item {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 14px 16px;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  transition: border-color 0.2s;
}

.match-item.risk {
  border-color: var(--orange);
  background: oklch(96% 0.01 55 / 0.3);
}

.match-item:hover {
  border-color: var(--muted);
}

.match-similarity {
  display: flex;
  align-items: center;
  gap: 10px;
}

.similarity-bar {
  height: 6px;
  flex: 1;
  border-radius: 3px;
  background: var(--border);
  min-width: 30px;
  transition: width 0.3s ease;
}

.similarity-bar.high-risk { background: #ef4444; }
.similarity-bar.med-risk { background: #f59e0b; }
.similarity-bar.low-risk { background: #16a34a; }

.similarity-value {
  font-size: 0.88rem;
  font-weight: 700;
  min-width: 52px;
  text-align: right;
}

.text-danger { color: #ef4444; }
.text-warning { color: #f59e0b; }
.text-safe { color: #16a34a; }

.match-meta {
  display: flex;
  gap: 16px;
  font-size: 0.8rem;
  color: var(--muted);
}

.match-source {
  font-size: 0.82rem;
  color: var(--accent);
  text-decoration: none;
  font-weight: 500;
  align-self: flex-start;
}

.match-source:hover {
  text-decoration: underline;
}

.match-source.muted {
  color: var(--muted);
  font-style: italic;
}

/* ── No matches ───────────────────────────────────────────────── */
.no-matches {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 32px;
  color: var(--muted);
  gap: 8px;
  background: var(--surface);
  border: 1px dashed var(--border);
  border-radius: var(--radius-sm);
}

.no-match-icon {
  font-size: 2rem;
}
</style>
