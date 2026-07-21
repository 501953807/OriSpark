<template>
  <div class="work-card card" @click="$emit('click')">
    <div class="card-thumb">
      <img v-if="work.thumbnail_url" :src="work.thumbnail_url" :alt="work.title" />
      <div v-else class="thumb-placeholder">
        <span class="thumb-icon">{{ fileTypeEmoji[work.file_type] || '📄' }}</span>
      </div>
      <div class="card-badge">{{ work.file_extension.toUpperCase() }}</div>
      <div v-if="work.is_verified" class="card-verified">🔒 已存证</div>
    </div>
    <div class="card-body">
      <div class="card-title" :title="work.title">{{ work.title }}</div>
      <div class="card-meta">
        <span>{{ formatDate(work.imported_at) }}</span>
        <span>{{ formatSize(work.file_size) }}</span>
      </div>
      <div class="card-tags" v-if="work.tags?.length">
        <span v-for="t in work.tags.slice(0, 3)" :key="t.id" class="tag">{{ t.tag }}</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { Work } from '@/types/work'

defineProps<{
  work: Work
}>()

defineEmits<{
  click: []
}>()

const fileTypeEmoji: Record<string, string> = {
  image: '🖼️', audio: '🎵', video: '🎬',
  document: '📄', design: '🎨', code: '💻',
}

function formatDate(d?: string): string {
  return d?.slice(0, 10) || ''
}

function formatSize(bytes: number): string {
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
  if (bytes < 1024 * 1024 * 1024) return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
  return (bytes / (1024 * 1024 * 1024)).toFixed(2) + ' GB'
}
</script>

<style scoped>
.work-card {
  cursor: pointer;
  overflow: hidden;
  padding: 0;
}
.card-thumb {
  height: 160px;
  position: relative;
  overflow: hidden;
  background: oklch(95% 0.003 240);
}
.card-thumb img {
  width: 100%; height: 100%; object-fit: cover;
}
.thumb-placeholder {
  width: 100%; height: 100%;
  display: flex; align-items: center; justify-content: center;
}
.thumb-icon { font-size: 2.5rem; }
.card-badge {
  position: absolute; top: 8px; left: 8px;
  padding: 2px 8px; border-radius: 100px;
  background: oklch(0 0 0 / 0.55); color: #fff;
  font-size: 0.62rem; font-weight: 700;
}
.card-verified {
  position: absolute; bottom: 8px; right: 8px;
  padding: 2px 8px; border-radius: 100px;
  background: oklch(56% 0.12 170 / 0.85); color: #fff;
  font-size: 0.65rem; font-weight: 600;
}
.card-body { padding: 12px 14px; }
.card-title {
  font-size: 0.85rem; font-weight: 600;
  overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
}
.card-meta {
  display: flex; gap: 10px;
  font-size: 0.7rem; color: var(--muted); margin-top: 4px;
}
.card-tags { display: flex; gap: 4px; margin-top: 8px; flex-wrap: wrap; }
.tag {
  padding: 2px 8px; border-radius: 100px;
  font-size: 0.65rem; font-weight: 600;
  background: oklch(56% 0.12 170 / 0.1); color: var(--accent);
}
</style>
