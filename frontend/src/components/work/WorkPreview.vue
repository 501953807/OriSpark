<template>
  <div class="work-preview" @click.self="$emit('close')">
    <div class="preview-content animate-scale-in">
      <button class="preview-close" @click="$emit('close')">×</button>
      <div class="preview-media">
        <img v-if="work.file_type === 'image' && work.file_path" :src="work.file_path" :alt="work.title" />
        <audio v-else-if="work.file_type === 'audio'" controls :src="work.file_path" />
        <video v-else-if="work.file_type === 'video'" controls :src="work.file_path" />
        <div v-else class="preview-fallback">
          <span class="preview-icon">📄</span>
          <p>{{ work.file_name }}</p>
        </div>
      </div>
      <div class="preview-info">
        <h3>{{ work.title }}</h3>
        <div class="preview-meta">
          <span>{{ work.file_extension?.toUpperCase() }}</span>
          <span>{{ work.file_type }}</span>
          <span v-if="work.width">{{ work.width }}×{{ work.height }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { Work } from '@/types/work'

defineProps<{
  work: Work
}>()

defineEmits<{ close: [] }>()
</script>

<style scoped>
.work-preview {
  position: fixed; inset: 0; z-index: 9999;
  background: oklch(0 0 0 / 0.7);
  backdrop-filter: blur(8px);
  display: flex; align-items: center; justify-content: center;
}
.preview-content {
  background: var(--surface); border-radius: var(--radius-xl);
  max-width: 90vw; max-height: 90vh; overflow: hidden;
  position: relative;
}
.preview-close {
  position: absolute; top: 12px; right: 12px; z-index: 10;
  background: oklch(0 0 0 / 0.5); color: #fff; border: none;
  width: 36px; height: 36px; border-radius: 50%; font-size: 1.3rem;
  cursor: pointer; display: flex; align-items: center; justify-content: center;
}
.preview-media {
  min-width: 300px; min-height: 200px;
  display: flex; align-items: center; justify-content: center;
  background: oklch(15% 0.005 240);
}
.preview-media img { max-width: 100%; max-height: 70vh; object-fit: contain; }
.preview-media audio, .preview-media video { max-width: 100%; }
.preview-fallback { text-align: center; color: #fff; padding: 60px; }
.preview-icon { font-size: 4rem; }
.preview-info { padding: 16px 20px; }
.preview-info h3 { margin: 0; font-size: 1.1rem; }
.preview-meta { display: flex; gap: 12px; font-size: 0.8rem; color: var(--muted); margin-top: 6px; }
</style>
