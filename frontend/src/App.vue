<template>
  <router-view v-slot="{ Component }">
    <ErrorBoundary>
      <component :is="Component" />
    </ErrorBoundary>
  </router-view>
  <ToastContainer />
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import ToastContainer from './components/common/ToastContainer.vue'
import ErrorBoundary from './components/common/ErrorBoundary.vue'
import { setToast } from './api/client'

const hasError = ref(false)

onMounted(() => {
  // Wire up toast to API client interceptor
  const w = window as any
  if (w.$toast) {
    setToast(w.$toast)
  }
})
</script>
