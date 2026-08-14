<!-- Materio Vuetify-Style Button Component (Nuxt version) -->
<template>
  <button
    class="m-btn"
    :class="[
      `m-btn--variant-${variant}`,
      `m-btn--size-${size}`,
      { 'm-btn--loading': loading },
      { 'm-btn--disabled': disabled },
      { 'm-btn--rounded': rounded },
      { 'm-btn--block': block },
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
}>()
defineEmits<{ (e: 'click', event: MouseEvent): void }>()
</script>

<style scoped>
.m-btn {
  position: relative;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 0.375rem;
  font-family: var(--m-font-family);
  font-size: var(--m-font-size-base);
  font-weight: var(--m-font-weight-medium);
  line-height: 1;
  white-space: nowrap;
  border: none;
  cursor: pointer;
  transition: all var(--m-transition);
  border-radius: var(--m-radius-sm);
  overflow: hidden;
}
.m-btn--variant-elevated, .m-btn--variant-flat {
  background: rgb(var(--m-primary-rgb, 140, 87, 255));
  color: var(--m-on-primary);
}
.m-btn--variant-elevated { box-shadow: var(--m-shadow-xs); }
.m-btn--variant-elevated:hover:not(:disabled) { background: var(--m-primary-darken-1); box-shadow: var(--m-shadow-sm); }
.m-btn--variant-flat:hover:not(:disabled) { background: var(--m-primary-darken-1); }
.m-btn--variant-outlined { background: transparent; color: rgb(var(--m-primary-rgb, 140, 87, 255)); border: 1px solid rgba(var(--m-primary-rgb, 140, 87, 255), 0.5); }
.m-btn--variant-outlined:hover:not(:disabled) { background: rgba(var(--m-primary-rgb, 140, 87, 255), 0.08); }
.m-btn--variant-text { background: transparent; color: rgb(var(--m-primary-rgb, 140, 87, 255)); }
.m-btn--variant-text:hover:not(:disabled) { background: rgba(var(--m-primary-rgb, 140, 87, 255), 0.08); }
.m-btn--variant-tonal { background: rgba(var(--m-primary-rgb, 140, 87, 255), 0.12); color: rgb(var(--m-primary-rgb, 140, 87, 255)); }
.m-btn--variant-tonal:hover:not(:disabled) { background: rgba(var(--m-primary-rgb, 140, 87, 255), 0.2); }
.m-btn--size-xs { height: 22px; padding: 0 10px; font-size: var(--m-font-size-xs); }
.m-btn--size-sm { height: 30px; padding: 0 14px; font-size: var(--m-font-size-sm); }
.m-btn--size-default { height: 38px; padding: 0 18px; }
.m-btn--size-lg { height: 46px; padding: 0 22px; font-size: var(--m-font-size-md); }
.m-btn--rounded { border-radius: 36px; }
.m-btn--block { display: flex; width: 100%; }
.m-btn--loading, .m-btn--disabled { cursor: not-allowed; opacity: var(--m-disabled-opacity); }
.m-btn__spinner { display: flex; align-items: center; justify-content: center; }
.m-btn__spinner-svg { width: 1em; height: 1em; animation: m-btn-spin 0.8s linear infinite; }
@keyframes m-btn-spin { to { transform: rotate(360deg); } }
.m-btn__prepend { margin-inline-end: 0.375rem; }
.m-btn__append { margin-inline-start: 0.375rem; }
.m-btn__content { display: flex; align-items: center; gap: 0.375rem; }
.m-btn__overlay {
  position: absolute; inset: 0; background: currentColor; opacity: 0;
  transition: opacity var(--m-transition-fast); border-radius: inherit;
}
.m-btn:hover:not(:disabled):not(.m-btn--loading) .m-btn__overlay { opacity: var(--m-hover-opacity); }
</style>
