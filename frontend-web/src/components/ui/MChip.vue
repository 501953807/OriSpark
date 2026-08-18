<!-- Materio Vuetify-Style Chip Component -->
<template>
  <span
    class="m-chip"
    :class="[
      `m-chip--color-${color}`,
      `m-chip--variant-${variant}`,
      { 'm-chip--disabled': disabled },
      { 'm-chip--removable': removable },
    ]"
  >
    <span v-if="$slots.default" class="m-chip__text">
      <slot />
    </span>
    <button
      v-if="removable"
      class="m-chip__close"
      @click="$emit('remove')"
      type="button"
    >
      <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round">
        <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
      </svg>
    </button>
  </span>
</template>

<script setup lang="ts">
defineProps<{
  color?: 'primary' | 'success' | 'warning' | 'error' | 'info' | 'grey'
  variant?: 'filled' | 'outlined' | 'plain'
  removable?: boolean
  disabled?: boolean
}>()

defineEmits<{
  (e: 'remove'): void
}>()
</script>

<style scoped>
.m-chip {
  display: inline-flex;
  align-items: center;
  gap: 0.375rem;
  height: 24px;
  padding: 0 12px;
  border-radius: var(--m-radius-full, 9999px);
  font-size: 0.75rem;
  font-weight: 600;
  line-height: 1;
  white-space: nowrap;
  transition: all var(--m-transition-fast);
}

/* ── Variants ── */
.m-chip--variant-filled {
  background: rgba(79, 70, 229, 0.12);
  color: #4F46E5;
}
.m-chip--variant-outlined {
  background: transparent;
  border: 1px solid rgba(79, 70, 229, 0.4);
  color: #4F46E5;
}
.m-chip--variant-plain {
  background: transparent;
  color: rgba(15, 23, 42, 0.7);
}

/* ── Colors ── */
.m-chip--color-success.m-chip--variant-filled {
  background: rgba(22, 163, 74, 0.12);
  color: #16A34A;
}
.m-chip--color-warning.m-chip--variant-filled {
  background: rgba(217, 119, 6, 0.12);
  color: #D97706;
}
.m-chip--color-error.m-chip--variant-filled {
  background: rgba(220, 38, 38, 0.12);
  color: #DC2626;
}
.m-chip--color-info.m-chip--variant-filled {
  background: rgba(2, 132, 199, 0.12);
  color: #0284C7;
}
.m-chip--color-grey.m-chip--variant-filled {
  background: rgba(100, 116, 139, 0.12);
  color: #64748B;
}

/* ── States ── */
.m-chip--disabled {
  opacity: var(--m-disabled-opacity);
  cursor: not-allowed;
}
.m-chip__close {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 16px;
  height: 16px;
  padding: 0;
  border: none;
  background: transparent;
  color: inherit;
  cursor: pointer;
  border-radius: 50%;
  opacity: 0.7;
  transition: opacity var(--m-transition-fast);
}
.m-chip__close:hover {
  opacity: 1;
}
</style>
