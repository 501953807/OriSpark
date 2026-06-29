<template>
  <div class="metadata-strip card">
    <div class="card-header-row">
      <h3>📝 元数据</h3>
    </div>
    <div class="info-list">
      <div class="info-row"><span class="il">标题</span><span class="iv">{{ work.title || '—' }}</span></div>
      <div v-if="work.synopsis" class="info-row"><span class="il">简介</span><span class="iv">{{ work.synopsis }}</span></div>
      <div class="info-row"><span class="il">作者</span><span class="iv">{{ authorName }}</span></div>
      <div v-if="work.copyright_year" class="info-row"><span class="il">版权年份</span><span class="iv">{{ work.copyright_year }}</span></div>
      <div v-if="work.license_type" class="info-row"><span class="il">许可证</span><span class="iv">{{ work.license_type }}</span></div>
      <div v-if="work.rights?.attribution_text" class="info-row"><span class="il">署名文本</span><span class="iv">{{ work.rights.attribution_text }}</span></div>
      <div v-if="work.current_stage" class="info-row"><span class="il">阶段</span><span class="iv">{{ stageLabel }}</span></div>
      <div v-if="work.completion_date" class="info-row"><span class="il">完成日期</span><span class="iv">{{ work.completion_date }}</span></div>
      <div v-if="work.custom_metadata?.creation_tool" class="info-row"><span class="il">创作工具</span><span class="iv">{{ work.custom_metadata.creation_tool }}</span></div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { getAllStages } from '@/composables/useWorkStages'

const props = defineProps<{
  work: {
    title: string
    synopsis?: string | null
    rights?: Record<string, any> | null
    custom_metadata?: Record<string, any> | null
    license_type?: string | null
    current_stage?: string | null
    completion_date?: string | null
    copyright_year?: number | null
  }
}>()

const authorName = computed(() => {
  return props.work.rights?.author_name
    || props.work.custom_metadata?.author_name
    || props.work.custom_metadata?.author
    || '未设置'
})

const stageLabel = computed(() => {
  if (!props.work.current_stage) return ''
  const all = getAllStages()
  const found = all.find((s: any) => s.value === props.work.current_stage)
  return found?.label || props.work.current_stage
})
</script>

<style scoped>
.metadata-strip { padding: 12px 16px; }
.card-header-row { margin-bottom: 8px; }
.card-header-row h3 { margin: 0; font-size: 0.82rem; }
.info-list { display: flex; flex-direction: column; gap: 0; }
.info-row {
  display: flex; justify-content: space-between; align-items: flex-start; gap: 8px;
  font-size: 0.75rem; padding: 5px 0; border-bottom: 1px solid oklch(94% 0.003 240);
}
.info-row:last-child { border-bottom: none; }
.il { color: var(--muted); font-weight: 600; flex-shrink: 0; }
.iv { text-align: right; word-break: break-all; }
</style>
