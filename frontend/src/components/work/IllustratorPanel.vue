<template>
  <div class="illustrator-panel">
    <!-- Project -->
    <section class="info-group" v-if="projectName">
      <h4 class="info-group-title">项目</h4>
      <div class="info-row">
        <span class="info-label">项目</span>
        <span class="info-value">{{ projectName }}</span>
      </div>
    </section>

    <!-- Stage -->
    <section class="info-group" v-if="currentStage">
      <h4 class="info-group-title">创作阶段</h4>
      <div class="info-row">
        <span class="info-label">阶段</span>
        <span class="info-value"><span class="stage-badge">{{ stageLabel }}</span></span>
      </div>
    </section>

    <!-- Dimensions -->
    <section class="info-group" v-if="width || height">
      <h4 class="info-group-title">尺寸</h4>
      <div class="info-row">
        <span class="info-label">分辨率</span>
        <span class="info-value">{{ dimensionText }}</span>
      </div>
    </section>

    <!-- Creation Tool -->
    <section class="info-group" v-if="creationTool">
      <h4 class="info-group-title">创作工具</h4>
      <div class="info-row">
        <span class="info-label">工具</span>
        <span class="info-value">{{ creationTool }}</span>
      </div>
    </section>

    <!-- Completion Date -->
    <section class="info-group" v-if="completionDate">
      <h4 class="info-group-title">时间</h4>
      <div class="info-row">
        <span class="info-label">完成日期</span>
        <span class="info-value">{{ completionDate }}</span>
      </div>
    </section>

    <!-- Location -->
    <section class="info-group" v-if="location">
      <h4 class="info-group-title">位置</h4>
      <div class="info-row">
        <span class="info-label">位置</span>
        <span class="info-value">{{ location }}</span>
      </div>
    </section>

    <!-- Tags -->
    <section class="info-group" v-if="autoTags.length">
      <h4 class="info-group-title">标签</h4>
      <div class="tags-wrap">
        <span v-for="tag in autoTags" :key="tag" class="tag-pill">{{ tag }}</span>
      </div>
    </section>

    <!-- AI Sessions -->
    <section class="info-group" v-if="aiSessionCount > 0">
      <h4 class="info-group-title">
        AI 创作记录
        <span class="count-badge">{{ aiSessionCount }}</span>
      </h4>
      <div class="info-row">
        <span class="info-label">工具</span>
        <span class="info-value">{{ latestAiTool }}</span>
      </div>
    </section>

    <!-- Empty state -->
    <div v-if="!hasAnyInfo" class="empty-hint">
      <span class="hint-icon">&#127912;</span>
      <p>暂无插画师专属信息</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { Work } from '@/types/work'

// ------------------------------------------------------------------
// Props
// ------------------------------------------------------------------
interface Props {
  work: Work | null
  exifData: Record<string, any> | null
  metadata: Record<string, any>
  tags?: Array<{ tag: string }>
}

const props = withDefaults(defineProps<Props>(), {
  work: null,
  exifData: null,
  metadata: () => ({}),
  tags: () => [],
})

// ------------------------------------------------------------------
// Derived values
// ------------------------------------------------------------------
const projectName = computed(() => props.work?.project?.name ?? null)
const currentStage = computed(() => props.work?.current_stage ?? null)
const width = computed(() => props.work?.width ?? null)
const height = computed(() => props.work?.height ?? null)
const creationTool = computed(() => props.metadata?.creation_tool ?? null)
const completionDate = computed(() => props.metadata?.completion_date ?? null)
const location = computed(() => props.metadata?.creation_location ?? null)
const autoTags = computed(() => {
  const tags = props.metadata?.auto_tags
  if (Array.isArray(tags)) return tags
  return []
})

const dimensionText = computed(() => {
  const w = width.value
  const h = height.value
  if (w && h) return `${w} × ${h}`
  if (w) return `${w}px`
  if (h) return `${h}px`
  return null
})

const stageLabels: Record<string, string> = {
  inspiration: '灵感',
  sketch: '草图',
  lineart: '线稿',
  coloring: '上色',
  detail: '细节',
  final: '定稿',
  concept: '概念',
  outline: '大纲',
  design: '设计',
  script: '剧本',
}

const stageLabel = computed(() => {
  const stage = currentStage.value
  if (!stage) return ''
  return stageLabels[stage] || stage
})

// AI sessions from store (passed via workData or accessed directly)
const aiSessions = computed(() => {
  const raw = (props.work as unknown as Record<string, unknown>)?.ai_sessions
  if (Array.isArray(raw)) return raw
  return []
})

const aiSessionCount = computed(() => aiSessions.value.length)
const latestAiTool = computed(() => {
  if (aiSessions.value.length === 0) return '—'
  const first = aiSessions.value[0] as Record<string, unknown>
  return first.tool_name ?? '—'
})

const hasAnyInfo = computed(() => {
  return !!(
    projectName.value ||
    currentStage.value ||
    width.value ||
    height.value ||
    creationTool.value ||
    completionDate.value ||
    location.value ||
    autoTags.value.length > 0 ||
    aiSessionCount.value > 0
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

.hint-icon {
  font-size: 2rem;
  opacity: 0.6;
}

.info-group {
  padding-bottom: 16px;
  border-bottom: 1px solid var(--border);
}

.info-group:last-child {
  border-bottom: none;
  padding-bottom: 0;
}

.info-group-title {
  font-size: 0.72rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--accent);
  margin: 0 0 10px 0;
  display: flex;
  align-items: center;
  gap: 6px;
}

.info-row {
  display: flex;
  align-items: baseline;
  gap: 12px;
  font-size: 0.85rem;
  margin-bottom: 6px;
}

.info-row:last-child {
  margin-bottom: 0;
}

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

.stage-badge {
  display: inline-block;
  padding: 2px 10px;
  border-radius: 9999px;
  font-size: 0.78rem;
  font-weight: 600;
  background: oklch(65% 0.18 35 / 0.12);
  color: oklch(45% 0.15 35);
}

.count-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 20px;
  height: 20px;
  padding: 0 6px;
  border-radius: 9999px;
  font-size: 0.7rem;
  font-weight: 700;
  background: oklch(45% 0.15 35 / 0.15);
  color: oklch(45% 0.15 35);
}

.tags-wrap {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.tag-pill {
  display: inline-block;
  padding: 2px 10px;
  border-radius: 9999px;
  font-size: 0.75rem;
  background: oklch(95% 0.02 35);
  color: oklch(40% 0.05 35);
  border: 1px solid oklch(85% 0.04 35 / 0.3);
}
</style>
