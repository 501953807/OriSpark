<template>
  <div class="loading-spinner" :class="{ 'loading-spinner--full': fullScreen }">
    <div class="spinner-ring">
      <div class="spinner-track"></div>
      <div class="spinner-arc"></div>
    </div>
    <p v-if="text" class="loading-text">{{ text }}</p>
  </div>
</template>

<script setup lang="ts">
defineProps<{ text?: string; fullScreen?: boolean }>()
</script>

<style scoped>
.loading-spinner {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 48px 24px;
  gap: 20px;
}

.loading-spinner--full {
  position: absolute;
  inset: 0;
  z-index: 100;
  background: var(--m-bg-subtle, #F1F5F9);
}

.dark .loading-spinner--full {
  background: var(--m-bg-subtle, #1E293B);
}

.spinner-ring {
  position: relative;
  width: 48px;
  height: 48px;
}

.spinner-track {
  position: absolute;
  inset: 0;
  border-radius: 50%;
  border: 3px solid var(--m-border, rgba(15,23,42,0.08));
}

.spinner-arc {
  position: absolute;
  inset: 0;
  border-radius: 50%;
  border: 3px solid transparent;
  border-top-color: #4F46E5;
  animation: spin 0.75s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.loading-text {
  font-size: 0.9rem;
  color: var(--m-grey-500, #64748B);
  margin: 0;
  font-weight: 500;
  letter-spacing: 0.02em;
}
</style>
