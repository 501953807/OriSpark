<template>
  <div class="work-list">
    <div v-if="loading" class="list-loading"><LoadingSpinner text="加载中..." /></div>
    <EmptyState v-else-if="!works.length" icon="🎨" title="暂无作品" description="导入你的第一个作品" />

    <div v-else class="list-body">
      <div v-for="work in works" :key="work.id" class="list-row" @click="$emit('select', work)">
        <div class="row-thumb">
          <img v-if="work.thumbnail_url" :src="work.thumbnail_url" :alt="work.title" />
          <span v-else>{{ fileTypeEmoji[work.file_type] || '📄' }}</span>
        </div>
        <div class="row-info">
          <div class="row-title">{{ work.title }}</div>
          <div class="row-meta">{{ work.file_type }} · {{ formatSize(work.file_size) }} · {{ formatDate(work.imported_at) }}</div>
        </div>
        <StatusBadge :status="work.is_verified ? 'confirmed' : 'draft'" :labels="statusLabels" :variants="statusVariants" />
        <code class="row-hash">{{ work.sha256?.slice(0, 12) || '—' }}</code>
        <button class="row-action" @click.stop="$emit('edit', work)">✏️</button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { Work } from '@/types/work'
import EmptyState from '@/components/common/EmptyState.vue'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'

defineProps<{
  works: Work[]
  loading?: boolean
}>()

defineEmits<{
  select: [work: Work]
  edit: [work: Work]
}>()

const fileTypeEmoji: Record<string, string> = {
  image: '🖼️', audio: '🎵', video: '🎬',
  document: '📄', design: '🎨', code: '💻',
}
const statusLabels = { confirmed: '已存证', draft: '待存证' }
const statusVariants = { confirmed: 'success', draft: 'info' }

function formatDate(d?: string) { return d?.slice(0, 10) || '' }
function formatSize(bytes: number): string {
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
}
</script>

<style scoped>
.work-list { min-height: 200px; }
.list-loading { padding: 40px; }
.list-body { display: flex; flex-direction: column; gap: 2px; }
.list-row {
  display: flex; align-items: center; gap: 12px;
  padding: 12px 14px; border-radius: var(--radius-sm); cursor: pointer;
  transition: background 0.15s;
}
.list-row:hover { background: oklch(96% 0.003 240); }
.row-thumb {
  width: 40px; height: 40px; border-radius: var(--radius-sm);
  overflow: hidden; flex-shrink: 0;
  background: oklch(95% 0.003 240);
  display: flex; align-items: center; justify-content: center;
  font-size: 1.2rem;
}
.row-thumb img { width: 100%; height: 100%; object-fit: cover; }
.row-info { flex: 1; min-width: 0; }
.row-title { font-size: 0.88rem; font-weight: 600; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.row-meta { font-size: 0.72rem; color: var(--muted); }
.row-hash { font-size: 0.65rem; color: var(--muted); font-family: monospace; }
.row-action {
  background: none; border: none; cursor: pointer;
  font-size: 0.9rem; color: var(--muted); padding: 4px 8px; border-radius: var(--radius-sm);
}
.row-action:hover { background: oklch(0 0 0 / 0.04); }
</style>
