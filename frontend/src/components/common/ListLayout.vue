<template>
  <div class="list-layout" :class="{ 'grid-view': gridView }">
    <!-- Toolbar -->
    <div class="list-toolbar">
      <slot name="search">
        <div v-if="searchable" class="search-wrapper">
          <svg class="search-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="11" cy="11" r="8" /><path d="m21 21-4.35-4.35" />
          </svg>
          <input
            v-model="searchQuery"
            class="search-input"
            :placeholder="searchPlaceholder"
            @input="$emit('search', searchQuery)"
          />
          <button v-if="searchQuery" class="search-clear" @click="clearSearch">&times;</button>
        </div>
      </slot>
      <slot name="filters" />
      <div class="list-toolbar-right">
        <slot name="viewToggle">
          <div v-if="viewToggle" class="view-toggle">
            <button :class="['btn-icon', { active: !gridView }]" @click="gridView = false" title="列表视图">
              <svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor"><rect y="0" width="16" height="1.5" rx="0.5"/><rect y="5.5" width="16" height="1.5" rx="0.5"/><rect y="11" width="16" height="1.5" rx="0.5"/></svg>
            </button>
            <button :class="['btn-icon', { active: gridView }]" @click="gridView = true" title="网格视图">
              <svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor"><rect x="0" y="0" width="6.5" height="6.5" rx="1"/><rect x="9" y="0" width="6.5" height="6.5" rx="1"/><rect x="0" y="9" width="6.5" height="6.5" rx="1"/><rect x="9" y="9" width="6.5" height="6.5" rx="1"/></svg>
            </button>
          </div>
        </slot>
        <slot name="batchActions" />
        <slot name="actions" />
      </div>
    </div>

    <!-- Bulk action bar (shown when items selected) -->
    <div v-if="selectedIds && selectedIds.size > 0" class="bulk-bar">
      <span>{{ selectedIds.size }} 项已选择</span>
      <slot name="bulkActions" :ids="selectedIds" />
      <button class="btn-ghost btn-sm" @click="clearSelection">取消选择</button>
    </div>

    <!-- Body with skeleton loading -->
    <div v-if="loading" class="list-loading">
      <slot name="skeleton">
        <SkeletonCard v-for="i in skeletonCount" :key="i" class="skeleton-item" />
      </slot>
    </div>
    <div v-else class="list-body">
      <slot />
    </div>

    <!-- Footer: pagination + sort info -->
    <div v-if="$slots.pagination" class="list-footer">
      <slot name="pagination" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import SkeletonCard from './SkeletonCard.vue'

const props = withDefaults(defineProps<{
  searchable?: boolean
  searchPlaceholder?: string
  viewToggle?: boolean
  loading?: boolean
  skeletonCount?: number
  selectedIds?: Set<string>
}>(), {
  searchable: false,
  searchPlaceholder: '搜索...',
  viewToggle: false,
  loading: false,
  skeletonCount: 6,
})

const gridView = ref(false)
const searchQuery = ref('')

defineEmits<{ search: [q: string] }>()

function clearSearch() {
  searchQuery.value = ''
  props.selectedIds?.clear()
}

function clearSelection() {
  props.selectedIds?.clear()
}
</script>

<style scoped>
.list-layout { display: flex; flex-direction: column; gap: 12px; }
.list-toolbar { display: flex; gap: 10px; align-items: center; flex-wrap: wrap; }
.list-toolbar-right { display: flex; gap: 8px; align-items: center; margin-left: auto; }

.search-wrapper { position: relative; flex: 1; min-width: 200px; max-width: 400px; }
.search-icon { position: absolute; left: 10px; top: 50%; transform: translateY(-50%); width: 16px; height: 16px; color: var(--muted); pointer-events: none; }
.search-input { padding: 8px 32px 8px 34px; border: 1px solid var(--border); border-radius: 8px; font-size: .84rem; min-width: 200px; max-width: 400px; background: var(--surface); color: var(--text-primary); width: 100%; }
.search-clear { position: absolute; right: 8px; top: 50%; transform: translateY(-50%); background: none; border: none; color: var(--muted); cursor: pointer; font-size: 1.1rem; padding: 2px 4px; border-radius: 4px; }
.search-clear:hover { color: var(--text-primary); }

.view-toggle { display: flex; gap: 2px; background: var(--surface); border: 1px solid var(--border); border-radius: 8px; padding: 2px; }
.btn-icon { padding: 4px 6px; border: none; background: none; border-radius: 6px; cursor: pointer; color: var(--muted); display: flex; align-items: center; transition: all .15s; }
.btn-icon.active { background: var(--accent); color: #fff; }
.btn-icon svg { width: 16px; height: 16px; }

.bulk-bar { display: flex; align-items: center; gap: 12px; padding: 8px 14px; background: oklch(56% 0.12 170 / 0.06); border: 1px solid oklch(56% 0.12 170 / 0.15); border-radius: var(--radius-sm, 8px); font-size: .82rem; color: var(--accent); }
.btn-ghost { background: none; border: none; cursor: pointer; color: var(--muted); font-size: .82rem; }
.btn-sm { padding: 4px 8px; font-size: .78rem; }

.list-body { flex: 1; }
.list-footer { display: flex; justify-content: center; padding-top: 12px; }

.list-loading { display: flex; flex-direction: column; gap: 12px; }
.skeleton-item { }
</style>
