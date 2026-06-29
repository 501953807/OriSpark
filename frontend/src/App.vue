<template>
  <router-view v-slot="{ Component }">
    <error-boundary>
      <component :is="Component" />
    </error-boundary>
  </router-view>
</template>

<script setup lang="ts">
import { onErrorCaptured, ref } from 'vue'

const hasError = ref(false)

onErrorCaptured((err, instance, info) => {
  console.error('[ErrorBoundary]', err, info)
  hasError.value = true
  return false // 阻止向上传播
})
</script>
