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
  border-radius: var(--m-radius-full, 9999px);
  font-size: 0.75rem;
  font-weight: 600;
  font-family: var(--m-font-family);
}
.status-dot {
  width: 6px; height: 6px;
  border-radius: 50%;
}
.default { background: rgba(100, 116, 139, 0.1); color: var(--m-grey-500, #64748B); }
.default .status-dot { background: var(--m-grey-500, #64748B); }
.success, .confirmed, .active { background: rgba(22,163,74,0.1); color: #16A34A; }
.success .status-dot, .confirmed .status-dot, .active .status-dot { background: #16A34A; }
.warning, .pending, .pending_review { background: rgba(217,119,6,0.1); color: #D97706; }
.warning .status-dot, .pending .status-dot, .pending_review .status-dot { background: #D97706; }
.error, .failed { background: rgba(220,38,38,0.1); color: #DC2626; }
.error .status-dot, .failed .status-dot { background: #DC2626; }
.info, .draft { background: rgba(79,70,229,0.1); color: #4F46E5; }
.info .status-dot, .draft .status-dot { background: #4F46E5; }
</style>
