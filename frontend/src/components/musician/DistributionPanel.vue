<template>
  <div class="dist-panel">
    <!-- Header -->
    <div class="panel-header">
      <h3 class="panel-title">&#128203; 多平台分发</h3>
      <span class="panel-desc">一键分发到全球音乐平台</span>
    </div>

    <!-- Distribute all button -->
    <button
      class="btn btn-primary btn-full"
      :disabled="distributingAny"
      @click="handleDistributeAll"
    >
      <span v-if="distributingAny" class="spinner-xs"></span>
      {{ distributingAny ? '分发中...' : '一键分发所有平台' }}
    </button>

    <!-- Platform grid -->
    <div class="platforms-grid">
      <div
        v-for="p in platforms"
        :key="p.type"
        :class="['platform-card', `platform-${p.type}`, { distributing: p.state === 'uploading' }]"
      >
        <!-- Icon + brand color stripe + name -->
        <div class="card-header">
          <span class="platform-icon" :style="{ color: p.color }">{{ p.icon }}</span>
          <span class="platform-name">{{ p.name }}</span>
        </div>

        <!-- Status badge -->
        <span :class="['status-badge', `status-${p.state}`]">
          {{ STATUS_MAP[p.state] }}
        </span>

        <!-- Progress bar if distributing -->
        <div v-if="p.state === 'uploading'" class="progress-bar">
          <div class="progress-fill" :style="{ width: `${p.progress}%` }" />
          <span class="progress-text">{{ p.progress }}%</span>
        </div>

        <!-- Metrics after distribution -->
        <div v-if="p.state === 'published'" class="platform-metrics">
          <span>&#128064; {{ formatNumber(p.plays ?? 0) }}</span>
          <span>&#128176; {{ formatRevenue(p.revenue ?? 0) }}</span>
          <span>{{ p.released_at ? formatDate(p.released_at) : '—' }}</span>
        </div>

        <!-- Publish URL if available -->
        <a
          v-if="p.url"
          :href="p.url"
          target="_blank"
          rel="noopener"
          class="platform-url"
        >
          {{ truncate(p.url, 40) }}
        </a>

        <!-- Platform-specific distribute button -->
        <button
          class="btn btn-full"
          :class="{ 'btn-distribute': p.state !== 'published', 'btn-distributing': p.state === 'uploading' }"
          :disabled="p.state === 'uploading' || p.state === 'published'"
          @click="handleDistribute(p.type)"
        >
          {{
            p.state === 'idle' ? '分发到 ' + p.name :
            p.state === 'uploading' ? '上传中...' :
            p.state === 'published' ? '已上架' :
            '分发失败'
          }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'

interface Props {
  releaseId: string
}

defineProps<Props>()

interface PlatformState {
  type: string
  name: string
  icon: string
  color: string
  state: 'idle' | 'uploading' | 'published' | 'failed'
  progress: number
  url?: string
  plays?: number
  revenue?: number
  released_at?: string
}

const STATUS_MAP: Record<PlatformState['state'], string> = {
  idle: '\u{1F7E4} 未分发',
  uploading: '\u{23F3} 分发中',
  published: '\u{2705} 已上架',
  failed: '\u{274C} 失败',
}

const initialState: PlatformState[] = [
  { type: 'spotify', name: 'Spotify', icon: '\u{1F3B5}', color: '#1DB954', state: 'idle', progress: 0 },
  { type: 'apple_music', name: 'Apple Music', icon: '\u{266B}', color: '#FC3C44', state: 'idle', progress: 0 },
  { type: 'netease', name: '网易云音乐', icon: '\u{1F3A4}', color: '#C4212B', state: 'idle', progress: 0 },
  { type: 'qq_music', name: 'QQ音乐', icon: '\u{1F3A7}', color: '#12B7F5', state: 'idle', progress: 0 },
]

const platforms = ref<PlatformState[]>(JSON.parse(JSON.stringify(initialState)))

const distributingAny = computed(() =>
  platforms.value.some((p) => p.state === 'uploading'),
)

function handleDistribute(type: string) {
  platforms.value = platforms.value.map((p) => {
    if (p.type !== type) return p
    if (p.state === 'uploading' || p.state === 'published') return p
    return { ...p, state: 'uploading', progress: 0 }
  })

  simulateProgress(type)
}

async function handleDistributeAll() {
  const idlePlatforms = platforms.value.filter((p) => p.state === 'idle')
  if (idlePlatforms.length === 0) return

  platforms.value = platforms.value.map((p) =>
    p.state === 'idle' ? { ...p, state: 'uploading', progress: 0 } : p,
  )

  for (const p of idlePlatforms) {
    simulateProgress(p.type)
    await new Promise((r) => setTimeout(r, 400))
  }

  ;(window as any)?.$toast?.show('所有平台分发中...', 'success')
}

function simulateProgress(type: string) {
  let progress = 0
  const timer = setInterval(() => {
    progress += Math.floor(Math.random() * 20) + 5
    if (progress >= 100) {
      progress = 100
      clearInterval(timer)

      const cfg = initialState.find((c) => c.type === type)
      platforms.value = platforms.value.map((p) => {
        if (p.type !== type) return p
        return {
          ...p,
          state: 'published',
          progress: 100,
          url: `https://${type === 'netease' ? 'music.163.com' : type === 'qq_music' ? 'y.qq.com' : `${type}.com/track/abc123`}`,
          plays: Math.floor(Math.random() * 50000),
          revenue: +(Math.random() * 500).toFixed(2),
          released_at: new Date().toISOString(),
        }
      })

      ;(window as any)?.$toast?.show(`${cfg?.name ?? type} 分发成功`, 'success')
    } else {
      platforms.value = platforms.value.map((p) => {
        if (p.type !== type) return p
        return { ...p, state: 'uploading', progress }
      })
    }
  }, 600)
}

function truncate(str: string, len: number): string {
  if (str.length <= len) return str
  return str.slice(0, len) + '...'
}

function formatNumber(n: number): string {
  if (n >= 10000) return (n / 10000).toFixed(1) + '万'
  if (n >= 1000) return (n / 1000).toFixed(1) + 'k'
  return String(n)
}

function formatRevenue(amount: number): string {
  return `¥${amount.toFixed(2)}`
}

function formatDate(iso: string): string {
  const d = new Date(iso)
  if (isNaN(d.getTime())) return iso
  return d.toLocaleDateString('zh-CN', { year: 'numeric', month: 'short', day: 'numeric' })
}
</script>

<style scoped>
.dist-panel {
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

/* ── Platforms grid (4-column responsive) ─────────────────────── */
.platforms-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 14px;
}

@media (min-width: 1024px) {
  .platforms-grid {
    grid-template-columns: repeat(4, 1fr);
  }
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

.platform-spotify::before { background: #1DB954; }
.platform-apple_music::before { background: #FC3C44; }
.platform-netease::before { background: #C4212B; }
.platform-qq_music::before { background: #12B7F5; }

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

/* ── Progress bar ─────────────────────────────────────────────── */
.progress-bar {
  position: relative;
  height: 6px;
  background: var(--border);
  border-radius: 3px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: var(--accent);
  transition: width 0.4s ease;
}

.progress-text {
  position: absolute;
  top: -16px;
  right: 0;
  font-size: 0.7rem;
  font-weight: 600;
  color: var(--muted);
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
  flex-wrap: wrap;
  gap: 8px;
  font-size: 0.78rem;
  color: var(--muted);
}

/* ── Button ────────────────────────────────────────────────────── */
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

.btn-primary {
  background: var(--accent);
  color: #fff;
  border-color: var(--accent);
}

.btn-primary:hover:not(:disabled) {
  opacity: 0.9;
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
  to {
    transform: rotate(360deg);
  }
}
</style>
