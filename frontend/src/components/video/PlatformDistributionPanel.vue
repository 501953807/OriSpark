<template>
  <div class="distribution-panel">
    <!-- Header -->
    <div class="panel-header">
      <h3 class="panel-title">&#128219; 多平台分发</h3>
      <span class="panel-desc">一键分发到多个内容平台</span>
    </div>

    <!-- Work selector -->
    <div class="selector-section">
      <label class="form-label">选择视频作品</label>
      <select v-model="selectedWorkId" class="form-select" :disabled="store.loading">
        <option value="" disabled>-- 请选择作品 --</option>
        <option v-for="v in storeVideos" :key="v.work_id" :value="v.work_id">
          {{ v.title }}
        </option>
      </select>
      <p v-if="storeVideos.length === 0 && !store.loading" class="empty-text">
        暂无视频作品
      </p>
    </div>

    <!-- Platform cards grid -->
    <div v-if="selectedWorkId" class="platforms-section">
      <div class="platforms-grid">
        <div
          v-for="platform in platformConfigs"
          :key="platform.type"
          :class="[
            'platform-card',
            `platform-${platform.type}`,
            { distributing: isDistributing(platform.type) }
          ]"
        >
          <!-- Icon + name -->
          <div class="card-header">
            <span class="platform-icon" :style="{ color: platform.color }">{{ platform.icon }}</span>
            <span class="platform-name">{{ platform.name }}</span>
          </div>

          <!-- Status badge -->
          <span :class="['status-badge', `status-${platform.state}`]">
            {{ STATUS_MAP[platform.state] }}
          </span>

          <!-- View / link if published -->
          <a
            v-if="platform.publishedUrl"
            :href="platform.publishedUrl"
            target="_blank"
            rel="noopener"
            class="platform-url"
          >
            {{ truncate(platform.publishedUrl, 36) }}
          </a>

          <!-- Metrics if published -->
          <div v-if="platform.viewCount !== undefined" class="platform-metrics">
            <span>&#128064; {{ formatNumber(platform.viewCount) }}</span>
            <span>&#10084;&#65039; {{ formatNumber(platform.likeCount ?? 0) }}</span>
          </div>

          <!-- Title/description inputs -->
          <div v-if="platform.state === 'idle'" class="platform-form">
            <input
              v-model="form[platform.type].title"
              class="form-input"
              placeholder="输入标题"
              maxlength="80"
            />
            <textarea
              v-model="form[platform.type].description"
              class="form-textarea"
              placeholder="输入描述（可选）"
              rows="2"
            ></textarea>
          </div>

          <!-- Distribute button -->
          <button
            class="btn btn-full btn-distribute"
            :class="{ 'btn-distributing': isDistributing(platform.type) }"
            :disabled="!form[platform.type].title || isDistributing(platform.type)"
            @click="handleDistribute(platform)"
          >
            <span v-if="isDistributing(platform.type)" class="spinner-xs"></span>
            {{
              platform.state === 'idle' ? '分发到 ' + platform.name :
              platform.state === 'uploading' ? '上传中...' :
              platform.state === 'published' ? '已发布' :
              '分发失败'
            }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useVideoStore } from '@/stores/useVideoStore'
import type { VideoWork, PlatformDistribution, PlatformType } from '@/types/video'

interface PlatformFormEntry {
  title: string
  description: string
}

interface PlatformCard {
  type: PlatformType
  name: string
  icon: string
  color: string
  state: 'idle' | 'uploading' | 'published' | 'failed'
  publishedUrl?: string
  viewCount?: number
  likeCount?: number
}

const store = useVideoStore()
const selectedWorkId = ref('')

const storeVideos = computed<VideoWork[]>(() => store.videos)

// ── Form state per platform ────────────────────────────────────
const form = ref<Record<PlatformType, PlatformFormEntry>>({
  bilibili: { title: '', description: '' },
  douyin: { title: '', description: '' },
  youtube: { title: '', description: '' },
  wechat: { title: '', description: '' },
})

// ── Platform configs ───────────────────────────────────────────
const platformConfigs = computed<PlatformCard[]>(() => {
  return PLATFORM_CONFIGS.map((cfg) => {
    const dist = store.distributions.find((d) => d.platform === cfg.type)
    return {
      ...cfg,
      state: dist?.status ?? 'idle',
      publishedUrl: dist?.published_url,
      viewCount: dist?.view_count,
      likeCount: dist?.like_count,
    }
  })
})

function isDistributing(type: PlatformType): boolean {
  return platformConfigs.value.some(
    (p) => p.type === type && p.state === 'uploading'
  )
}

// ── Distribute action ──────────────────────────────────────────
async function handleDistribute(p: PlatformCard) {
  if (!selectedWorkId.value || !form.value[p.type].title) return

  try {
    const result = await store.distributeToPlatform(
      selectedWorkId.value,
      p.type,
      form.value[p.type].title,
      form.value[p.type].description || undefined
    )

    if (result?.status === 'published') {
      ;(window as any)?.$toast?.show(`${p.name} 分发成功`, 'success')
    } else {
      ;(window as any)?.$toast?.show(`${p.name} 分发失败`, 'error')
    }
  } catch (e: unknown) {
    const msg = e instanceof Error ? e.message : `分发到 ${p.name} 失败`
    ;(window as any)?.$toast?.show(msg, 'error')
  }
}

