<template>
  <Teleport to="body">
    <TransitionGroup name="toast" tag="div" class="toast-container">
      <div
        v-for="toast in toasts"
        :key="toast.id"
        :class="['toast', `toast-${toast.type}`]"
      >
        <span class="toast-icon">{{ iconMap[toast.type] }}</span>
        <span class="toast-message">{{ toast.message }}</span>
        <button class="toast-close" @click="remove(toast.id)">×</button>
      </div>
    </TransitionGroup>
  </Teleport>
</template>

<script setup lang="ts">
import { ref } from 'vue'

interface Toast {
  id: number
  message: string
  type: 'success' | 'error' | 'warning' | 'info'
}

const toasts = ref<Toast[]>([])
let idCounter = 0

const iconMap: Record<string, string> = {
  success: '✅',
  error: '❌',
  warning: '⚠️',
  info: 'ℹ️',
}

function show(message: string, type: Toast['type'] = 'info', duration: number = 3000) {
  const id = ++idCounter
  toasts.value.push({ id, message, type })
  if (duration > 0) {
    setTimeout(() => remove(id), duration)
  }
}

function remove(id: number) {
  const idx = toasts.value.findIndex(t => t.id === id)
  if (idx > -1) toasts.value.splice(idx, 1)
}

// Expose for use from anywhere
;(window as any).$toast = { show, remove }
defineExpose({ show, remove })
</script>

<style scoped>
.toast-container {
  position: fixed;
  bottom: 24px;
  right: 24px;
  z-index: 9999;
  display: flex;
  flex-direction: column-reverse;
  gap: 8px;
}
.toast {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 20px;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  box-shadow: 0 4px 24px oklch(0 0 0 / 0.12);
  font-size: 0.88rem;
  min-width: 280px;
  max-width: 420px;
}
.toast-success { border-left: 4px solid var(--green); }
.toast-error   { border-left: 4px solid #e53e3e; }
.toast-warning { border-left: 4px solid var(--orange); }
.toast-info    { border-left: 4px solid var(--blue); }
.toast-message { flex: 1; }
.toast-close {
  background: none; border: none; cursor: pointer;
  font-size: 1.2rem; color: var(--muted); padding: 0 4px;
}
.toast-enter-active { animation: slide-in-right 0.3s ease; }
.toast-leave-active { animation: slide-in-right 0.3s ease reverse; }
</style>
