<template>
  <div class="work-list">
    <div v-if="loading" class="empty-state">加载中...</div>
    <EmptyState v-else-if="!works.length" icon="📦" title="暂无仓库" description="点击"+新建"创建第一个协同仓库。" />
    <div v-else class="work-items">
      <div
        v-for="work in works"
        :key="work.id"
        :class="['work-item', { selected: work.id === selectedId }]"
        @click="$emit('select', work)"
      >
        <div class="work-title">{{ work.title || '未命名仓库' }}</div>
        <div class="work-meta">
          <n-tag size="small" :type="statusTagType(work.status)">
            {{ statusLabel(work.status) }}
          </n-tag>
          <span class="meta-count">{{ work.branch_count || 0 }} 分支</span>
          <span class="meta-count">{{ work.pr_count || 0 }} MR</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { NTag } from 'naive-ui'
import type { ForkMergeWork } from '@/types/forkMerge'
import EmptyState from '@/components/common/EmptyState.vue'

defineProps<{
  works: ForkMergeWork[]
  loading: boolean
  selectedId?: string
}>()

defineEmits<{
  select: [work: ForkMergeWork]
  create: []
}>()

function statusTagType(status: string): 'default' | 'success' | 'warning' | 'error' | 'info' {
  const map: Record<string, 'default' | 'success' | 'warning' | 'error' | 'info'> = {
    active: 'success', closed: 'default', archived: 'info',
  }
  return map[status] || 'default'
}

function statusLabel(status: string): string {
  const map: Record<string, string> = {
    active: '进行中', closed: '已关闭', archived: '已归档',
  }
  return map[status] || status
}
</script>

<style scoped>
.work-list { display: flex; flex-direction: column; gap: 8px; }

.work-items { display: flex; flex-direction: column; gap: 6px; }

.work-item {
  padding: 12px;
  background: var(--bg);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  cursor: pointer;
  transition: background 0.15s, border-color 0.15s;
}

.work-item:hover { background: var(--surface); }
.work-item.selected { border-color: var(--accent); background: var(--surface); }

.work-title { font-size: 0.9rem; font-weight: 600; color: var(--fg); margin-bottom: 4px; }

.work-meta { display: flex; align-items: center; gap: 8px; font-size: 0.78rem; color: var(--muted); }

.meta-count { font-size: 0.72rem; }

.empty-state { padding: 32px; text-align: center; color: var(--muted); }
</style>
