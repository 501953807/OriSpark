<template>
  <div class="album-card">
    <div class="card-body">
      <div class="card-cover-area">
        <div
          v-if="coverUrl"
          class="cover-image"
          :style="{ backgroundImage: `url(${coverUrl})` }"
        />
        <div v-else class="cover-placeholder">
          &#127925;
        </div>

        <span
          class="type-badge"
          :style="{ backgroundColor: typeColor }"
        >
          {{ typeLabel }}
        </span>
      </div>

      <div class="card-details">
        <h3 class="album-title">
          {{ album.title || '未命名专辑' }}
        </h3>

        <div v-if="album.label" class="detail-row">
          <span class="detail-label">厂牌</span>
          <span class="detail-value">{{ album.label }}</span>
        </div>

        <div v-if="album.total_tracks != null" class="detail-row">
          <span class="detail-label">曲目</span>
          <span class="detail-value">{{ album.total_tracks }} 首</span>
        </div>

        <div v-if="album.duration_seconds != null" class="detail-row">
          <span class="detail-label">总时长</span>
          <span class="detail-value">{{ formatDuration(album.duration_seconds) }}</span>
        </div>

        <div v-if="album.release_date" class="detail-row">
          <span class="detail-label">发布日期</span>
          <span class="detail-value">{{ formatDate(album.release_date!) }}</span>
        </div>
      </div>
    </div>

    <div class="card-footer">
      <button class="btn btn-ghost btn-sm" @click="$emit('edit', album)">
        <span class="icon">&#9998;</span> 编辑
      </button>
      <button class="btn btn-ghost btn-sm btn-danger" @click="$emit('delete', album)">
        <span class="icon">&#128465;</span> 删除
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { Album, AlbumType } from '@/types/musician'

const TYPE_LABELS: Record<AlbumType, string> = {
  single: '单曲',
  ep: 'EP',
  album: '专辑',
  compilation: '合集',
}

const TYPE_COLORS: Record<AlbumType, string> = {
  single: '#8b5cf6',
  ep: '#3b82f6',
  album: '#06b6d4',
  compilation: '#f59e0b',
}

interface Props {
  album: Album
}

const props = defineProps<Props>()

const emit = defineEmits<{
  edit: [album: Album]
  delete: [album: Album]
}>()

const typeLabel = computed(() => TYPE_LABELS[props.album.album_type])
const typeColor = computed(() => TYPE_COLORS[props.album.album_type])
const coverUrl = computed(() => {
  const p = props.album.cover_art_path
  if (!p) return ''
  if (p.startsWith('http')) return p
  return `/uploads/${p}`
})

function formatDuration(seconds: number): string {
  const h = Math.floor(seconds / 3600)
  const m = Math.floor((seconds % 3600) / 60)
  const s = seconds % 60
  if (h > 0) {
    return `${h}h ${m}m ${s}s`
  }
  return `${m}m ${s}s`
}

function formatDate(dateStr: string): string {
  const d = new Date(dateStr)
  if (isNaN(d.getTime())) return dateStr
  return d.toLocaleDateString('zh-CN', { year: 'numeric', month: 'long', day: 'numeric' })
}
</script>

<style scoped>
.album-card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  overflow: hidden;
  transition: box-shadow 0.2s, transform 0.15s;
}

.album-card:hover {
  box-shadow: 0 4px 20px oklch(0 0 0 / 0.06);
  transform: translateY(-1px);
}

/* ── Cover ────────────────────────────────────────────────────── */
.card-cover-area {
  position: relative;
  height: 200px;
  background: var(--bg);
}

.cover-image {
  width: 100%;
  height: 100%;
  background-size: cover;
  background-position: center;
}

.cover-placeholder {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  height: 100%;
  font-size: 3rem;
  color: var(--muted);
}

.type-badge {
  position: absolute;
  top: 10px;
  right: 10px;
  padding: 3px 10px;
  border-radius: 100px;
  font-size: 0.72rem;
  font-weight: 600;
  color: #fff;
  line-height: 1.4;
}

/* ── Details ──────────────────────────────────────────────────── */
.card-details {
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.album-title {
  font-size: 0.95rem;
  font-weight: 600;
  color: var(--fg);
  margin: 0;
}

.detail-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-size: 0.84rem;
}

.detail-label {
  color: var(--muted);
  font-size: 0.78rem;
}

.detail-value {
  font-weight: 500;
  color: var(--fg);
}

/* ── Footer ──────────────────────────────────────────────────── */
.card-footer {
  display: flex;
  gap: 0;
  border-top: 1px solid var(--border);
}

.card-footer .btn {
  flex: 1;
  border: none;
  border-radius: 0;
  justify-content: center;
}

.icon {
  font-size: 0.82rem;
}

.btn-sm {
  padding: 8px 12px;
  font-size: 0.8rem;
}

.btn-danger:hover {
  color: #ef4444;
  background: oklch(95% 0.02 0 / 0.5);
}
</style>
