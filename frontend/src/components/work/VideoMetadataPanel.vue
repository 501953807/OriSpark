<template>
  <div class="video-panel">
    <!-- Video Specs -->
    <section class="info-group" v-if="specsGroup.length">
      <h4 class="info-group-title">视频规格</h4>
      <div v-for="item in specsGroup" :key="item.label" class="info-row">
        <span class="info-label">{{ item.label }}</span>
        <span class="info-value">{{ item.value }}</span>
      </div>
    </section>

    <!-- Fingerprint Status -->
    <section class="info-group" v-if="fingerprintGroup.length">
      <h4 class="info-group-title">指纹状态</h4>
      <div v-for="item in fingerprintGroup" :key="item.label" class="info-row">
        <span class="info-label">{{ item.label }}</span>
        <span class="info-value">
          <span v-if="item.statusClass" :class="'badge-status ' + item.statusClass">{{ item.value }}</span>
          <span v-else>{{ item.value }}</span>
        </span>
      </div>
    </section>

    <!-- Distribution -->
    <section class="info-group" v-if="distGroup.length">
      <h4 class="info-group-title">平台分发</h4>
      <div v-for="item in distGroup" :key="item.label" class="info-row">
        <span class="info-label">{{ item.label }}</span>
        <span class="info-value">
          <span v-if="item.isPlatformList">
            <span v-for="p in item.platforms" :key="p.name" :class="'platform-chip status-' + p.status">
              {{ p.icon }} {{ p.name }}
            </span>
          </span>
          <span v-else>{{ item.value }}</span>
        </span>
      </div>
    </section>

    <!-- Empty state -->
    <div v-if="!hasAnyData" class="empty-hint">
      <span class="hint-icon">🎥</span>
      <p>暂无视频元数据</p>
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
  if (props.work?.custom_metadata?.video && typeof props.work.custom_metadata.video === 'object')
    return props.work.custom_metadata.video
  return null
})

const videoSpecs = computed(() => raw.value?.video_specs ?? {})
const fingerprintInfo = computed(() => raw.value?.fingerprint ?? {})

const durationSec = computed(() => videoSpecs.value?.duration_seconds ?? props.work?.duration ?? null)
const format = computed(() => videoSpecs.value?.format ?? raw.value?.format ?? null)
const resolution = computed(() => {
  const w = videoSpecs.value?.width ?? props.work?.width
  const h = videoSpecs.value?.height ?? props.work?.height
  if (w && h) return `${w} x ${h}`
  return videoSpecs.value?.resolution ?? null
})
const fileSize = computed(() => videoSpecs.value?.file_size ?? null)
const codec = computed(() => videoSpecs.value?.codec ?? null)

const fpStatus = computed(() => fingerprintInfo.value?.status ?? raw.value?.fingerprint_status ?? null)
const framesExtracted = computed(() => fingerprintInfo.value?.frames_extracted ?? null)
const matchCount = computed(() => fingerprintInfo.value?.match_count ?? raw.value?.match_count ?? null)

const platforms = computed(() => {
  const p = raw.value?.distributions ?? []
  return Array.isArray(p) ? p : []
})

function fmt(val: string | number | null | undefined): string {
  if (val == null || val === '') return '—'
  if (typeof val === 'number' && val > 1024 * 1024) return `${(val / (1024 * 1024)).toFixed(1)} MB`
  if (typeof val === 'number' && val > 1024) return `${(val / 1024).toFixed(1)} KB`
  return String(val)
}

const specsGroup = computed(() => {
  const items: Array<{ label: string; value: string }> = []
  if (durationSec.value) items.push({ label: '时长', value: fmt(`${Math.round(durationSec.value / 60)}分${Math.round(durationSec.value % 60)}秒`) })
  if (resolution.value) items.push({ label: '分辨率', value: fmt(String(resolution.value)) })
  if (format.value) items.push({ label: '格式', value: fmt(format.value.toUpperCase()) })
  if (codec.value) items.push({ label: '编码', value: fmt(codec.value) })
  if (fileSize.value) items.push({ label: '文件大小', value: fmt(fileSize.value) })
  return items
})

const fingerprintGroup = computed(() => {
  const items: Array<{ label: string; value: string; statusClass?: string }> = []
  if (fpStatus.value) {
    const clsMap: Record<string, string> = { pending: 'status-pending', processing: 'status-processing', completed: 'status-completed', failed: 'status-failed' }
    const labelsMap: Record<string, string> = { pending: '待扫描', processing: '扫描中', completed: '已完成', failed: '失败' }
    const fs = fpStatus.value as string
    items.push({ label: '指纹状态', value: labelsMap[fs] ?? fs, statusClass: clsMap[fs] })
  }
  if (framesExtracted.value != null) items.push({ label: '提取帧数', value: fmt(framesExtracted.value) })
  if (matchCount.value != null) items.push({ label: '匹配数', value: fmt(matchCount.value) })
  return items
})

const distGroup = computed(() => {
  if (!platforms.value.length) return []
  return [{ label: '分发平台', value: '', isPlatformList: true, platforms: platforms.value }]
})

const hasAnyData = computed(() => {
  return !!(
    durationSec.value ||
    resolution.value ||
    format.value ||
    codec.value ||
    fpStatus.value ||
    framesExtracted.value ||
    platforms.value.length
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

.badge-status {
  display: inline-block;
  padding: 2px 10px;
  border-radius: 10px;
  font-size: 0.78rem;
  font-weight: 600;
}

.status-pending { background: oklch(62% 0.18 55 / 0.12); color: #b45309; }
.status-processing { background: oklch(58% 0.14 245 / 0.1); color: var(--blue); }
.status-completed { background: oklch(56% 0.12 170 / 0.12); color: #16a34a; }
.status-failed { background: oklch(56% 0.16 0 / 0.1); color: #ef4444; }

.platform-chip {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 2px 10px;
  margin: 2px 4px 2px 0;
  border-radius: 10px;
  font-size: 0.78rem;
  font-weight: 500;
  border: 1px solid var(--border);
  background: var(--surface);
}

.platform-chip.status-published { border-color: #16a34a; color: #16a34a; }
.platform-chip.status-failed { border-color: #ef4444; color: #ef4444; }
.platform-chip.status-uploading { border-color: #f59e0b; color: #f59e0b; }
</style>
