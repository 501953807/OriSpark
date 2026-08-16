<!-- Materio Vuetify-Style Alert Component -->
<template>
  <div
    class="m-alert"
    :class="[
      `m-alert--variant-${variant}`,
      `m-alert--color-${color}`,
      { 'm-alert--dense': dense },
      { 'm-alert--dismissible': dismissible },
    ]"
  >
    <div v-if="$slots.icon || icon" class="m-alert__icon">
      <slot name="icon">
        <svg v-if="color === 'error'" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round">
          <circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/>
        </svg>
        <svg v-else-if="color === 'warning'" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round">
          <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/>
        </svg>
        <svg v-else-if="color === 'success'" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round">
          <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/>
        </svg>
        <svg v-else width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round">
          <circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/>
        </svg>
      </slot>
    </div>
    <div class="m-alert__content">
      <div v-if="$slots.title" class="m-alert__title"><slot name="title" /></div>
      <div class="m-alert__text"><slot /></div>
    </div>
    <button v-if="dismissible" class="m-alert__close" @click="$emit('dismiss')" type="button">
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round">
        <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
      </svg>
    </button>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  color?: 'primary' | 'success' | 'warning' | 'error' | 'info'
  variant?: 'plain' | 'outlined' | 'filled'
  dense?: boolean
  dismissible?: boolean
  icon?: boolean
}>()
defineEmits<{ (e: 'dismiss'): void }>()
</script>

<style scoped>
.m-alert {
  position: relative;
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 12px 16px;
  border-radius: var(--m-radius-sm);
  font-size: var(--m-font-size-base);
  line-height: var(--m-line-height);
}

.m-alert--variant-filled {
  background: var(--m-primary-light);
  color: var(--m-primary);
  border: 1px solid rgba(140, 87, 255, 0.2);
}
.m-alert--variant-outlined {
  background: transparent;
  border: 1px solid var(--m-border);
  color: var(--m-on-surface);
}
.m-alert--variant-plain {
  background: transparent;
  border: none;
  color: var(--m-on-surface);
}

.m-alert--color-success.m-alert--variant-filled { background: var(--m-success-light); color: var(--m-success); border-color: rgba(86, 202, 0, 0.2); }
.m-alert--color-warning.m-alert--variant-filled { background: var(--m-warning-light); color: var(--m-warning); border-color: rgba(255, 180, 0, 0.2); }
.m-alert--color-error.m-alert--variant-filled { background: var(--m-error-light); color: var(--m-error); border-color: rgba(255, 76, 81, 0.2); }
.m-alert--color-info.m-alert--variant-filled { background: var(--m-info-light); color: var(--m-info); border-color: rgba(0, 177, 255, 0.2); }

.m-alert--color-success.m-alert--variant-outlined { border-color: var(--m-success); color: var(--m-success); }
.m-alert--color-warning.m-alert--variant-outlined { border-color: var(--m-warning); color: var(--m-warning); }
.m-alert--color-error.m-alert--variant-outlined { border-color: var(--m-error); color: var(--m-error); }
.m-alert--color-info.m-alert--variant-outlined { border-color: var(--m-info); color: var(--m-info); }

.m-alert--dense { padding: 8px 12px; font-size: var(--m-font-size-sm); }
.m-alert__icon { flex-shrink: 0; display: flex; align-items: center; margin-top: 1px; }
.m-alert__content { flex: 1; min-width: 0; }
.m-alert__title { font-weight: var(--m-font-weight-semibold); margin-bottom: 4px; }
.m-alert__text { opacity: 0.9; }
.m-alert__close {
  flex-shrink: 0; width: 24px; height: 24px; padding: 0;
  border: none; background: transparent; color: inherit;
  cursor: pointer; border-radius: var(--m-radius-sm); opacity: 0.6;
  display: flex; align-items: center; justify-content: center;
  transition: opacity var(--m-transition-fast);
}
.m-alert__close:hover { opacity: 1; }
</style>
