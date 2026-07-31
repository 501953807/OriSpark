<!-- app/layouts/default.vue (updated with motion control) -->
<script setup lang="ts">
import { useMotionStore } from '@/stores/motion'
import MotionControlPanel from '@/components/MotionControlPanel.vue'

const motionStore = useMotionStore()
</script>

<template>
  <div class="portal-layout">
    <PortalHeader />
    <main class="portal-main">
      <slot />
    </main>
    <PortalFooter />

    <!-- Motion Control Panel (floating) -->
    <MotionControlPanel v-motion:enter="{ duration: 600, opacity: [0, 1], y: [20, 0] }" />
  </div>
</template>

<style scoped>
.portal-layout {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

.portal-main {
  flex: 1;
}

/* Motion control panel positioning */
/* The component handles its own positioning via CSS */
</style>
