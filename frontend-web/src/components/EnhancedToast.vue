<!-- src/components/EnhancedToast.vue -->
<script setup lang="ts">
import { ref, computed, watch } from 'vue'

interface ToastOptions {
  message: string
  type?: 'success' | 'error' | 'info' | 'warning'
  duration?: number
  icon?: string
}

const props = defineProps<{
  visible: boolean
  options?: ToastOptions
}>()

const emit = defineEmits(['close', 'update:visible'])

const timeoutRef = ref<ReturnType<typeof setTimeout> | null>(null)

const type = computed(() => props.options?.type || 'info')
const message = computed(() => props.options?.message || '')
const icon = computed(() => props.options?.icon || '')
const duration = computed(() => props.options?.duration || 3000)

const getPulseColor = computed(() => {
  const colors = {
    success: '#10b981',
    error: '#ef4444',
    info: '#0ea5e9',
    warning: '#f59e0b'
  }
  return colors[type.value] || colors.info
})

const hasRadialPulse = computed(() => true)

const startTimer = () => {
  if (duration.value <= 0) return

  timeoutRef.value = setTimeout(() => {
    emit('close')
  }, duration.value)
}

const stopTimer = () => {
  if (typeof timeoutRef.value === 'number' && timeoutRef.value !== null) {
    clearTimeout(timeoutRef.value)
    timeoutRef.value = null
  }
}

watch(() => props.visible, (newVal) => {
  if (newVal) {
    startTimer()
  } else {
    stopTimer()
  }
}, { immediate: true })

const onClose = () => {
  stopTimer()
  emit('close')
  emit('update:visible', false)
}

const getClassNames = () => {
  const base = ['toast']
  if (type.value) base.push(type.value)
  if (hasRadialPulse.value) base.push('has-radial-pulse')
  return base.join(' ')
}
</script>

<template>
  <div
    v-if="visible"
    :class="getClassNames()"
    class="enhanced-toast"
    role="status"
    aria-live="polite"
    @click.stop="onClose"
  >
    <div class="toast-content">
      <span v-if="icon" class="toast-icon">{{ icon }}</span>
      <span class="toast-message">{{ message }}</span>
    </div>
  </div>
</template>

<style scoped>
.enhanced-toast {
  position: fixed;
  top: 2rem;
  left: 50%;
  transform: translateX(-50%) translateY(-20px);
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  padding: 1rem 1.5rem;
  border-radius: 12px;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2);
  z-index: 3000;
  transition: transform 0.4s cubic-bezier(0.34, 1.56, 0.64, 1), opacity 0.3s ease;
  display: flex;
  align-items: center;
  gap: 0.75rem;
  min-width: 280px;
}

.enhanced-toast.show {
  transform: translateX(-50%) translateY(0);
}

.has-radial-pulse::before {
  content: '';
  position: absolute;
  inset: -25px;
  border-radius: 50%;
  background: radial-gradient(circle, var(--pulse-color, #0ea5e9), transparent 70%);
  opacity: 0;
  animation: pulseRing 1.5s ease-out;
  pointer-events: none;
}

@keyframes pulseRing {
  0% {
    transform: scale(0.5);
    opacity: 0.6;
  }
  100% {
    transform: scale(2.5);
    opacity: 0;
  }
}

.toast-content {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  z-index: 1;
}

.toast-icon {
  font-size: 1.25rem;
  flex-shrink: 0;
}

.toast-message {
  font-size: 0.95rem;
  color: #1f2937;
  line-height: 1.4;
}

/* Type-specific styles */
.toast.success {
  border-left: 4px solid #10b981;
}

.toast.error {
  border-left: 4px solid #ef4444;
}

.toast.info {
  border-left: 4px solid #0ea5e9;
}

.toast.warning {
  border-left: 4px solid #f59e0b;
}

/* Exit animation */
.toast.exit {
  transform: translateX(-50%) translateY(-20px) !important;
  opacity: 0;
}

/* Reduced motion preference */
@media (prefers-reduced-motion: reduce) {
  .enhanced-toast {
    transition: none !important;
  }

  .has-radial-pulse::before {
    animation: none !important;
    opacity: 0 !important;
  }
}
</style>
