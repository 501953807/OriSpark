<!-- src/components/DragDropFeedback.vue -->
<script setup lang="ts">
import { ref, computed } from 'vue'
const props = defineProps<{
  active?: boolean
  type?: 'drop' | 'drag' | 'hover'
}>()

const defaultProps = {
  drop: { color: '#10b981', scale: 1.1 },
  drag: { color: '#0ea5e9', scale: 1.05 },
  hover: { color: '#3b82f6', scale: 1.02 }
}

const currentType = props.type || 'hover'
const style = computed(() => ({
  transform: `scale(${styleMap[currentType].scale})`,
  boxShadow: `0 8px 20px ${styleMap[currentType].color}40`,
  transition: 'all 0.2s cubic-bezier(0.34, 1.56, 0.64, 1)'
}))

const styleMap = {
  drop: { color: '#10b981', scale: 1.1 },
  drag: { color: '#0ea5e9', scale: 1.05 },
  hover: { color: '#3b82f6', scale: 1.02 }
}
</script>

<template>
  <div
    class="drag-drop-feedback"
    :class="[active ? 'active' : '', currentType]"
  >
    <!-- Visual feedback indicator -->
    <div class="feedback-indicator" :style="style"></div>
  </div>
</template>

<style scoped>
.drag-drop-feedback {
  position: relative;
  pointer-events: none;
  z-index: 100;
}

.feedback-indicator {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  border-radius: 50%;
  opacity: 0.6;
  animation: ripple 0.6s ease-out;
}

@keyframes ripple {
  0% {
    width: 20px;
    height: 20px;
    opacity: 0.8;
  }
  100% {
    width: 100px;
    height: 100px;
    opacity: 0;
  }
}

/* Different colors for different states */
.drop .feedback-indicator { background: #10b981; }
.drag .feedback-indicator { background: #0ea5e9; }
.hover .feedback-indicator { background: rgba(59, 130, 246, 0.3); }

/* Reduced motion preference */
@media (prefers-reduced-motion: reduce) {
  .drag-drop-feedback {
    display: none !important;
  }
}
</style>
