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
.default { background: oklch(0 0 0 / 0.04); color: var(--muted); }
.default .status-dot { background: var(--muted); }
.success, .confirmed, .active { background: oklch(56% 0.12 170 / 0.1); color: var(--green); }
.success .status-dot, .confirmed .status-dot, .active .status-dot { background: var(--green); }
.warning, .pending, .pending_review { background: oklch(62% 0.18 55 / 0.1); color: var(--orange); }
.warning .status-dot, .pending .status-dot, .pending_review .status-dot { background: var(--orange); }
.error, .failed { background: oklch(58% 0.18 30 / 0.1); color: #e53e3e; }
.error .status-dot, .failed .status-dot { background: #e53e3e; }
.info, .draft { background: oklch(58% 0.14 245 / 0.1); color: var(--blue); }
.info .status-dot, .draft .status-dot { background: var(--blue); }
</style>
