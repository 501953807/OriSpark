<!-- src/components/SecureToggle.vue -->
<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useMotionStore } from '@/stores/motion'

defineProps<{
  locked?: boolean
}>()

const emit = defineEmits(['update:locked', 'toggle'])

const motionStore = useMotionStore()
const isLockedRef = ref(!!props.locked)

const toggle = () => {
  isLockedRef.value = !isLockedRef.value
  emit('update:locked', isLockedRef.value)
  emit('toggle', isLockedRef.value)
}

watch(() => props.locked, (newVal) => {
  if (newVal !== undefined) {
    isLockedRef.value = newVal
  }
})

// Compute if animation should play based on store state
const playAnimation = computed(() => motionStore.shouldAnimate)
</script>

<template>
  <div
    class="secure-toggle-container"
    :class="{ locked: isLocked }"
    @click="toggle"
    role="switch"
    :aria-checked="isLocked"
    tabindex="0"
    @keydown.enter="toggle"
    @keydown.space.prevent="toggle"
  >
    <div class="toggle-track">
      <div class="toggle-knob"></div>
      <svg class="lock-icon" viewBox="0 0 24 24" aria-hidden="true">
        <path d="M18 8h-1V6c0-2.76-2.24-5-5-5S7 3.24 7 6v2H6c-1.1 0-2 .9-2 2v10c0 1.1.9 2 2 2h12c1.1 0 2-.9 2-2V10c0-1.1-.9-2-2-2zm-6 9c-1.1 0-2-.9-2-2s.9-2 2-2 2 .9 2 2-.9 2-2 2zm3.1-9H8.9V6c0-1.71 1.39-3 3.1-3 1.71 0 3.1 1.29 3.1 3v2z"/>
      </svg>
    </div>
  </div>
</template>

<style scoped>
.secure-toggle-container {
  position: relative;
  width: 90px;
  height: 45px;
  cursor: pointer;
  outline: none;
}

.secure-toggle-container:focus-visible {
  box-shadow: 0 0 0 3px rgba(14, 165, 233, 0.3);
  border-radius: 22px;
}

.toggle-track {
  position: absolute;
  inset: 0;
  background: linear-gradient(135deg, #cbd5e1, #94a3b8);
  border-radius: 22px;
  transition: transform 0.4s cubic-bezier(0.34, 1.56, 0.64, 1),
              background 0.4s ease,
              box-shadow 0.4s ease;
  box-shadow: inset 0 2px 4px rgba(0,0,0,0.2), 0 2px 4px rgba(0,0,0,0.1);
}

.secure-toggle-container.locked .toggle-track {
  background: linear-gradient(135deg, #10b981, #059669);
  transform: translateX(45px);
  box-shadow: inset 0 2px 4px rgba(0,0,0,0.2), 0 4px 12px rgba(16, 185, 129, 0.3);
}

.toggle-knob {
  position: absolute;
  top: 4px;
  left: 4px;
  width: 37px;
  height: 37px;
  background: white;
  border-radius: 50%;
  box-shadow: 0 2px 8px rgba(0,0,0,0.3);
  transition: transform 0.4s cubic-bezier(0.34, 1.56, 0.64, 1);
}

.secure-toggle-container.locked .toggle-knob {
  transform: translateX(45px);
}

.lock-icon {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 20px;
  height: 20px;
  fill: currentColor;
  opacity: 0.8;
  transition: opacity 0.3s ease;
}

.secure-toggle-container .lock-icon {
  opacity: 0.8;
}

.secure-toggle-container.locked .lock-icon {
  color: #fff;
  opacity: 0.9;
}

/* Bounce effect on change when enabled */
.secure-toggle-container.animate-change {
  animation: lockToggleBounce 0.4s ease;
}

@keyframes lockToggleBounce {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.08); }
}

/* Reduced motion preference */
@media (prefers-reduced-motion: reduce) {
  .toggle-track, .toggle-knob, .lock-icon {
    transition: none !important;
  }

  .secure-toggle-container.animate-change {
    animation: none !important;
  }
}
</style>
