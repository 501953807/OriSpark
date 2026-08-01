<!-- src/App.vue -->
<template>
  <div class="app-root">
    <!-- Content is rendered by router-view via SharedElementTransition -->
    <SharedElementTransition />
  </div>
</template>

<script setup lang="ts">
import SharedElementTransition from '@/components/SharedElementTransition.vue'
</script>

<style>
/* Root app styles */
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
