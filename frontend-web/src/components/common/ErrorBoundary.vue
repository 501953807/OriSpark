<script setup lang="ts">
import { ref, onErrorCaptured } from 'vue'

const hasError = ref(false)
const error = ref<Error | null>(null)

onErrorCaptured((err, instance, info) => {
  hasError.value = true
  error.value = err instanceof Error ? err : new Error(String(err))
  console.error('[ErrorBoundary]', err)
  return false // prevent propagation
})
</script>

<template>
  <div v-if="hasError" class="error-boundary-fallback">
    <h2>Something went wrong</h2>
    <p>{{ error?.message }}</p>
    <button @click="hasError = false; error = null">Retry</button>
  </div>
  <slot v-else />
</template>

<style scoped>
.error-boundary-fallback {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 200px;
  padding: 2rem;
  text-align: center;
  color: #e53e3e;
}
.error-boundary-fallback h2 {
  margin-bottom: 0.5rem;
  font-size: 1.25rem;
}
.error-boundary-fallback p {
  margin-bottom: 1rem;
  color: #718096;
  font-size: 0.875rem;
  max-width: 400px;
}
.error-boundary-fallback button {
  padding: 0.5rem 1.5rem;
  border: 1px solid #e53e3e;
  border-radius: 0.375rem;
  background: transparent;
  color: #e53e3e;
  cursor: pointer;
}
.error-boundary-fallback button:hover {
  background: #e53e3e;
  color: white;
}
</style>
