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
  background: var(--bg, oklch(98% 0.002 240));
}

.dark .loading-spinner--full {
  background: var(--bg, oklch(13% 0.01 240));
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
  border: 3px solid var(--border, oklch(90% 0.005 240));
}

.spinner-arc {
  position: absolute;
  inset: 0;
  border-radius: 50%;
  border: 3px solid transparent;
  border-top-color: var(--accent, oklch(56% 0.12 170));
  animation: spin 0.75s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.loading-text {
  font-size: 0.9rem;
  color: var(--muted, oklch(55% 0.01 240));
  margin: 0;
  font-weight: 500;
  letter-spacing: 0.02em;
}
</style>
