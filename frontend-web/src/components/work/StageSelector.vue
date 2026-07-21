<template>
  <div class="stage-selector">
    <select :value="modelValue" @change="$emit('update:modelValue', ($event.target as HTMLSelectElement).value)">
      <option value="">未设置</option>
      <option v-for="s in stages" :key="s.value" :value="s.value" :style="{ '--stage-color': s.color }">
        {{ s.label }}
      </option>
    </select>
    <span v-if="selectedIndex >= 0" class="stage-count">{{ selectedIndex + 1 }}/{{ stages.length }}</span>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { StageOption } from '@/composables/useWorkStages'
import { getStagesForFileType, ILLUSTRATION_STAGES, GENERIC_STAGES } from '@/composables/useWorkStages'

const props = defineProps<{
  modelValue?: string | null
  fileType?: string
}>()
defineEmits<{ 'update:modelValue': [val: string | null] }>()

const stages = computed(() => getStagesForFileType(props.fileType || 'image'))

const selectedIndex = computed(() => {
  if (!props.modelValue) return -1
  return stages.value.findIndex(s => s.value === props.modelValue)
})
</script>

<style scoped>
.stage-selector {
  display: flex;
  align-items: center;
  gap: 8px;
}

select {
  padding: 6px 10px;
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  font-size: 0.85rem;
  font-family: var(--font-body);
  color: var(--fg);
  background: var(--surface);
  cursor: pointer;
  outline: none;
}

select:focus {
  border-color: var(--accent);
  box-shadow: 0 0 0 3px oklch(56% 0.12 170 / 0.1);
}

.stage-count {
  font-size: 0.7rem;
  color: var(--muted);
  font-weight: 600;
}
</style>
