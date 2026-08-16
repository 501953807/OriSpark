<!-- Materio Chip / Badge Component -->
<template>
  <span class="m-chip" :class="[`m-chip--${color}`, `m-chip--${variant}`, { 'm-chip--dot': dot, 'm-chip--clickable': clickable }]" @click="clickable && $emit('click')">
    <span v-if="$slots.default" class="m-chip__label"><slot /></span>
    <span v-if="icon || $slots.icon" class="m-chip__icon"><slot name="icon"><slot :name="`${color}-icon`" /></slot></span>
    <button v-if="closable" class="m-chip__close" @click.stop="$emit('close')" type="button">×</button>
  </span>
</template>

<script setup lang="ts">
defineProps<{
  color?: 'primary' | 'success' | 'warning' | 'error' | 'info' | 'default'
  variant?: 'filled' | 'tonal' | 'outlined'
  dot?: boolean
  closable?: boolean
  clickable?: boolean
  icon?: boolean
}>()
defineEmits<{ (e: 'click'): void; (e: 'close'): void }>()
</script>

<style scoped>
.m-chip {
  display: inline-flex; align-items: center; gap: 4px;
  padding: 3px 10px;
  border-radius: 100px;
  font-size: 12px; font-weight: 500;
  white-space: nowrap;
  transition: all var(--m-transition-fast);
  line-height: 1.4;
}
.m-chip--filled { background: var(--m-primary-light); color: var(--m-primary); }
.m-chip--tonal { background: var(--m-primary-light); color: var(--m-primary); }
.m-chip--outlined { background: transparent; color: var(--m-primary); border: 1px solid var(--m-primary-light); }
.m-chip--color-success.m-chip--filled, .m-chip--color-success.m-chip--tonal { background: var(--m-success-light); color: var(--m-success); }
.m-chip--color-warning.m-chip--filled, .m-chip--color-warning.m-chip--tonal { background: var(--m-warning-light); color: var(--m-warning); }
.m-chip--color-error.m-chip--filled, .m-chip--color-error.m-chip--tonal { background: var(--m-error-light); color: var(--m-error); }
.m-chip--color-info.m-chip--filled, .m-chip--color-info.m-chip--tonal { background: var(--m-info-light); color: var(--m-info); }
.m-chip--color-default.m-chip--filled { background: var(--m-grey-100); color: var(--m-grey-700); }
.m-chip--color-default.m-chip--outlined { border-color: var(--m-border); color: var(--m-grey-700); }
.m-chip--dot { padding: 3px 6px; }
.m-chip--dot .m-chip__label { display: none; }
.m-chip--clickable { cursor: pointer; }
.m-chip--clickable:hover { opacity: 0.85; }
.m-chip__icon { display: flex; align-items: center; }
.m-chip__close {
  background: none; border: none; color: inherit; cursor: pointer;
  font-size: 14px; line-height: 1; padding: 0 2px; opacity: 0.7;
  border-radius: 50%; transition: opacity var(--m-transition-fast);
}
.m-chip__close:hover { opacity: 1; }
</style>
