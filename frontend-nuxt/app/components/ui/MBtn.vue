<!-- Materio Vuetify-Style Button Component -->
<template>
  <button
    class="m-btn"
    :class="[
      `m-btn--variant-${variant}`,
      `m-btn--size-${size}`,
      { 'm-btn--loading': loading },
      { 'm-btn--disabled': disabled || loading },
      { 'm-btn--rounded': rounded },
      { 'm-btn--block': block },
      `m-btn--color-${color}`,
    ]"
    :disabled="disabled || loading"
    @click="$emit('click', $event)"
  >
    <span v-if="loading" class="m-btn__spinner">
      <svg class="m-btn__spinner-svg" viewBox="0 0 24 24">
        <circle cx="12" cy="12" r="10" fill="none" stroke="currentColor" stroke-width="2.5" stroke-dasharray="31.4 31.4" stroke-linecap="round" />
      </svg>
    </span>
    <span v-if="$slots.prepend && !loading" class="m-btn__prepend"><slot name="prepend" /></span>
    <span class="m-btn__content"><slot /></span>
    <span v-if="$slots.append && !loading" class="m-btn__append"><slot name="append" /></span>
    <span class="m-btn__overlay" />
  </button>
</template>

<script setup lang="ts">
defineProps<{
  variant?: 'flat' | 'elevated' | 'outlined' | 'text' | 'tonal'
  size?: 'xs' | 'sm' | 'default' | 'lg'
  loading?: boolean
  disabled?: boolean
  rounded?: boolean
  block?: boolean
  color?: 'primary' | 'success' | 'warning' | 'error' | 'info' | 'default'
}>()
defineEmits<{ (e: 'click', event: MouseEvent): void }>()
</script>

<style scoped>
.m-btn {
  position: relative;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  font-family: var(--m-font-family);
  font-size: var(--m-font-size-base);
  font-weight: var(--m-font-weight-medium);
  line-height: 1;
  white-space: nowrap;
  border: none;
  cursor: pointer;
  transition: all var(--m-transition-fast);
  border-radius: var(--m-radius-sm);
  overflow: hidden;
  text-decoration: none;
}

/* Variants */
.m-btn--variant-elevated {
  background: var(--m-primary);
  color: #fff;
  box-shadow: var(--m-shadow-xs);
}
.m-btn--variant-elevated:hover:not(:disabled) {
  background: var(--m-primary-dark);
  box-shadow: var(--m-shadow-sm);
}

.m-btn--variant-flat {
  background: var(--m-primary);
  color: #fff;
}
.m-btn--variant-flat:hover:not(:disabled) {
  background: var(--m-primary-dark);
}

.m-btn--variant-outlined {
  background: transparent;
  color: var(--m-primary);
  border: 1px solid var(--m-border);
}
.m-btn--variant-outlined:hover:not(:disabled) {
  background: var(--m-primary-light);
  border-color: var(--m-primary);
}

.m-btn--variant-text {
  background: transparent;
  color: var(--m-primary);
}
.m-btn--variant-text:hover:not(:disabled) {
  background: var(--m-primary-light);
}

.m-btn--variant-tonal {
  background: var(--m-primary-light);
  color: var(--m-primary);
}
.m-btn--variant-tonal:hover:not(:disabled) {
  background: rgba(79, 70, 229, 0.2);
}

/* Sizes */
.m-btn--size-xs { height: 24px; padding: 0 8px; font-size: var(--m-font-size-xs); }
.m-btn--size-sm { height: 30px; padding: 0 12px; font-size: var(--m-font-size-sm); }
.m-btn--size-default { height: 36px; padding: 0 16px; }
.m-btn--size-lg { height: 44px; padding: 0 20px; font-size: var(--m-font-size-md); }

.m-btn--rounded { border-radius: 36px; }
.m-btn--block { display: flex; width: 100%; }
.m-btn--loading, .m-btn--disabled { cursor: not-allowed; opacity: var(--m-disabled-opacity); }

/* Color overrides */
.m-btn--color-success.m-btn--variant-elevated,
.m-btn--color-success.m-btn--variant-flat { background: var(--m-success); color: #fff; }
.m-btn--color-success.m-btn--variant-elevated:hover:not(:disabled),
.m-btn--color-success.m-btn--variant-flat:hover:not(:disabled) { background: var(--m-success); }
.m-btn--color-success.m-btn--variant-outlined { color: var(--m-success); border-color: var(--m-success); }
.m-btn--color-success.m-btn--variant-outlined:hover:not(:disabled) { background: var(--m-success-light); }
.m-btn--color-success.m-btn--variant-tonal { background: var(--m-success-light); color: var(--m-success); }
.m-btn--color-success.m-btn--variant-tonal:hover:not(:disabled) { background: rgba(86, 202, 0, 0.2); }

.m-btn--color-error.m-btn--variant-elevated,
.m-btn--color-error.m-btn--variant-flat { background: var(--m-error); color: #fff; }
.m-btn--color-error.m-btn--variant-elevated:hover:not(:disabled),
.m-btn--color-error.m-btn--variant-flat:hover:not(:disabled) { background: rgb(200, 50, 55); }
.m-btn--color-error.m-btn--variant-outlined { color: var(--m-error); border-color: var(--m-error); }
.m-btn--color-error.m-btn--variant-outlined:hover:not(:disabled) { background: var(--m-error-light); }
.m-btn--color-error.m-btn--variant-tonal { background: var(--m-error-light); color: var(--m-error); }

.m-btn--color-warning.m-btn--variant-elevated,
.m-btn--color-warning.m-btn--variant-flat { background: var(--m-warning); color: #0f172a; }
.m-btn--color-warning.m-btn--variant-outlined { color: var(--m-warning); border-color: var(--m-warning); }
.m-btn--color-warning.m-btn--variant-tonal { background: var(--m-warning-light); color: var(--m-warning); }

.m-btn--color-info.m-btn--variant-elevated,
.m-btn--color-info.m-btn--variant-flat { background: var(--m-info); color: #fff; }
.m-btn--color-info.m-btn--variant-outlined { color: var(--m-info); border-color: var(--m-info); }
.m-btn--color-info.m-btn--variant-tonal { background: var(--m-info-light); color: var(--m-info); }

/* Subtle elements */
.m-btn__spinner { display: flex; align-items: center; justify-content: center; }
.m-btn__spinner-svg { width: 1em; height: 1em; animation: m-btn-spin 0.8s linear infinite; }
@keyframes m-btn-spin { to { transform: rotate(360deg); } }
.m-btn__prepend { margin-inline-end: 4px; }
.m-btn__append { margin-inline-start: 4px; }
.m-btn__content { display: flex; align-items: center; gap: 6px; }
.m-btn__overlay {
  position: absolute; inset: 0; background: currentColor; opacity: 0;
  transition: opacity var(--m-transition-fast); border-radius: inherit;
}
.m-btn:hover:not(:disabled):not(.m-btn--loading) .m-btn__overlay { opacity: var(--m-hover-opacity); }
</style>
