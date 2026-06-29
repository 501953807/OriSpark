<template>
  <Teleport to="body">
    <Transition name="modal">
      <div v-if="visible" class="modal-overlay" @click.self="$emit('close')">
        <div class="modal-card animate-scale-in">
          <div class="modal-header">
            <h3 class="modal-title">{{ title }}</h3>
            <button class="modal-close" @click="$emit('close')">×</button>
          </div>
          <div class="modal-body">
            <p class="modal-message">{{ message }}</p>
          </div>
          <div class="modal-footer">
            <button class="btn btn-secondary" @click="$emit('close')">{{ cancelText }}</button>
            <button
              class="btn"
              :class="confirmVariant === 'danger' ? 'btn-danger' : 'btn-primary'"
              @click="$emit('confirm')"
            >
              {{ confirmText }}
            </button>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup lang="ts">
defineProps<{
  visible: boolean
  title?: string
  message?: string
  confirmText?: string
  cancelText?: string
  confirmVariant?: 'primary' | 'danger'
}>()

defineEmits<{
  close: []
  confirm: []
}>()
</script>

<style scoped>
.modal-overlay {
  position: fixed; inset: 0;
  background: oklch(0 0 0 / 0.4);
  backdrop-filter: blur(4px);
  display: flex; align-items: center; justify-content: center;
  z-index: 9998;
}
.modal-card {
  background: var(--surface);
  border-radius: var(--radius-xl);
  padding: 28px;
  max-width: 420px;
  width: 90%;
  box-shadow: 0 16px 64px oklch(0 0 0 / 0.16);
}
.modal-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 16px; }
.modal-title { font-size: 1.15rem; font-weight: 700; margin: 0; }
.modal-close { background: none; border: none; cursor: pointer; font-size: 1.4rem; color: var(--muted); }
.modal-message { color: var(--muted); line-height: 1.6; margin: 0; }
.modal-footer { display: flex; justify-content: flex-end; gap: 10px; margin-top: 24px; }
.btn-danger { background: #e53e3e; color: #fff; }
.btn-danger:hover { background: #c53030; }
.modal-enter-active { animation: scale-in 0.25s ease; }
.modal-leave-active { animation: scale-in 0.2s ease reverse; }
</style>
