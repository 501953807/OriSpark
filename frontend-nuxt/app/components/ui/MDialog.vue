<!-- Materio Dialog Component -->
<template>
  <Teleport to="body">
    <transition name="m-dialog-overlay">
      <div v-if="modelValue" class="m-dialog__overlay" @click.self="$emit('update:modelValue', false)">
        <div class="m-dialog" :class="[{ 'm-dialog--fullscreen': fullscreen }]">
          <div class="m-dialog__header">
            <h3 class="m-dialog__title">{{ title }}</h3>
            <button class="m-dialog__close" @click="$emit('update:modelValue', false)" type="button">×</button>
          </div>
          <div class="m-dialog__body"><slot /></div>
          <div v-if="$slots.actions" class="m-dialog__actions">
            <slot name="actions" />
          </div>
        </div>
      </div>
    </transition>
  </Teleport>
</template>

<script setup lang="ts">
defineProps<{
  modelValue?: boolean
  title?: string
  fullscreen?: boolean
}>()
defineEmits<{ (e: 'update:modelValue', v: boolean): void }>()
</script>

<style scoped>
.m-dialog__overlay {
  position: fixed; inset: 0; z-index: 200;
  background: rgba(0, 0, 0, 0.4);
  display: flex; align-items: center; justify-content: center;
  padding: 24px;
}
.m-dialog {
  background: var(--m-surface);
  border-radius: var(--m-radius-md);
  box-shadow: var(--m-shadow-lg);
  width: 100%; max-width: 520px;
  max-height: 90vh;
  display: flex; flex-direction: column;
  overflow: hidden;
}
.m-dialog--fullscreen { max-width: 100%; max-height: 100%; border-radius: 0; }
.m-dialog__header {
  display: flex; align-items: center; justify-content: space-between;
  padding: 20px 24px;
  border-bottom: 1px solid var(--m-border);
}
.m-dialog__title { margin: 0; font-size: 18px; font-weight: 600; color: var(--m-on-surface); }
.m-dialog__close {
  background: none; border: none; font-size: 24px; line-height: 1;
  color: var(--m-grey-500); cursor: pointer; padding: 4px;
  border-radius: var(--m-radius-sm); transition: all var(--m-transition-fast);
}
.m-dialog__close:hover { background: var(--m-grey-100); color: var(--m-on-surface); }
.m-dialog__body { padding: 24px; overflow-y: auto; flex: 1; }
.m-dialog__actions {
  display: flex; justify-content: flex-end; gap: 8px;
  padding: 16px 24px; border-top: 1px solid var(--m-border);
}
.m-dialog-overlay-enter-active, .m-dialog-overlay-leave-active { transition: opacity var(--m-transition-fast); }
.m-dialog-overlay-enter-from, .m-dialog-overlay-leave-to { opacity: 0; }
</style>