// ── Helpers ────────────────────────────────────────────────────
function truncate(str: string, len: number): string {
  if (str.length <= len) return str
  return str.slice(0, len) + '...'
}

function formatNumber(n: number): string {
  if (n >= 10000) return (n / 10000).toFixed(1) + '万'
  if (n >= 1000) return (n / 1000).toFixed(1) + 'k'
  return String(n)
}

const PLATFORM_CONFIGS: Omit<PlatformCard, 'state' | 'publishedUrl' | 'viewCount' | 'likeCount'>[] = [
  { type: 'bilibili', name: 'B站', icon: '\u{5B48}', color: '#00a1d6' },
  { type: 'douyin', name: '抖音', icon: '\u{1F3AC}', color: '#fe2c55' },
  { type: 'youtube', name: 'YouTube', icon: '\u{25B6}', color: '#ff0000' },
  { type: 'wechat', name: '视频号', icon: '\u{1F49E}', color: '#07C160' },
]

const STATUS_MAP: Record<string, string> = {
  idle: '\u{1F7E4} 未分发',
  uploading: '\u{23F3} 上传中',
  published: '\u{2705} 已发布',
  failed: '\u{274C} 失败',
}
</script>

<style scoped>
.distribution-panel {
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
.selector-section {
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

/* ── Platforms grid ───────────────────────────────────────────── */
.platforms-section {
  display: flex;
  flex-direction: column;
  gap: 0;
}

.platforms-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
  gap: 14px;
}

/* ── Platform card ────────────────────────────────────────────── */
.platform-card {
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding: 18px 20px;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  transition: border-color 0.2s, box-shadow 0.2s, transform 0.15s;
  position: relative;
  overflow: hidden;
}

.platform-card:hover {
  border-color: var(--muted);
  transform: translateY(-1px);
}

.platform-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 3px;
  background: var(--accent);
  opacity: 0;
  transition: opacity 0.2s;
}

.platform-card:hover::before {
  opacity: 1;
}

.platform-bilibili::before { background: #00a1d6; }
.platform-douyin::before { background: #fe2c55; }
.platform-youtube::before { background: #ff0000; }
.platform-wechat::before { background: #07C160; }

.platform-card.distributing {
  border-color: var(--accent);
  box-shadow: 0 0 0 2px oklch(var(--accent) / 0.15);
}

.card-header {
  display: flex;
  align-items: center;
  gap: 10px;
}

.platform-icon {
  font-size: 1.3rem;
  line-height: 1;
}

.platform-name {
  font-size: 0.95rem;
  font-weight: 600;
  color: var(--fg);
}

/* ── Status badge ─────────────────────────────────────────────── */
.status-badge {
  align-self: flex-start;
  font-size: 0.7rem;
  font-weight: 600;
  padding: 2px 8px;
  border-radius: 10px;
}

.status-idle {
  background: oklch(50% 0.02 240 / 0.12);
  color: var(--fg);
}

.status-uploadin g {
  background: #f59e0b;
  color: #fff;
  animation: pulse-badge 1.5s ease-in-out infinite;
}

.status-published {
  background: #16a34a;
  color: #fff;
}

.status-failed {
  background: #ef4444;
  color: #fff;
}

@keyframes pulse-badge {
  0%, 100% { opacity: 1; transform: scale(1); }
  50% { opacity: 0.75; transform: scale(1.05); }
}

/* ── URL + metrics ────────────────────────────────────────────── */
.platform-url {
  font-size: 0.78rem;
  color: var(--accent);
  text-decoration: none;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  display: block;
}

.platform-url:hover {
  text-decoration: underline;
}

.platform-metrics {
  display: flex;
  gap: 12px;
  font-size: 0.78rem;
  color: var(--muted);
}

/* ── Form inputs ──────────────────────────────────────────────── */
.platform-form {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.form-input,
.form-textarea {
  padding: 8px 12px;
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  font-size: 0.84rem;
  background: var(--bg);
  color: var(--fg);
  font-family: inherit;
  resize: vertical;
  transition: border-color 0.2s;
}

.form-input:focus,
.form-textarea:focus {
  outline: none;
  border-color: var(--accent);
}

/* ── Distribute button ────────────────────────────────────────── */
.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 10px 18px;
  border-radius: var(--radius-sm);
  font-size: 0.84rem;
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

.btn-distribute {
  background: var(--accent);
  color: #fff;
  border-color: var(--accent);
}

.btn-distribute:hover:not(:disabled) {
  opacity: 0.9;
}

.btn-distributing {
  pointer-events: none;
}

.spinner-xs {
  display: inline-block;
  width: 12px;
  height: 12px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-top-color: #fff;
  border-radius: 50%;
  animation: spin 0.6s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}
</style>
