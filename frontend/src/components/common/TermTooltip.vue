<template>
  <span class="term-wrapper" @mouseenter="show = true" @mouseleave="show = false">
    <slot />
    <span v-if="show" class="term-tooltip">{{ term }}: {{ explanation }}</span>
  </span>
</template>

<script setup lang="ts">
import { ref } from 'vue'
defineProps<{ term: string; explanation: string }>()
const show = ref(false)
</script>

<style scoped>
.term-wrapper { position: relative; cursor: help; border-bottom: 1px dotted var(--text-secondary); }
.term-tooltip {
  position: absolute; bottom: 100%; left: 50%; transform: translateX(-50%);
  background: var(--text-primary, #333); color: var(--bg-card, #fff);
  padding: 6px 12px; border-radius: 6px; font-size: 0.76rem; font-weight: 400;
  white-space: nowrap; z-index: 9999; margin-bottom: 4px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.15);
}
</style>
