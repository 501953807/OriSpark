<!-- src/components/SharedElementTransition.vue -->
<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useMotionStore } from '@/stores/motion'

const motionStore = useMotionStore()
const router = useRouter()
const route = useRoute()

// Track whether we're entering/exiting a shared element transition
const isEntering = ref(false)
const sharedElementKey = ref<string | null>(null)

// Detect when navigating through shared elements (e.g., list -> detail)
watch(() => route.fullPath, (newVal, oldVal) => {
  if (oldVal && newVal) {
    // Simple heuristic: if path segments match except ID, it might be a shared element transition
    const oldSegments = oldVal.path.split('/').filter(s => s)
    const newSegments = newVal.path.split('/').filter(s => s)

    if (oldSegments.length === newSegments.length - 1) {
      // We're navigating to a detail page
      isEntering.value = true
      sharedElementKey.value = `${oldVal.path}-${newVal.path}`

      setTimeout(() => {
        isEntering.value = false
        sharedElementKey.value = null
      }, 300)
    }
  }
})

// Determine if we should apply 3D transformation based on motion settings
const shouldApply3DTransition = computed(() =>
  motionStore.immersionLevel >= 2 && motionStore.shouldAnimate
)
</script>

<template>
  <router-view v-slot="{ Component }">
    <transition
      :key="sharedElementKey || route.fullPath"
      @before-enter="onBeforeEnter"
      @enter="onEnter"
      @after-enter="onAfterEnter"
      @before-leave="onBeforeLeave"
      @leave="onLeave"
      @after-leave="onAfterLeave"
    >
      <keep-alive>
        <component :is="Component" :key="route.fullPath" />
      </keep-alive>
    </transition>
  </router-view>
</template>

<style scoped>
/* Custom transition classes injected via JS */
.slide-fade-enter-active,
.slide-fade-leave-active {
  transition: all 0.3s ease;
}

.slide-fade-enter-from,
.slide-fade-leave-to {
  opacity: 0;
  transform: translateX(20px);
}

/* 3D shared element transition */
.shared-element-enter,
.shared-element-leave-to {
  transform: scale(0.95) rotateX(10deg);
  opacity: 0;
}

/* When immersion level is high, add more dramatic effects */
.depth-3 .slide-fade-enter-active,
.depth-3 .slide-fade-leave-active {
  transition-duration: 0.4s;
  easing-function: cubic-bezier(0.34, 1.56, 0.64, 1);
}

@media (prefers-reduced-motion: reduce) {
  .slide-fade-enter-active,
  .slide-fade-leave-active,
  .shared-element-enter,
  .shared-element-leave-to {
    transition: none !important;
    animation: none !important;
  }

  .slide-fade-enter-from,
  .slide-fade-leave-to,
  .shared-element-enter,
  .shared-element-leave-to {
    opacity: 1 !important;
    transform: none !important;
  }
}
</style>
