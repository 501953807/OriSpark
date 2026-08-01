<!-- src/components/SharedElementTransition.vue -->
<script setup lang="ts">
import { ref, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'

const router = useRouter()
const route = useRoute()

const isEntering = ref(false)

watch(() => route.fullPath, (newVal, oldVal) => {
  if (oldVal && newVal && oldVal !== newVal) {
    isEntering.value = true
    setTimeout(() => {
      isEntering.value = false
    }, 250)
  }
})
</script>

<template>
  <router-view v-slot="{ Component }">
    <transition
      name="slide-fade"
      :css="true"
    >
      <keep-alive>
        <component :is="Component" :key="'app-layout'" />
      </keep-alive>
    </transition>
  </router-view>
</template>

<style scoped>
.slide-fade-enter-active,
.slide-fade-leave-active {
  transition: opacity 0.2s ease, transform 0.2s ease;
}

.slide-fade-enter-from,
.slide-fade-leave-to {
  opacity: 0;
  transform: translateX(8px);
}

@media (prefers-reduced-motion: reduce) {
  .slide-fade-enter-active,
  .slide-fade-leave-active {
    transition: none !important;
  }

  .slide-fade-enter-from,
  .slide-fade-leave-to {
    opacity: 1 !important;
    transform: none !important;
  }
}
</style>
