<template>
  <div class="status-badge" :class="variant">
    <span class="status-dot"></span>
    {{ label }}
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{
  status: string
  labels?: Record<string, string>
  variants?: Record<string, string>
}>()

const label = computed(() => {
  return props.labels?.[props.status] || props.status
})

const variant = computed(() => {
  return props.variants?.[props.status] || 'default'
})
</script>

<style scoped>
.status-badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 3px 12px;
  border-radius: 100px;
  font-size: 0.75rem;
  font-weight: 600;
}
.status-dot {
  width: 6px; height: 6px;
  border-radius: 50%;
}
.default { background: rgba(0,0,0,0.04); color: var(--muted); }
.default .status-dot { background: var(--muted); }
.success, .confirmed, .active { background: rgba(86,202,0,0.1); color: var(--m-success, #56CA00); }
.success .status-dot, .confirmed .status-dot, .active .status-dot { background: var(--m-success, #56CA00); }
.warning, .pending, .pending_review { background: rgba(255,180,0,0.1); color: var(--m-warning, #FFB400); }
.warning .status-dot, .pending .status-dot, .pending_review .status-dot { background: var(--m-warning, #FFB400); }
.error, .failed { background: rgba(255,76,81,0.1); color: var(--m-error, #FF4C51); }
.error .status-dot, .failed .status-dot { background: var(--m-error, #FF4C51); }
.info, .draft { background: rgba(140,87,255,0.1); color: var(--m-primary, #8C57FF); }
.info .status-dot, .draft .status-dot { background: var(--m-primary, #8C57FF); }
</style>
