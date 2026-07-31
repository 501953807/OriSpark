<!-- src/App.vue -->
<template>
  <div class="app-root">
    <!-- Motion Control Panel (fixed position) -->
    <MotionControlPanel />

    <!-- Shared element page transitions -->
    <SharedElementTransition />

    <!-- Content is rendered by router-view via SharedElementTransition -->
    <router-view />
  </div>
</template>

<script setup lang="ts">
import { onMounted } from 'vue'
import { useMotionStore } from '@/stores/motion'
import SharedElementTransition from '@/components/SharedElementTransition.vue'
import MotionControlPanel from '@/components/MotionControlPanel.vue'

const motionStore = useMotionStore()

// Ensure motion store is initialized
onMounted(() => {
  // Frame rate monitoring is already started in initMotionStore()
})
</script>

<style>
/* Root app styles with brand motion variables */
.app-root {
  min-height: 100vh;
  background: var(--brand-bg-light, #f8fafc);
}

/* Apply brand motion styles throughout the app */
button,
input,
textarea,
select {
  -webkit-tap-highlight-color: transparent;
}

/* Brand entrance animation helper class */
.brand-entrance {
  animation: brandEntrance 1s ease-out forwards;
  opacity: 0;
}

@keyframes brandEntrance {
  from {
    opacity: 0;
    transform: translateY(20px) scale(0.98);
  }
  to {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}

/* Brand pulse ring utility */
.brand-pulse {
  position: relative;
  overflow: hidden;
}

.brand-pulse::after {
  content: '';
  position: absolute;
  top: 50%;
  left: 50%;
  width: 0;
  height: 0;
  border-radius: 50%;
  background: radial-gradient(circle, rgba(14, 165, 233, 0.3), transparent);
  transform: translate(-50%, -50%);
  transition: width 0.6s, height 0.6s;
}

.brand-pulse.active::after {
  width: 300px;
  height: 300px;
}

/* Reduced motion preference */
@media (prefers-reduced-motion: reduce) :root {
  * {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
    scroll-behavior: auto !important;
  }
}
</style>
