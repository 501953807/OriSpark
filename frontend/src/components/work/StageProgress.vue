<template>
  <div class="stage-progress">
    <div class="progress-track">
      <div
        v-for="(stage, i) in stages"
        :key="stage.value"
        class="progress-node"
        :class="{
          'completed': i < currentIndex,
          'current': i === currentIndex,
          'future': i > currentIndex,
        }"
        :style="{ '--stage-color': stage.color }"
        :title="stage.label"
      >
        <div class="node-dot" />
        <div v-if="i < stages.length - 1" class="node-connector" :class="{ 'completed': i < currentIndex }" />
      </div>
    </div>
    <div class="progress-labels">
      <span
        v-for="(stage, i) in stages"
        :key="stage.value"
        class="label"
        :class="{ 'active': i === currentIndex }"
        :style="{ '--stage-color': stage.color }"
      >
        {{ stage.label }}
      </span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { StageOption } from '@/composables/useWorkStages'
import { getStagesForFileType } from '@/composables/useWorkStages'

const props = defineProps<{
  file_type: string
  current_stage?: string | null
}>()

const stages = computed(() => getStagesForFileType(props.file_type))

const currentIndex = computed(() => {
  if (!props.current_stage) return -1
  return stages.value.findIndex(s => s.value === props.current_stage)
})
</script>

<style scoped>
.stage-progress {
  display: flex;
  flex-direction: column;
  gap: 6px;
  padding: 8px 0;
}

.progress-track {
  display: flex;
  align-items: center;
  position: relative;
  padding: 4px 0;
}

.progress-node {
  position: relative;
  display: flex;
  align-items: center;
  flex-shrink: 0;
}

.node-dot {
  width: 14px;
  height: 14px;
  border-radius: 50%;
  border: 2px solid var(--stage-color, #6B7280);
  background: var(--surface);
  transition: all 0.2s;
  z-index: 1;
}

.node-connector {
  width: 24px;
  height: 2px;
  background: oklch(85% 0.01 240);
  flex-shrink: 0;
  transition: background 0.2s;
}

.node-connector.completed {
  background: var(--stage-color, #6B7280);
}

.progress-node.completed .node-dot {
  background: var(--stage-color, #6B7280);
  border-color: var(--stage-color, #6B7280);
}

.progress-node.current .node-dot {
  background: var(--stage-color, #6B7280);
  border-color: var(--stage-color, #6B7280);
  box-shadow: 0 0 0 4px oklch(60% 0.15 var(--hue, 200) / 0.2);
  animation: pulse 2s infinite;
}

.progress-labels {
  display: flex;
  gap: 4px;
  overflow-x: auto;
}

.label {
  font-size: 0.65rem;
  color: var(--muted);
  white-space: nowrap;
  transition: color 0.2s;
}

.label.active {
  color: var(--stage-color, #6B7280);
  font-weight: 600;
}

@keyframes pulse {
  0%, 100% { box-shadow: 0 0 0 4px oklch(60% 0.15 var(--hue, 200) / 0.2); }
  50% { box-shadow: 0 0 0 8px oklch(60% 0.15 var(--hue, 200) / 0.1); }
}
</style>
