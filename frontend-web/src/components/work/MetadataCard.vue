<template>
  <div class="metadata-card card">
    <div class="card-header-row">
      <h3>📝 元数据</h3>
      <button class="btn btn-ghost btn-sm" @click="$emit('edit')">编辑</button>
    </div>
    <div class="info-list">
      <div class="info-row"><span class="il">标题</span><span class="iv">{{ work.title || '—' }}</span></div>
      <div v-if="work.synopsis" class="info-row"><span class="il">简介</span><span class="iv">{{ work.synopsis }}</span></div>
      <div class="info-row"><span class="il">作者</span><span class="iv">{{ work.rights?.author_name || work.custom_metadata?.author_name || work.custom_metadata?.author || '未设置' }}</span></div>
      <div v-if="work.copyright_year" class="info-row"><span class="il">版权年份</span><span class="iv">{{ work.copyright_year }}</span></div>
      <div v-if="work.license_type" class="info-row"><span class="il">许可证</span><span class="iv">{{ work.license_type }}</span></div>
      <div v-if="work.rights?.attribution_text" class="info-row"><span class="il">署名文本</span><span class="iv">{{ work.rights.attribution_text }}</span></div>
      <div v-if="work.current_stage" class="info-row"><span class="il">阶段</span><span class="iv">{{ getStageLabel(work.current_stage) }}</span></div>
      <div v-if="work.completion_date" class="info-row"><span class="il">完成日期</span><span class="iv">{{ work.completion_date }}</span></div>
      <div v-if="work.custom_metadata?.creation_tool" class="info-row"><span class="il">创作工具</span><span class="iv">{{ work.custom_metadata.creation_tool }}</span></div>
      <div v-if="work.project" class="info-row"><span class="il">项目</span><span class="iv">{{ work.project.name || work.project_id }}</span></div>
      <div v-if="work.tags?.length" class="info-row">
        <span class="il">标签</span>
        <span class="iv tags-wrapper">
          <span v-for="t in work.tags" :key="t.id" class="mini-tag">{{ t.tag }}</span>
        </span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { getStageColor, getAllStages } from '@/composables/useWorkStages'

defineProps<{
  work: {
    title: string
    synopsis?: string | null
    rights?: Record<string, any> | null
    custom_metadata?: Record<string, any> | null
    license_type?: string | null
    current_stage?: string | null
    completion_date?: string | null
    copyright_year?: number | null
    project?: { name: string } | null
    project_id?: string | null
    tags?: Array<{ id: string; tag: string }>
  }
}>()

defineEmits<{ edit: [] }>()

function getStageLabel(stage: string): string {
  const all = getAllStages()
  const found = all.find(s => s.value === stage)
  return found?.label || stage
}
</script>

<style scoped>
.metadata-card { padding: 16px 20px; }
.metadata-card h3 { margin: 0; font-size: 0.88rem; }
.card-header-row { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; }
.card-header-row h3 { margin: 0; font-size: 0.88rem; }
.info-list { display: flex; flex-direction: column; gap: 6px; }
.info-row { display: flex; justify-content: space-between; align-items: flex-start; gap: 8px; font-size: 0.78rem; padding: 4px 0; border-bottom: 1px solid oklch(94% 0.003 240); }
.info-row:last-child { border-bottom: none; }
.il { color: var(--muted); font-weight: 600; flex-shrink: 0; }
.iv { text-align: right; word-break: break-all; }
.tags-wrapper { display: flex; gap: 3px; flex-wrap: wrap; justify-content: flex-end; }
.mini-tag {
  padding: 1px 6px;
  border-radius: 100px;
  font-size: 0.68rem;
  background: oklch(56% 0.12 170 / 0.1);
  color: var(--accent);
}
.btn-sm { padding: 5px 10px; font-size: 0.75rem; }
</style>
