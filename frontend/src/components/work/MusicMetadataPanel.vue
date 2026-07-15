<template>
  <div class="music-panel">
    <!-- Release Info -->
    <section class="info-group" v-if="work?.title || release.title">
      <h4 class="info-group-title">发行信息</h4>
      <div class="info-row">
        <span class="info-label">作品</span>
        <span class="info-value">{{ work?.title || release.title }}</span>
      </div>
      <div class="info-row" v-if="release.isrc">
        <span class="info-label">ISRC</span>
        <span class="info-value mono">{{ release.isrc }}</span>
      </div>
      <div class="info-row" v-if="release.album_title">
        <span class="info-label">专辑</span>
        <span class="info-value">{{ release.album_title }}</span>
      </div>
    </section>

    <!-- Audio Specs -->
    <section class="info-group" v-if="audioGroup.length">
      <h4 class="info-group-title">音频规格</h4>
      <div v-for="item in audioGroup" :key="item.label" class="info-row">
        <span class="info-label">{{ item.label }}</span>
        <span class="info-value">{{ item.value }}</span>
      </div>
    </section>

    <!-- Genre & Mood -->
    <section class="info-group" v-if="genreGroup.length">
      <h4 class="info-group-title">风格与情绪</h4>
      <div v-for="item in genreGroup" :key="item.label" class="info-row">
        <span class="info-label">{{ item.label }}</span>
        <span class="info-value">{{ item.value }}</span>
      </div>
    </section>

    <!-- Distribution Status -->
    <section class="info-group" v-if="distGroup.length">
      <h4 class="info-group-title">分发状态</h4>
      <div v-for="item in distGroup" :key="item.label" class="info-row">
        <span class="info-label">{{ item.label }}</span>
        <span class="info-value">
          <span v-if="item.statusClass" :class="'badge-status ' + item.statusClass">{{ item.value }}</span>
          <span v-else>{{ item.value }}</span>
        </span>
      </div>
    </section>

    <!-- Empty state -->
    <div v-if="!hasAnyData" class="empty-hint">
      <span class="hint-icon">&#127925;</span>
      <p>暂无音乐元数据</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { Work } from '@/types/work'

interface Props {
  work: Work | null
  exifData: Record<string, any> | null
}

const props = withDefaults(defineProps<Props>(), {
  work: null,
  exifData: null,
})

const raw = computed(() => {
  if (props.exifData && typeof props.exifData === 'object') return props.exifData
  if (props.work?.custom_metadata?.music && typeof props.work.custom_metadata.music === 'object')
    return props.work.custom_metadata.music
  return null
})

const release = computed(() => raw.value?.release ?? {})
const audioSpecs = computed(() => raw.value?.audio_specs ?? {})

const isrc = computed(() => release.value?.isrc ?? null)
const albumTitle = computed(() => release.value?.album_title ?? null)
const distributionStatus = computed(() => release.value?.distribution_status ?? null)
const distributedAt = computed(() => release.value?.distributed_at ?? null)

const durationSeconds = computed(() => audioSpecs.value?.duration_seconds ?? null)
const bitrate = computed(() => audioSpecs.value?.bitrate ?? null)
const format = computed(() => audioSpecs.value?.format ?? null)
const sampleRate = computed(() => audioSpecs.value?.sample_rate ?? null)
const channels = computed(() => audioSpecs.value?.channels ?? null)

const genre = computed(() => raw.value?.genre ?? null)
const mood = computed(() => raw.value?.mood ?? null)
const bpm = computed(() => raw.value?.bpm ?? null)

function fmt(val: string | number | null | undefined): string {
  if (val == null || val === '') return '—'
  return String(val)
}

const audioGroup = computed(() => {
  const items: Array<{ label: string; value: string }> = []
  if (durationSeconds.value) items.push({ label: '时长', value: fmt(`${Math.round(durationSeconds.value / 60)}分${Math.round(durationSeconds.value % 60)}秒`) })
  if (bitrate.value) items.push({ label: '码率', value: fmt(`${bitrate.value} kbps`) })
  if (format.value) items.push({ label: '格式', value: fmt(format.value.toUpperCase()) })
  if (sampleRate.value) items.push({ label: '采样率', value: fmt(`${sampleRate.value} Hz`) })
  if (channels.value) items.push({ label: '声道', value: fmt(channels.value === 2 ? '立体声' : '单声道') })
  return items
})

const genreGroup = computed(() => {
  const items: Array<{ label: string; value: string }> = []
  if (genre.value) items.push({ label: '流派', value: fmt(genre.value) })
  if (mood.value) items.push({ label: '情绪', value: fmt(mood.value) })
  if (bpm.value) items.push({ label: 'BPM', value: fmt(String(bpm.value)) })
  return items
})

const distGroup = computed(() => {
  const items: Array<{ label: string; value: string; statusClass?: string }> = []
  if (distributionStatus.value) {
    const clsMap: Record<string, string> = { pending: 'status-pending', distributing: 'status-distributing', distributed: 'status-distributed' }
    const labelsMap: Record<string, string> = { pending: '待分发', distributing: '分发中', distributed: '已分发' }
    const ds = distributionStatus.value as string
    items.push({ label: '分发状态', value: labelsMap[ds] ?? ds, statusClass: clsMap[ds] })
  }
  if (isrc.value) items.push({ label: 'ISRC', value: fmt(isrc.value) })
  return items
})

const hasAnyData = computed(() => {
  return !!(
    isrc.value ||
    albumTitle.value ||
    durationSeconds.value ||
    bitrate.value ||
    format.value ||
    genre.value ||
    mood.value ||
    bpm.value ||
    distributionStatus.value
  )
})
</script>

<style scoped>
.empty-hint {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 32px 16px;
  color: var(--muted);
  gap: 8px;
}

.hint-icon { font-size: 2rem; opacity: 0.6; }

.info-group {
  padding-bottom: 16px;
  border-bottom: 1px solid var(--border);
}

.info-group:last-child { border-bottom: none; padding-bottom: 0; }

.info-group-title {
  font-size: 0.72rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--accent);
  margin: 0 0 10px 0;
}

.info-row {
  display: flex;
  align-items: baseline;
  gap: 12px;
  font-size: 0.85rem;
  margin-bottom: 6px;
}

.info-row:last-child { margin-bottom: 0; }

.info-label {
  color: var(--muted);
  font-weight: 600;
  font-size: 0.8rem;
  min-width: 60px;
  flex-shrink: 0;
}

.info-value {
  color: var(--fg);
  font-size: 0.85rem;
  word-break: break-word;
}

.mono {
  font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
  font-size: 0.8rem;
}

.badge-status {
  display: inline-block;
  padding: 2px 10px;
  border-radius: 10px;
  font-size: 0.78rem;
  font-weight: 600;
}

.status-pending { background: oklch(62% 0.18 55 / 0.12); color: #b45309; }
.status-distributing { background: oklch(58% 0.14 245 / 0.1); color: var(--blue); }
.status-distributed { background: oklch(56% 0.12 170 / 0.12); color: #16a34a; }
</style>
