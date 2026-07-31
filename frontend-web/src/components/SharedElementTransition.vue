<!-- src/components/SharedElementTransition.vue -->
<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useMotionStore } from '@/stores/motion'

const motionStore = useMotionStore()
const router = useRouter()
const route = useRoute()

const isEntering = ref(false)
const sharedElementKey = ref<string | null>(null)

watch(() => route.fullPath, (newVal, oldVal) => {
  if (oldVal && newVal && oldVal !== newVal) {
    const oldSegments = oldVal.split('/').filter(Boolean)
    const newSegments = newVal.split('/').filter(Boolean)
    if (oldSegments.length === newSegments.length - 1) {
      isEntering.value = true
      sharedElementKey.value = `${oldVal}-${newVal}`
      setTimeout(() => {
        isEntering.value = false
        sharedElementKey.value = null
      }, 300)
    }
  }
})

const shouldApply3DTransition = computed(() =>
  motionStore.immersionLevel >= 2 && motionStore.shouldAnimate
)
</script>

<template>
  <router-view v-slot="{ Component }">
    <transition
      :name="shouldApply3DTransition ? 'slide-fade' : 'slide-fade'"
      :css="true"
    >
      <keep-alive>
        <component :is="Component" :key="route.fullPath" />
      </keep-alive>
    </transition>
  </router-view>
</template>

<style scoped>
.slide-fade-enter-active,
.slide-fade-leave-active {
  transition: opacity 0.25s ease, transform 0.25s ease;
}

.slide-fade-enter-from,
.slide-fade-leave-to {
  opacity: 0;
  transform: translateX(12px);
}

.depth-3 .slide-fade-enter-active,
.depth-3 .slide-fade-leave-active {
  transition: opacity 0.3s ease, transform 0.3s ease;
}

.depth-3 .slide-fade-enter-from,
.depth-3 .slide-fade-leave-to {
  opacity: 0;
  transform: translateX(24px) scale(0.97);
}

@media (prefers-reduced-motion: reduce) {
  .slide-fade-enter-active,
  .slide-fade-leave-active,
  .depth-3 .slide-fade-enter-active,
  .depth-3 .slide-fade-leave-active {
    transition: none !important;
  }

  .slide-fade-enter-from,
  .slide-fade-leave-to,
  .depth-3 .slide-fade-enter-from,
  .depth-3 .slide-fade-leave-to {
    opacity: 1 !important;
    transform: none !important;
  }
}
</style>
