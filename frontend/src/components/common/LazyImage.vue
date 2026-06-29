<template>
  <img
    :src="loadedSrc"
    :alt="alt"
    :loading="'lazy'"
    :class="['lazy-img', { loaded }]"
    @load="onLoad"
    @error="onError"
  />
  <div v-if="!loaded" class="lazy-placeholder">
    <span>{{ placeholderIcon }}</span>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'

const props = withDefaults(defineProps<{
  src: string
  alt?: string
  placeholderIcon?: string
}>(), {
  placeholderIcon: '🖼️',
})

const loaded = ref(false)
const loadedSrc = ref('')
const errored = ref(false)

let observer: IntersectionObserver | null = null

function onLoad() { loaded.value = true }
function onError() { errored.value = true; loaded.value = true }

onMounted(() => {
  if ('IntersectionObserver' in window) {
    observer = new IntersectionObserver(entries => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          loadedSrc.value = props.src
          observer?.unobserve(entry.target)
        }
      })
    }, { rootMargin: '200px' })
    // Observe the parent element
    const el = document.querySelector(`[data-lazy-src="${props.src}"]`)
    if (el) observer.observe(el)
  } else {
    loadedSrc.value = props.src
  }
})
</script>

<style scoped>
.lazy-img { width: 100%; height: 100%; object-fit: cover; opacity: 0; transition: opacity 0.3s; }
.lazy-img.loaded { opacity: 1; }
.lazy-placeholder {
  position: absolute; inset: 0;
  display: flex; align-items: center; justify-content: center;
  background: oklch(95% 0.003 240);
  font-size: 2rem;
}
</style>
