<template>
  <div class="project-strip card">
    <div class="card-header-row">
      <h3>📁 所属项目</h3>
    </div>
    <div v-if="work?.project" class="project-display">
      <span class="project-name">{{ work.project.name }}</span>
      <span class="project-count">{{ work.project.work_count || 0 }} 个作品</span>
    </div>
    <div v-else class="project-none">未分配项目</div>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  work: {
    id: string
    project_id?: string | null
    project?: { name: string; id: string; work_count?: number } | null
  } | null
}>()
</script>

<style scoped>
.project-strip { padding: 12px 16px; }
.card-header-row { margin-bottom: 8px; }
.card-header-row h3 { margin: 0; font-size: 0.82rem; }
.project-display { display: flex; align-items: center; gap: 8px; }
.project-name { font-size: 0.85rem; font-weight: 600; }
.project-count { font-size: 0.7rem; color: var(--muted); }
.project-none { font-size: 0.78rem; color: var(--muted); font-style: italic; }
</style>
