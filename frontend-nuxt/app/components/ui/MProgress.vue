<!-- Materio Progress Component -->
<template>
  <div class="m-progress" :class="[{ 'm-progress--striped': striped, 'm-progress--animated': animated }]">
    <div class="m-progress__bar" :style="{ width: percent + '%', background: barColor }">
      <div v-if="striped" class="m-progress__stripe" />
    </div>
    <div v-if="showLabel" class="m-progress__label">{{ label ?? percent + '%' }}</div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
const props = defineProps<{
  modelValue?: number
  max?: number
  color?: 'primary' | 'success' | 'warning' | 'error' | 'info'
  striped?: boolean
  animated?: boolean
  showLabel?: boolean
  label?: string
}>()
const percent = computed(() => Math.round((props.modelValue ?? 0) / (props.max ?? 100) * 100))
const barColor = computed(() => {
  const colors: Record<string, string> = {
    primary: 'var(--m-primary)',
    success: 'var(--m-success)',
    warning: 'var(--m-warning)',
    error: 'var(--m-error)',
    info: 'var(--m-info)',
  }
  return colors[props.color ?? 'primary'] ?? 'var(--m-primary)'
})
</script>

<style scoped>
.m-progress {
  height: 8px;
  background: var(--m-grey-100);
  border-radius: var(--m-radius-full);
  overflow: hidden;
  position: relative;
}
.m-progress__bar {
  height: 100%;
  border-radius: var(--m-radius-full);
  transition: width 0.4s ease;
}
.m-progress--striped .m-progress__bar {
  background-image: linear-gradient(
    45deg,
    rgba(255,255,255,0.15) 25%,
    transparent 25%,
    transparent 50%,
    rgba(255,255,255,0.15) 50%,
    rgba(255,255,255,0.15) 75%,
    transparent 75%
  );
  background-size: 16px 16px;
}
.m-progress--animated .m-progress__bar {
  animation: m-progress-stripes 1s linear infinite;
}
@keyframes m-progress-stripes {
  from { background-position: 16px 0; }
  to { background-position: 0 0; }
}
.m-progress__label {
  position: absolute; right: 0; top: -18px;
  font-size: 12px; color: var(--m-grey-500);
}
</style>
