<template>
  <img
    :src="src"
    :alt="alt"
    :loading="'lazy'"
    :class="['lazy-img', { loaded }]"
    @load="loaded = true"
    @error="loaded = true"
  />
  <div v-if="!loaded" class="lazy-placeholder">
    <span>{{ placeholderIcon }}</span>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  src: string
  alt?: string
  placeholderIcon?: string
}>()

const loaded = defineModel<boolean>({ default: false })
</script>

<style scoped>
.lazy-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  opacity: 0;
  transition: opacity 0.3s;
}
.lazy-img.loaded {
  opacity: 1;
}
.lazy-placeholder {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background: oklch(95% 0.003 240);
  font-size: 2rem;
  z-index: 1;
}
</style>
