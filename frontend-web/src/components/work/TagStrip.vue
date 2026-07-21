<template>
  <div class="tag-strip card">
    <div class="card-header-row">
      <h3>🏷️ 标签</h3>
    </div>
    <div class="tag-list">
      <div v-if="workTags.length === 0" class="card-empty">暂无标签</div>
      <div v-for="t in workTags" :key="t.id" class="tag-pill-compact">
        <span class="tag-name">{{ t.tag }}</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { WorkTag } from '@/types/work'

defineProps<{
  workTags: WorkTag[]
}>()
</script>

<style scoped>
.tag-strip { padding: 12px 16px; }
.card-header-row { margin-bottom: 8px; }
.card-header-row h3 { margin: 0; font-size: 0.82rem; }
.tag-list { display: flex; gap: 6px; flex-wrap: wrap; }
.tag-pill-compact {
  display: flex; align-items: center; gap: 3px;
  padding: 3px 8px; border-radius: 100px;
  font-size: 0.75rem; background: oklch(56% 0.12 170 / 0.1);
  color: var(--accent); font-weight: 600;
}
.card-empty { font-size: 0.78rem; color: var(--muted); padding: 4px 0; }
</style>
