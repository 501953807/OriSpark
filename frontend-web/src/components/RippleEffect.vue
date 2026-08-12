<template>
  <div v-if="showRipple" class="ripple-container">
    <span
      v-for="r in ripples"
      :key="r.id"
      class="ripple"
      :data-id="r.id"
      :style="{
        left: r.x + 'px',
        top: r.y + 'px',
        backgroundColor: store.brandRippleColor,
        animationDuration: store.brandRippleDuration + 'ms',
      }"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onUnmounted } from 'vue'
import { useMotionStore } from '@/stores/useMotionStore'

type Ripple = { id: number; x: number; y: number }

const store = useMotionStore()
const ripples = ref<Ripple[]>([])
let nextId = 0

const showRipple = computed(() => {
  if (store.prefersReducedMotion) return false
  if (store.effectiveLevel === 0) return false
  return true
})

function handleClick(e: MouseEvent) {
  const el = e.currentTarget as HTMLElement
  if (!el) return
  const rect = el.getBoundingClientRect()
  ripples.value.push({
    id: nextId++,
    x: e.clientX - rect.left,
    y: e.clientY - rect.top,
  })
}

function onRippleEnd(e: AnimationPlaybackEvent) {
  const el = e.target as HTMLElement
  const rid = Number(el.dataset?.id)
  if (Number.isNaN(rid)) return
  const idx = ripples.value.findIndex(r => r.id === rid)
  if (idx !== -1) ripples.value.splice(idx, 1)
}

onUnmounted(() => {
  ripples.value = []
})
</script>

<style scoped>
.ripple-container {
  position: absolute;
  inset: 0;
  pointer-events: none;
  overflow: hidden;
  z-index: 1;
}

.ripple {
  position: absolute;
  width: 8px;
  height: 8px;
  border-radius: 50%;
  transform: translate(-50%, -50%);
  animation: ripple-expand var(--ripple-duration, 600ms) ease-out forwards;
}

@keyframes ripple-expand {
  0% {
    width: 8px;
    height: 8px;
    opacity: 0.6;
  }
  100% {
    width: 400px;
    height: 400px;
    opacity: 0;
  }
}
</style>
